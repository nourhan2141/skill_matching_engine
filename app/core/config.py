import os

# Note: Pydantic's BaseSettings is deliberately deferred here as a pragmatic choice for a v1,
# but ideally these configurations should be centralized and validated via BaseSettings in the future.
MAX_CV_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_JD_CHARS = 20000

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_EXTRACTION_MODEL = os.getenv("GROQ_EXTRACTION_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
