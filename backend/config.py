"""
Configuration module for the Marketing Assistant AI.
Handles environment variables and application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directories exist
(DATA_DIR / "past_campaigns").mkdir(exist_ok=True)
(DATA_DIR / "user_queries").mkdir(exist_ok=True)
(DATA_DIR / "style_guidelines").mkdir(exist_ok=True)

# API configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", 8000))

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Cohere configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Vector database configuration
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(DATA_DIR / "vector_store"))

# Brand configuration
BRAND_NAME = os.getenv("BRAND_NAME", "Adriana James")

# Content types
CONTENT_TYPES = [
    "website_copy",
    "email",
    "social_media",
    "blog_post",
    "sales_copy",
    "ad_copy",
    "video_script",
    "case_study",
    "product_description",
    "landing_page",
    "press_release",
    "newsletter"
]

# Tone options - specifically matching Adriana James' communication style
TONE_OPTIONS = [
    "empowering",
    "assertive",
    "inspirational",
    "direct"
]

# Content length options
LENGTH_OPTIONS = [
    "short",  # < 100 words
    "medium",  # 100-300 words
    "long",    # > 300 words
]

# Default brand style guidelines - fixed to match Adriana James' distinct communication style
DEFAULT_BRAND_STYLE = {
    "tone": ["empowering", "assertive", "inspirational", "direct"],
    "voice_characteristics": ["clear", "confident", "conversational", "teaching"],
    "writing_patterns": ["direct commands", "personal pronouns", "repetitive rhythms", "embedded commands", "cause-effect statements"],
    "taboo_words": ["cheap", "discount", "bargain", "failure", "impossible", "difficult", "might", "try", "consider"],
    "preferred_terms": {
        "problems": "challenges",
        "try": "take action",
        "difficult": "ready for growth",
        "failure": "learning opportunity",
        "hope": "know",
        "maybe": "will",
        "might help you": "you can do this",
        "consider doing this": "decide now to change your thinking",
        "this could work": "this works because"
    }
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))

# Create logs directory if it doesn't exist
(BASE_DIR / "logs").mkdir(exist_ok=True)
