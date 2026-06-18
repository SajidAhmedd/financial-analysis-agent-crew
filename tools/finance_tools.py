"""
Finance Tools - Fetches stock market data using Yahoo Finance.

WHY THIS EXISTS:
- Agents need real financial data to analyze
- yfinance library provides free access to Yahoo Finance data
- This tool wraps yfinance into easy-to-use functions

WHAT IT PROVIDES:
- get_stock_price_history() - Historical prices for charts
- get_company_info() - Company details and description
- get_key_metrics() - Financial KPIs (P/E, Market Cap, etc.)
- get_price_statistics() - Returns, volatility calculations
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def get_stock_price_history(
    ticker: str,
    days_back: int = 30
) -> pd.DataFrame:
    """
    Fetch historical stock prices.

    WHAT IT DOES:
    - Downloads daily price data (Open, High, Low, Close, Volume)
    - Returns a pandas DataFrame for easy analysis

    PARAMETERS:
    - ticker: Stock symbol (e.g., "AAPL", "GOOGL", "MSFT")
    - days_back: How many days of history to fetch

    RETURNS:
    - DataFrame with columns: Open, High, Low, Close, Volume
    - Index is the date

    EXAMPLE:
    >>> df = get_stock_price_history("AAPL", days_back=30)
    >>> print(df.head())
    """
    try:
        # Create a Ticker object - this represents the stock
        stock = yf.Ticker(ticker)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Download historical data
        # period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        history = stock.history(start=start_date, end=end_date)

        if history.empty:
            print(f"Warning: No data found for {ticker}")
            return pd.DataFrame()

        return history

    except Exception as e:
        print(f"Error fetching price history for {ticker}: {e}")
        return pd.DataFrame()


def get_company_info(ticker: str) -> Dict[str, Any]:
    """
    Fetch company information and profile.

    WHAT IT DOES:
    - Gets company details like name, sector, industry
    - Gets business description
    - Gets key contact info (website, address)

    RETURNS:
    - Dictionary with company information

    EXAMPLE:
    >>> info = get_company_info("AAPL")
    >>> print(info['name'])  # Apple Inc.
    >>> print(info['sector'])  # Technology
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extract relevant information (yfinance returns a LOT of data)
        # We pick the most useful fields
        company_info = {
            "name": info.get("longName", "N/A"),
            "symbol": ticker.upper(),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "No description available."),
            "website": info.get("website", "N/A"),
            "country": info.get("country", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "currency": info.get("currency", "USD"),
        }

        return company_info

    except Exception as e:
        print(f"Error fetching company info for {ticker}: {e}")
        return {"name": ticker, "symbol": ticker, "error": str(e)}


def get_key_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetch key financial metrics (KPIs).

    WHAT IT DOES:
    - Gets valuation metrics (P/E ratio, Market Cap)
    - Gets trading info (52-week high/low, volume)
    - Gets dividend information
    - Gets profitability metrics

    WHY THESE METRICS MATTER:
    - P/E Ratio: Is the stock expensive relative to earnings?
    - Market Cap: How big is the company?
    - 52-Week Range: Where is price relative to yearly range?
    - Dividend Yield: How much income does it pay?

    RETURNS:
    - Dictionary with key financial metrics
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        metrics = {
            # Price Information
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
            "previous_close": info.get("previousClose", "N/A"),
            "open_price": info.get("open", info.get("regularMarketOpen", "N/A")),

            # 52-Week Range
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", "N/A"),

            # Volume
            "volume": info.get("volume", info.get("regularMarketVolume", "N/A")),
            "avg_volume": info.get("averageVolume", "N/A"),

            # Valuation Metrics
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "peg_ratio": info.get("pegRatio", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),

            # Dividends
            "dividend_yield": info.get("dividendYield", "N/A"),
            "dividend_rate": info.get("dividendRate", "N/A"),

            # Profitability
            "profit_margin": info.get("profitMargins", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "earnings_growth": info.get("earningsGrowth", "N/A"),

            # Analyst Targets
            "target_mean_price": info.get("targetMeanPrice", "N/A"),
            "recommendation": info.get("recommendationKey", "N/A"),
        }

        return metrics

    except Exception as e:
        print(f"Error fetching metrics for {ticker}: {e}")
        return {"error": str(e)}


def get_price_statistics(ticker: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Calculate price statistics from historical data.

    WHAT IT DOES:
    - Calculates returns (daily, total period)
    - Calculates volatility (risk measure)
    - Finds high/low for the period
    - Calculates moving averages

    WHY THESE MATTER:
    - Returns: How much has the stock gained/lost?
    - Volatility: How risky is this stock?
    - Moving Averages: What's the trend?
    """
    try:
        # Get historical data
        history = get_stock_price_history(ticker, days_back)

        if history.empty:
            return {"error": "No historical data available"}

        # Calculate daily returns
        # Returns = (Today's Price - Yesterday's Price) / Yesterday's Price
        history['daily_return'] = history['Close'].pct_change()

        # Calculate statistics
        stats = {
            # Period returns
            "period_start_price": round(history['Close'].iloc[0], 2),
            "period_end_price": round(history['Close'].iloc[-1], 2),
            "period_return_pct": round(
                ((history['Close'].iloc[-1] - history['Close'].iloc[0])
                / history['Close'].iloc[0]) * 100, 2
            ),

            # High and Low
            "period_high": round(history['High'].max(), 2),
            "period_low": round(history['Low'].min(), 2),

            # Average daily return
            "avg_daily_return_pct": round(history['daily_return'].mean() * 100, 4),

            # Volatility (standard deviation of returns)
            # Higher = more risky
            "daily_volatility_pct": round(history['daily_return'].std() * 100, 4),

            # Annualized volatility (daily * sqrt(252 trading days))
            "annualized_volatility_pct": round(
                history['daily_return'].std() * (252 ** 0.5) * 100, 2
            ),

            # Average volume
            "avg_volume": int(history['Volume'].mean()),

            # Number of trading days in data
            "trading_days": len(history),
        }

        # Add moving averages if we have enough data
        if len(history) >= 20:
            stats["sma_20"] = round(history['Close'].tail(20).mean(), 2)
        if len(history) >= 10:
            stats["sma_10"] = round(history['Close'].tail(10).mean(), 2)

        return stats

    except Exception as e:
        print(f"Error calculating statistics for {ticker}: {e}")
        return {"error": str(e)}


def format_large_number(num: Any) -> str:
    """
    Format large numbers for display (e.g., 1500000000 -> "1.5B").

    Helper function to make numbers human-readable.
    """
    if num == "N/A" or num is None:
        return "N/A"

    try:
        num = float(num)
        if num >= 1_000_000_000_000:  # Trillion
            return f"${num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:  # Billion
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:  # Million
            return f"${num / 1_000_000:.2f}M"
        elif num >= 1_000:  # Thousand
            return f"${num / 1_000:.2f}K"
        else:
            return f"${num:.2f}"
    except (ValueError, TypeError):
        return str(num)


# MAIN FUNCTION - Combines all data for an agent

def get_full_stock_analysis(ticker: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Get complete stock analysis - combines all tools into one call.

    This is what the Data Analyst Agent will primarily use.
    Returns everything needed for analysis in one dictionary.
    """
    print(f"Fetching full analysis for {ticker}...")

    analysis = {
        "ticker": ticker.upper(),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": days_back,
        "company_info": get_company_info(ticker),
        "key_metrics": get_key_metrics(ticker),
        "price_statistics": get_price_statistics(ticker, days_back),
    }

    # Add formatted market cap for easy reading
    if analysis["key_metrics"].get("market_cap") != "N/A":
        analysis["key_metrics"]["market_cap_formatted"] = format_large_number(
            analysis["key_metrics"]["market_cap"]
        )

    return analysis

# TEST CODE - Run this file directly to test

if __name__ == "__main__":
    # Test with Apple stock
    print("=" * 60)
    print("TESTING FINANCE TOOLS")
    print("=" * 60)

    test_ticker = "AAPL"

    # Test 1: Company Info
    print(f"\n1. Company Info for {test_ticker}:")
    print("-" * 40)
    info = get_company_info(test_ticker)
    print(f"   Name: {info['name']}")
    print(f"   Sector: {info['sector']}")
    print(f"   Industry: {info['industry']}")

    # Test 2: Key Metrics
    print(f"\n2. Key Metrics for {test_ticker}:")
    print("-" * 40)
    metrics = get_key_metrics(test_ticker)
    print(f"   Current Price: ${metrics.get('current_price', 'N/A')}")
    print(f"   P/E Ratio: {metrics.get('pe_ratio', 'N/A')}")
    print(f"   Market Cap: {format_large_number(metrics.get('market_cap'))}")
    print(f"   52-Week High: ${metrics.get('fifty_two_week_high', 'N/A')}")
    print(f"   52-Week Low: ${metrics.get('fifty_two_week_low', 'N/A')}")

    # Test 3: Price Statistics
    print(f"\n3. Price Statistics (30 days) for {test_ticker}:")
    print("-" * 40)
    stats = get_price_statistics(test_ticker, 30)
    print(f"   Period Return: {stats.get('period_return_pct', 'N/A')}%")
    print(f"   Daily Volatility: {stats.get('daily_volatility_pct', 'N/A')}%")
    print(f"   Period High: ${stats.get('period_high', 'N/A')}")
    print(f"   Period Low: ${stats.get('period_low', 'N/A')}")

    # Test 4: Full Analysis
    print(f"\n4. Full Analysis for {test_ticker}:")
    print("-" * 40)
    full = get_full_stock_analysis(test_ticker)
    print(f"   Analysis Date: {full['analysis_date']}")
    print(f"   Data retrieved successfully!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)