import time
import logging
from typing import List, Optional
from app.services.emotion.text_base import BaseTextEmotionAdapter
from app.schemas.emotion import TextEmotionResult, EmotionScore
from app.core.config import settings
from app.core.telemetry import resolve_device, get_system_resources

logger = logging.getLogger(__name__)

# Full 28-class GoEmotions taxonomy from Google / SamLowe/roberta-base-go_emotions
GO_EMOTIONS_TAXONOMY = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral"
]

class GoEmotionsAdapter(BaseTextEmotionAdapter):
    """Production Text Emotion Recognition adapter using RoBERTa fine-tuned on GoEmotions."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_name = model_name or settings.TEXT_EMOTION_MODEL
        self.device = resolve_device(device or settings.EMOTION_DEVICE)
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        logger.info(f"Initialized GoEmotionsAdapter on device: {self.device}")

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        """Pre-load model weights into memory once."""
        self._load()

    def unload(self) -> None:
        """Free memory if needed."""
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _load(self) -> None:
        if not self._is_loaded:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            logger.info(f"Loading GoEmotions TER model: {self.model_name} on {self.device}...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            self._is_loaded = True
            res = get_system_resources()
            logger.info(f"GoEmotions model loaded successfully. System RAM RSS: {res.get('ram_rss_mb')} MB")

    def analyze(self, text: str) -> TextEmotionResult:
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        self._load()
        import torch

        start_time = time.perf_counter()

        # Tokenize with truncation to max 256 tokens for bounded inference latency
        clean_text = text.strip()
        inputs = self._tokenizer(
            clean_text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self._model(**inputs).logits
            scores = torch.sigmoid(logits)[0].cpu().numpy()

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        id2label = getattr(self._model.config, "id2label", None) or {
            str(i): GO_EMOTIONS_TAXONOMY[i] for i in range(len(GO_EMOTIONS_TAXONOMY))
        }

        emotion_scores: List[EmotionScore] = []
        for idx, score in enumerate(scores):
            lbl = id2label.get(str(idx), id2label.get(idx, f"label_{idx}"))
            emotion_scores.append(EmotionScore(
                label=str(lbl).lower(),
                score=float(round(float(score), 4))
            ))

        # Sort highest score first
        emotion_scores.sort(key=lambda x: x.score, reverse=True)
        top_lbl = emotion_scores[0].label if emotion_scores else "neutral"

        return TextEmotionResult(
            top_emotion=top_lbl,
            emotions=emotion_scores,
            model_version=self.model_name,
            duration_ms=latency_ms,
            device=self.device
        )

class MockTextEmotionAdapter(BaseTextEmotionAdapter):
    """Deterministic Mock TER adapter for testing."""

    def __init__(self, device: str = "cpu") -> None:
        self.device = device

    def is_loaded(self) -> bool:
        return True

    def warmup(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def analyze(self, text: str) -> TextEmotionResult:
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        lower = text.lower()
        top = "neutral"
        high_score = 0.85

        if any(w in lower for w in ["scared", "fear", "threat", "afraid", "danger", "பயப்படுகிறேன்", "डर"]):
            top = "fear"
        elif any(w in lower for w in ["sad", "grief", "crying", "hurt", "pain", "வருத்தம்", "दुःख"]):
            top = "sadness"
        elif any(w in lower for w in ["angry", "mad", "hate", "rage", "கோபம்", "गुस्सा"]):
            top = "anger"
        elif any(w in lower for w in ["shelter", "help", "please", "urgent"]):
            top = "nervousness"

        emotions: List[EmotionScore] = [
            EmotionScore(label=top, score=high_score),
            EmotionScore(label="caring", score=0.25),
            EmotionScore(label="neutral", score=0.15),
        ]

        return TextEmotionResult(
            top_emotion=top,
            emotions=emotions,
            model_version="mock-roberta-goemotions",
            duration_ms=1.5,
            device=self.device
        )
