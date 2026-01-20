# Project Context

## Purpose

EchoInStone is a comprehensive audio processing tool designed to transcribe, diarize, and align speaker segments from audio files with a focus on achieving the most accurate and faithful transcription possible. It supports various audio sources including YouTube videos and podcasts, providing a flexible pipeline for processing audio data, prioritizing precision and reliability over speed.

**Core Goals:**
- Extract accurate text transcriptions from audio using state-of-the-art ASR models
- Identify and separate different speakers in audio files
- Align transcribed text with corresponding audio segments
- Support multiple audio input sources (YouTube, podcasts, direct files)
- Provide extensible and modular architecture for future enhancements

## Tech Stack

### Core Technologies
- **Python 3.12+** - Primary programming language
- **Poetry** - Dependency management and packaging
- **PyTorch 2.7.0** - Machine learning framework (Intel XPU optimized)
- **Transformers 4.50.0** - Hugging Face transformers for ML models

### Audio Processing Libraries
- **OpenAI Whisper Large v3 Turbo** - Automatic speech recognition
  - Model size: ~1.5GB (quantized)
  - System requirements: 8GB+ RAM, GPU recommended (Intel XPU/4GB+ VRAM)
  - Accuracy optimized for English and multilingual content
- **Pyannote Audio 3.3.2** - Speaker diarization
  - Model size: ~25MB
  - System requirements: 4GB+ RAM, GPU acceleration supported
  - Requires Hugging Face authentication token
- **PyDub 0.25.1** - Audio file manipulation
- **Accelerate 1.3.0** - Model acceleration

### Data Processing
- **Requests 2.32.3** - HTTP client for API calls
- **Feedparser 6.0.11** - RSS/podcast feed parsing
- **PyTubeFix 8.12.1** - YouTube video/audio downloading

### Development & Testing
- **pytest-bdd 8.1.0** - Behavior-driven development testing
- **pytest-cov 6.0.0** - Test coverage reporting
- **ffmpeg** - Audio/video processing (system dependency)

### External Services
- **Hugging Face Hub** - Model hosting and authentication
- **PyTorch XPU** - Intel Arc GPU acceleration support

## Project Conventions

### Code Style

**Python Standards:**
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black compatible)
- Use descriptive variable and function names
- Prefer snake_case for variables and functions
- Use PascalCase for class names

**Import Organization:**
```python
# Standard library imports
import os
import json

# Third-party imports
import requests
from transformers import pipeline

# Local imports
from EchoInStone.capture import AudioDownloader
```

### Architecture Patterns

**Modular Architecture:**
- **Separation of Concerns:** Code organized into distinct modules (capture, processing, utils)
- **Interface Pattern:** Abstract base classes define contracts (e.g., `AudioTranscriberInterface`)
- **Factory Pattern:** `DownloaderFactory` for dynamic downloader selection
- **Orchestrator Pattern:** `AudioProcessingOrchestrator` coordinates processing pipeline

**Design Principles:**
- **Single Responsibility:** Each class has one primary responsibility
- **Dependency Injection:** Interfaces allow for easy testing and extension
- **Composition over Inheritance:** Prefer composition for complex behaviors
- **Error Handling:** Comprehensive exception handling with logging

**Module Structure:**
```
EchoInStone/
├── capture/          # Audio acquisition and downloading
├── processing/       # ML model processing (ASR, diarization, alignment)
├── utils/           # Shared utilities (logging, data saving, timing)
├── config.py        # Configuration management
└── main.py          # Entry point
```

### Testing Strategy

**BDD (Behavior-Driven Development):**
- Use pytest-bdd for behavior-driven tests
- Feature files describe user-facing scenarios
- Step definitions implement test logic
- Tests validate end-to-end functionality

**Test Coverage:**
- Unit tests for individual components
- Integration tests for complete workflows
- BDD tests for user scenarios
- Coverage reporting with pytest-cov (HTML and XML reports)

**Test Categories:**
- **Unit Tests:** `tests/` directory - technical implementation verification
- **BDD Tests:** `features/` directory - behavioral scenario validation
- **Coverage:** Minimum 80% code coverage target

## Domain Context

**Audio Processing Domain Knowledge:**

**Automatic Speech Recognition (ASR):**

- Converts audio waveforms to text transcripts
- Whisper model handles multiple languages and accents
- Requires careful audio preprocessing for optimal results

**Speaker Diarization:**
- Identifies "who spoke when" in audio
- Pyannote model segments audio by speaker
- Critical for multi-speaker content analysis

**Audio Alignment:**
- Maps transcribed text to specific audio timestamps
- Custom algorithm ensures temporal accuracy
- Essential for subtitle generation and audio-text synchronization

**Audio Sources:**
- **YouTube:** Video platform content extraction
- **Podcasts:** RSS feed processing and episode downloading
- **Direct URLs:** HTTP-accessible audio files
- **Local Files:** Direct file system access

**Performance Considerations:**
- ML models are computationally intensive
- GPU acceleration (Intel XPU) for faster processing
- Memory optimization for large audio files
- Trade-off between accuracy and processing speed

## Important Constraints

**Technical Constraints:**
- Python 3.12+ requirement for modern language features
- GPU memory limitations for large audio files
- Network bandwidth for downloading large files
- Hugging Face API rate limits and authentication

**Model Constraints:**
- Whisper model requires significant computational resources
- Pyannote diarization model needs authentication token
- Model outputs may vary with audio quality
- GPU acceleration may not be available on all systems

**Data Constraints:**
- Audio file size limits based on available RAM
- Network timeouts for large downloads
- Supported audio formats: MP3, WAV, M4A, FLAC, OGG, WebM
- Character encoding for international content

## External Dependencies

**Critical External Services:**
- **Hugging Face Hub:** Model hosting and authentication
  - Token required for Pyannote diarization model
  - Rate limits apply to API calls
  - Models may change or be deprecated

**Intel XPU Support:**
- PyTorch XPU wheels for Intel Arc GPU acceleration
- Requires compatible hardware and drivers
- Fallback to CPU processing if GPU unavailable

**Audio Processing:**
- ffmpeg system dependency for audio format conversion
- System PATH must include ffmpeg executable
- Version compatibility important for audio codecs

**Network Dependencies:**
- YouTube API for video information
- Podcast RSS feed accessibility
- Direct URL accessibility for audio files
- Proxy/firewall considerations for enterprise environments
