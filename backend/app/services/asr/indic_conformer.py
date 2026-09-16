import io
import logging
from typing import Optional, Dict, Set
import numpy as np
import torch
import torchaudio
from app.services.asr.base import BaseASRAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

# 22 official Indian languages supported by IndicConformer-600M-Multi + English
SUPPORTED_INDIC_LANGUAGES: Set[str] = {
    "as", "bn", "brx", "doi", "gu", "hi", "kn", "kok", "ks", "mai",
    "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta",
    "te", "ur", "en"
}

# Display name to ISO code normalization
LANGUAGE_NORMALIZATION: Dict[str, str] = {
    "tamil": "ta",
    "ta": "ta",
    "hindi": "hi",
    "hi": "hi",
    "telugu": "te",
    "te": "te",
    "kannada": "kn",
    "kn": "kn",
    "malayalam": "ml",
    "ml": "ml",
    "marathi": "mr",
    "mr": "mr",
    "bengali": "bn",
    "bn": "bn",
    "gujarati": "gu",
    "gu": "gu",
    "punjabi": "pa",
    "pa": "pa",
    "odia": "or",
    "or": "or",
    "assamese": "as",
    "as": "as",
    "urdu": "ur",
    "ur": "ur",
    "english": "en",
    "en": "en",
}

TARGET_SAMPLE_RATE = 16000

def preprocess_audio_for_indic_conformer(audio_bytes: bytes) -> torch.Tensor:
    """Load and preprocess audio bytes into a 16 kHz mono PyTorch tensor."""
    if not audio_bytes or len(audio_bytes) < 32:
        raise ValueError("Audio data is empty or corrupted")

    try:
        import av
        container = av.open(io.BytesIO(audio_bytes))
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=TARGET_SAMPLE_RATE)
        arrays = []
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                arrays.append(resampled.to_ndarray())
        if not arrays:
            raise ValueError("No audible frames found in audio stream")
        waveform_np = np.concatenate(arrays, axis=1).squeeze(0).astype(np.float32)
        waveform_tensor = torch.from_numpy(waveform_np).unsqueeze(0)  # Shape: (1, num_samples)
    except Exception as e:
        # Fallback to torchaudio if av container decoding is not applicable
        try:
            waveform_tensor, sr = torchaudio.load(io.BytesIO(audio_bytes))
            waveform_tensor = torch.mean(waveform_tensor, dim=0, keepdim=True)
            if sr != TARGET_SAMPLE_RATE:
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=TARGET_SAMPLE_RATE)
                waveform_tensor = resampler(waveform_tensor)
        except Exception as inner_e:
            logger.warning(f"Audio decoding failed: {e}; torchaudio fallback: {inner_e}")
            raise ValueError("Invalid or corrupted audio file format")

    if waveform_tensor.shape[-1] < int(0.2 * TARGET_SAMPLE_RATE):
        # Minimum 200ms audio required
        pad_size = int(0.2 * TARGET_SAMPLE_RATE) - waveform_tensor.shape[-1]
        waveform_tensor = torch.nn.functional.pad(waveform_tensor, (0, pad_size))

    return waveform_tensor

class IndicConformerAdapter(BaseASRAdapter):
    """Production ASR adapter powered by IndicConformer-600M-Multi (AI4Bharat).
    
    Architecture: Multilingual Conformer-based Hybrid CTC + RNNT ASR model.
    Supports 22 official Indian languages + English with configurable CTC/RNNT decoding.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        default_decoder: Optional[str] = None,
        token: Optional[str] = None
    ) -> None:
        self.model_name = model_name or settings.ASR_MODEL_NAME
        self.default_decoder = (default_decoder or settings.ASR_DECODER).lower()
        self.token = token or settings.HF_TOKEN
        self._model = None
        self._is_loaded = False

    def is_loaded(self) -> bool:
        return self._is_loaded

    def _load_model(self):
        if not self._is_loaded:
            from transformers import AutoModel
            logger.info(f"Loading IndicConformer model: {self.model_name}...")
            try:
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    token=self.token
                )
                self._is_loaded = True
                logger.info(f"IndicConformer model '{self.model_name}' loaded successfully.")
            except Exception as e:
                err_msg = str(e)
                if "401" in err_msg or "gated" in err_msg.lower() or "restricted" in err_msg.lower():
                    logger.error(
                        "IndicConformer access restricted: User must accept license on Hugging Face "
                        "and configure the HF_TOKEN environment variable."
                    )
                    raise RuntimeError(
                        "Access to ai4bharat/indic-conformer-600m-multilingual requires Hugging Face authentication. "
                        "Please configure HF_TOKEN with accepted access."
                    )
                raise RuntimeError(f"Failed to load IndicConformer model: {e}")

    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        decoder: Optional[str] = None
    ) -> str:
        if not audio_bytes:
            raise ValueError("Audio bytes are empty")

        # Normalize and validate language
        norm_lang = "en"
        if language:
            clean_lang = language.strip().lower()
            norm_lang = LANGUAGE_NORMALIZATION.get(clean_lang, clean_lang)
            if norm_lang not in SUPPORTED_INDIC_LANGUAGES:
                raise ValueError(
                    f"Unsupported language code '{language}'. Supported languages: {sorted(list(SUPPORTED_INDIC_LANGUAGES))}"
                )

        # Validate decoder
        active_decoder = (decoder or self.default_decoder).lower()
        if active_decoder not in ["ctc", "rnnt"]:
            raise ValueError(f"Invalid decoder '{active_decoder}'. Supported decoders: 'ctc', 'rnnt'.")

        self._load_model()

        # Preprocess audio to 16 kHz mono tensor
        waveform = preprocess_audio_for_indic_conformer(audio_bytes)

        # Execute model forward pass
        with torch.no_grad():
            transcript = self._model(waveform, norm_lang, active_decoder)

        if isinstance(transcript, list):
            transcript = " ".join(str(t) for t in transcript if t)
        elif not isinstance(transcript, str):
            transcript = str(transcript)

        return transcript.strip()


class MockIndicConformerAdapter(BaseASRAdapter):
    """Deterministic Mock IndicConformer adapter for testing and offline development."""

    def __init__(self, default_decoder: str = "ctc") -> None:
        self.default_decoder = default_decoder

    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        decoder: Optional[str] = None
    ) -> str:
        if not audio_bytes:
            raise ValueError("Audio bytes are empty")
        if len(audio_bytes) < 64 or b'corrupt' in audio_bytes.lower():
            raise ValueError("Audio data is corrupted or too short")

        norm_lang = "en"
        if language:
            clean_lang = language.strip().lower()
            norm_lang = LANGUAGE_NORMALIZATION.get(clean_lang, clean_lang)
            if norm_lang not in SUPPORTED_INDIC_LANGUAGES:
                raise ValueError(
                    f"Unsupported language code '{language}'. Supported languages: {sorted(list(SUPPORTED_INDIC_LANGUAGES))}"
                )

        active_decoder = (decoder or self.default_decoder).lower()
        if active_decoder not in ["ctc", "rnnt"]:
            raise ValueError(f"Invalid decoder '{active_decoder}'. Supported decoders: 'ctc', 'rnnt'.")

        # Fictional real-world natural transcriptions in native scripts
        sample_transcripts = {
            "ta": "எனக்கு உடனடியாக பாதுகாப்பான தங்குமிடம் தேவை.",
            "hi": "मुझे तुरंत सुरक्षित आश्रय और सहायता की आवश्यकता है।",
            "te": "నాకు తక్షణమే సురక్షితమైన ఆశ్రయం మరియు సహాయం కావాలి.",
            "kn": "ನನಗೆ ತಕ್ಷಣ ಸುರಕ್ಷಿತ ಆಶ್ರಯ ಮತ್ತು ಸಹಾಯ ಬೇಕಾಗಿದೆ.",
            "ml": "എനിക്ക് ഉടൻ സുരക്ഷിതമായ അഭയവും സഹായവും ആവശ്യമാണ്.",
            "mr": "मला त्वरित सुरक्षित निवारा आणि मदतीची आवश्यकता आहे.",
            "bn": "আমার অবিলম্বে নিরাপদ আশ্রয় এবং সহায়তা প্রয়োজন।",
            "en": "I need immediate safe shelter and confidential assistance."
        }

        return sample_transcripts.get(norm_lang, sample_transcripts["en"])