#!/usr/bin/env bash

set -euo pipefail

# Example: analyze a YouTube video with scene detection + OCR
poetry run python main.py "https://www.youtube.com/watch?v=plZRCMx_Jd8" \
  --enable_video_analysis \
  --scene_output scene_analysis.json

# Example: analyze a direct MP4 file URL
poetry run python main.py "https://example.com/demo.mp4" \
  --enable_video_analysis \
  --scene_output scene_analysis.json

# Example: analyze a local video file
poetry run python main.py "/path/to/local/video.mp4" \
  --enable_video_analysis \
  --scene_output scene_analysis.json
