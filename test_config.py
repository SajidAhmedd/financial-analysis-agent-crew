"""Quick test to verify configuration is working."""

from config.settings import (
    GEMINI_API_KEY,
    NEWS_API_KEY,
    DEFAULT_DAYS_BACK,
    validate_config
)

print("Testing configuration...")
print(f"Gemini API Key: {'SET' if GEMINI_API_KEY else 'MISSING'}")
print(f"NewsAPI Key: {'SET' if NEWS_API_KEY else 'MISSING (optional)'}")
print(f"Default days back: {DEFAULT_DAYS_BACK}")
print()

validate_config()