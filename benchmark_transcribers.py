"""Benchmark tool for comparing transcription backends.

Usage:
    python benchmark_transcribers.py <audio_or_video_file> [--short]
"""

import argparse
import os
import sys
import tempfile
import time
import tracemalloc
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio from a video file to a temporary WAV file."""
    from pydub import AudioSegment

    ext = os.path.splitext(video_path)[1].lower()
    if ext in (".mp4", ".webm", ".mkv", ".avi", ".mov"):
        logger.info(f"Extracting audio from video: {video_path}")
        audio = AudioSegment.from_file(video_path)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(tmp.name, format="wav")
        logger.info(f"Audio extracted to: {tmp.name}")
        return tmp.name
    return video_path


def truncate_audio(audio_path: str, max_seconds: int = 60) -> str:
    """Truncate audio to the first max_seconds seconds."""
    from pydub import AudioSegment

    logger.info(f"Truncating audio to first {max_seconds} seconds")
    audio = AudioSegment.from_file(audio_path)
    truncated = audio[: max_seconds * 1000]
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    truncated.export(tmp.name, format="wav")
    return tmp.name


def benchmark_transformers(audio_path: str) -> dict | None:
    """Benchmark the transformers (WhisperAudioTranscriber) backend."""
    try:
        from EchoInStone.processing import WhisperAudioTranscriber
    except Exception as e:
        logger.warning(f"Transformers backend not available: {e}")
        return None

    result = {}

    # Model load time
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        transcriber = WhisperAudioTranscriber()
    except Exception as e:
        logger.warning(f"Failed to load transformers backend: {e}")
        tracemalloc.stop()
        return None
    result["model_load_time"] = time.perf_counter() - t0

    # Transcription time
    t0 = time.perf_counter()
    text, timestamps = transcriber.transcribe(audio_path)
    result["transcription_time"] = time.perf_counter() - t0

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result["peak_memory_mb"] = peak / (1024 * 1024)
    result["text_length"] = len(text) if text else 0
    result["num_chunks"] = len(timestamps) if timestamps else 0

    return result


def benchmark_faster_whisper(audio_path: str) -> dict | None:
    """Benchmark the faster-whisper backend."""
    try:
        from EchoInStone.processing import FasterWhisperAudioTranscriber

        if FasterWhisperAudioTranscriber is None:
            raise ImportError("FasterWhisperAudioTranscriber is None")
    except Exception as e:
        logger.warning(f"Faster-whisper backend not available: {e}")
        return None

    result = {}

    # Model load time
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        transcriber = FasterWhisperAudioTranscriber()
    except Exception as e:
        logger.warning(f"Failed to load faster-whisper backend: {e}")
        tracemalloc.stop()
        return None
    result["model_load_time"] = time.perf_counter() - t0

    # Transcription time
    t0 = time.perf_counter()
    text, timestamps = transcriber.transcribe(audio_path)
    result["transcription_time"] = time.perf_counter() - t0

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result["peak_memory_mb"] = peak / (1024 * 1024)
    result["text_length"] = len(text) if text else 0
    result["num_chunks"] = len(timestamps) if timestamps else 0

    return result


def format_time(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.1f}s"


def print_results(results: dict[str, dict | None]):
    """Print a comparison table."""
    backends = [name for name, r in results.items() if r is not None]
    if not backends:
        print("\nNo backends were available for benchmarking.")
        return

    print("\n" + "=" * 60)
    print("TRANSCRIPTION BENCHMARK RESULTS")
    print("=" * 60)

    header = f"{'Metric':<25}"
    for name in backends:
        header += f" {name:>15}"
    print(header)
    print("-" * 60)

    metrics = [
        ("Model load time", "model_load_time", format_time),
        ("Transcription time", "transcription_time", format_time),
        ("Peak memory (MB)", "peak_memory_mb", lambda x: f"{x:.1f}"),
        ("Output text length", "text_length", lambda x: str(int(x))),
        ("Timestamp chunks", "num_chunks", lambda x: str(int(x))),
    ]

    for label, key, fmt in metrics:
        row = f"{label:<25}"
        for name in backends:
            val = results[name].get(key)
            row += f" {fmt(val):>15}" if val is not None else f" {'N/A':>15}"
        print(row)

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Benchmark transcription backends")
    parser.add_argument("audio_path", help="Path to audio or video file")
    parser.add_argument("--short", action="store_true", help="Use only first 60 seconds")
    args = parser.parse_args()

    if not os.path.isfile(args.audio_path):
        print(f"Error: File not found: {args.audio_path}")
        sys.exit(1)

    audio_path = extract_audio_from_video(args.audio_path)

    if args.short:
        audio_path = truncate_audio(audio_path)

    logger.info(f"Benchmarking with: {audio_path}")

    results = {}

    logger.info("--- Benchmarking transformers backend ---")
    results["transformers"] = benchmark_transformers(audio_path)

    logger.info("--- Benchmarking faster-whisper backend ---")
    results["faster-whisper"] = benchmark_faster_whisper(audio_path)

    print_results(results)


if __name__ == "__main__":
    main()
