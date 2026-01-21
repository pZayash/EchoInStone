import hashlib
import logging
from typing import Optional

import cv2
import pytesseract

from .ocr_text_extractor_interface import OCRResult, OCRTextExtractorInterface
from ..config import OCR_CONFIDENCE_THRESHOLD, OCR_LANGUAGE, OCR_USE_PADDLE_FALLBACK, TESSERACT_CMD

logger = logging.getLogger(__name__)


class TesseractOCRTextExtractor(OCRTextExtractorInterface):
    def __init__(self,
                 confidence_threshold: float | None = None,
                 language: str | None = None,
                 use_paddle_fallback: bool | None = None):
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else OCR_CONFIDENCE_THRESHOLD
        )
        self.language = language if language is not None else OCR_LANGUAGE
        self.use_paddle_fallback = (
            use_paddle_fallback if use_paddle_fallback is not None else OCR_USE_PADDLE_FALLBACK
        )
        self._paddle_ocr = None
        self._cache: dict[str, OCRResult] = {}
        self._cache_limit = 128

    def extract_text(self, image) -> OCRResult:
        if image is None:
            return OCRResult(text="", confidence=0.0, engine="none")

        cache_key = self._hash_image(image)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        if TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

        try:
            text, confidence = self._extract_with_regions(image)
            if not text:
                text, confidence = self._extract_with_tesseract(image)

            if self.use_paddle_fallback and confidence < self.confidence_threshold:
                paddle_result = self._extract_with_paddle(image)
                if paddle_result and paddle_result.confidence >= confidence:
                    result = paddle_result
                else:
                    result = OCRResult(text=text, confidence=confidence, engine="tesseract")
            else:
                if confidence < self.confidence_threshold:
                    result = OCRResult(text="", confidence=confidence, engine="tesseract")
                else:
                    result = OCRResult(text=text, confidence=confidence, engine="tesseract")

            self._store_cache(cache_key, result)
            return result
        except Exception as exc:
            logger.warning(f"Tesseract OCR failed: {exc}")
            if self.use_paddle_fallback:
                paddle_result = self._extract_with_paddle(image)
                if paddle_result:
                    self._store_cache(cache_key, paddle_result)
                    return paddle_result
            result = OCRResult(text="", confidence=0.0, engine="tesseract")
            self._store_cache(cache_key, result)
            return result

    def _extract_with_paddle(self, image) -> Optional[OCRResult]:
        try:
            if self._paddle_ocr is None:
                from paddleocr import PaddleOCR

                self._paddle_ocr = PaddleOCR(use_angle_cls=True, lang=self.language)

            result = self._paddle_ocr.ocr(image, cls=True)
            if not result:
                return OCRResult(text="", confidence=0.0, engine="paddleocr")

            lines = result[0]
            texts = []
            confidences = []
            for line in lines:
                if len(line) >= 2 and isinstance(line[1], (list, tuple)):
                    text, score = line[1]
                    if text:
                        texts.append(text)
                        confidences.append(float(score))

            text = " ".join(texts)
            confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
            return OCRResult(text=text, confidence=confidence, engine="paddleocr")
        except Exception as exc:
            logger.warning(f"PaddleOCR fallback failed: {exc}")
            return None

    def _extract_with_regions(self, image) -> tuple[str, float]:
        regions = self._detect_text_regions(image)
        if not regions:
            return "", 0.0

        texts = []
        confidences = []
        for region in regions:
            region_text, region_conf = self._extract_with_tesseract(region)
            if region_text:
                texts.append(region_text)
                confidences.append(region_conf)

        if not texts:
            return "", 0.0
        combined_text = "\n".join(texts)
        combined_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
        return combined_text, combined_confidence

    def _extract_with_tesseract(self, image) -> tuple[str, float]:
        data = pytesseract.image_to_data(
            image, lang=self.language, output_type=pytesseract.Output.DICT
        )
        text_parts = [t.strip() for t in data.get("text", []) if t and t.strip()]
        confidences = [
            float(conf)
            for conf in data.get("conf", [])
            if conf not in ("-1", None, "")
        ]
        text = " ".join(text_parts)
        confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
        return text, confidence

    @staticmethod
    def _detect_text_regions(image) -> list:
        if image is None:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            15,
            10,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = gray.shape
        min_area = max(100, int(width * height * 0.0005))
        max_area = int(width * height * 0.4)
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area < min_area or area > max_area:
                continue
            if w < 20 or h < 20:
                continue
            aspect = w / float(h)
            if aspect > 20 or aspect < 0.2:
                continue
            regions.append((y, x, image[y:y + h, x:x + w]))

        regions.sort(key=lambda item: (item[0], item[1]))
        return [roi for _, _, roi in regions]

    @staticmethod
    def _hash_image(image) -> str:
        try:
            payload = image.tobytes()
            shape = f"{image.shape}".encode("utf-8")
        except Exception:
            payload = str(image).encode("utf-8")
            shape = b""
        return hashlib.sha256(shape + payload).hexdigest()

    def _store_cache(self, key: str, result: OCRResult) -> None:
        if key in self._cache:
            return
        if len(self._cache) >= self._cache_limit:
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key, None)
        self._cache[key] = result
