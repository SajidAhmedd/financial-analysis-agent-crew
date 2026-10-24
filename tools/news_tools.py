"""
News Tools - Fetches news and performs sentiment analysis.

WHY THIS EXISTS:
- Market Researcher Agent needs current news about stocks
- News sentiment impacts stock prices
- Provides context beyond just numbers

DATA SOURCES:
- DuckDuckGo Search (free, no API key needed)
- NewsAPI (optional, better results if you have a key)

WHAT IT PROVIDES:
- search_stock_news() - Find recent news articles
- analyze_sentiment() - Simple sentiment scoring
- get_news_summary() - Formatted news for reports
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

# Try to import DuckDuckGo search (the package was renamed from duckduckgo-search to ddgs)
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False
        print("Warning: ddgs not installed. Run: pip install ddgs")

# Import our config for NewsAPI key
import sys
import os

# Add project root to path so we can import config
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import NEWS_API_KEY

# SENTIMENT ANALYSIS (Simple keyword-based)

# Keywords that suggest positive sentiment
POSITIVE_KEYWORDS = [
    'surge', 'jump', 'gain', 'rise', 'climb', 'soar', 'rally', 'up',
    'growth', 'profit', 'success', 'beat', 'exceed', 'record', 'high',
    'upgrade', 'buy', 'bullish', 'optimistic', 'strong', 'positive',
    'breakthrough', 'innovation', 'deal', 'partnership', 'launch',
    'expansion', 'revenue', 'earnings', 'outperform', 'winner'
]

# Keywords that suggest negative sentiment
NEGATIVE_KEYWORDS = [
    'drop', 'fall', 'decline', 'plunge', 'crash', 'sink', 'tumble', 'down',
    'loss', 'fail', 'miss', 'below', 'low', 'downgrade', 'sell', 'bearish',
    'pessimistic', 'weak', 'negative', 'warning', 'risk', 'concern', 'fear',
    'lawsuit', 'investigation', 'scandal', 'layoff', 'cut', 'debt', 'loser',
    'underperform', 'struggle', 'trouble', 'crisis'
]


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of text using keyword matching.

    HOW IT WORKS:
    - Counts positive and negative keywords in the text
    - Calculates a sentiment score from -1 (negative) to +1 (positive)
    - Simple but effective for financial news

    NOTE: For production, you'd use a proper NLP model like:
    - VADER (Valence Aware Dictionary for Sentiment Reasoning)
    - FinBERT (BERT fine-tuned for financial text)
    - TextBlob

    We keep it simple here to avoid extra dependencies.

    RETURNS:
    - score: -1 to +1
    - label: "positive", "negative", or "neutral"
    - positive_count: number of positive keywords found
    - negative_count: number of negative keywords found
    """
    text_lower = text.lower()

    # Count keyword matches
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)

    total = positive_count + negative_count

    if total == 0:
        score = 0.0
        label = "neutral"
    else:
        # Score from -1 to +1
        score = (positive_count - negative_count) / total

        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"

    return {
        "score": round(score, 3),
        "label": label,
        "positive_keywords": positive_count,
        "negative_keywords": negative_count,
    }


# NEWS SEARCH - DuckDuckGo (Free, no API key)

def search_news_duckduckgo(
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for news using DuckDuckGo.

    WHY DUCKDUCKGO:
    - Free, no API key required
    - Good for general news search
    - Returns recent, relevant results

    PARAMETERS:
    - query: Search query (e.g., "Apple stock news")
    - max_results: Maximum number of results to return

    RETURNS:
    - List of news articles with title, link, snippet, date
    """
    if not DDGS_AVAILABLE:
        return [{"error": "DuckDuckGo search not available"}]

    try:
        articles = []

        with DDGS() as ddgs:
            # Search for news specifically
            results = ddgs.news(
                query,
                max_results=max_results,
                timelimit='m'  # Last month
            )

            for result in results:
                article = {
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "snippet": result.get("body", ""),
                    "source": result.get("source", "Unknown"),
                    "date": result.get("date", ""),
                }

                # Add sentiment analysis
                combined_text = f"{article['title']} {article['snippet']}"
                article["sentiment"] = analyze_sentiment(combined_text)

                articles.append(article)

        return articles

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return [{"error": str(e)}]

# NEWS SEARCH - NewsAPI (Better results, requires free API key)

def search_news_newsapi(
    query: str,
    max_results: int = 10,
    days_back: int = 7
) -> List[Dict[str, Any]]:
    """
    Search for news using NewsAPI.

    WHY NEWSAPI:
    - Higher quality results
    - Better filtering options
    - More reliable for financial news

    REQUIRES: NEWS_API_KEY in .env file
    Free tier: 100 requests/day, 1 month old articles

    PARAMETERS:
    - query: Search query
    - max_results: Maximum results to return
    - days_back: How far back to search
    """
    if not NEWS_API_KEY:
        return [{"error": "NewsAPI key not configured"}]

    try:
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        # NewsAPI endpoint
        url = "https://newsapi.org/v2/everything"

        params = {
            "q": query,
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": max_results,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            return [{"error": data.get("message", "Unknown error")}]

        articles = []
        for item in data.get("articles", []):
            article = {
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "source": item.get("source", {}).get("name", "Unknown"),
                "date": item.get("publishedAt", ""),
                "author": item.get("author", "Unknown"),
            }

            # Add sentiment
            combined_text = f"{article['title']} {article['snippet']}"
            article["sentiment"] = analyze_sentiment(combined_text)

            articles.append(article)

        return articles

    except requests.exceptions.RequestException as e:
        print(f"NewsAPI request error: {e}")
        return [{"error": str(e)}]
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return [{"error": str(e)}]

# MAIN SEARCH FUNCTION - Uses best available source

def search_stock_news(
    ticker: str,
    company_name: str = "",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search for news about a stock - main function for agents.

    HOW IT WORKS:
    1. Tries NewsAPI first (if key available)
    2. Falls back to DuckDuckGo (free)
    3. Analyzes sentiment of all articles
    4. Returns aggregated results

    PARAMETERS:
    - ticker: Stock symbol (e.g., "AAPL")
    - company_name: Full company name (e.g., "Apple Inc")
    - max_results: Maximum articles to return

    RETURNS:
    - Dictionary with articles, overall sentiment, and summary
    """
    # Build search query
    if company_name:
        query = f"{company_name} ({ticker}) stock news"
    else:
        query = f"{ticker} stock news"

    print(f"Searching news for: {query}")

    # Try NewsAPI first, then DuckDuckGo
    articles = []
    source_used = ""

    if NEWS_API_KEY:
        articles = search_news_newsapi(query, max_results)
        source_used = "NewsAPI"

        # Check if NewsAPI failed
        if articles and "error" in articles[0]:
            print(f"NewsAPI failed, falling back to DuckDuckGo")
            articles = search_news_duckduckgo(query, max_results)
            source_used = "DuckDuckGo"
    else:
        articles = search_news_duckduckgo(query, max_results)
        source_used = "DuckDuckGo"

    # Filter out error entries
    valid_articles = [a for a in articles if "error" not in a]

    # Calculate overall sentiment
    if valid_articles:
        avg_score = sum(a["sentiment"]["score"] for a in valid_articles) / len(valid_articles)

        positive_count = sum(1 for a in valid_articles if a["sentiment"]["label"] == "positive")
        negative_count = sum(1 for a in valid_articles if a["sentiment"]["label"] == "negative")
        neutral_count = sum(1 for a in valid_articles if a["sentiment"]["label"] == "neutral")

        if avg_score > 0.15:
            overall_label = "positive"
        elif avg_score < -0.15:
            overall_label = "negative"
        else:
            overall_label = "neutral"

        overall_sentiment = {
            "score": round(avg_score, 3),
            "label": overall_label,
            "positive_articles": positive_count,
            "negative_articles": negative_count,
            "neutral_articles": neutral_count,
        }
    else:
        overall_sentiment = {
            "score": 0,
            "label": "unknown",
            "positive_articles": 0,
            "negative_articles": 0,
            "neutral_articles": 0,
        }

    return {
        "ticker": ticker.upper(),
        "query": query,
        "source": source_used,
        "search_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_articles": len(valid_articles),
        "overall_sentiment": overall_sentiment,
        "articles": valid_articles,
    }


def get_news_summary(ticker: str, company_name: str = "", max_articles: int = 5) -> str:
    """
    Get a formatted text summary of news for reports.

    This is used by the Report Writer Agent to include
    news in the final report.

    RETURNS:
    - Formatted string with news headlines and sentiment
    """
    news_data = search_stock_news(ticker, company_name, max_articles)

    lines = []
    lines.append(f"NEWS SUMMARY FOR {ticker.upper()}")
    lines.append("=" * 50)
    lines.append(f"Search Date: {news_data['search_date']}")
    lines.append(f"Source: {news_data['source']}")
    lines.append(f"Total Articles Found: {news_data['total_articles']}")
    lines.append("")

    # Overall sentiment
    sentiment = news_data['overall_sentiment']
    lines.append(f"OVERALL SENTIMENT: {sentiment['label'].upper()} (score: {sentiment['score']})")
    lines.append(f"  - Positive articles: {sentiment['positive_articles']}")
    lines.append(f"  - Negative articles: {sentiment['negative_articles']}")
    lines.append(f"  - Neutral articles: {sentiment['neutral_articles']}")
    lines.append("")

    # Individual articles
    lines.append("RECENT HEADLINES:")
    lines.append("-" * 50)

    for i, article in enumerate(news_data['articles'][:max_articles], 1):
        sentiment_icon = {
            "positive": "[+]",
            "negative": "[-]",
            "neutral": "[=]"
        }.get(article['sentiment']['label'], "[?]")

        lines.append(f"{i}. {sentiment_icon} {article['title']}")
        lines.append(f"   Source: {article['source']}")
        if article.get('snippet'):
            # Truncate long snippets
            snippet = article['snippet'][:150] + "..." if len(article['snippet']) > 150 else article['snippet']
            lines.append(f"   Summary: {snippet}")
        lines.append("")

    return "\n".join(lines)

# TEST CODE

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING NEWS TOOLS")
    print("=" * 60)

    test_ticker = "AAPL"
    test_company = "Apple Inc"

    # Test 1: Sentiment Analysis
    print("\n1. Testing Sentiment Analysis:")
    print("-" * 40)

    positive_text = "Apple stock surges to record high after beating earnings expectations"
    negative_text = "Apple faces lawsuit as stock plunges amid declining iPhone sales"
    neutral_text = "Apple announces quarterly results scheduled for next week"

    print(f"Positive text: {analyze_sentiment(positive_text)}")
    print(f"Negative text: {analyze_sentiment(negative_text)}")
    print(f"Neutral text: {analyze_sentiment(neutral_text)}")

    # Test 2: News Search
    print(f"\n2. Searching news for {test_ticker}:")
    print("-" * 40)

    news_results = search_stock_news(test_ticker, test_company, max_results=5)

    print(f"Source used: {news_results['source']}")
    print(f"Articles found: {news_results['total_articles']}")
    print(f"Overall sentiment: {news_results['overall_sentiment']['label']}")

    if news_results['articles']:
        print("\nTop 3 Headlines:")
        for i, article in enumerate(news_results['articles'][:3], 1):
            print(f"  {i}. [{article['sentiment']['label']}] {article['title'][:60]}...")

    # Test 3: News Summary
    print(f"\n3. News Summary for {test_ticker}:")
    print("-" * 40)
    summary = get_news_summary(test_ticker, test_company, max_articles=3)
    print(summary)

    print("\n" + "=" * 60)
    print("NEWS TOOLS TESTS COMPLETED!")
    print("=" * 60)