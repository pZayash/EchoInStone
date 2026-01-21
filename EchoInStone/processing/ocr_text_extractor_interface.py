from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str


class OCRTextExtractorInterface(ABC):
    @abstractmethod
    def extract_text(self, image) -> OCRResult:
        """Extracts text from an image frame."""
        raise NotImplementedError
