# Financial Analysis Agent Crew

AI-powered multi-agent system for comprehensive stock analysis. Uses specialized AI agents to research market news, analyze financial data, and generate professional PDF reports.

## Features

- **Multi-Agent Architecture**: Three specialized AI agents work together
  - Market Researcher: Gathers and analyzes news sentiment
  - Data Analyst: Analyzes financial metrics and creates charts
  - Report Writer: Synthesizes findings into professional reports

- **Real-Time Data**: Fetches live stock data from Yahoo Finance
- **News Sentiment Analysis**: Analyzes recent news to gauge market sentiment
- **Professional PDF Reports**: Generates comprehensive financial analysis reports
- **Interactive Dashboard**: Modern Streamlit UI with real-time progress tracking

## Quick Start

### 1. Clone and Setup

```bash
cd financial_analysis_agent_crew
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- **GROQ_API_KEY** (Required): Get free at https://console.groq.com
- **NEWS_API_KEY** (Optional): Get free at https://newsapi.org

### 3. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

1. Enter a stock ticker (e.g., AAPL, MSFT, GOOGL)
2. Set the analysis period (days)
3. Click "Run Analysis"
4. Download the PDF report and conversation log

## Project Structure

```
financial_analysis_agent_crew/
├── agents/
│   ├── market_researcher.py   # News & sentiment analysis
│   ├── data_analyst.py        # Financial data analysis
│   ├── report_writer.py       # Report generation
│   └── orchestrator.py        # Agent coordination
├── tools/
│   ├── finance_tools.py       # Yahoo Finance integration
│   ├── news_tools.py          # News fetching
│   ├── chart_tools.py         # Visualization
│   └── pdf_tools.py           # PDF generation
├── config/
│   └── settings.py            # Configuration
├── output/                    # Generated reports
├── app.py                     # Streamlit UI
├── requirements.txt
└── .env.example
```

## Technology Stack

- **LLM**: Groq (LLaMA 3.3 70B)
- **UI**: Streamlit
- **Data**: Yahoo Finance, NewsAPI
- **Visualization**: Matplotlib, Plotly
- **PDF**: FPDF2

## License

MIT License
