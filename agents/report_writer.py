"""
Report Writer Agent - Synthesizes all research into a professional report.

ROLE: Financial Report Writer
GOAL: Synthesize all research into a professional report

WHAT IT DOES:
1. Receives data from Market Researcher and Data Analyst
2. Uses LLM to write professional narrative sections (SINGLE API CALL)
3. Generates the final PDF report
4. Ensures consistency and professional tone

TOOLS IT USES:
- pdf_tools.generate_report()

INPUTS FROM OTHER AGENTS:
- Market Researcher: news_data, sentiment, ai_analysis
- Data Analyst: metrics, stats, charts, ai_analysis

LLM: Groq (LLaMA 3.1 70B) - Fast and high quality

OPTIMIZATION:
- Uses a SINGLE LLM call for all content to minimize latency
- Parses response to extract executive summary, analysis, and recommendations
"""

from groq import Groq
from typing import Dict, Any, Optional
from datetime import datetime
import time
import json
import re

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import GROQ_API_KEY, GROQ_MODEL, AGENT_SETTINGS
from tools.pdf_tools import generate_report

# AGENT CLASS
class ReportWriterAgent:
    """
    Report Writer Agent - Synthesizes research into professional reports.

    HOW IT WORKS:
    1. Receives compiled data from other agents
    2. Uses SINGLE LLM call to write ALL sections (optimized for speed)
    3. Parses response to extract sections
    4. Calls pdf_tools to create the final PDF

    KEY ROLE:
    - This is the FINAL agent in the pipeline
    - It produces the actual deliverable (PDF)
    - It ensures professional, consistent writing
    """

    def __init__(self):
        """Initialize the agent with its configuration."""
        # Get agent settings from config
        settings = AGENT_SETTINGS.get('report_writer', {})
        self.role = settings.get('role', 'Financial Report Writer')
        self.goal = settings.get('goal', 'Synthesize research into professional reports')

        # Initialize Groq client
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Get one free at https://console.groq.com")

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

        # Conversation history for context
        self.conversation_history = []

        # Retry settings (Groq has generous limits, but just in case)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

        # System prompt that defines agent behavior
        self.system_prompt = f"""You are a {self.role}.

Your goal is to: {self.goal}

You are the final member of a team of AI agents creating financial analysis reports.
You receive research from:
- Market Researcher: News analysis and sentiment data
- Data Analyst: Financial metrics and statistical analysis

Your responsibilities:
1. Synthesize all research into coherent narratives
2. Write in a professional, objective tone
3. Highlight key findings and insights
4. Provide balanced, data-driven recommendations
5. Ensure the report is actionable and valuable

Writing guidelines:
- Be EXTREMELY CONCISE - brevity is key
- Use clear, professional language
- Support statements with specific numbers from the data
- Present both opportunities and risks
- Never use asterisks (*) for bullets - always use dashes (-)
- No markdown formatting (no ** or ##)
- Avoid speculation or guarantees
- Include appropriate disclaimers

Remember: Your output goes directly into a PDF report.
Keep it brief, professional, and data-focused."""

    def log(self, message: str):
        """Log agent activity (for conversation tracking)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] ReportWriter: {message}"
        self.conversation_history.append(log_entry)
        print(log_entry)

    def _call_llm_with_retry(self, messages: list) -> str:
        """
        Call the LLM with retry logic for rate limiting.
        Returns None if all retries fail.
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1200
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error
                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        self.log(f"Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{self.max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.log(f"Rate limit exceeded after {self.max_retries} attempts")
                        return None
                else:
                    self.log(f"LLM error: {error_str[:100]}")
                    return None

        return None

    def write_report(
        self,
        ticker: str,
        market_research: Dict[str, Any],
        financial_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main method: Create a complete financial report.
        OPTIMIZED: Uses single LLM call for all content.
        """
        self.log(f"Starting report generation for {ticker}")

        # Extract key information
        company_name = financial_analysis.get('company_name', ticker)
        self.log(f"Writing report for: {company_name}")

        # Step 1: Compile all the data we need
        self.log("Compiling research data...")
        compiled_data = self._compile_research_data(market_research, financial_analysis)

        # Step 2: Generate ALL content in a single LLM call (OPTIMIZED)
        self.log("Generating report content (single AI call)...")
        content = self._generate_all_content(ticker, company_name, compiled_data)

        executive_summary = content['executive_summary']
        detailed_analysis = content['detailed_analysis']
        recommendations = content['recommendations']

        self.log("Content generation complete")

        # Step 3: Generate the PDF
        self.log("Generating PDF report...")

        # Combine executive summary and detailed analysis for the report
        full_ai_analysis = f"{executive_summary}\n\n{detailed_analysis}"

        pdf_path = generate_report(
            ticker=ticker,
            company_info=financial_analysis.get('company_info', {}),
            key_metrics=financial_analysis.get('key_metrics', {}),
            price_stats=financial_analysis.get('price_statistics', {}),
            news_data=market_research.get('news_data', {}),
            chart_paths=financial_analysis.get('chart_paths', {}),
            ai_analysis=full_ai_analysis,
            recommendations=recommendations
        )

        self.log(f"Report saved to: {pdf_path}")

        # Step 4: Compile results
        results = {
            "ticker": ticker.upper(),
            "company_name": company_name,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent": self.role,
            "pdf_path": pdf_path,
            "executive_summary": executive_summary,
            "detailed_analysis": detailed_analysis,
            "recommendations": recommendations,
            "conversation_log": self.conversation_history.copy()
        }

        self.log(f"Report generation complete for {ticker}")
        return results

    def _compile_research_data(
        self,
        market_research: Dict[str, Any],
        financial_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile all research data into a structured format for the LLM."""
        # Market Research Data
        news_data = market_research.get('news_data', {})
        market_sentiment = market_research.get('overall_sentiment', {})
        market_ai = market_research.get('ai_analysis', {})

        # Financial Analysis Data
        company_info = financial_analysis.get('company_info', {})
        key_metrics = financial_analysis.get('key_metrics', {})
        price_stats = financial_analysis.get('price_statistics', {})
        financial_ai = financial_analysis.get('ai_analysis', {})

        compiled = {
            # Company basics
            "company_name": company_info.get('name', 'Unknown'),
            "sector": company_info.get('sector', 'N/A'),
            "industry": company_info.get('industry', 'N/A'),
            "description": company_info.get('description', '')[:500],

            # Price info
            "current_price": key_metrics.get('current_price', 'N/A'),
            "market_cap": key_metrics.get('market_cap_formatted', 'N/A'),
            "pe_ratio": key_metrics.get('pe_ratio', 'N/A'),
            "fifty_two_week_high": key_metrics.get('fifty_two_week_high', 'N/A'),
            "fifty_two_week_low": key_metrics.get('fifty_two_week_low', 'N/A'),

            # Performance
            "period_return": price_stats.get('period_return_pct', 'N/A'),
            "volatility": price_stats.get('annualized_volatility_pct', 'N/A'),

            # Sentiment
            "sentiment_label": market_sentiment.get('label', 'unknown'),
            "sentiment_score": market_sentiment.get('score', 0),
            "positive_news": market_sentiment.get('positive_articles', 0),
            "negative_news": market_sentiment.get('negative_articles', 0),

            # AI Analysis from other agents
            "market_summary": market_ai.get('summary', ''),
            "market_themes": market_ai.get('key_themes', ''),
            "market_risks": market_ai.get('risks', ''),
            "financial_summary": financial_ai.get('summary', ''),
            "valuation_assessment": financial_ai.get('valuation', ''),
            "risk_assessment": financial_ai.get('risk', ''),
            "strengths": financial_ai.get('strengths', ''),
            "concerns": financial_ai.get('concerns', ''),
        }

        return compiled

    def _generate_all_content(
        self,
        ticker: str,
        company_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate ALL report content in a SINGLE LLM call.
        This is optimized to reduce API calls and maximize speed.
        """
        user_prompt = f"""TASK: Generate a complete financial analysis report for {company_name} ({ticker}).
You must write THREE sections. Separate each section with the exact markers shown.

=== COMPANY DATA ===
- Sector: {data['sector']}
- Industry: {data['industry']}
- Current Price: ${data['current_price']}
- Market Cap: {data['market_cap']}
- P/E Ratio: {data['pe_ratio']}
- 52-Week High: ${data['fifty_two_week_high']}
- 52-Week Low: ${data['fifty_two_week_low']}
- Period Return: {data['period_return']}%
- Volatility: {data['volatility']}%
- Market Sentiment: {data['sentiment_label']} (score: {data['sentiment_score']})
- Positive News: {data['positive_news']} articles
- Negative News: {data['negative_news']} articles

=== INSIGHTS FROM MARKET RESEARCHER ===
Summary: {data['market_summary']}
Key Themes: {data['market_themes']}
Risks: {data['market_risks']}

=== INSIGHTS FROM DATA ANALYST ===
Summary: {data['financial_summary']}
Valuation: {data['valuation_assessment']}
Risk Assessment: {data['risk_assessment']}
Strengths: {data['strengths']}
Concerns: {data['concerns']}

=== YOUR OUTPUT FORMAT ===
You MUST use these exact section markers:

---EXECUTIVE_SUMMARY---
Write exactly 3 SHORT paragraphs (150 words total max):
1. Company overview with sector/industry (2-3 sentences)
2. Key metrics: price, P/E, market cap, period return (2-3 sentences)
3. Market sentiment summary and overall assessment (2-3 sentences)

---DETAILED_ANALYSIS---
Write exactly 2 SHORT paragraphs (120 words total max):
1. Valuation assessment - is it fairly valued? (2-3 sentences)
2. Risk/reward profile with strengths and concerns (2-3 sentences)

---RECOMMENDATIONS---
Write in this EXACT format (100 words max):
Investment Considerations:
- [Key factor 1]
- [Key factor 2]
- [Key factor 3]

Risk Factors:
- [Risk 1]
- [Risk 2]

Conclusion: [One sentence balanced assessment with disclaimer]

CRITICAL RULES:
- Be CONCISE - every word must add value
- Use dashes (-) for ALL bullet points, never asterisks (*)
- Do NOT include section headers in your content
- Do NOT give direct buy/sell advice
- Do NOT use markdown formatting like ** or ##
- Keep total response under 400 words"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = self._call_llm_with_retry(messages)

        if result:
            # Parse the response into sections
            return self._parse_sections(result, ticker, company_name, data)
        else:
            # Return fallback content
            return self._get_fallback_content(ticker, company_name, data)

    def _parse_sections(
        self,
        response: str,
        ticker: str,
        company_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Parse the LLM response into separate sections."""

        # Default to fallback if parsing fails
        fallback = self._get_fallback_content(ticker, company_name, data)

        try:
            # Extract sections using markers
            exec_match = re.search(
                r'---EXECUTIVE_SUMMARY---\s*(.*?)\s*(?=---DETAILED_ANALYSIS---|$)',
                response, re.DOTALL | re.IGNORECASE
            )
            detail_match = re.search(
                r'---DETAILED_ANALYSIS---\s*(.*?)\s*(?=---RECOMMENDATIONS---|$)',
                response, re.DOTALL | re.IGNORECASE
            )
            rec_match = re.search(
                r'---RECOMMENDATIONS---\s*(.*?)$',
                response, re.DOTALL | re.IGNORECASE
            )

            executive_summary = exec_match.group(1).strip() if exec_match else fallback['executive_summary']
            detailed_analysis = detail_match.group(1).strip() if detail_match else fallback['detailed_analysis']
            recommendations = rec_match.group(1).strip() if rec_match else fallback['recommendations']

            # Validate that we got real content
            if len(executive_summary) < 100:
                executive_summary = fallback['executive_summary']
            if len(detailed_analysis) < 100:
                detailed_analysis = fallback['detailed_analysis']
            if len(recommendations) < 100:
                recommendations = fallback['recommendations']

            # Post-process: Clean up formatting
            executive_summary = self._clean_content(executive_summary)
            detailed_analysis = self._clean_content(detailed_analysis)
            recommendations = self._clean_content(recommendations)

            return {
                'executive_summary': executive_summary,
                'detailed_analysis': detailed_analysis,
                'recommendations': recommendations
            }

        except Exception as e:
            self.log(f"Error parsing LLM response: {str(e)[:50]}")
            return fallback

    def _clean_content(self, text: str) -> str:
        """Clean up LLM-generated content for PDF output."""
        # First: Replace asterisk bullets with dashes (before other processing)
        text = re.sub(r'^\s*\*\s+', '- ', text, flags=re.MULTILINE)
        # Remove markdown bold markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        # Remove markdown italic markers (single asterisks around words)
        text = re.sub(r'(?<=\s)\*(\S.*?\S)\*(?=\s|$|[.,!?])', r'\1', text)
        # Remove markdown headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _get_fallback_content(
        self,
        ticker: str,
        company_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate fallback content when API fails."""

        executive_summary = f"""{company_name} ({ticker}) is a {data['sector']} company operating in the {data['industry']} industry.

The stock is currently trading at ${data['current_price']} with a P/E ratio of {data['pe_ratio']} and a market capitalization of {data['market_cap']}. Over the analysis period, the stock has shown {data['period_return']}% returns with {data['volatility']}% annualized volatility.

Market sentiment based on recent news analysis is {data['sentiment_label']}, with a sentiment score of {data['sentiment_score']}. The analysis identified {data['positive_news']} positive articles and {data['negative_news']} negative articles in recent coverage.

This report provides a comprehensive analysis of the company's financial metrics, market position, and recent news sentiment to help inform investment decisions."""

        detailed_analysis = f"""The valuation metrics for {company_name} show a P/E ratio of {data['pe_ratio']}, which should be considered in the context of the {data['sector']} sector averages and the company's growth trajectory.

From a risk perspective, the stock exhibits {data['volatility']}% annualized volatility. The 52-week trading range spans from ${data['fifty_two_week_low']} to ${data['fifty_two_week_high']}, indicating the price movement investors have experienced over the past year.

The current market sentiment is {data['sentiment_label']}, which reflects the overall tone of recent news coverage and analyst commentary. Investors should consider both the quantitative metrics and qualitative factors when evaluating this investment opportunity."""

        recommendations = f"""INVESTMENT CONSIDERATIONS:

When evaluating {company_name} ({ticker}), investors should consider the following factors:

1. Current valuation metrics including a P/E ratio of {data['pe_ratio']}
2. Recent price performance showing {data['period_return']}% returns over the analysis period
3. Market sentiment is currently {data['sentiment_label']} based on news analysis
4. Volatility of {data['volatility']}% suggests the level of price fluctuation to expect

RISK FACTORS TO MONITOR:

- Overall market conditions and sector-specific trends
- Company earnings reports and guidance
- Competitive landscape changes
- Macroeconomic factors affecting the {data['sector']} sector

CONCLUSION:

This analysis provides a data-driven overview of {company_name}'s current financial position and market sentiment. Investors should conduct their own due diligence and consider their individual risk tolerance and investment objectives before making any investment decisions. This AI-generated report is for informational purposes only and does not constitute financial advice."""

        return {
            'executive_summary': executive_summary,
            'detailed_analysis': detailed_analysis,
            'recommendations': recommendations
        }

    def get_conversation_log(self) -> str:
        """Get the full conversation log as a string."""
        return "\n".join(self.conversation_history)


# TEST CODE
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING REPORT WRITER AGENT (Groq)")
    print("=" * 60)

    # Import other agents to get real data
    from agents.market_researcher import MarketResearcherAgent
    from agents.data_analyst import DataAnalystAgent

    test_ticker = "AAPL"

    # Step 1: Initialize all agents
    print("\n1. Initializing agents...")
    print("-" * 40)

    try:
        market_researcher = MarketResearcherAgent()
        print(f"   Market Researcher: Ready")

        data_analyst = DataAnalystAgent()
        print(f"   Data Analyst: Ready")

        report_writer = ReportWriterAgent()
        print(f"   Report Writer: Ready")
        print(f"\n   Role: {report_writer.role}")
        print(f"   Goal: {report_writer.goal}")
        print(f"   Model: {report_writer.model}")
    except Exception as e:
        print(f"   Error initializing agents: {e}")
        exit(1)

    # Step 2: Run Market Research
    print("\n2. Running Market Research...")
    print("-" * 40)
    market_research = market_researcher.research(
        ticker=test_ticker,
        company_name="Apple Inc"
    )
    print(f"   Sentiment: {market_research.get('overall_sentiment', {}).get('label', 'unknown')}")

    # Step 3: Run Financial Analysis
    print("\n3. Running Financial Analysis...")
    print("-" * 40)
    financial_analysis = data_analyst.analyze(
        ticker=test_ticker,
        days_back=30,
        sentiment_data=market_research
    )
    print(f"   Charts created: {len(financial_analysis.get('chart_paths', {}))}")

    # Step 4: Generate Report
    print("\n4. Generating Final Report...")
    print("-" * 40)
    report = report_writer.write_report(
        ticker=test_ticker,
        market_research=market_research,
        financial_analysis=financial_analysis
    )

    # Display results
    print("\n5. Report Results:")
    print("-" * 40)
    print(f"\n   Ticker: {report['ticker']}")
    print(f"   Company: {report['company_name']}")
    print(f"   Report Date: {report['report_date']}")
    print(f"\n   PDF Path: {report['pdf_path']}")

    print("\n   Executive Summary Preview:")
    print("   " + "-" * 36)
    summary = report.get('executive_summary', '')[:300]
    print(f"   {summary}...")

    print("\n6. Conversation Log:")
    print("-" * 40)
    for log in report.get('conversation_log', []):
        print(f"   {log}")

    print("\n" + "=" * 60)
    print("REPORT WRITER AGENT TEST COMPLETED!")
    print(f"\nOpen the report: {report['pdf_path']}")
    print("=" * 60)
