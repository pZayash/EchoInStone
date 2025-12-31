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