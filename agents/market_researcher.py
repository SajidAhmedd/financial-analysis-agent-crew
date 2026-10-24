"""
Market Researcher Agent - Gathers and analyzes market news.

ROLE: Market Research Analyst
GOAL: Gather and analyze market news, sentiment, and trends

WHAT IT DOES:
1. Searches for news about a given stock
2. Analyzes sentiment of the news
3. Identifies key themes and trends
4. Provides summary for the report

TOOLS IT USES:
- news_tools.search_stock_news()
- news_tools.analyze_sentiment()

LLM: Mistral / Groq / Gemini with automatic fallback (config/llm_client.py)
"""

from config.llm_client import LLMClient
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import AGENT_SETTINGS
from tools.news_tools import search_stock_news, analyze_sentiment

# AGENT CLASS

class MarketResearcherAgent:
    """
    Market Researcher Agent - Specializes in news and sentiment analysis.

    HOW IT WORKS:
    1. Agent receives a task (e.g., "Research news for AAPL")
    2. Agent uses tools to gather data (news search)
    3. Agent uses LLM to analyze and summarize findings
    4. Agent returns structured results

    WHY A CLASS:
    - Encapsulates all agent logic
    - Maintains state (conversation history)
    - Easy to configure and extend
    """

    def __init__(self):
        """Initialize the agent with its configuration."""
        # Get agent settings from config
        settings = AGENT_SETTINGS.get('market_researcher', {})
        self.role = settings.get('role', 'Market Research Analyst')
        self.goal = settings.get('goal', 'Gather and analyze market news')

        # LLM client - tries each provider in LLM_PROVIDERS in order (see config/llm_client.py)
        self.client = LLMClient()
        self.model = self.client.model

        # Conversation history for context
        self.conversation_history = []

        # System prompt that defines agent behavior
        self.system_prompt = f"""You are a {self.role}.

Your goal is to: {self.goal}

You are part of a team of AI agents working together to create financial analysis reports.
Your specific responsibilities are:
1. Search for and gather recent news about stocks
2. Analyze the sentiment of news articles (positive, negative, neutral)
3. Identify key themes, trends, and important events
4. Summarize your findings in a clear, professional manner

When analyzing news:
- Focus on facts and data, not speculation
- Note any significant events (earnings, product launches, lawsuits, etc.)
- Identify the overall market sentiment
- Highlight any risks or opportunities mentioned in the news

Always be objective and professional in your analysis."""

    def log(self, message: str):
        """Log agent activity (for conversation tracking)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] MarketResearcher: {message}"
        self.conversation_history.append(log_entry)
        print(log_entry)

    def research(self, ticker: str, company_name: str = "") -> Dict[str, Any]:
        """
        Main method: Research news and sentiment for a stock.

        WHAT IT DOES:
        1. Uses news_tools to fetch articles
        2. Uses the LLM to analyze and summarize
        3. Returns structured findings

        PARAMETERS:
        - ticker: Stock symbol (e.g., "AAPL")
        - company_name: Full company name for better search

        RETURNS:
        - Dictionary with news data, sentiment, and AI analysis
        """
        self.log(f"Starting research for {ticker} ({company_name})")

        # Step 1: Gather news using our tool
        self.log("Searching for news articles...")
        news_data = search_stock_news(
            ticker=ticker,
            company_name=company_name,
            max_results=10
        )

        articles_count = news_data.get('total_articles', 0)
        self.log(f"Found {articles_count} news articles")

        # Step 2: Prepare data for LLM analysis
        news_summary = self._format_news_for_analysis(news_data)

        # Step 3: Use the LLM to analyze the news
        self.log("Analyzing news with AI...")
        ai_analysis = self._analyze_with_llm(ticker, company_name, news_summary, news_data)

        # Step 4: Compile results
        results = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "research_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent": self.role,
            "news_data": news_data,
            "overall_sentiment": news_data.get('overall_sentiment', {}),
            "ai_analysis": ai_analysis,
            "conversation_log": self.conversation_history.copy()
        }

        self.log(f"Research complete for {ticker}")
        return results

    def _format_news_for_analysis(self, news_data: Dict[str, Any]) -> str:
        """Format news articles into a text summary for the LLM."""
        lines = []
        lines.append(f"NEWS ARTICLES ({news_data.get('total_articles', 0)} found):")
        lines.append(f"Overall Sentiment: {news_data.get('overall_sentiment', {}).get('label', 'unknown')}")
        lines.append("")

        for i, article in enumerate(news_data.get('articles', [])[:10], 1):
            sentiment = article.get('sentiment', {}).get('label', 'unknown')
            lines.append(f"{i}. [{sentiment.upper()}] {article.get('title', 'No title')}")
            lines.append(f"   Source: {article.get('source', 'Unknown')}")
            if article.get('snippet'):
                lines.append(f"   Summary: {article.get('snippet', '')[:200]}")
            lines.append("")

        return "\n".join(lines)

    def _analyze_with_llm(
        self,
        ticker: str,
        company_name: str,
        news_summary: str,
        news_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Use the LLM to analyze the news and provide insights.

        WHAT THE LLM DOES:
        1. Reads the news summary
        2. Identifies key themes and events
        3. Assesses overall sentiment
        4. Provides actionable insights
        """
        user_prompt = f"""TASK: Analyze the following news for {company_name} ({ticker}) and provide your assessment.

{news_summary}

Please provide your analysis in the following format:

1. SENTIMENT ASSESSMENT:
Provide a 2-3 sentence assessment of the overall market sentiment based on the news.

2. KEY THEMES:
List 3-5 key themes or topics appearing in the news.

3. NOTABLE EVENTS:
List any significant events mentioned (earnings, product launches, partnerships, etc.)

4. RISKS AND CONCERNS:
Note any risks or concerns mentioned in the news.

5. OPPORTUNITIES:
Note any positive developments or opportunities mentioned.

6. SUMMARY:
Provide a brief 3-4 sentence executive summary of your findings.

Be concise, professional, and objective in your analysis."""

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
                "sentiment_assessment": self._extract_section(analysis_text, "SENTIMENT ASSESSMENT"),
                "key_themes": self._extract_section(analysis_text, "KEY THEMES"),
                "notable_events": self._extract_section(analysis_text, "NOTABLE EVENTS"),
                "risks": self._extract_section(analysis_text, "RISKS AND CONCERNS"),
                "opportunities": self._extract_section(analysis_text, "OPPORTUNITIES"),
                "summary": self._extract_section(analysis_text, "SUMMARY"),
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

            # Find the next section (numbered item or double newline)
            remaining = text[start_idx:]

            # Look for next numbered section
            import re
            next_section = re.search(r'\n\d+\.\s+[A-Z]', remaining)

            if next_section:
                end_idx = next_section.start()
                return remaining[:end_idx].strip()
            else:
                # Return until double newline or end
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
    print("TESTING MARKET RESEARCHER AGENT")
    print("=" * 60)

    # Create the agent
    print("\n1. Initializing agent...")
    print("-" * 40)

    try:
        agent = MarketResearcherAgent()
        print(f"   Role: {agent.role}")
        print(f"   Goal: {agent.goal}")
        print(f"   Model: {agent.model}")
        print("   Agent initialized successfully!")
    except Exception as e:
        print(f"   Error initializing agent: {e}")
        exit(1)

    # Run research
    print("\n2. Running research for AAPL...")
    print("-" * 40)

    results = agent.research(
        ticker="AAPL",
        company_name="Apple Inc"
    )

    # Display results
    print("\n3. Research Results:")
    print("-" * 40)

    print(f"\n   Ticker: {results['ticker']}")
    print(f"   Company: {results['company_name']}")
    print(f"   Research Date: {results['research_date']}")

    sentiment = results.get('overall_sentiment', {})
    print(f"\n   Overall Sentiment: {sentiment.get('label', 'unknown').upper()}")
    print(f"   Sentiment Score: {sentiment.get('score', 0)}")

    print("\n   AI Analysis Summary:")
    print("   " + "-" * 36)
    ai_analysis = results.get('ai_analysis', {})
    summary = ai_analysis.get('summary', 'No summary available')
    # Print summary with word wrap
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
    print("MARKET RESEARCHER AGENT TEST COMPLETED!")
    print("=" * 60)
