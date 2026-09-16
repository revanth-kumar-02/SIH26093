import time
import logging
from typing import Optional, Dict
from app.services.stress.base import BaseStressAdapter
from app.schemas.stress import StressDetectionResult
from app.core.config import settings
from app.core.telemetry import resolve_device, get_system_resources

logger = logging.getLogger(__name__)

# Documented Dreaddit binary label mapping:
# In Dreaddit (EMNLP 2019) benchmark dataset:
# Class 0 = Not Stressed
# Class 1 = Stressed
DREADDIT_LABELS = {0: "not_stressed", 1: "stressed"}

class MentalBertDreadditAdapter(BaseStressAdapter):
    """Production Stress Detection adapter using MentalBERT fine-tuned on the Dreaddit dataset.
    
    Model checkpoint: jtvallente/mentalbert_dreaddit_best
    Dataset: Dreaddit (EMNLP 2019) Reddit stress dataset
    Domain Disclaimer: Dreaddit-trained stress detection is NOT clinically validated
    and does not represent trauma diagnosis, suicidal risk, or danger classification.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_name = model_name or settings.STRESS_MODEL_NAME
        self.device = resolve_device(device or settings.STRESS_DEVICE)
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        logger.info(f"Initialized MentalBertDreadditAdapter for {self.model_name} on {self.device}")

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        """Preload model weights into memory."""
        self._load()

    def unload(self) -> None:
        """Unload model to free RAM/VRAM."""
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
            start = time.perf_counter()
            logger.info(f"Loading Dreaddit MentalBERT stress model: {self.model_name} on {self.device}...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            self._is_loaded = True
            load_time = round((time.perf_counter() - start) * 1000.0, 2)
            res = get_system_resources()
            logger.info(f"Dreaddit model loaded in {load_time}ms. System RAM RSS: {res.get('ram_rss_mb')} MB")

    def analyze(self, text: str) -> StressDetectionResult:
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        self._load()
        import torch
        import numpy as np

        start_time = time.perf_counter()
        clean_text = text.strip()

        # Tokenize with max length 256 for bounded inference latency
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
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        p_not_stressed = float(round(float(probs[0]), 4))
        p_stressed = float(round(float(probs[1]), 4))

        pred_idx = int(np.argmax(probs))
        pred_label = DREADDIT_LABELS.get(pred_idx, "stressed" if pred_idx == 1 else "not_stressed")
        pred_score = p_stressed if pred_idx == 1 else p_not_stressed

        probabilities: Dict[str, float] = {
            "not_stressed": p_not_stressed,
            "stressed": p_stressed
        }

        return StressDetectionResult(
            label=pred_label,
            score=pred_score,
            probabilities=probabilities,
            model_version=self.model_name,
            duration_ms=latency_ms,
            device=self.device
        )

class MockStressAdapter(BaseStressAdapter):
    """Deterministic Mock Stress adapter for fast offline testing."""

    def __init__(self, device: str = "cpu") -> None:
        self.device = device
        self._is_loaded = True

    def is_loaded(self) -> bool:
        return True

    def warmup(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def analyze(self, text: str) -> StressDetectionResult:
        if not text or not text.strip():
            raise ValueError("Text input is empty")

        lower = text.lower()
        stress_keywords = [
            "threat", "scared", "fear", "kill", "die", "hurt", "terror",
            "danger", "panic", "stalk", "abuse", "trauma", "attack",
            "nightmare", "anxious", "anxiety", "shaking", "suffocating",
            "unsafe", "terrified", "help me"
        ]

        if any(w in lower for w in stress_keywords):
            label = "stressed"
            score = 0.942
            probabilities = {"not_stressed": 0.058, "stressed": 0.942}
        else:
            label = "not_stressed"
            score = 0.915
            probabilities = {"not_stressed": 0.915, "stressed": 0.085}

        return StressDetectionResult(
            label=label,
            score=score,
            probabilities=probabilities,
            model_version="mock-mentalbert-dreaddit",
            duration_ms=1.2,
            device=self.device
        )
