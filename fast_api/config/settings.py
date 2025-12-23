"""
Application settings for F5-TTS Vietnamese API
"""

import os

# API Metadata
API_TITLE = "F5-TTS Vietnamese API"
API_VERSION = "1.0.0"

# CORS Settings
CORS_ALLOW_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# HuggingFace Cache Settings
HF_HOME = os.getenv("HF_HOME", "/home/psilab/.cache/huggingface")
HF_HUB_CACHE = os.getenv("HF_HUB_CACHE", "/home/psilab/.cache/huggingface/hub")

# Model Settings
MODEL_NAME = "F5TTS_Base"
VOCODER_NAME = "vocos"
SAMPLE_RATE = 24000

# TTS Generation Limits
MIN_TEXT_LENGTH = 1
MAX_TEXT_LENGTH = 5000
MIN_SPEED = 0.5
MAX_SPEED = 2.0
MIN_CFG_STRENGTH = 1.0
MAX_CFG_STRENGTH = 5.0

# Rate Limiting
RATE_LIMIT_REQUESTS = 1000
