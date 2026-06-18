"""
Data Analyst Agent - Analyzes financial data and creates visualizations.

ROLE: Financial Data Analyst
GOAL: Analyze stock data, calculate KPIs, and create visualizations

WHAT IT DOES:
1. Fetches stock price history and company info
2. Calculates key financial metrics
3. Generates charts and visualizations
4. Provides data-driven analysis

TOOLS IT USES:
- finance_tools (all functions)
- chart_tools (all functions)

LLM: Groq (LLaMA 3.1 70B) - Fast and high quality
"""

from groq import Groq
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import GROQ_API_KEY, GROQ_MODEL, AGENT_SETTINGS
from tools.finance_tools import (
    get_company_info,
    get_key_metrics,
    get_price_statistics,
    get_stock_price_history,
    get_full_stock_analysis,
    format_large_number
)
from tools.chart_tools import create_all_charts

# AGENT CLASS

class DataAnalystAgent:
    """
    Data Analyst Agent - Specializes in financial data analysis.

    HOW IT WORKS:
    1. Agent receives a task (e.g., "Analyze financials for AAPL")
    2. Agent uses finance_tools to gather numerical data
    3. Agent uses chart_tools to create visualizations
    4. Agent uses LLM to interpret data and provide insights
    5. Agent returns structured results with charts

    KEY DIFFERENCE FROM MARKET RESEARCHER:
    - Market Researcher focuses on NEWS (qualitative)
    - Data Analyst focuses on NUMBERS (quantitative)
    """

    def __init__(self):
        """Initialize the agent with its configuration."""
        # Get agent settings from config
        settings = AGENT_SETTINGS.get('data_analyst', {})
        self.role = settings.get('role', 'Financial Data Analyst')
        self.goal = settings.get('goal', 'Analyze stock data and create visualizations')

        # Initialize Groq client
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Get one free at https://console.groq.com")

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

        # Conversation history for context
        self.conversation_history = []

        # System prompt that defines agent behavior
        self.system_prompt = f"""You are a {self.role}.

Your goal is to: {self.goal}

You are part of a team of AI agents working together to create financial analysis reports.
Your specific responsibilities are:
1. Analyze stock price data and identify trends
2. Interpret key financial metrics (P/E ratio, Market Cap, etc.)
3. Calculate and explain risk metrics (volatility, returns)
4. Provide data-driven insights and observations

When analyzing financial data:
- Be precise with numbers and percentages
- Compare metrics to typical market values when relevant
- Identify any unusual patterns or outliers
- Explain what the numbers mean in plain English
- Note both strengths and weaknesses in the data

Always be objective and base your analysis on the actual data provided."""

    def log(self, message: str):
        """Log agent activity (for conversation tracking)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] DataAnalyst: {message}"
        self.conversation_history.append(log_entry)
        print(log_entry)

    def analyze(
        self,
        ticker: str,
        days_back: int = 30,
        sentiment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method: Analyze financial data for a stock.

        WHAT IT DOES:
        1. Fetches all financial data using finance_tools
        2. Creates charts using chart_tools
        3. Uses Groq to interpret the data
        4. Returns structured analysis with chart paths

        PARAMETERS:
        - ticker: Stock symbol (e.g., "AAPL")
        - days_back: How many days of history to analyze
        - sentiment_data: Optional sentiment from Market Researcher
                        (used to create sentiment chart)

        RETURNS:
        - Dictionary with all financial data, charts, and AI analysis
        """
        self.log(f"Starting financial analysis for {ticker}")

        # Step 1: Gather company info
        self.log("Fetching company information...")
        company_info = get_company_info(ticker)
        company_name = company_info.get('name', ticker)
        self.log(f"Analyzing: {company_name}")

        # Step 2: Get key metrics
        self.log("Fetching key financial metrics...")
        key_metrics = get_key_metrics(ticker)
        self.log(f"Retrieved {len([v for v in key_metrics.values() if v != 'N/A'])} metrics")

        # Step 3: Get price history and statistics
        self.log(f"Fetching {days_back} days of price history...")
        price_history = get_stock_price_history(ticker, days_back)
        price_stats = get_price_statistics(ticker, days_back)

        if not price_history.empty:
            self.log(f"Got {len(price_history)} trading days of data")
        else:
            self.log("Warning: No price history available")

        # Step 4: Create charts
        self.log("Generating charts...")
        chart_paths = create_all_charts(
            ticker=ticker,
            price_data=price_history,
            metrics=key_metrics,
            sentiment_data=sentiment_data.get('overall_sentiment', {}) if sentiment_data else {}
        )
        self.log(f"Created {len(chart_paths)} charts")

        # Step 5: Format data for LLM analysis
        formatted_data = self._format_data_for_analysis(
            ticker=ticker,
            company_info=company_info,
            key_metrics=key_metrics,
            price_stats=price_stats
        )

        # Step 6: Use Groq to analyze the data
        self.log("Analyzing data with AI...")
        ai_analysis = self._analyze_with_llm(ticker, company_name, formatted_data)

        # Step 7: Compile results
        results = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period_days": days_back,
            "agent": self.role,
            "company_info": company_info,
            "key_metrics": key_metrics,
            "price_statistics": price_stats,
            "price_history": price_history,  # DataFrame for potential further use
            "chart_paths": chart_paths,
            "ai_analysis": ai_analysis,
            "conversation_log": self.conversation_history.copy()
        }

        self.log(f"Financial analysis complete for {ticker}")
        return results

    def _format_data_for_analysis(
        self,
        ticker: str,
        company_info: Dict[str, Any],
        key_metrics: Dict[str, Any],
        price_stats: Dict[str, Any]
    ) -> str:
        """Format financial data into text for LLM analysis."""
        lines = []

        # Company Overview
        lines.append("COMPANY OVERVIEW:")
        lines.append(f"  Name: {company_info.get('name', 'N/A')}")
        lines.append(f"  Sector: {company_info.get('sector', 'N/A')}")
        lines.append(f"  Industry: {company_info.get('industry', 'N/A')}")
        lines.append("")

        # Price Information
        lines.append("CURRENT PRICE DATA:")
        lines.append(f"  Current Price: ${key_metrics.get('current_price', 'N/A')}")
        lines.append(f"  Previous Close: ${key_metrics.get('previous_close', 'N/A')}")
        lines.append(f"  52-Week High: ${key_metrics.get('fifty_two_week_high', 'N/A')}")
        lines.append(f"  52-Week Low: ${key_metrics.get('fifty_two_week_low', 'N/A')}")
        lines.append(f"  Market Cap: {format_large_number(key_metrics.get('market_cap', 'N/A'))}")
        lines.append("")

        # Valuation Metrics
        lines.append("VALUATION METRICS:")
        lines.append(f"  P/E Ratio (Trailing): {key_metrics.get('pe_ratio', 'N/A')}")
        lines.append(f"  P/E Ratio (Forward): {key_metrics.get('forward_pe', 'N/A')}")
        lines.append(f"  PEG Ratio: {key_metrics.get('peg_ratio', 'N/A')}")
        lines.append(f"  Price to Book: {key_metrics.get('price_to_book', 'N/A')}")
        lines.append("")

        # Performance Metrics
        lines.append("PERFORMANCE (Analysis Period):")
        lines.append(f"  Period Return: {price_stats.get('period_return_pct', 'N/A')}%")
        lines.append(f"  Period High: ${price_stats.get('period_high', 'N/A')}")
        lines.append(f"  Period Low: ${price_stats.get('period_low', 'N/A')}")
        lines.append(f"  Avg Daily Return: {price_stats.get('avg_daily_return_pct', 'N/A')}%")
        lines.append("")

        # Risk Metrics
        lines.append("RISK METRICS:")
        lines.append(f"  Daily Volatility: {price_stats.get('daily_volatility_pct', 'N/A')}%")
        lines.append(f"  Annualized Volatility: {price_stats.get('annualized_volatility_pct', 'N/A')}%")
        lines.append(f"  Trading Days Analyzed: {price_stats.get('trading_days', 'N/A')}")
        lines.append("")

        # Growth & Profitability
        lines.append("GROWTH & PROFITABILITY:")
        profit_margin = key_metrics.get('profit_margin', 'N/A')
        if profit_margin != 'N/A' and profit_margin is not None:
            lines.append(f"  Profit Margin: {float(profit_margin) * 100:.2f}%")
        else:
            lines.append(f"  Profit Margin: N/A")

        rev_growth = key_metrics.get('revenue_growth', 'N/A')
        if rev_growth != 'N/A' and rev_growth is not None:
            lines.append(f"  Revenue Growth: {float(rev_growth) * 100:.2f}%")
        else:
            lines.append(f"  Revenue Growth: N/A")

        lines.append(f"  Analyst Recommendation: {key_metrics.get('recommendation', 'N/A')}")
        lines.append(f"  Target Price: ${key_metrics.get('target_mean_price', 'N/A')}")

        return "\n".join(lines)

    def _analyze_with_llm(
        self,
        ticker: str,
        company_name: str,
        formatted_data: str
    ) -> Dict[str, str]:
        """
        Use Groq to analyze the financial data.

        WHAT THE LLM DOES:
        1. Interprets the financial metrics
        2. Identifies strengths and weaknesses
        3. Compares to market norms
        4. Provides investment considerations
        """
        user_prompt = f"""TASK: Analyze the following financial data for {company_name} ({ticker}) and provide your assessment.

{formatted_data}

Please provide your analysis in the following format:

1. VALUATION ASSESSMENT:
Is the stock fairly valued, overvalued, or undervalued based on P/E and other metrics? Explain in 2-3 sentences.

2. PERFORMANCE ANALYSIS:
How has the stock performed in the analysis period? Comment on returns and price movement.

3. RISK ASSESSMENT:
Assess the risk level based on volatility. Is this a high-risk or low-risk stock? Compare to typical market volatility (~15-20% annualized).

4. FINANCIAL HEALTH:
Comment on profitability and growth metrics. Is the company financially healthy?

5. KEY STRENGTHS:
List 2-3 key strengths based on the data.

6. KEY CONCERNS:
List 2-3 concerns or weaknesses based on the data.

7. DATA SUMMARY:
Provide a 3-4 sentence executive summary of the financial analysis.

Be precise with numbers and provide context for the metrics."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            analysis_text = response.choices[0].message.content

            # Parse the response into sections
            analysis = {
                "full_analysis": analysis_text,
                "valuation": self._extract_section(analysis_text, "VALUATION ASSESSMENT"),
                "performance": self._extract_section(analysis_text, "PERFORMANCE ANALYSIS"),
                "risk": self._extract_section(analysis_text, "RISK ASSESSMENT"),
                "financial_health": self._extract_section(analysis_text, "FINANCIAL HEALTH"),
                "strengths": self._extract_section(analysis_text, "KEY STRENGTHS"),
                "concerns": self._extract_section(analysis_text, "KEY CONCERNS"),
                "summary": self._extract_section(analysis_text, "DATA SUMMARY"),
            }

            return analysis

        except Exception as e:
            self.log(f"Error in LLM analysis: {str(e)}")
            return {
                "full_analysis": f"Error generating analysis: {str(e)}",
                "summary": "Analysis could not be completed due to an error."
            }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the LLM response."""
        try:
            # Find the section
            start_markers = [f"{section_name}:", f"{section_name}\n", f"**{section_name}**"]
            start_idx = -1

            for marker in start_markers:
                idx = text.upper().find(marker.upper())
                if idx != -1:
                    start_idx = idx + len(marker)
                    break

            if start_idx == -1:
                return ""

            # Find the next section
            remaining = text[start_idx:]

            import re
            next_section = re.search(r'\n\d+\.\s+[A-Z]', remaining)

            if next_section:
                end_idx = next_section.start()
                return remaining[:end_idx].strip()
            else:
                end_idx = remaining.find('\n\n')
                if end_idx != -1:
                    return remaining[:end_idx].strip()
                return remaining.strip()

        except Exception:
            return ""

    def get_conversation_log(self) -> str:
        """Get the full conversation log as a string."""
        return "\n".join(self.conversation_history)


# TEST CODE

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING DATA ANALYST AGENT (Groq)")
    print("=" * 60)

    # Create the agent
    print("\n1. Initializing agent...")
    print("-" * 40)

    try:
        agent = DataAnalystAgent()
        print(f"   Role: {agent.role}")
        print(f"   Goal: {agent.goal}")
        print(f"   Model: {agent.model}")
        print("   Agent initialized successfully!")
    except Exception as e:
        print(f"   Error initializing agent: {e}")
        exit(1)

    # Run analysis
    print("\n2. Running financial analysis for AAPL...")
    print("-" * 40)

    # Simulate sentiment data from Market Researcher
    mock_sentiment = {
        "overall_sentiment": {
            "score": 0.35,
            "label": "positive",
            "positive_articles": 4,
            "negative_articles": 1,
            "neutral_articles": 2
        }
    }

    results = agent.analyze(
        ticker="AAPL",
        days_back=30,
        sentiment_data=mock_sentiment
    )

    # Display results
    print("\n3. Analysis Results:")
    print("-" * 40)

    print(f"\n   Ticker: {results['ticker']}")
    print(f"   Company: {results['company_name']}")
    print(f"   Analysis Date: {results['analysis_date']}")
    print(f"   Period: {results['period_days']} days")

    # Key metrics summary
    metrics = results.get('key_metrics', {})
    print(f"\n   Current Price: ${metrics.get('current_price', 'N/A')}")
    print(f"   P/E Ratio: {metrics.get('pe_ratio', 'N/A')}")
    print(f"   Market Cap: {format_large_number(metrics.get('market_cap', 'N/A'))}")

    # Price stats
    stats = results.get('price_statistics', {})
    print(f"\n   Period Return: {stats.get('period_return_pct', 'N/A')}%")
    print(f"   Volatility: {stats.get('annualized_volatility_pct', 'N/A')}% (annualized)")

    # Charts created
    charts = results.get('chart_paths', {})
    print(f"\n   Charts Generated: {len(charts)}")
    for chart_type, path in charts.items():
        print(f"     - {chart_type}: {os.path.basename(path)}")

    # AI Summary
    print("\n   AI Analysis Summary:")
    print("   " + "-" * 36)
    ai_analysis = results.get('ai_analysis', {})
    summary = ai_analysis.get('summary', 'No summary available')
    words = summary.split()
    line = "   "
    for word in words:
        if len(line) + len(word) > 70:
            print(line)
            line = "   " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    print("\n4. Conversation Log:")
    print("-" * 40)
    for log in results.get('conversation_log', []):
        print(f"   {log}")

    print("\n" + "=" * 60)
    print("DATA ANALYST AGENT TEST COMPLETED!")
    print("=" * 60)
