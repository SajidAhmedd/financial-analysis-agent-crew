"""
Configuration settings for Financial Agent Crew.

WHY THIS FILE EXISTS:
- Centralizes all configuration in one place
- Loads sensitive API keys from .env file (not hardcoded)
- Provides default values for optional settings
- Makes it easy to change settings without modifying code

LLM PROVIDERS:
- Mistral, Groq and Google Gemini all have free tiers
- LLM_PROVIDERS sets the order they are tried in; if one is rate-limited or
  down, the request falls back to the next (see config/llm_client.py)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads the .env file and makes variables available via os.getenv()
load_dotenv()

# =============================================================================
# API KEYS
# =============================================================================

# LLM providers, tried in this order (only those with an API key are used)
# Free keys: https://console.mistral.ai  https://console.groq.com  https://aistudio.google.com/apikey
LLM_PROVIDERS = os.getenv("LLM_PROVIDERS", "mistral,groq,gemini")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NewsAPI Key - Used by Market Researcher for fetching news
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# =============================================================================
# MODEL SETTINGS
# =============================================================================

# Models per provider (override with MISTRAL_MODEL / GROQ_MODEL / GEMINI_MODEL)
# Defaults live in config/llm_client.py: mistral-small-latest, openai/gpt-oss-20b, gemini-flash-latest

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
    from config.llm_client import configured_providers

    providers = configured_providers(LLM_PROVIDERS)
    if not providers:
        print("=" * 50)
        print("CONFIGURATION ERROR:")
        print("  - No LLM API key found. Set at least one of MISTRAL_API_KEY, GROQ_API_KEY or GEMINI_API_KEY.")
        print("=" * 50)
        return False

    print(f"Configuration loaded successfully! (LLM providers: {', '.join(providers)})")
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
