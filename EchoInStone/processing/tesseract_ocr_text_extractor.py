import hashlib
import inspect
import logging
import os
import shutil
import sys
from typing import Optional

import cv2
import pytesseract

from .ocr_text_extractor_interface import OCRResult, OCRTextExtractorInterface
from ..config import (
    OCR_CONFIDENCE_THRESHOLD,
    OCR_LANGUAGE,
    OCR_USE_PADDLE_FALLBACK,
    OCR_VERBOSE_LOGGING_ENABLED,
    PADDLEOCR_MODEL_DIR,
    MODEL_STORAGE_DIR,
    TESSERACT_CMD,
)
from ..config import (
    OCR_SAVE_SOURCE_IMAGES_ENABLED,
    OCR_SOURCE_IMAGES_MAX_PER_SCENE,
    OCR_SOURCE_IMAGE_FORMAT,
    PADDLEOCR_ENABLE_PIR_API,
)
from ..utils.data_saver import DataSaver

logger = logging.getLogger(__name__)


class TesseractOCRTextExtractor(OCRTextExtractorInterface):
    def __init__(self,
                 confidence_threshold: float | None = None,
                 language: str | None = None,
                 use_paddle_fallback: bool | None = None,
                 paddle_model_dir: str | None = None,
                 verbose_logging: bool | None = None,
                 data_saver: DataSaver | None = None,
                 job_id: str | None = None,
                 scene_id: int | None = None):
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else OCR_CONFIDENCE_THRESHOLD
        )
        self.language = language if language is not None else OCR_LANGUAGE
        self.use_paddle_fallback = (
            use_paddle_fallback if use_paddle_fallback is not None else OCR_USE_PADDLE_FALLBACK
        )
        self.verbose_logging = (
            verbose_logging if verbose_logging is not None else OCR_VERBOSE_LOGGING_ENABLED
        )
        self.paddle_model_dir = (
            paddle_model_dir
            if paddle_model_dir is not None
            else PADDLEOCR_MODEL_DIR
        )
        if self.paddle_model_dir is None:
            self.paddle_model_dir = os.path.join(MODEL_STORAGE_DIR, "paddleocr")
        self._paddle_ocr = None
        self._cache: dict[str, OCRResult] = {}
        self._cache_limit = 128
        self._tesseract_checked = False
        self._tesseract_available = False
        self._paddle_disabled = False
        self._paddle_disable_reason = ""
        # optional artifact saving
        self.data_saver = data_saver
        self.job_id = job_id
        self.scene_id = scene_id

    def extract_text(self, image) -> OCRResult:
        if image is None:
            return OCRResult(text="", confidence=0.0, engine="none")

        tesseract_available = self._ensure_tesseract_available()
        if not tesseract_available and not self.use_paddle_fallback:
            logger.error("OCR unavailable: Tesseract is missing and PaddleOCR fallback is disabled.")
            return OCRResult(text="", confidence=0.0, engine="none")

        cache_key = self._hash_image(image)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            text, confidence = "", 0.0
            if tesseract_available:
                text, confidence = self._extract_with_regions(image)
                if not text:
                    text, confidence = self._extract_with_tesseract(image)

            if self.use_paddle_fallback and confidence < self.confidence_threshold:
                logger.info(
                    "Tesseract confidence %.2f below threshold %.2f; trying PaddleOCR fallback.",
                    confidence,
                    self.confidence_threshold,
                )
                paddle_result = self._extract_with_paddle(image)
                if paddle_result and paddle_result.confidence >= confidence:
                    result = paddle_result
                else:
                    result = OCRResult(text=text, confidence=confidence, engine="tesseract")
            else:
                result = OCRResult(text=text if text else "", confidence=confidence, engine="tesseract")

            self._store_cache(cache_key, result)
            return result
        except Exception as exc:
            logger.warning("Tesseract OCR failed: %s", exc)
            if self.use_paddle_fallback:
                logger.info("Attempting PaddleOCR fallback after Tesseract failure.")
                paddle_result = self._extract_with_paddle(image)
                if paddle_result:
                    self._store_cache(cache_key, paddle_result)
                    return paddle_result
            result = OCRResult(text="", confidence=0.0, engine="tesseract")
            self._store_cache(cache_key, result)
            return result

    def _ensure_tesseract_available(self) -> bool:
        if self._tesseract_checked:
            return self._tesseract_available

        self._tesseract_checked = True
        cmd_path = self._resolve_tesseract_cmd()
        if cmd_path:
            if os.path.isfile(cmd_path):
                pytesseract.pytesseract.tesseract_cmd = cmd_path
            else:
                logger.error("Tesseract command not found at %s.", cmd_path)
                self._tesseract_available = False
                return self._tesseract_available
        else:
            logger.error(
                "Tesseract OCR not found in PATH or common locations. %s",
                self._tesseract_install_hint(),
            )
            self._tesseract_available = False
            return self._tesseract_available

        try:
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception as exc:
            logger.error(
                "Tesseract OCR appears misconfigured: %s. %s",
                exc,
                self._tesseract_install_hint(),
            )
            self._tesseract_available = False
        return self._tesseract_available

    def _resolve_tesseract_cmd(self) -> str | None:
        if TESSERACT_CMD:
            return TESSERACT_CMD

        which_cmd = shutil.which("tesseract")
        if which_cmd:
            return which_cmd

        platform = sys.platform.lower()
        if platform.startswith("win"):
            candidates = [
                os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR", "tesseract.exe"),
                os.path.join(
                    os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR", "tesseract.exe"
                ),
                os.path.join(os.environ.get("LocalAppData", ""), "Tesseract-OCR", "tesseract.exe"),
            ]
            for candidate in candidates:
                if candidate and os.path.isfile(candidate):
                    return candidate
        return None

    @staticmethod
    def _tesseract_install_hint() -> str:
        platform = sys.platform.lower()
        if platform.startswith("win"):
            return "Install Tesseract from https://github.com/tesseract-ocr/tesseract and add it to PATH."
        if platform.startswith("darwin"):
            return "Install Tesseract with `brew install tesseract`."
        return "Install Tesseract with your package manager (e.g., `sudo apt install tesseract-ocr`)."

    def _extract_with_paddle(self, image) -> Optional[OCRResult]:
        if self._paddle_disabled:
            return None
        try:
            if self._paddle_ocr is None:
                from paddleocr import PaddleOCR

                self._configure_paddle_home()
                self._paddle_ocr = self._init_paddle_ocr(PaddleOCR)

            result = self._call_paddle_ocr(image)
            if not result:
                if self.verbose_logging:
                    logger.info("PaddleOCR returned empty result list.")
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
            if self.verbose_logging:
                logger.info(
                    "PaddleOCR extracted %d lines with confidence %.2f.",
                    len(texts),
                    confidence,
                )
            # optionally save artifact
            try:
                if OCR_SAVE_SOURCE_IMAGES_ENABLED and self.data_saver is not None:
                    self._maybe_save_artifact(
                        image=image,
                        engine="paddleocr",
                        variant="default",
                        preprocessing=[],
                        ocr_confidence=confidence,
                        text_excerpt=(text[:200] if text else ""),
                    )
            except Exception:
                logger.debug("Failed to save paddleocr image artifact.")
            return OCRResult(text=text, confidence=confidence, engine="paddleocr")
        except Exception as exc:
            self._paddle_disabled = True
            self._paddle_disable_reason = str(exc)
            logger.warning("PaddleOCR fallback failed: %s", exc)
            return None

    def _init_paddle_ocr(self, paddle_ocr_cls) -> object:
        kwargs = {"lang": self.language}
        try:
            signature = inspect.signature(paddle_ocr_cls.__init__)
            if "use_angle_cls" in signature.parameters:
                kwargs["use_angle_cls"] = True
        except (TypeError, ValueError):
            logger.debug("Unable to inspect PaddleOCR signature; using default kwargs.")
        try:
            return paddle_ocr_cls(**kwargs)
        except TypeError as exc:
            logger.warning("PaddleOCR init with %s failed (%s); retrying with defaults.", kwargs, exc)
            return paddle_ocr_cls()

    def _call_paddle_ocr(self, image):
        kwargs = {}
        try:
            signature = inspect.signature(self._paddle_ocr.ocr)
            if "cls" in signature.parameters:
                kwargs["cls"] = True
            else:
                logger.info("PaddleOCR.ocr does not accept 'cls'; running without it.")
        except (TypeError, ValueError):
            logger.debug("Unable to inspect PaddleOCR.ocr signature; running without 'cls'.")
        return self._paddle_ocr.ocr(image, **kwargs)

    def _configure_paddle_home(self) -> None:
        if not self.paddle_model_dir:
            return
        model_dir = os.path.abspath(self.paddle_model_dir)
        os.makedirs(model_dir, exist_ok=True)
        os.environ.setdefault("PADDLE_HOME", model_dir)
        # Work around PaddleOCR PIR incompatibilities for some ops.
        os.environ.setdefault(
            "FLAGS_enable_pir_api",
            "1" if PADDLEOCR_ENABLE_PIR_API else "0",
        )

    def _extract_with_regions(self, image) -> tuple[str, float]:
        regions = self._detect_text_regions(image)
        if not regions:
            if self.verbose_logging:
                logger.info("No text regions detected for OCR.")
            return "", 0.0
        if self.verbose_logging:
            logger.info("Detected %d text regions for OCR.", len(regions))

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
        text, confidence = self._run_tesseract(image, config="--oem 3 --psm 6")
        if self.verbose_logging:
            logger.info("Tesseract base OCR confidence %.2f (len=%d).", confidence, len(text))
        if text and confidence >= self.confidence_threshold:
            return text, confidence

        enhanced = self._preprocess_for_ocr(image)
        if enhanced is not None:
            enhanced_text, enhanced_confidence = self._run_tesseract(
                enhanced, config="--oem 3 --psm 6"
            )
            if self.verbose_logging:
                logger.info(
                    "Tesseract preprocessed OCR confidence %.2f (len=%d).",
                    enhanced_confidence,
                    len(enhanced_text),
                )
            if enhanced_text or enhanced_confidence > confidence:
                text, confidence = enhanced_text, enhanced_confidence

        if confidence >= self.confidence_threshold and text:
            return text, confidence

        best_text, best_confidence = text, confidence
        retry_candidates = [image, enhanced] if enhanced is not None else [image]
        for candidate in retry_candidates:
            retry_text, retry_confidence = self._run_tesseract_variants(candidate)
            if retry_confidence > best_confidence:
                best_text, best_confidence = retry_text, retry_confidence

        if self.verbose_logging and best_confidence < self.confidence_threshold:
            logger.info(
                "Tesseract OCR confidence %.2f below threshold %.2f after retries.",
                best_confidence,
                self.confidence_threshold,
            )
        return best_text, best_confidence

    def _run_tesseract(self, image, config: str) -> tuple[str, float]:
        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=config,
            output_type=pytesseract.Output.DICT,
        )
        text_parts = [t.strip() for t in data.get("text", []) if t and t.strip()]
        confidences = [
            float(conf)
            for conf in data.get("conf", [])
            if conf not in ("-1", None, "")
        ]
        text = " ".join(text_parts)
        confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
        # optionally save artifact of the tesseract input
        try:
            if OCR_SAVE_SOURCE_IMAGES_ENABLED and self.data_saver is not None:
                self._maybe_save_artifact(
                    image=image,
                    engine="tesseract",
                    variant=config.replace(" ", "_"),
                    preprocessing=[],
                    ocr_confidence=confidence,
                    text_excerpt=(text[:200] if text else ""),
                )
        except Exception:
            logger.debug("Failed to save tesseract image artifact.")
        return text, confidence

    def _run_tesseract_variants(self, image) -> tuple[str, float]:
        configs = [
            "--oem 3 --psm 3",
            "--oem 3 --psm 4",
            "--oem 3 --psm 6",
            "--oem 3 --psm 11",
            "--oem 1 --psm 6",
        ]
        best_text, best_confidence = "", 0.0
        for config in configs:
            variant_text, variant_confidence = self._run_tesseract(image, config=config)
            if self.verbose_logging:
                logger.info(
                    "Tesseract variant %s confidence %.2f (len=%d).",
                    config,
                    variant_confidence,
                    len(variant_text),
                )
            if variant_confidence > best_confidence:
                best_text, best_confidence = variant_text, variant_confidence
        return best_text, best_confidence

    @staticmethod
    def _preprocess_for_ocr(image):
        if image is None:
            return None
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return thresh
        except Exception:
            return None

    def _maybe_save_artifact(
        self,
        image,
        engine: str,
        variant: str,
        preprocessing: list,
        ocr_confidence: float | None = None,
        text_excerpt: str | None = None,
    ) -> None:
        """
        Helper to persist OCR source images and update manifest when configured.
        """
        try:
            if not OCR_SAVE_SOURCE_IMAGES_ENABLED or self.data_saver is None:
                return
            # delegate to DataSaver
            self.data_saver.save_image_artifact(
                job_id=self.job_id,
                scene_id=self.scene_id,
                image=image,
                engine=engine,
                variant=variant,
                preprocessing=preprocessing,
                ocr_confidence=ocr_confidence,
                text_excerpt=text_excerpt,
                max_per_scene=OCR_SOURCE_IMAGES_MAX_PER_SCENE,
                image_format=OCR_SOURCE_IMAGE_FORMAT,
            )
        except Exception as exc:
            logger.debug("Error saving OCR artifact: %s", exc)

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
