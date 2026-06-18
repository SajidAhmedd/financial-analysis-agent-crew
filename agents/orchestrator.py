"""
Orchestrator - Coordinates all agents to produce financial reports.

ROLE: Agent Coordinator / Workflow Manager
GOAL: Manage the multi-agent pipeline from input to final report

WHAT IT DOES:
1. Receives user request (ticker symbol)
2. Initializes all required agents
3. Executes agents in the correct order
4. Passes data between agents
5. Handles errors gracefully
6. Returns the final report

WORKFLOW:
User Input → Market Researcher → Data Analyst → Report Writer → PDF Output

This is the MAIN ENTRY POINT for the entire system.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import traceback

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import validate_config
from agents.market_researcher import MarketResearcherAgent
from agents.data_analyst import DataAnalystAgent
from agents.report_writer import ReportWriterAgent

# ORCHESTRATOR CLASS
class AgentOrchestrator:
    """
    Orchestrator - The conductor of the agent orchestra.

    HOW IT WORKS:
    1. User calls run_analysis(ticker)
    2. Orchestrator initializes all agents
    3. Executes agents in sequence, passing data
    4. Collects all logs for transparency
    5. Returns final report path and metadata

    WHY THIS PATTERN:
    - Separation of concerns: Agents don't know about each other
    - Centralized control: Easy to modify workflow
    - Error isolation: One agent failing doesn't crash everything
    - Logging: Full visibility into what happened
    """

    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize the orchestrator.

        PARAMETERS:
        - progress_callback: Optional function to report progress
                            Used by Streamlit UI to show status updates
                            Signature: callback(stage: str, message: str, progress: float)
        """
        self.progress_callback = progress_callback
        self.conversation_log = []
        self.start_time = None
        self.end_time = None

        # Agent instances (created when needed)
        self.market_researcher = None
        self.data_analyst = None
        self.report_writer = None

    def log(self, message: str, stage: str = "orchestrator"):
        """
        Log orchestrator activity.

        Also calls progress_callback if provided (for UI updates).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "stage": stage,
            "message": message
        }
        self.conversation_log.append(log_entry)
        print(f"[{timestamp}] [{stage.upper()}] {message}")

    def _report_progress(self, stage: str, message: str, progress: float):
        """Report progress to callback if available."""
        self.log(message, stage)
        if self.progress_callback:
            try:
                self.progress_callback(stage, message, progress)
            except Exception as e:
                print(f"Progress callback error: {e}")

    def run_analysis(
        self,
        ticker: str,
        company_name: str = "",
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.

        THIS IS THE MAIN ENTRY POINT.

        WORKFLOW:
        1. Validate configuration
        2. Initialize agents
        3. Run Market Researcher
        4. Run Data Analyst (with sentiment data)
        5. Run Report Writer (with all data)
        6. Return results

        PARAMETERS:
        - ticker: Stock symbol (e.g., "AAPL", "GOOGL", "MSFT")
        - company_name: Optional full company name (improves news search)
        - days_back: Days of historical data to analyze

        RETURNS:
        - Dictionary with:
            - success: bool
            - pdf_path: path to generated report
            - summary: executive summary text
            - all agent outputs
            - full conversation log
        """
        self.start_time = datetime.now()
        ticker = ticker.upper().strip()

        self._report_progress("init", f"Starting analysis for {ticker}", 0.0)

        # Initialize result structure
        result = {
            "success": False,
            "ticker": ticker,
            "company_name": company_name,
            "pdf_path": None,
            "error": None,
            "market_research": None,
            "financial_analysis": None,
            "report": None,
            "conversation_log": [],
            "execution_time": None
        }

        try:
            # === STEP 0: Validate Configuration ===
            self._report_progress("init", "Validating configuration...", 0.05)
            if not validate_config():
                raise ValueError("Configuration validation failed. Check your .env file.")

            # === STEP 1: Initialize Agents ===
            self._report_progress("init", "Initializing agents...", 0.1)
            self._initialize_agents()

            # === STEP 2: Run Market Researcher ===
            self._report_progress(
                "market_research",
                f"Researching news and sentiment for {ticker}...",
                0.2
            )
            market_research = self.market_researcher.research(
                ticker=ticker,
                company_name=company_name
            )
            result["market_research"] = market_research

            # Get company name from research if not provided
            if not company_name:
                company_name = market_research.get('company_name', ticker)
                result["company_name"] = company_name

            sentiment = market_research.get('overall_sentiment', {}).get('label', 'unknown')
            self._report_progress(
                "market_research",
                f"Market research complete. Sentiment: {sentiment}",
                0.4
            )

            # === STEP 3: Run Data Analyst ===
            self._report_progress(
                "data_analysis",
                f"Analyzing financial data for {ticker}...",
                0.45
            )
            financial_analysis = self.data_analyst.analyze(
                ticker=ticker,
                days_back=days_back,
                sentiment_data=market_research  # Pass sentiment for chart
            )
            result["financial_analysis"] = financial_analysis

            # Update company name if we got it from financial data
            if not result["company_name"] or result["company_name"] == ticker:
                result["company_name"] = financial_analysis.get('company_name', ticker)

            charts_count = len(financial_analysis.get('chart_paths', {}))
            self._report_progress(
                "data_analysis",
                f"Financial analysis complete. Generated {charts_count} charts.",
                0.65
            )

            # === STEP 4: Run Report Writer ===
            self._report_progress(
                "report_writing",
                "Generating final report...",
                0.7
            )
            report = self.report_writer.write_report(
                ticker=ticker,
                market_research=market_research,
                financial_analysis=financial_analysis
            )
            result["report"] = report
            result["pdf_path"] = report.get('pdf_path')

            self._report_progress(
                "report_writing",
                "Report generation complete.",
                0.9
            )

            # === STEP 5: Finalize ===
            result["success"] = True

        except Exception as e:
            # Capture any errors
            error_msg = str(e)
            error_trace = traceback.format_exc()
            self.log(f"ERROR: {error_msg}", "error")
            self.log(f"Traceback: {error_trace}", "error")
            result["error"] = error_msg
            result["success"] = False

        finally:
            # Calculate execution time
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            result["execution_time"] = round(execution_time, 2)

            # Compile all conversation logs
            result["conversation_log"] = self._compile_conversation_logs()

            # Final progress update
            if result["success"]:
                self._report_progress(
                    "complete",
                    f"Analysis complete! Report saved. ({execution_time:.1f}s)",
                    1.0
                )
            else:
                self._report_progress(
                    "error",
                    f"Analysis failed: {result['error']}",
                    1.0
                )

        return result

    def _initialize_agents(self):
        """Initialize all agent instances."""
        self.log("Creating Market Researcher agent...", "init")
        self.market_researcher = MarketResearcherAgent()

        self.log("Creating Data Analyst agent...", "init")
        self.data_analyst = DataAnalystAgent()

        self.log("Creating Report Writer agent...", "init")
        self.report_writer = ReportWriterAgent()

        self.log("All agents initialized successfully.", "init")

    def _compile_conversation_logs(self) -> list:
        """
        Compile conversation logs from all agents.

        This creates a unified timeline of all agent activities.
        """
        all_logs = []

        # Add orchestrator logs
        for log in self.conversation_log:
            all_logs.append({
                "agent": "Orchestrator",
                "timestamp": log["timestamp"],
                "stage": log["stage"],
                "message": log["message"]
            })

        # Add Market Researcher logs
        if self.market_researcher:
            for log in self.market_researcher.conversation_history:
                all_logs.append({
                    "agent": "Market Researcher",
                    "timestamp": log.split("]")[0].replace("[", "") if "]" in log else "",
                    "stage": "market_research",
                    "message": log.split(": ", 1)[1] if ": " in log else log
                })

        # Add Data Analyst logs
        if self.data_analyst:
            for log in self.data_analyst.conversation_history:
                all_logs.append({
                    "agent": "Data Analyst",
                    "timestamp": log.split("]")[0].replace("[", "") if "]" in log else "",
                    "stage": "data_analysis",
                    "message": log.split(": ", 1)[1] if ": " in log else log
                })

        # Add Report Writer logs
        if self.report_writer:
            for log in self.report_writer.conversation_history:
                all_logs.append({
                    "agent": "Report Writer",
                    "timestamp": log.split("]")[0].replace("[", "") if "]" in log else "",
                    "stage": "report_writing",
                    "message": log.split(": ", 1)[1] if ": " in log else log
                })

        return all_logs

    def get_conversation_log_formatted(self) -> str:
        """Get a nicely formatted conversation log string."""
        logs = self._compile_conversation_logs()
        lines = []
        lines.append("=" * 60)
        lines.append("AGENT CONVERSATION LOG")
        lines.append("=" * 60)

        current_agent = None
        for log in logs:
            agent = log.get("agent", "Unknown")
            if agent != current_agent:
                lines.append(f"\n--- {agent} ---")
                current_agent = agent

            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            lines.append(f"[{timestamp}] {message}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# CONVENIENCE FUNCTION

def analyze_stock(
    ticker: str,
    company_name: str = "",
    days_back: int = 30,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze a stock.

    This is the simplest way to use the system:

    >>> from agents.orchestrator import analyze_stock
    >>> result = analyze_stock("AAPL")
    >>> print(result["pdf_path"])

    PARAMETERS:
    - ticker: Stock symbol
    - company_name: Optional company name
    - days_back: Days of history
    - progress_callback: Optional callback for progress updates

    RETURNS:
    - Complete result dictionary
    """
    orchestrator = AgentOrchestrator(progress_callback=progress_callback)
    return orchestrator.run_analysis(
        ticker=ticker,
        company_name=company_name,
        days_back=days_back
    )

# TEST CODE

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ORCHESTRATOR")
    print("=" * 60)

    test_ticker = "AAPL"

    # Create orchestrator
    print("\n1. Creating Orchestrator...")
    print("-" * 40)
    orchestrator = AgentOrchestrator()
    print("   Orchestrator created successfully!")

    # Run full analysis
    print(f"\n2. Running Full Analysis for {test_ticker}...")
    print("-" * 40)
    print("   (This will take 30-60 seconds...)\n")

    result = orchestrator.run_analysis(
        ticker=test_ticker,
        company_name="Apple Inc",
        days_back=30
    )

    # Display results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\n   Success: {result['success']}")
    print(f"   Ticker: {result['ticker']}")
    print(f"   Company: {result['company_name']}")
    print(f"   Execution Time: {result['execution_time']} seconds")

    if result['success']:
        print(f"\n   PDF Report: {result['pdf_path']}")

        # Show executive summary preview
        report = result.get('report', {})
        summary = report.get('executive_summary', '')[:200]
        print(f"\n   Executive Summary Preview:")
        print(f"   {summary}...")
    else:
        print(f"\n   Error: {result['error']}")

    # Show conversation log summary
    print(f"\n3. Conversation Log:")
    print("-" * 40)
    log_entries = result.get('conversation_log', [])
    print(f"   Total log entries: {len(log_entries)}")

    # Group by agent
    agent_counts = {}
    for log in log_entries:
        agent = log.get('agent', 'Unknown')
        agent_counts[agent] = agent_counts.get(agent, 0) + 1

    print("   Entries by agent:")
    for agent, count in agent_counts.items():
        print(f"     - {agent}: {count} entries")

    print("\n   Recent log entries:")
    for log in log_entries[-5:]:
        print(f"     [{log.get('agent')}] {log.get('message')[:50]}...")

    print("\n" + "=" * 60)
    print("ORCHESTRATOR TEST COMPLETED!")
    if result['success']:
        print(f"\nOpen your report: {result['pdf_path']}")
    print("=" * 60)