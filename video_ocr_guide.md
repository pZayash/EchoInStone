# Video OCR Optimization Guide

## Best Practices

- Prefer 720p or higher resolution video sources.
- Ensure text is high-contrast against the background.
- Avoid rapid camera motion or zoom during slide content.
- Use large fonts and avoid thin or decorative typefaces.
- Keep slides on screen for at least 2-3 seconds.

## Configuration Tips

- Use `VIDEO_PROCESSING_PROFILE = "quality"` for the most OCR-friendly sampling.
- Increase `VIDEO_MAX_SCENE_SAMPLES` if slides change slowly.
- If Tesseract struggles, enable `OCR_USE_PADDLE_FALLBACK`.

## Troubleshooting

- If OCR output is empty, confirm Tesseract is installed and reachable.
- If OCR output is noisy, try higher resolution sources and reduce compression.
