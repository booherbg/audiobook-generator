"""Shared paths and audio constants for the pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MODEL_DIR = BUILD / "models"
DOCS = ROOT / "docs"
AUDIO_ROOT = DOCS / "audio"
MANIFEST = DOCS / "manifest.json"

# Audio
SAMPLE_RATE = 24000        # Kokoro native output
OUT_SR = 44100             # final MP3 sample rate
MP3_BITRATE = "64k"        # mono spoken-word
LUFS = -16.0               # EBU R128 integrated loudness target
TRUE_PEAK = -1.5           # dBTP ceiling
LRA = 11.0                 # loudness range
PARA_PAUSE_MS = 400        # silence between paragraphs

# Chaptering
WPM = 155                  # narration pace estimate
MAX_CHAPTER_MIN = 18       # sub-split threshold

# Models
KOKORO_MODEL = MODEL_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES = MODEL_DIR / "voices-v1.0.bin"
