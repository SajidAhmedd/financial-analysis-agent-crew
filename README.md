---
title: Financial Analysis Agent Crew
emoji: 📈
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
short_description: AI agents that research a stock and write a PDF report
---

# Financial Analysis Agent Crew

AI-powered multi-agent system for comprehensive stock analysis. Uses specialized AI agents to research market news, analyze financial data, and generate professional PDF reports.

**Live demo: [finance.sajidahmed.dev](https://finance.sajidahmed.dev)**

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
git clone https://github.com/SajidAhmedd/financial-analysis-agent-crew.git
cd financial-analysis-agent-crew
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add at least one free LLM key. Providers are tried in the order set by `LLM_PROVIDERS`
(default `mistral,groq,gemini`); if one is rate-limited or down, the request falls back to the next:
- **MISTRAL_API_KEY**: https://console.mistral.ai
- **GROQ_API_KEY**: https://console.groq.com
- **GEMINI_API_KEY**: https://aistudio.google.com/apikey
- **NEWS_API_KEY** (Optional): https://newsapi.org - DuckDuckGo news is used otherwise

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
financial-analysis-agent-crew/
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

- **LLM**: Mistral, Groq and Google Gemini through one OpenAI-compatible client with automatic fallback
- **UI**: Streamlit
- **Data**: Yahoo Finance, DuckDuckGo News, NewsAPI
- **Visualization**: Matplotlib, Plotly
- **PDF**: FPDF2

## Deployment

The live demo runs as a Docker container on Hugging Face Spaces. Every push to `main` is deployed by
`.github/workflows/deploy-hf.yml`, which also pings the demo twice a day to keep the free Space awake.
`finance.sajidahmed.dev` is served through a Cloudflare Worker that proxies the Space.

```bash
docker build -t financial-agent-crew .
docker run -p 7860:7860 --env-file .env financial-agent-crew
```

## License

MIT License
