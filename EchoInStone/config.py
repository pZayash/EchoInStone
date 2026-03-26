# config.py

# Authentication token for accessing Hugging Face models
# To obtain a token, follow these steps:
# 1. Go to https://huggingface.co/settings/tokens
# 2. Click on "New token"
# 3. Copy the generated token and paste it below
# Note: Keep this token secure and do not share it publicly
HUGGING_FACE_TOKEN = "your_token_here"

# Segment splitting configuration
# Controls how consecutive segments of the same speaker are merged/split
SEGMENT_TARGET_DURATION = 30    # Target segment duration in seconds
SEGMENT_MIN_DURATION = 20       # Minimum segment duration in seconds
SEGMENT_MAX_DURATION = 60       # Maximum segment duration in seconds
SEGMENT_PAUSE_THRESHOLD = 2.0   # Pause threshold for splitting in seconds

# Video scene analysis configuration
# Disabled by default — scene detection needs further refinement before practical use
VIDEO_ANALYSIS_ENABLED = False
VIDEO_FRAME_SAMPLING_SECONDS = 1.0
VIDEO_SCENE_DETECTOR_THRESHOLD = 27.0
VIDEO_MAX_WORKERS = 2
VIDEO_ENABLE_PARALLEL = True
VIDEO_MAX_SCENE_SAMPLES = 5
VIDEO_PROCESSING_PROFILE = "balanced"
VIDEO_PROFILE_SETTINGS = {
    "fast": {
        "frame_sampling_seconds": 2.0,
        "max_workers": 4,
        "enable_parallel": True,
        "max_scene_samples": 3,
    },
    "balanced": {
        "frame_sampling_seconds": 1.0,
        "max_workers": 2,
        "enable_parallel": True,
        "max_scene_samples": 5,
    },
    "quality": {
        "frame_sampling_seconds": 0.5,
        "max_workers": 2,
        "enable_parallel": False,
        "max_scene_samples": 8,
    },
}

# OCR configuration
OCR_LANGUAGE = "en"
OCR_CONFIDENCE_THRESHOLD = 40.0
OCR_USE_PADDLE_FALLBACK = True
OCR_VERBOSE_LOGGING_ENABLED = True
TESSERACT_CMD = None
MODEL_STORAGE_DIR = "models"
PADDLEOCR_MODEL_DIR = None
# Save OCR source images and artifacts (for debugging/QA). Can be disabled for privacy.
OCR_SAVE_SOURCE_IMAGES_ENABLED = True
OCR_SOURCE_IMAGES_MAX_PER_SCENE = 10
OCR_SOURCE_IMAGE_FORMAT = "png"
# PaddleOCR/PaddlePaddle runtime flags
PADDLEOCR_ENABLE_PIR_API = False

# Transcriber backend configuration
TRANSCRIBER_BACKEND = "auto"  # "auto", "transformers", "faster-whisper"
FASTER_WHISPER_MODEL_SIZE = "large-v3-turbo"
FASTER_WHISPER_COMPUTE_TYPE = "auto"
WHISPER_BATCH_SIZE = 24

# Subtitle-first configuration
SUBTITLE_FIRST_ENABLED = True
SUBTITLE_PREFERRED_LANGUAGES = ["en", "ru"]
SUBTITLE_PREFER_MANUAL = True