"""
Path configurations for F5-TTS Vietnamese API
"""

from pathlib import Path

# Base directory (parent of fast_api/)
BASE_DIR = Path(__file__).parent.parent.parent

# Audio directories
REF_AUDIO_DIR = BASE_DIR / "original_voice_ref"
OUTPUT_DIR = BASE_DIR / "output"

# Static files
STATIC_DIR = BASE_DIR / "fast_api" / "static"
SAMPLES_DIR = STATIC_DIR / "samples"

# Model files
MODEL_DIR = BASE_DIR / "model"
VOCAB_FILE = MODEL_DIR / "vocab.txt"
CHECKPOINT_FILE = MODEL_DIR / "model_last.pt"
