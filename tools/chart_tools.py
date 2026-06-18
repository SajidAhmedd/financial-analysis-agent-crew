"""
Chart Tools - Creates financial visualizations.

WHY THIS EXISTS:
- Visual representation of data for reports
- Charts make complex data easy to understand
- Professional-looking outputs for stakeholders

WHAT IT CREATES:
- Price history charts (line chart with moving averages)
- KPI comparison charts (bar charts)
- Sentiment distribution charts (pie charts)
- All charts saved as PNG images for PDF embedding
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Set the style for all charts
plt.style.use('seaborn-v0_8-whitegrid')  # Clean, professional look

# Add project root to path
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import OUTPUT_DIR

# HELPER FUNCTIONS

def ensure_output_dir():
    """Make sure the output directory exists."""
    charts_dir = os.path.join(project_root, OUTPUT_DIR, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    return charts_dir


def get_chart_path(ticker: str, chart_type: str) -> str:
    """Generate a file path for saving a chart."""
    charts_dir = ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ticker}_{chart_type}_{timestamp}.png"
    return os.path.join(charts_dir, filename)

# PRICE CHART

def create_price_chart(
    ticker: str,
    price_data: pd.DataFrame,
    include_moving_averages: bool = True,
    save: bool = True
) -> str:
    """
    Create a stock price history chart.

    WHAT IT SHOWS:
    - Daily closing prices over time
    - Optional: 10-day and 20-day moving averages
    - Volume bars at the bottom

    WHY MOVING AVERAGES:
    - Smooth out daily noise
    - Show the overall trend
    - Common technical analysis tool

    PARAMETERS:
    - ticker: Stock symbol for title
    - price_data: DataFrame from finance_tools.get_stock_price_history()
    - include_moving_averages: Whether to show MA lines
    - save: Whether to save to file

    RETURNS:
    - Path to saved chart image
    """
    if price_data.empty:
        print(f"No price data available for {ticker}")
        return ""

    # Create figure with 2 subplots (price on top, volume on bottom)
    # gridspec_kw controls the height ratio (price chart 3x taller than volume)
    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(12, 8),
        gridspec_kw={'height_ratios': [3, 1]},
        sharex=True  # Share x-axis between subplots
    )

    # Get dates for x-axis
    dates = price_data.index

    # --- TOP SUBPLOT: Price Chart ---

    # Plot closing price
    ax1.plot(
        dates,
        price_data['Close'],
        label='Close Price',
        color='#2962FF',  # Blue
        linewidth=2
    )

    # Add moving averages if requested and enough data
    if include_moving_averages:
        if len(price_data) >= 10:
            ma10 = price_data['Close'].rolling(window=10).mean()
            ax1.plot(
                dates, ma10,
                label='10-Day MA',
                color='#FF6D00',  # Orange
                linewidth=1.5,
                linestyle='--'
            )

        if len(price_data) >= 20:
            ma20 = price_data['Close'].rolling(window=20).mean()
            ax1.plot(
                dates, ma20,
                label='20-Day MA',
                color='#00C853',  # Green
                linewidth=1.5,
                linestyle='--'
            )

    # Customize price chart
    ax1.set_title(f'{ticker.upper()} Stock Price', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Fill the area under the price line (subtle effect)
    ax1.fill_between(dates, price_data['Close'], alpha=0.1, color='#2962FF')

    # --- BOTTOM SUBPLOT: Volume Chart ---

    # Color volume bars based on price change
    colors = []
    for i in range(len(price_data)):
        if i == 0:
            colors.append('#26A69A')  # Green for first day
        elif price_data['Close'].iloc[i] >= price_data['Close'].iloc[i-1]:
            colors.append('#26A69A')  # Green for up days
        else:
            colors.append('#EF5350')  # Red for down days

    ax2.bar(dates, price_data['Volume'], color=colors, alpha=0.7)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45)

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Save the chart
    if save:
        chart_path = get_chart_path(ticker, "price")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        print(f"Price chart saved: {chart_path}")
        plt.close()
        return chart_path
    else:
        plt.show()
        return ""

# KPI METRICS CHART

def create_kpi_chart(
    ticker: str,
    metrics: Dict[str, Any],
    save: bool = True
) -> str:
    """
    Create a bar chart comparing key financial metrics.

    WHAT IT SHOWS:
    - Visual comparison of important KPIs
    - Color-coded for quick interpretation
    - Industry-standard metrics

    PARAMETERS:
    - ticker: Stock symbol for title
    - metrics: Dictionary from finance_tools.get_key_metrics()
    - save: Whether to save to file

    RETURNS:
    - Path to saved chart image
    """
    # Select metrics to display (only numeric values)
    display_metrics = {}

    # Map of metric names to display labels
    metric_labels = {
        'pe_ratio': 'P/E Ratio',
        'forward_pe': 'Forward P/E',
        'peg_ratio': 'PEG Ratio',
        'price_to_book': 'Price/Book',
        'profit_margin': 'Profit Margin',
        'revenue_growth': 'Revenue Growth',
        'earnings_growth': 'Earnings Growth',
    }

    for key, label in metric_labels.items():
        value = metrics.get(key, 'N/A')
        if value != 'N/A' and value is not None:
            try:
                # Convert percentages (0.25 -> 25%)
                num_value = float(value)
                if key in ['profit_margin', 'revenue_growth', 'earnings_growth']:
                    num_value = num_value * 100  # Convert to percentage
                display_metrics[label] = num_value
            except (ValueError, TypeError):
                pass

    if not display_metrics:
        print(f"No numeric metrics available for {ticker}")
        return ""

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = list(display_metrics.keys())
    values = list(display_metrics.values())

    # Color bars based on value (green for positive, red for negative)
    colors = ['#26A69A' if v >= 0 else '#EF5350' for v in values]

    # Create horizontal bar chart
    bars = ax.barh(labels, values, color=colors, edgecolor='white', height=0.6)

    # Add value labels on the bars
    for bar, value in zip(bars, values):
        width = bar.get_width()
        label_x = width + (max(values) * 0.02)  # Position slightly right of bar
        ax.text(
            label_x, bar.get_y() + bar.get_height()/2,
            f'{value:.2f}',
            va='center',
            fontsize=10,
            fontweight='bold'
        )

    # Customize chart
    ax.set_title(f'{ticker.upper()} Key Financial Metrics', fontsize=16, fontweight='bold')
    ax.set_xlabel('Value', fontsize=12)
    ax.axvline(x=0, color='gray', linewidth=0.8)  # Add zero line
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()

    # Save the chart
    if save:
        chart_path = get_chart_path(ticker, "kpi")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        print(f"KPI chart saved: {chart_path}")
        plt.close()
        return chart_path
    else:
        plt.show()
        return ""

# SENTIMENT CHART

def create_sentiment_chart(
    ticker: str,
    sentiment_data: Dict[str, Any],
    save: bool = True
) -> str:
    """
    Create a pie chart showing news sentiment distribution.

    WHAT IT SHOWS:
    - Percentage of positive, negative, neutral news
    - Visual representation of market sentiment

    PARAMETERS:
    - ticker: Stock symbol for title
    - sentiment_data: overall_sentiment from news_tools.search_stock_news()
    - save: Whether to save to file

    RETURNS:
    - Path to saved chart image
    """
    # Extract sentiment counts
    positive = sentiment_data.get('positive_articles', 0)
    negative = sentiment_data.get('negative_articles', 0)
    neutral = sentiment_data.get('neutral_articles', 0)

    total = positive + negative + neutral

    if total == 0:
        print(f"No sentiment data available for {ticker}")
        return ""

    # Prepare data for pie chart
    sizes = [positive, neutral, negative]
    labels = ['Positive', 'Neutral', 'Negative']
    colors = ['#26A69A', '#78909C', '#EF5350']  # Green, Gray, Red
    explode = (0.05, 0, 0.05)  # Slightly separate positive and negative

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- LEFT: Pie Chart ---
    wedges, texts, autotexts = ax1.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        shadow=True
    )

    # Style the percentage text
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')

    ax1.set_title(f'{ticker.upper()} News Sentiment', fontsize=14, fontweight='bold')

    # --- RIGHT: Sentiment Score Gauge ---
    score = sentiment_data.get('score', 0)

    # Create a simple horizontal bar to show score
    ax2.barh(['Sentiment'], [score], color='#2962FF' if score >= 0 else '#EF5350', height=0.3)
    ax2.set_xlim(-1, 1)
    ax2.axvline(x=0, color='gray', linewidth=2)

    # Add labels
    ax2.text(-1, -0.5, 'Bearish', ha='left', fontsize=12, color='#EF5350')
    ax2.text(1, -0.5, 'Bullish', ha='right', fontsize=12, color='#26A69A')
    ax2.text(score, 0.25, f'Score: {score:.2f}', ha='center', fontsize=14, fontweight='bold')

    ax2.set_title('Sentiment Score', fontsize=14, fontweight='bold')
    ax2.set_yticks([])
    ax2.grid(True, axis='x', alpha=0.3)

    # Add overall label
    overall_label = sentiment_data.get('label', 'neutral').upper()
    fig.suptitle(
        f'Overall Market Sentiment: {overall_label}',
        fontsize=16,
        fontweight='bold',
        y=1.02
    )

    plt.tight_layout()

    # Save the chart
    if save:
        chart_path = get_chart_path(ticker, "sentiment")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        print(f"Sentiment chart saved: {chart_path}")
        plt.close()
        return chart_path
    else:
        plt.show()
        return ""

# COMBINED CHART FUNCTION

def create_all_charts(
    ticker: str,
    price_data: pd.DataFrame,
    metrics: Dict[str, Any],
    sentiment_data: Dict[str, Any]
) -> Dict[str, str]:
    """
    Create all charts for a stock analysis.

    This is the main function the Data Analyst Agent will use.
    Creates all charts in one call and returns paths.

    RETURNS:
    - Dictionary with chart type -> file path
    """
    print(f"\nGenerating charts for {ticker}...")

    chart_paths = {}

    # Price chart
    if not price_data.empty:
        chart_paths['price'] = create_price_chart(ticker, price_data)

    # KPI chart
    if metrics and 'error' not in metrics:
        chart_paths['kpi'] = create_kpi_chart(ticker, metrics)

    # Sentiment chart
    if sentiment_data:
        chart_paths['sentiment'] = create_sentiment_chart(ticker, sentiment_data)

    print(f"Generated {len(chart_paths)} charts for {ticker}")
    return chart_paths

# TEST CODE

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING CHART TOOLS")
    print("=" * 60)

    # Import the tools we need for test data
    from tools.finance_tools import get_stock_price_history, get_key_metrics
    from tools.news_tools import search_stock_news

    test_ticker = "AAPL"

    # Get test data
    print(f"\nFetching data for {test_ticker}...")

    price_data = get_stock_price_history(test_ticker, days_back=60)
    metrics = get_key_metrics(test_ticker)
    news_data = search_stock_news(test_ticker, "Apple Inc", max_results=10)

    # Test 1: Price Chart
    print("\n1. Creating Price Chart...")
    print("-" * 40)
    price_chart = create_price_chart(test_ticker, price_data)
    print(f"   Created: {price_chart}")

    # Test 2: KPI Chart
    print("\n2. Creating KPI Chart...")
    print("-" * 40)
    kpi_chart = create_kpi_chart(test_ticker, metrics)
    print(f"   Created: {kpi_chart}")

    # Test 3: Sentiment Chart
    print("\n3. Creating Sentiment Chart...")
    print("-" * 40)
    sentiment_chart = create_sentiment_chart(test_ticker, news_data['overall_sentiment'])
    print(f"   Created: {sentiment_chart}")

    # Test 4: All Charts
    print("\n4. Creating All Charts at Once...")
    print("-" * 40)
    all_charts = create_all_charts(
        test_ticker,
        price_data,
        metrics,
        news_data['overall_sentiment']
    )
    print(f"   Charts created: {list(all_charts.keys())}")

    print("\n" + "=" * 60)
    print("CHART TOOLS TESTS COMPLETED!")
    print(f"Check the '{OUTPUT_DIR}/charts' folder for generated images")
    print("=" * 60)