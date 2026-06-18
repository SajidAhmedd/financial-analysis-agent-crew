"""
Financial Analysis Agent Crew - Streamlit UI

A modern, dark-themed interface for the multi-agent financial analysis system.
Features:
- Live agent conversation console
- Glassmorphism design elements
- Real-time progress tracking
- Professional dashboard layout
"""

import streamlit as st
import time
from datetime import datetime
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.orchestrator import AgentOrchestrator
from tools.finance_tools import get_company_info

# =============================================================================
# PAGE CONFIG & CUSTOM CSS
# =============================================================================

st.set_page_config(
    page_title="Financial Agent Crew",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for unique styling
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    * {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom Header */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
        letter-spacing: -1px;
    }

    .sub-header {
        color: #8892b0;
        font-size: 1rem;
        font-weight: 400;
        margin-top: -10px;
        margin-bottom: 30px;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .glass-card-highlight {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 24px;
        margin-bottom: 20px;
    }

    /* Agent Console */
    .console-container {
        background: #0d1117;
        border-radius: 12px;
        border: 1px solid #30363d;
        padding: 0;
        font-family: 'JetBrains Mono', monospace;
        overflow: hidden;
    }

    .console-header {
        background: #161b22;
        padding: 12px 16px;
        border-bottom: 1px solid #30363d;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .console-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }

    .console-dot-red { background: #ff5f56; }
    .console-dot-yellow { background: #ffbd2e; }
    .console-dot-green { background: #27ca40; }

    .console-title {
        color: #8b949e;
        font-size: 0.85rem;
        margin-left: 8px;
    }

    .console-body {
        padding: 16px;
        max-height: 400px;
        overflow-y: auto;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .console-line {
        margin: 4px 0;
    }

    .console-timestamp {
        color: #6e7681;
    }

    .console-agent-orchestrator { color: #58a6ff; }
    .console-agent-researcher { color: #a371f7; }
    .console-agent-analyst { color: #3fb950; }
    .console-agent-writer { color: #f78166; }
    .console-message { color: #c9d1d9; }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-running {
        background: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        border: 1px solid rgba(56, 139, 253, 0.4);
    }

    .status-success {
        background: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
    }

    .status-error {
        background: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.4);
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 20px;
        text-align: center;
        margin: 6px 3px;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .metric-label {
        color: #8892b0;
        font-size: 0.8rem;
        margin-top: 4px;
        white-space: nowrap;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 32px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: white;
        font-size: 1.1rem;
        padding: 12px 16px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }

    /* Progress Animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .pulse-animation {
        animation: pulse 2s infinite;
    }

    /* Agent Cards */
    .agent-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }

    .agent-card:hover {
        border-color: rgba(102, 126, 234, 0.3);
        transform: translateX(4px);
    }

    .agent-icon {
        font-size: 1.5rem;
        margin-right: 12px;
    }

    .agent-name {
        color: #e6e6e6;
        font-weight: 600;
        font-size: 1rem;
    }

    .agent-status {
        color: #8892b0;
        font-size: 0.85rem;
    }

    /* Sidebar */
    .css-1d391kg {
        background: rgba(15, 15, 26, 0.8);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Download Button */
    .download-btn {
        background: linear-gradient(90deg, #3fb950 0%, #2ea043 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(46, 160, 67, 0.4);
    }

    /* Divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 30px 0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# HELPER FUNCTIONS

def render_header():
    """Render the main header."""
    st.markdown('<h1 class="main-header">Financial Agent Crew</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Multi-Agent Stock Analysis System</p>', unsafe_allow_html=True)


def render_agent_console(logs: list, is_running: bool = False):
      """Render the terminal-style agent console."""

      status = "● RUNNING" if is_running else "● READY"
      status_class = "pulse-animation" if is_running else ""

      # Build log lines
      if not logs:
          content = '<div style="color: #6e7681;">Waiting for analysis to start...</div>'
      else:
          lines = []
          for log in logs[-25:]:
              agent = log.get('agent', 'System')
              message = log.get('message', '')
              timestamp = log.get('timestamp', '')

              # Skip verbose API error messages and backend noise
              skip_keywords = [
                  'generativelanguage.googleapis.com',
                  'quota_metric',
                  'quota_dimensions',
                  'retry_delay',
                  'violations',
                  'FreeTier',
                  'Please retry',
                  'limit:',
                  'links {',
                  'url:',
                  'Error code: 400',
                  'Error code: 429',
                  'error_code',
                  "'error':",
                  '"error":',
                  'model `llama',
                  'Rate limited',
                  'LLM error:',
                  'Error in LLM',
              ]

              if any(keyword in message for keyword in skip_keywords):
                  continue

              # Skip empty messages
              if not message.strip():
                  continue

              # Color based on agent
              agent_colors = {
                  'Orchestrator': '#58a6ff',
                  'Market Researcher': '#a371f7',
                  'Data Analyst': '#3fb950',
                  'Report Writer': '#f78166',
                  'Init': '#58a6ff',
                  'Market_Research': '#a371f7',
                  'Data_Analysis': '#3fb950',
                  'Report_Writing': '#f78166',
                  'System': '#58a6ff',
                  'Complete': '#3fb950',
                  'Error': '#f85149'
              }
              color = agent_colors.get(agent, '#58a6ff')

              # Truncate very long messages
              if len(message) > 100:
                  message = message[:100] + "..."

              lines.append(f'''<div style="margin: 4px 0;">
                  <span style="color: #6e7681;">[{timestamp}]</span>
                  <span style="color: {color}; font-weight: 600;">[{agent}]</span>
                  <span style="color: #c9d1d9;">{message}</span>
              </div>''')

          content = ''.join(lines) if lines else '<div style="color: #6e7681;">Processing...</div>'

      # Render the console
      st.markdown(f"""
          <div style="
              background: #0d1117;
              border-radius: 12px;
              border: 1px solid #30363d;
              overflow: hidden;
              font-family: 'JetBrains Mono', 'Courier New', monospace;
          ">
              <div style="
                  background: #161b22;
                  padding: 12px 16px;
                  border-bottom: 1px solid #30363d;
                  display: flex;
                  align-items: center;
                  gap: 8px;
              ">
                  <span style="width: 12px; height: 12px; border-radius: 50%; background: #ff5f56; display: inline-block;"></span>
                  <span style="width: 12px; height: 12px; border-radius: 50%; background: #ffbd2e; display: inline-block;"></span>
                  <span style="width: 12px; height: 12px; border-radius: 50%; background: #27ca40; display: inline-block;"></span>
                  <span style="color: #8b949e; font-size: 0.85rem; margin-left: 8px;">Agent Console</span>
                  <span class="{status_class}" style="color: #3fb950; margin-left: auto;">{status}</span>
              </div>
              <div style="padding: 16px; max-height: 400px; overflow-y: auto; font-size: 0.85rem; line-height: 1.6;">
                  {content}
              </div>
          </div>
      """, unsafe_allow_html=True)

def render_metric_card(value: str, label: str):
    """Render a styled metric card."""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)


def format_logs_for_export(logs: list, ticker: str, result: dict = None) -> str:
    """Format conversation logs for text file export."""
    lines = []
    lines.append("=" * 60)
    lines.append("FINANCIAL ANALYSIS AGENT CREW - CONVERSATION LOG")
    lines.append("=" * 60)
    lines.append(f"Ticker: {ticker.upper()}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    if result:
        exec_time = result.get("execution_time", "N/A")
        lines.append(f"Total Execution Time: {exec_time} seconds")
        lines.append("")

    lines.append("-" * 60)
    lines.append("AGENT CONVERSATION LOG")
    lines.append("-" * 60)
    lines.append("")

    for log in logs:
        agent = log.get('agent', 'System')
        message = log.get('message', '')
        timestamp = log.get('timestamp', '')

        if message.strip():
            lines.append(f"[{timestamp}] {agent}:")
            lines.append(f"  {message}")
            lines.append("")

    lines.append("-" * 60)
    lines.append("END OF LOG")
    lines.append("-" * 60)

    return "\n".join(lines)


def save_logs_to_file(logs: list, ticker: str, result: dict = None) -> str:
    """Save conversation logs to a file and return the path."""
    from config.settings import OUTPUT_DIR

    # Ensure output directory exists
    log_dir = os.path.join(OUTPUT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ticker.upper()}_conversation_log_{timestamp}.txt"
    filepath = os.path.join(log_dir, filename)

    # Format and save
    content = format_logs_for_export(logs, ticker, result)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def render_agent_status(agent_name: str, icon: str, status: str, is_active: bool = False):
    """Render an agent status card."""
    status_color = "#3fb950" if status == "Complete" else "#58a6ff" if is_active else "#6e7681"
    pulse = "pulse-animation" if is_active else ""

    st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 12px 16px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div>
                <span style="font-size: 1.2rem; margin-right: 10px;">{icon}</span>
                <span style="color: #e6e6e6; font-weight: 600;">{agent_name}</span>
            </div>
            <span class="{pulse}" style="color: {status_color}; font-size: 0.85rem;">
                {status}
            </span>
        </div>
    """, unsafe_allow_html=True)


# SIDEBAR

with st.sidebar:
    st.markdown("### 🎯 Analysis Settings")
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Ticker input
    ticker = st.text_input(
        "Stock Ticker",
        value="AAPL",
        placeholder="e.g., AAPL, GOOGL, MSFT",
        help="Enter the stock symbol you want to analyze"
    ).upper().strip()

    # Company name (optional)
    company_name = st.text_input(
        "Company Name (Optional)",
        value="",
        placeholder="e.g., Apple Inc",
        help="Providing the company name improves news search results"
    )

    # Days to analyze
    days_back = st.selectbox(
        "Analysis Period",
        options=[7, 14, 30, 60, 90],
        index=2,
        format_func=lambda x: f"{x} days"
    )

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Agent status section
    st.markdown("### 🤖 Agent Status")

    # Placeholders for agent status (will be updated during analysis)
    agent_status_placeholder = st.empty()

    with agent_status_placeholder.container():
        render_agent_status("Market Researcher", "🔍", "Standby")
        render_agent_status("Data Analyst", "📊", "Standby")
        render_agent_status("Report Writer", "📝", "Standby")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Run button
    run_analysis = st.button("🚀 Run Analysis", use_container_width=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Info
    st.markdown("""
        <div style="color: #6e7681; font-size: 0.8rem;">
            <strong>How it works:</strong><br>
            1. Market Researcher gathers news<br>
            2. Data Analyst crunches numbers<br>
            3. Report Writer creates PDF<br><br>
            <em>Powered by Groq AI</em>
        </div>
    """, unsafe_allow_html=True)


# MAIN CONTENT

# Header
render_header()

# Create main layout columns
col_main, col_side = st.columns([2, 1])

with col_main:
    # Agent Console
    st.markdown("### 💻 Agent Console")
    console_placeholder = st.empty()

    # Initialize session state
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    with console_placeholder.container():
        render_agent_console(st.session_state.logs, is_running=False)

with col_side:
    # Quick stats placeholder
    st.markdown("### 📈 Quick Stats")
    stats_placeholder = st.empty()

    with stats_placeholder.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"""
            <div style="text-align: center; padding: 20px; color: #6e7681;">
                Enter a ticker and click<br>
                <strong style="color: #e6e6e6;">Run Analysis</strong><br>
                to get started
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Results section placeholder
results_placeholder = st.empty()


# ANALYSIS EXECUTION

if run_analysis:
    if not ticker:
        st.error("Please enter a stock ticker!")
    else:
        # Clear previous results
        st.session_state.logs = []

        # Progress tracking
        progress_data = {"stage": "init", "message": "", "progress": 0}

        def progress_callback(stage: str, message: str, progress: float):
            """Callback to update UI during analysis."""
            progress_data["stage"] = stage
            progress_data["message"] = message
            progress_data["progress"] = progress

            # Add to logs
            st.session_state.logs.append({
                "agent": stage.replace("_", " ").title(),
                "message": message,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

        # Update agent statuses
        with agent_status_placeholder.container():
            render_agent_status("Market Researcher", "🔍", "Running...", is_active=True)
            render_agent_status("Data Analyst", "📊", "Waiting")
            render_agent_status("Report Writer", "📝", "Waiting")

        # Show running console
        with console_placeholder.container():
            render_agent_console([{
                "agent": "System",
                "message": f"Initializing analysis for {ticker}...",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }], is_running=True)

        # Run the analysis
        with st.spinner(""):
            orchestrator = AgentOrchestrator(progress_callback=progress_callback)
            result = orchestrator.run_analysis(
                ticker=ticker,
                company_name=company_name,
                days_back=days_back
            )

        # Store result in session state so it persists after download
        st.session_state.analysis_result = result
        st.session_state.analysis_complete = True

        # Update final agent statuses
        with agent_status_placeholder.container():
            if result["success"]:
                render_agent_status("Market Researcher", "🔍", "Complete")
                render_agent_status("Data Analyst", "📊", "Complete")
                render_agent_status("Report Writer", "📝", "Complete")
            else:
                render_agent_status("Market Researcher", "🔍", "Error")
                render_agent_status("Data Analyst", "📊", "Error")
                render_agent_status("Report Writer", "📝", "Error")

        # Update console with final logs
        with console_placeholder.container():
            render_agent_console(result.get("conversation_log", []), is_running=False)

        # Show results
        if result["success"]:
            # Update quick stats
            with stats_placeholder.container():
                metrics = result.get("financial_analysis", {}).get("key_metrics", {})
                sentiment = result.get("market_research", {}).get("overall_sentiment", {})

                col1, col2 = st.columns(2, gap="small")
                with col1:
                    price = metrics.get("current_price", "N/A")
                    render_metric_card(f"${price}" if price != "N/A" else "N/A", "Current Price")
                with col2:
                    sent_label = sentiment.get("label", "N/A").upper()
                    render_metric_card(sent_label, "Sentiment")

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                col3, col4 = st.columns(2, gap="small")
                with col3:
                    pe = metrics.get("pe_ratio", "N/A")
                    pe_str = f"{pe:.1f}" if isinstance(pe, (int, float)) else "N/A"
                    render_metric_card(pe_str, "P/E Ratio")
                with col4:
                    exec_time = result.get("execution_time", 0)
                    render_metric_card(f"{exec_time}s", "Time")

            # Results section
            with results_placeholder.container():
                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
                st.markdown("### 📄 Analysis Results")

                # Success message with download
                st.markdown(f"""
                    <div class="glass-card-highlight">
                        <h3 style="color: #3fb950; margin-top: 0;">✅ Analysis Complete!</h3>
                        <p style="color: #c9d1d9;">
                            Successfully analyzed <strong>{result['company_name']}</strong> ({ticker})
                        </p>
                        <p style="color: #8892b0; font-size: 0.9rem;">
                            Report generated in {result['execution_time']} seconds
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                # Download button
                pdf_path = result.get("pdf_path")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    col_pdf, col_log = st.columns(2)
                    with col_pdf:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col_log:
                        # Download conversation log
                        log_content = format_logs_for_export(
                            result.get("conversation_log", []),
                            ticker,
                            result
                        )
                        st.download_button(
                            label="📋 Download Log",
                            data=log_content,
                            file_name=f"{ticker.upper()}_conversation_log.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                # Executive Summary
                report = result.get("report", {})
                if report.get("executive_summary"):
                    with st.expander("📋 Executive Summary", expanded=True):
                        st.markdown(f"""
                            <div style="color: #c9d1d9; line-height: 1.8;">
                                {report['executive_summary']}
                            </div>
                        """, unsafe_allow_html=True)

                # Show charts
                charts = result.get("financial_analysis", {}).get("chart_paths", {})
                if charts:
                    with st.expander("📊 Generated Charts", expanded=True):
                        chart_cols = st.columns(len(charts))
                        for idx, (chart_type, chart_path) in enumerate(charts.items()):
                            if os.path.exists(chart_path):
                                with chart_cols[idx]:
                                    st.image(chart_path, caption=chart_type.title(), use_container_width=True)

                # Recommendations
                if report.get("recommendations"):
                    with st.expander("💡 Recommendations"):
                        st.markdown(f"""
                            <div style="color: #c9d1d9; line-height: 1.8;">
                                {report['recommendations']}
                            </div>
                        """, unsafe_allow_html=True)

                # Full conversation log
                with st.expander("🔍 Full Agent Conversation Log"):
                    for log in result.get("conversation_log", []):
                        agent = log.get("agent", "Unknown")
                        message = log.get("message", "")
                        timestamp = log.get("timestamp", "")

                        agent_color = {
                            "Orchestrator": "#58a6ff",
                            "Market Researcher": "#a371f7",
                            "Data Analyst": "#3fb950",
                            "Report Writer": "#f78166"
                        }.get(agent, "#8892b0")

                        st.markdown(f"""
                            <div style="margin: 8px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                                <span style="color: #6e7681;">[{timestamp}]</span>
                                <span style="color: {agent_color};">[{agent}]</span>
                                <span style="color: #c9d1d9;">{message}</span>
                            </div>
                        """, unsafe_allow_html=True)

        else:
            # Error state
            with results_placeholder.container():
                st.markdown(f"""
                    <div class="glass-card" style="border-color: rgba(248, 81, 73, 0.4);">
                        <h3 style="color: #f85149; margin-top: 0;">❌ Analysis Failed</h3>
                        <p style="color: #c9d1d9;">
                            {result.get('error', 'Unknown error occurred')}
                        </p>
                        <p style="color: #8892b0; font-size: 0.9rem;">
                            Please check the console log above for details.
                        </p>
                    </div>
                """, unsafe_allow_html=True)


# DISPLAY PERSISTED RESULTS (when not running new analysis)

# If we have results from a previous run, display them
elif st.session_state.analysis_complete and st.session_state.analysis_result:
    result = st.session_state.analysis_result

    # Update agent statuses from stored result
    with agent_status_placeholder.container():
        if result.get("success"):
            render_agent_status("Market Researcher", "🔍", "Complete")
            render_agent_status("Data Analyst", "📊", "Complete")
            render_agent_status("Report Writer", "📝", "Complete")
        else:
            render_agent_status("Market Researcher", "🔍", "Standby")
            render_agent_status("Data Analyst", "📊", "Standby")
            render_agent_status("Report Writer", "📝", "Standby")

    # Update console with stored logs
    with console_placeholder.container():
        render_agent_console(result.get("conversation_log", []), is_running=False)

    if result.get("success"):
        # Update quick stats from stored result
        with stats_placeholder.container():
            metrics = result.get("financial_analysis", {}).get("key_metrics", {})
            sentiment = result.get("market_research", {}).get("overall_sentiment", {})

            col1, col2 = st.columns(2, gap="small")
            with col1:
                price = metrics.get("current_price", "N/A")
                render_metric_card(f"${price}" if price != "N/A" else "N/A", "Current Price")
            with col2:
                sent_label = sentiment.get("label", "N/A").upper()
                render_metric_card(sent_label, "Sentiment")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            col3, col4 = st.columns(2, gap="small")
            with col3:
                pe = metrics.get("pe_ratio", "N/A")
                pe_str = f"{pe:.1f}" if isinstance(pe, (int, float)) else "N/A"
                render_metric_card(pe_str, "P/E Ratio")
            with col4:
                exec_time = result.get("execution_time", 0)
                render_metric_card(f"{exec_time}s", "Time")

        # Results section from stored data
        with results_placeholder.container():
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 📄 Analysis Results")

            # Success message with download
            st.markdown(f"""
                <div class="glass-card-highlight">
                    <h3 style="color: #3fb950; margin-top: 0;">✅ Analysis Complete!</h3>
                    <p style="color: #c9d1d9;">
                        Successfully analyzed <strong>{result.get('company_name', 'Unknown')}</strong> ({result.get('ticker', 'N/A')})
                    </p>
                    <p style="color: #8892b0; font-size: 0.9rem;">
                        Report generated in {result.get('execution_time', 0)} seconds
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Download buttons
            pdf_path = result.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                col_pdf, col_log = st.columns(2)
                with col_pdf:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_persisted"
                    )
                with col_log:
                    # Download conversation log
                    stored_ticker = result.get('ticker', 'UNKNOWN')
                    log_content = format_logs_for_export(
                        result.get("conversation_log", []),
                        stored_ticker,
                        result
                    )
                    st.download_button(
                        label="📋 Download Log",
                        data=log_content,
                        file_name=f"{stored_ticker.upper()}_conversation_log.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="download_log_persisted"
                    )

            # Executive Summary
            report = result.get("report", {})
            if report.get("executive_summary"):
                with st.expander("📋 Executive Summary", expanded=True):
                    st.markdown(f"""
                        <div style="color: #c9d1d9; line-height: 1.8;">
                            {report['executive_summary']}
                        </div>
                    """, unsafe_allow_html=True)

            # Show charts
            charts = result.get("financial_analysis", {}).get("chart_paths", {})
            if charts:
                with st.expander("📊 Generated Charts", expanded=True):
                    chart_cols = st.columns(len(charts))
                    for idx, (chart_type, chart_path) in enumerate(charts.items()):
                        if os.path.exists(chart_path):
                            with chart_cols[idx]:
                                st.image(chart_path, caption=chart_type.title(), use_container_width=True)

            # Recommendations
            if report.get("recommendations"):
                with st.expander("💡 Recommendations"):
                    st.markdown(f"""
                        <div style="color: #c9d1d9; line-height: 1.8;">
                            {report['recommendations']}
                        </div>
                    """, unsafe_allow_html=True)

            # Full conversation log
            with st.expander("🔍 Full Agent Conversation Log"):
                for log in result.get("conversation_log", []):
                    agent = log.get("agent", "Unknown")
                    message = log.get("message", "")
                    timestamp = log.get("timestamp", "")

                    agent_color = {
                        "Orchestrator": "#58a6ff",
                        "Market Researcher": "#a371f7",
                        "Data Analyst": "#3fb950",
                        "Report Writer": "#f78166"
                    }.get(agent, "#8892b0")

                    st.markdown(f"""
                        <div style="margin: 8px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                            <span style="color: #6e7681;">[{timestamp}]</span>
                            <span style="color: {agent_color};">[{agent}]</span>
                            <span style="color: #c9d1d9;">{message}</span>
                        </div>
                    """, unsafe_allow_html=True)


# FOOTER
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; color: #6e7681; font-size: 0.8rem; padding: 20px;">
        <strong>Financial Agent Crew</strong> · Built with Streamlit & Groq AI<br>
        Multi-Agent System for Automated Stock Analysis
    </div>
""", unsafe_allow_html=True)