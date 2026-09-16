from abc import ABC, abstractmethod
from app.schemas.stress import StressDetectionResult

class BaseStressAdapter(ABC):
    """Abstract base adapter for Dreaddit-based stress detection models."""

    @abstractmethod
    def is_loaded(self) -> bool:
        """Returns True if model weights are loaded in memory."""
        pass

    @abstractmethod
    def warmup(self) -> None:
        """Explicitly preloads model weights into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unloads model weights to free RAM/VRAM."""
        pass

    @abstractmethod
    def analyze(self, text: str) -> StressDetectionResult:
        """Analyzes text and returns structured StressDetectionResult."""
        pass
