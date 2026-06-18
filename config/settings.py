"""
Configuration settings for Financial Agent Crew.

WHY THIS FILE EXISTS:
- Centralizes all configuration in one place
- Loads sensitive API keys from .env file (not hardcoded)
- Provides default values for optional settings
- Makes it easy to change settings without modifying code

SWITCHED TO GROQ:
- Faster inference (Groq's specialty)
- More generous rate limits (30 req/min free)
- LLaMA 3.1 70B provides excellent quality
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads the .env file and makes variables available via os.getenv()
load_dotenv()

# =============================================================================
# API KEYS
# =============================================================================

# Groq API Key - Used by agents for reasoning and text generation
# Get yours free at: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Legacy: Gemini API Key (keeping for backward compatibility)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NewsAPI Key - Used by Market Researcher for fetching news
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# =============================================================================
# MODEL SETTINGS
# =============================================================================

# Groq Model - LLaMA 3.3 70B is the latest and best
GROQ_MODEL = "llama-3.3-70b-versatile"

# Alternative Groq models you can use:
# - "llama-3.3-70b-versatile"   # Latest, best quality (recommended)
# - "llama-3.1-8b-instant"      # Fastest, good for simple tasks
# - "llama3-70b-8192"           # Previous version, stable
# - "mixtral-8x7b-32768"        # Good balance of speed/quality

# Legacy Gemini model
GEMINI_MODEL = "gemini-2.0-flash"

# =============================================================================
# OTHER SETTINGS
# =============================================================================

# How many days of historical data to fetch by default
DEFAULT_DAYS_BACK = int(os.getenv("DEFAULT_DAYS_BACK", 30))

# Where to save generated reports
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output/reports")


def validate_config():
    """
    Check that required configuration is present.
    Call this at app startup to fail fast if something is missing.
    """
    errors = []
    warnings = []

    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is missing. Get one free at https://console.groq.com")

    if not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY is missing (optional - using Groq instead)")

    if errors:
        print("=" * 50)
        print("CONFIGURATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print("=" * 50)
        return False

    if warnings:
        for warning in warnings:
            print(f"  Note: {warning}")

    print("Configuration loaded successfully! (Using Groq API)")
    return True


# Prompts and roles for each agent
AGENT_SETTINGS = {
    "market_researcher": {
        "role": "Market Research Analyst",
        "goal": "Gather and analyze market news, sentiment, and trends",
    },
    "data_analyst": {
        "role": "Financial Data Analyst",
        "goal": "Analyze stock data, calculate KPIs, and create visualizations",
    },
    "report_writer": {
        "role": "Financial Report Writer",
        "goal": "Synthesize all research into a professional report",
    },
}
