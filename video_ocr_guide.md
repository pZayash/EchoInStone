# Video OCR Optimization Guide

## Best Practices

- Prefer 720p or higher resolution video sources.
- Ensure text is high-contrast against the background.
- Avoid rapid camera motion or zoom during slide content.
- Use large fonts and avoid thin or decorative typefaces.
- Keep slides on screen for at least 2-3 seconds.

## Tesseract Installation

- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- Windows: Install from https://github.com/tesseract-ocr/tesseract and add the install folder to PATH.
- If PATH is not available, set `TESSERACT_CMD` in `EchoInStone/config.py` to the full path of `tesseract.exe`.

## Configuration Tips

- Use `VIDEO_PROCESSING_PROFILE = "quality"` for the most OCR-friendly sampling.
- Increase `VIDEO_MAX_SCENE_SAMPLES` if slides change slowly.
- If Tesseract struggles, enable `OCR_USE_PADDLE_FALLBACK`.
- To control PaddleOCR model downloads, set `MODEL_STORAGE_DIR` or `PADDLEOCR_MODEL_DIR`.

## Troubleshooting

- If OCR output is empty, confirm Tesseract is installed and reachable.
- If OCR output is noisy, try higher resolution sources and reduce compression.
- If PaddleOCR fails, check `PADDLE_HOME` points to a writable model directory.
