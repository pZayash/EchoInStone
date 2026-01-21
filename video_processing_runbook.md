# Video Processing Runbook

## Common Failures

### Tesseract OCR not found
- Symptom: OCR results are empty or logs indicate missing Tesseract.
- Fix: Install Tesseract and ensure it is available on the PATH.
- Optional: Set `TESSERACT_CMD` in `EchoInStone/config.py`.

### Scene detection returns zero scenes
- Symptom: Scene analysis output is empty or contains a single zero-length scene.
- Fix: Verify the input is a valid video file and playable by `ffmpeg` or a media player.
- Check: Ensure `scenedetect` and `opencv-python` are installed.

### Video download fails
- Symptom: Logs show a download error or `video_path` is `None`.
- Fix: Confirm the URL is reachable and the video format is supported (`.mp4`, `.webm`, `.mkv`, `.avi`, `.mov`).

### OCR confidence is too low
- Symptom: `extracted_text` is empty with low confidence values.
- Fix: Use the `quality` profile or increase resolution of the source video.

## Diagnostic Tips

- Enable debug logging to capture OCR and scene detection diagnostics.
- Run with a local video file to reduce network variability.
- Compare `scene_analysis.json` with `speaker_transcriptions.json` for alignment checks.
