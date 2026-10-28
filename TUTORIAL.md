# Financial Analysis Agent Crew: A Beginner's Tutorial

This tutorial walks you through the whole code base of the Financial Analysis Agent Crew, file by file and function by function. By the end you should be able to explain what every part does, why it was written that way, and where you would change it.

You need mid-level Python: functions, classes, imports and `try/except`. You do **not** need to know web apps, finance APIs, charting or AI libraries. Each one is explained when it first appears.

## Contents

1. [How to use this tutorial](#1-how-to-use-this-tutorial)
2. [The big picture](#2-the-big-picture)
3. [Folder map](#3-folder-map)
4. [Python concepts you need](#4-python-concepts-you-need)
5. [The libraries](#5-the-libraries)
6. [Every file and every function](#6-every-file-and-every-function)
7. [One run traced from start to finish](#7-one-run-traced-from-start-to-finish)
8. [Things to notice](#8-things-to-notice)
9. [Exercises](#9-exercises)
10. [Glossary](#10-glossary)

---

## 1. How to use this tutorial

This tutorial is meant to be read **next to the code**, not on its own.

1. Open the repo folder in VS Code (`File → Open Folder…`).
2. Open `TUTORIAL.md` and press **Ctrl+K V** (Cmd+K V on a Mac). The Markdown preview opens in a side panel, so the tutorial sits on the right and the code on the left.
3. Every link like [config/llm_client.py:107-146](config/llm_client.py#L107-L146) is clickable. In the preview, clicking it opens that file at those lines. Read the explanation, then look left at the real code.
4. Links to sections of this file (like the contents list above) jump inside the tutorial.

Why this way? You only really understand code by reading it. The tutorial tells you *what to look for* and *why it's there*; the code shows you *exactly how*. Snippets here are short extracts. The link always takes you to the full version.

Read sections 2 to 5 first, in order. Section 6 is long and follows the order in which files import each other, so each file is explained only after the files it depends on. You can stop after any file and come back later.

---

## 2. The big picture

### What the project does

You type a stock ticker such as **AAPL** (Apple) into a web page and press **Run Analysis**. About a minute later you can download a multi-page **PDF report** with:

- the company's profile, current price and valuation numbers (P/E ratio, market cap…),
- price and volume charts with moving averages,
- recent news headlines and whether the news sounds positive or negative,
- an AI-written summary, analysis and list of considerations and risks.

The work is split between three **agents**. Here an agent is simply a Python class with one job, its own instructions for the LLM (large language model), and the tools it needs:

| Agent | Job | Tools it uses |
|---|---|---|
| **Market Researcher** | find recent news and judge its mood | news search + keyword sentiment |
| **Data Analyst** | fetch prices and company numbers, draw charts | Yahoo Finance + matplotlib |
| **Report Writer** | write the final text and build the PDF | fpdf2 |

Each agent also asks an LLM to interpret what it found. A fourth class, the **orchestrator**, runs the agents in order and passes each one's output to the next. That is the "crew".

### How the pieces fit together

```
           You (browser)
                |
                v
   +------------------------------+
   |  Streamlit UI   (app.py)      |  sidebar: ticker, company, days, Run button
   +------------------------------+
                |  orchestrator.run_analysis(ticker, company_name, days_back)
                v
   +------------------------------------------------------------------+
   |  AgentOrchestrator  (agents/orchestrator.py)                      |
   |                                                                   |
   |   1. MarketResearcherAgent ---> 2. DataAnalystAgent ---> 3. ReportWriterAgent
   |      (agents/market_researcher)    (agents/data_analyst)   (agents/report_writer)
   |            |       |                  |      |      |           |        |
   +------------|-------|------------------|------|------|-----------|--------|--+
                v       |                  v      v      |           |        v
        tools/news_tools|        tools/finance_tools  tools/chart_tools   tools/pdf_tools
        DuckDuckGo or   |        Yahoo Finance        matplotlib PNGs     fpdf2 PDF
        NewsAPI         |                                  |               |
                        v                                  v               v
              +-----------------------------+        output/reports/charts/*.png
              | LLMClient (config/llm_client.py)      output/reports/*.pdf
              |  Mistral -> Groq -> Gemini  |
              |  (first that answers wins)  |
              +-----------------------------+
```

Things to notice already:

- **Everything runs inside one Python process.** There is no separate backend server; Streamlit calls the orchestrator directly as a normal function. Compare this with a FastAPI + UI design, where the UI and backend talk over HTTP.
- **Three LLM calls per run**, one per agent, all through `LLMClient`, which tries several providers in turn if one fails.
- **The order matters.** The Data Analyst draws the sentiment chart, so it needs the Market Researcher's results first. The Report Writer needs both.
- **Files are the hand-off to the PDF.** Charts are saved as PNG files, then the PDF code loads them from disk.

---

## 3. Folder map

Every file in the repo, one line each.

```
financial-analysis-agent-crew/
├── .dockerignore              files Docker should not copy into the image (.env, output/, venv…)
├── .env.example               template for your secret keys; copy it to .env
├── .github/workflows/
│   └── deploy-hf.yml          GitHub Actions: push to Hugging Face Spaces, ping the demo twice a day
├── .gitignore                 files git should not track (.env, output/, caches)
├── Dockerfile                 recipe for the container that runs the Streamlit app on port 7860
├── LICENSE                    MIT licence
├── README.md                  overview; the block at the top is also the Hugging Face Space config
├── agents/
│   ├── __init__.py            empty; marks agents/ as a package so "from agents.x import y" works
│   ├── market_researcher.py   agent 1: news search + sentiment + LLM summary
│   ├── data_analyst.py        agent 2: prices, metrics, charts + LLM interpretation
│   ├── report_writer.py       agent 3: one LLM call for all report text, then the PDF
│   └── orchestrator.py        runs the three agents in order and collects their logs
├── app.py                     the Streamlit web UI (about 1,000 lines, mostly CSS and layout)
├── config/
│   ├── __init__.py            empty package marker
│   ├── llm_client.py          one LLM client that falls back across Mistral, Groq and Gemini
│   └── settings.py            reads .env, holds settings and each agent's role/goal
├── requirements.txt           the Python packages to install
├── test_config.py             a small script that prints whether keys are set (not a real test)
└── tools/
    ├── __init__.py            empty package marker
    ├── chart_tools.py         draws price, KPI and sentiment charts as PNG files
    ├── finance_tools.py       fetches prices, company info and metrics from Yahoo Finance
    ├── news_tools.py          searches news (NewsAPI or DuckDuckGo) and scores sentiment
    └── pdf_tools.py           builds the PDF report with fpdf2
```

Folders created when the app runs (ignored by git): `output/reports/` for PDFs, `output/reports/charts/` for PNG charts.

---

## 4. Python concepts you need

These are the Python features this code uses beyond "functions, classes, imports, try/except". Each has a one-line recap and a pointer to an example.

**f-strings and triple-quoted f-strings.** `f"Hello {name}"` inserts values. A triple-quoted `f"""..."""` can span many lines; the agents build whole LLM prompts this way, e.g. [agents/market_researcher.py:177-201](agents/market_researcher.py#L177-L201). Inside an f-string `${price}` prints a literal `$` followed by the value. It is not special syntax, just a dollar sign.

**Type hints.** `def get_company_info(ticker: str) -> Dict[str, Any]:` documents that it takes a string and returns a dictionary. Python doesn't enforce them. [tools/finance_tools.py:68](tools/finance_tools.py#L68).

**`dict.get(key, default)`.** Returns the value, or `default` if the key is missing, instead of raising `KeyError`. This project uses it hundreds of times, because data from Yahoo or the LLM may lack any field. [tools/finance_tools.py:91-101](tools/finance_tools.py#L91-L101).

**Generator expressions with `sum`.** `sum(1 for w in words if w in text)` counts matches without building a list. [tools/news_tools.py:92-93](tools/news_tools.py#L92-L93).

**`@dataclass`.** Auto-writes `__init__` from typed fields. `field(default_factory=dict)` gives each object its own new dict. [config/llm_client.py:26-34](config/llm_client.py#L26-L34).

**`@property`.** Makes a method look like an attribute: `provider.api_key` runs code but reads like a field. [config/llm_client.py:36-46](config/llm_client.py#L36-L46).

**`**kwargs`.** Collects any extra keyword arguments into a dict and passes them on unchanged. `create(..., **kwargs)` forwards `temperature=0.3, max_tokens=1500` to the real API. [config/llm_client.py:80](config/llm_client.py#L80), [config/llm_client.py:94](config/llm_client.py#L94).

**`*` unpacking.** `self.set_text_color(*color)` turns the tuple `(38, 166, 154)` into three separate arguments. [tools/pdf_tools.py:265](tools/pdf_tools.py#L265).

**`types.SimpleNamespace`.** A blank object you can hang attributes on: `SimpleNamespace(completions=x)` lets you write `obj.completions`. Used to imitate the OpenAI client's `client.chat.completions.create` shape. [config/llm_client.py:137](config/llm_client.py#L137).

**Inheritance and overriding.** `class FinancialReportPDF(FPDF)` reuses everything in `FPDF` and replaces `header()` and `footer()`, which the parent class calls automatically on every page. `super().__init__()` runs the parent's set-up first. [tools/pdf_tools.py:66-119](tools/pdf_tools.py#L66-L119).

**Callbacks and closures.** A *callback* is a function you hand to someone else to call later. The UI defines `progress_callback` and gives it to the orchestrator; the orchestrator calls it at each step. Because it is defined inside the `if` block, it can use the `progress_data` dict defined just above it. That is a *closure*. [app.py:656-669](app.py#L656-L669).

**`try / except / finally`.** `finally` always runs, whether the `try` succeeded or raised. The orchestrator uses it to record the run time even after an error. [agents/orchestrator.py:239-260](agents/orchestrator.py#L239-L260).

**Fallback imports.** `try: from ddgs import DDGS` / `except ImportError: from duckduckgo_search import DDGS` supports both the new and old package names. [tools/news_tools.py:25-34](tools/news_tools.py#L25-L34).

**`sys.path` and `__file__`.** `sys.path` is the list of folders Python searches for imports. `os.path.abspath(__file__)` is the path of the current file; going up two `dirname`s gives the project root. Many files add the root to `sys.path` so they can be run directly as scripts. [tools/news_tools.py:41-42](tools/news_tools.py#L41-L42). (Section 8 shows a case where this happens too late.)

**`if __name__ == "__main__":`.** Code under this line runs only when you execute the file directly (`python tools/finance_tools.py`), not when it is imported. Every tool and agent file has such a block as a manual test. [tools/finance_tools.py:302](tools/finance_tools.py#L302).

**Regular expressions (`re`).** A mini-language for text patterns. `re.search(r'---RECOMMENDATIONS---\s*(.*?)$', text, re.DOTALL)` finds a marker and captures everything after it. [agents/report_writer.py:369-380](agents/report_writer.py#L369-L380).

**`lambda`.** A one-line nameless function: `format_func=lambda x: f"{x} days"`. [app.py:567](app.py#L567).

---

## 5. The libraries

All the packages in [requirements.txt](requirements.txt), in that file's order.

**Streamlit** (`streamlit`). Builds a web page from a plain Python script. Each `st.text_input`, `st.button`, `st.image` call adds a widget. The key idea: **every time the user interacts, the whole script runs again from top to bottom.** Values that must survive between runs go in `st.session_state` (a dict that persists). `st.empty()` creates a *placeholder*, a spot on the page you can fill or overwrite later.

```python
import streamlit as st
name = st.text_input("Ticker", value="AAPL")
if st.button("Go"):
    st.session_state.last = name      # survives the next re-run
st.write(st.session_state.get("last", "nothing yet"))
```
*Why here:* a full web UI without writing HTML/JavaScript or a separate server.
*Where:* only [app.py](app.py).

**OpenAI SDK** (`openai`). The official Python client for OpenAI's chat API. Many other providers (Mistral, Groq, Google Gemini) offer **OpenAI-compatible** endpoints: same request format, different web address. So one library can talk to all of them by changing `base_url` and `api_key`.

```python
from openai import OpenAI
client = OpenAI(api_key="...", base_url="https://api.groq.com/openai/v1")
r = client.chat.completions.create(model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "Say hi"}])
print(r.choices[0].message.content)
```
*Why here:* one dependency for three providers, which makes the fallback simple.
*Where:* [config/llm_client.py:23](config/llm_client.py#L23), [config/llm_client.py:127](config/llm_client.py#L127). (This project does not use OpenAI's own service.)

**yfinance** (`yfinance`, imported as `yf`). An unofficial library that downloads data from Yahoo Finance: price history, company profile, ratios. Free, no key needed, but Yahoo may rate-limit or change things without notice.

```python
import yfinance as yf
t = yf.Ticker("AAPL")
print(t.info["longName"])          # 'Apple Inc.'
print(t.history(period="5d"))      # a pandas DataFrame of prices
```
*Where:* [tools/finance_tools.py](tools/finance_tools.py) only.

**pandas** (`pandas`, as `pd`). The standard table library. A **DataFrame** is a table with named columns and an *index* (row labels; here, dates). `df['Close']` is one column (a *Series*). `.pct_change()`, `.mean()`, `.std()`, `.rolling(10).mean()` compute statistics over a column.

```python
import pandas as pd
df = pd.DataFrame({"Close": [100, 102, 101]})
print(df["Close"].pct_change())    # NaN, 0.02, -0.0098
```
*Where:* yfinance returns DataFrames; statistics in [tools/finance_tools.py:199-238](tools/finance_tools.py#L199-L238); moving averages in [tools/chart_tools.py:107-126](tools/chart_tools.py#L107-L126).

**matplotlib** (`matplotlib`, as `plt`). The classic Python plotting library. You create a *figure* with one or more *axes* (plots), draw on them, then `savefig` to a PNG.

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [10, 12, 11])
plt.savefig("demo.png"); plt.close()
```
*Why here:* the PDF needs image files, and matplotlib writes PNGs directly.
*Where:* [tools/chart_tools.py](tools/chart_tools.py).

**Plotly** (`plotly`). An interactive charting library. **Listed but never imported anywhere.** The README mentions it too. You could remove it from `requirements.txt` ([section 8](#8-things-to-notice)).

**fpdf2** (`fpdf2`, imported as `fpdf`). Creates PDF files from Python. You add pages, set fonts and colours, and write `cell`s (one-line boxes), `multi_cell`s (wrapping text) and images. Its built-in fonts (Helvetica…) only support the **Latin-1** character set, which is why the code has a `sanitize_text` function.

```python
from fpdf import FPDF
pdf = FPDF(); pdf.add_page(); pdf.set_font("Helvetica", size=12)
pdf.cell(0, 10, "Hello PDF")
pdf.output("hello.pdf")
```
*Where:* [tools/pdf_tools.py](tools/pdf_tools.py).

**requests** (`requests`). Makes HTTP calls. `requests.get(url, params=..., timeout=10)` fetches a web address.
*Where:* the NewsAPI call, [tools/news_tools.py:219-220](tools/news_tools.py#L219-L220).

**python-dotenv** (`python-dotenv`, imported as `dotenv`). `load_dotenv()` reads a `.env` file and puts each `KEY=value` line into the process's environment variables, where `os.getenv("KEY")` can read them. *Why:* secrets stay out of the code and out of git.
*Where:* [config/settings.py:17-21](config/settings.py#L17-L21).

**Beautiful Soup** (`beautifulsoup4`). An HTML parser for scraping web pages. **Listed but never imported.**

**ddgs** (`ddgs`, formerly `duckduckgo-search`). Searches DuckDuckGo from Python, including a news search, with no API key.

```python
from ddgs import DDGS
with DDGS() as d:
    for r in d.news("Apple stock", max_results=3):
        print(r["title"])
```
*Where:* [tools/news_tools.py:146-152](tools/news_tools.py#L146-L152).

---

## 6. Every file and every function

Files are in **dependency order**: each file appears only after every project file it imports. One subtlety: `config/settings.py` imports `config/llm_client.py` *inside* a function, so `llm_client.py` comes first.

### 6.1 The LLM client: config/llm_client.py

Imports: no project files.

**The problem it solves.** Free LLM tiers have strict *rate limits* (too many requests per minute → error 429). A demo that fails whenever one provider is busy looks broken. So this file tries each provider in a list and returns the first good answer. It is written to look exactly like the OpenAI client, so the agents call `client.chat.completions.create(...)` as if it were OpenAI.

**`class Provider`** [config/llm_client.py:26-46](config/llm_client.py#L26-L46). A dataclass describing one provider: its name, web address (`base_url`), which environment variables may hold its key, which variable may override its model, the default model, and any `extra_body` parameters only it understands.

- **`api_key`** property [config/llm_client.py:36-42](config/llm_client.py#L36-L42): returns the first non-empty key from the listed variables, ignoring placeholder values that start with `your_`. Gemini accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
- **`model`** property [config/llm_client.py:44-46](config/llm_client.py#L44-L46): the override variable if set, otherwise the default.

Because these are properties, they read the environment **every time** they are accessed, not once at start-up.

**`PROVIDERS`** [config/llm_client.py:49-73](config/llm_client.py#L49-L73). A dict of the three providers. Groq gets `extra_body={"reasoning_effort": "low"}` ([line 57](config/llm_client.py#L57)). *Why?* The `gpt-oss` model "thinks" before answering, and that thinking counts against `max_tokens`; keeping it short leaves room for the actual answer.

**`class _Completions`** [config/llm_client.py:76-104](config/llm_client.py#L76-L104). Its **`create`** method [lines 80-104](config/llm_client.py#L80-L104) is the heart of the fallback:

```python
errors = []
for provider, client in self._client.providers:
    try:
        response = client.chat.completions.create(
            model=provider.model,
            messages=messages,
            extra_body=provider.extra_body or None,
            **kwargs,
        )
        if response.choices and response.choices[0].message.content:
            self._client.last_provider = provider.name
            return response
        errors.append(f"{provider.name}: empty response")
    except Exception as e:
        errors.append(f"{provider.name}: {str(e)[:200]}")
        ...
raise RuntimeError("All LLM providers failed - " + " | ".join(errors))
```

It tries each provider; an exception *or* an empty answer moves on to the next. Only if all fail does it raise, with every provider's error joined into one message. Note that the `model` argument callers pass is **ignored** (the docstring says so): each provider uses its own model.

**`class LLMClient`** [config/llm_client.py:107-146](config/llm_client.py#L107-L146).

- **`__init__(order)`** [lines 117-137](config/llm_client.py#L117-L137): reads `LLM_PROVIDERS` (e.g. `"mistral,groq,gemini"`), and for each provider **that has a key** creates a real `OpenAI` client pointed at that provider:

```python
client = OpenAI(api_key=provider.api_key, base_url=provider.base_url, max_retries=0, timeout=30)
```

`max_retries=0` is deliberate: the OpenAI library would normally retry a failed request itself, which can take a long time. Here, "retrying" means moving to the next provider, which is faster for the visitor. An unknown provider name raises `ValueError`; so does having no usable keys at all. The last line, `self.chat = SimpleNamespace(completions=_Completions(self))`, builds the `client.chat.completions` shape.

Look at [line 118](config/llm_client.py#L118): if `LLM_PROVIDERS` is not set, the default is just `"groq"`. `config/settings.py` uses a different default. This mismatch causes a real crash, shown in [section 8](#8-things-to-notice).

- **`model`** [lines 139-142](config/llm_client.py#L139-L142): the first provider's model, for display.
- **`provider_names`** [lines 144-146](config/llm_client.py#L144-L146): the names in order. Not used elsewhere.

**`configured_providers(order)`** [config/llm_client.py:149-155](config/llm_client.py#L149-L155). Returns the providers in the list that have a key, without creating clients. Used by `validate_config`.

### 6.2 Settings: config/settings.py

Imports: `dotenv`; `config.llm_client` inside `validate_config`.

**`load_dotenv()`** [config/settings.py:21](config/settings.py#L21) runs the moment this module is imported. From then on `os.getenv` sees your `.env` values. Every agent imports this module before it creates an `LLMClient`, which is how the client can find the keys.

**Module-level settings** [config/settings.py:29-52](config/settings.py#L29-L52): `LLM_PROVIDERS` (default `"mistral,groq,gemini"`), the three API keys, `NEWS_API_KEY`, `DEFAULT_DAYS_BACK` and `OUTPUT_DIR` (default `output/reports`). Only `LLM_PROVIDERS`, `NEWS_API_KEY` and `OUTPUT_DIR` are used by the app; the three LLM key constants are just printed by `test_config.py`, since `llm_client.py` reads the environment itself.

**`validate_config()`** [config/settings.py:55-71](config/settings.py#L55-L71). Prints a clear error and returns `False` if no provider has a key. The import of `configured_providers` is placed inside the function, which avoids a *circular import* problem and keeps import order simple. The orchestrator calls this before creating agents, to "fail fast" with a readable message.

**`AGENT_SETTINGS`** [config/settings.py:75-88](config/settings.py#L75-L88). A role and goal for each agent, inserted into its system prompt. Changing "Financial Report Writer" here changes what the LLM is told it is.

### 6.3 Market data: tools/finance_tools.py

Imports: no project files.

Every function catches its own exceptions and returns an empty result or an `"error"` key instead of crashing. *Why?* A missing number should give a report with "N/A", not a failed run.

**`get_stock_price_history(ticker, days_back)`** [tools/finance_tools.py:22-65](tools/finance_tools.py#L22-L65). Computes a start date `days_back` days ago and calls `yf.Ticker(ticker).history(start=..., end=...)` ([line 55](tools/finance_tools.py#L55)). The result is a DataFrame indexed by date with columns `Open, High, Low, Close, Volume` (and a few others). Note that 30 *calendar* days give only about 21 *trading* days, because markets close at weekends and on holidays.

**`get_company_info(ticker)`** [tools/finance_tools.py:68-107](tools/finance_tools.py#L68-L107). `stock.info` is a big dict (over 100 fields) from Yahoo. This picks nine useful ones and renames them, e.g. `longName → name`, `longBusinessSummary → description` ([lines 91-101](tools/finance_tools.py#L91-L101)). Renaming here means the rest of the code never needs to know Yahoo's field names.

**`get_key_metrics(ticker)`** [tools/finance_tools.py:110-172](tools/finance_tools.py#L110-L172). The same idea for numbers: price, 52-week range, volume, market cap, P/E, forward P/E, PEG, price-to-book, dividends, margins, growth, analyst target. A couple use a nested fallback such as `info.get("currentPrice", info.get("regularMarketPrice", "N/A"))`, because Yahoo fills different fields for different kinds of security. Missing values become the string `"N/A"`, so later code checks for `"N/A"` a lot.

**`get_price_statistics(ticker, days_back)`** [tools/finance_tools.py:175-244](tools/finance_tools.py#L175-L244). Fetches history again and computes:

```python
history['daily_return'] = history['Close'].pct_change()
...
"daily_volatility_pct": round(history['daily_return'].std() * 100, 4),
"annualized_volatility_pct": round(
    history['daily_return'].std() * (252 ** 0.5) * 100, 2
),
```

- **Daily return** = how much the closing price changed since the day before, as a fraction.
- **Volatility** = the standard deviation of daily returns: how much prices jump around. Higher means riskier.
- **Annualised** volatility multiplies by √252 because there are about 252 trading days a year, and for independent day-to-day changes, spread grows with the square root of time.
- **SMA** (simple moving average) of the last 10 and 20 closes, only if there are enough days ([lines 235-238](tools/finance_tools.py#L235-L238)).

**`format_large_number(num)`** [tools/finance_tools.py:247-269](tools/finance_tools.py#L247-L269). Turns `2870000000000` into `"$2.87T"`. It always uses `$`, even for non-US stocks.

**`get_full_stock_analysis(ticker, days_back)`** [tools/finance_tools.py:274-298](tools/finance_tools.py#L274-L298). Calls the three functions above and adds a `market_cap_formatted` field ([lines 293-296](tools/finance_tools.py#L293-L296)). The comment says "This is what the Data Analyst Agent will primarily use", **but the agent never calls it**. The agent calls the functions one by one, so `market_cap_formatted` is never set, which breaks the market cap in the PDF ([section 8](#8-things-to-notice)).

**Test block** [tools/finance_tools.py:302-346](tools/finance_tools.py#L302-L346): `python tools/finance_tools.py` prints Apple's data. A great way to see the real shapes of the dicts.

### 6.4 News and sentiment: tools/news_tools.py

Imports: `config.settings` (for `NEWS_API_KEY`).

**Import fallback** [tools/news_tools.py:25-34](tools/news_tools.py#L25-L34). Tries `ddgs`, then the old `duckduckgo_search`, and records `DDGS_AVAILABLE`. If neither is installed, the module still loads and only DuckDuckGo search is disabled.

**Keyword lists** [tools/news_tools.py:49-64](tools/news_tools.py#L49-L64). About 30 "positive" words (`surge`, `beat`, `upgrade`, `up`, `high`…) and 30 "negative" ones (`drop`, `lawsuit`, `downgrade`, `low`, `cut`…).

**`analyze_sentiment(text)`** [tools/news_tools.py:67-116](tools/news_tools.py#L67-L116). A very simple sentiment model:

```python
positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
...
score = (positive_count - negative_count) / total
```

The score runs from −1 (all negative words) to +1 (all positive). Above 0.2 is "positive", below −0.2 "negative", otherwise "neutral". The docstring is honest that real systems use trained models like VADER or FinBERT. Note that `word in text_lower` checks for a **substring**, not a whole word, so `"up"` is found inside `"update"`. Section 8 shows what that does.

**`search_news_duckduckgo(query, max_results)`** [tools/news_tools.py:121-173](tools/news_tools.py#L121-L173). Uses `DDGS().news(...)` limited to the last month (`timelimit='m'`), maps each result to a common shape (`title, link, snippet, source, date`) and attaches a sentiment to each article. `with DDGS() as ddgs:` is a context manager: the session is closed properly at the end. On failure it returns `[{"error": "..."}]`, a list with one error dict.

**`search_news_newsapi(query, max_results, days_back)`** [tools/news_tools.py:177-251](tools/news_tools.py#L177-L251). The same result shape from NewsAPI's REST API: build query parameters ([lines 209-217](tools/news_tools.py#L209-L217)), `requests.get`, `raise_for_status()` (turns HTTP errors like 401 into exceptions), then map `description → snippet` and so on. Mapping both sources into **one shape** is what lets the rest of the code ignore which source was used.

**`search_stock_news(ticker, company_name, max_results)`** [tools/news_tools.py:255-344](tools/news_tools.py#L255-L344). The function agents call.

1. Builds the query: `"Apple Inc (AAPL) stock news"` if a company name is given, else `"AAPL stock news"` ([lines 278-281](tools/news_tools.py#L278-L281)).
2. Uses NewsAPI if a key is set, falling back to DuckDuckGo if NewsAPI returns an error; otherwise DuckDuckGo ([lines 289-300](tools/news_tools.py#L289-L300)).
3. Drops error entries, then computes an **overall** sentiment: the average score, plus counts of positive/negative/neutral articles. The overall thresholds are ±0.15, slightly looser than the per-article ±0.2 ([lines 313-318](tools/news_tools.py#L313-L318)).

Its return dict (`ticker, query, source, total_articles, overall_sentiment, articles`) is passed all the way to the PDF.

**`get_news_summary(...)`** [tools/news_tools.py:347-394](tools/news_tools.py#L347-L394). Formats news as plain text with `[+] [-] [=]` markers. Not used by the app; only by this file's test block.

### 6.5 Charts: tools/chart_tools.py

Imports: `config.settings` (for `OUTPUT_DIR`).

[Line 24](tools/chart_tools.py#L24) sets a global matplotlib style for every chart.

**`ensure_output_dir()`** [tools/chart_tools.py:35-39](tools/chart_tools.py#L35-L39) and **`get_chart_path(ticker, chart_type)`** [tools/chart_tools.py:42-47](tools/chart_tools.py#L42-L47). Build a path like `output/reports/charts/AAPL_price_20261028_101500.png` under the project root, creating folders as needed. The timestamp keeps old charts from being overwritten.

**`create_price_chart(ticker, price_data, ...)`** [tools/chart_tools.py:51-170](tools/chart_tools.py#L51-L170). Two stacked plots that share the date axis:

```python
fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(12, 8),
    gridspec_kw={'height_ratios': [3, 1]},
    sharex=True  # Share x-axis between subplots
)
```

Top (`ax1`): closing price, plus 10- and 20-day moving averages computed with `.rolling(window=10).mean()` ([lines 107-126](tools/chart_tools.py#L107-L126)). Bottom (`ax2`): volume bars, green on days the close rose and red on days it fell ([lines 140-147](tools/chart_tools.py#L140-L147)). Then `savefig` at 150 dpi and `plt.close()` ([lines 162-167](tools/chart_tools.py#L162-L167)). Closing matters: matplotlib keeps every open figure in memory otherwise. With `save=False` it calls `plt.show()` instead, which is only useful on a desktop.

**`create_kpi_chart(ticker, metrics, ...)`** [tools/chart_tools.py:174-266](tools/chart_tools.py#L174-L266). A horizontal bar for each available ratio. Margins and growth rates come from Yahoo as fractions (0.25), so they are multiplied by 100 ([lines 215-216](tools/chart_tools.py#L215-L216)). Bars are green if positive, red if negative. Note that this puts different units (a P/E of 30 and a margin of 25%) on one axis, so bar lengths aren't really comparable. It's a visual summary, not a true comparison.

**`create_sentiment_chart(ticker, sentiment_data, ...)`** [tools/chart_tools.py:270-365](tools/chart_tools.py#L270-L365). Left: a pie chart of positive/neutral/negative article counts ([lines 311-319](tools/chart_tools.py#L311-L319)). Right: a single bar on a −1 to +1 scale showing the overall score, labelled Bearish/Bullish ([lines 332-339](tools/chart_tools.py#L332-L339)).

**`create_all_charts(ticker, price_data, metrics, sentiment_data)`** [tools/chart_tools.py:369-401](tools/chart_tools.py#L369-L401). Calls the three functions when there is data for them and returns `{"price": path, "kpi": path, "sentiment": path}`. A chart function that finds nothing to draw returns `""`, and that empty string is still stored; later code checks `if chart_paths.get('price')`, which treats `""` as "no chart".

### 6.6 The PDF: tools/pdf_tools.py

Imports: `config.settings` (for `OUTPUT_DIR`).

**`sanitize_text(text)`** [tools/pdf_tools.py:33-62](tools/pdf_tools.py#L33-L62). fpdf2's built-in fonts can only draw Latin-1 characters. LLMs love curly quotes (’ “ ”), en/em dashes and "…", which would make fpdf2 raise an error. This swaps the common ones for plain versions, then drops anything else outside Latin-1:

```python
text = text.encode('latin-1', errors='ignore').decode('latin-1')
```

`errors='ignore'` silently deletes characters it can't encode. So emoji or Chinese characters simply disappear from the PDF.

**`class FinancialReportPDF(FPDF)`** [tools/pdf_tools.py:66-284](tools/pdf_tools.py#L66-L284). A customised PDF with helper methods:

- **`__init__`** [lines 79-87](tools/pdf_tools.py#L79-L87): stores ticker, company and date; sets 15 mm margins and automatic page breaks.
- **`header`** [lines 89-107](tools/pdf_tools.py#L89-L107) and **`footer`** [lines 109-119](tools/pdf_tools.py#L109-L119): **overridden** hooks that fpdf2 calls on every new page. The footer prints `Page 3/{nb}`; `{{nb}}` in the f-string becomes the literal text `{nb}`, which fpdf2 replaces with the total page count when the file is saved (enabled by `alias_nb_pages()`).
- **`add_title_page`** [lines 121-153](tools/pdf_tools.py#L121-L153): big centred title, company, ticker, date.
- **`add_section_header`** [lines 155-169](tools/pdf_tools.py#L155-L169): blue heading with an underline.
- **`add_paragraph`** [lines 171-176](tools/pdf_tools.py#L171-L176): wrapping text via `multi_cell`, sanitised.
- **`add_key_value`** [lines 178-186](tools/pdf_tools.py#L178-L186): a "Sector: Technology" line.
- **`add_metrics_table`** [lines 188-228](tools/pdf_tools.py#L188-L228): a two-column table with striped rows. Rows whose value is `"N/A"` or `None` are **skipped** ([lines 202-203](tools/pdf_tools.py#L202-L203)). Floats under 1 get four decimals, others two.
- **`add_image_full_width`** [lines 230-247](tools/pdf_tools.py#L230-L247): puts a PNG 180 mm wide (A4 is 210 mm minus two 15 mm margins), or a "[Image not found]" note.
- **`add_news_item`** [lines 249-284](tools/pdf_tools.py#L249-L284): a numbered headline with a coloured `[P]/[N]` sentiment letter, source and snippet.

**`generate_report(...)`** [tools/pdf_tools.py:288-475](tools/pdf_tools.py#L288-L475). Builds the whole document in a fixed order: title page; executive summary (company description, sector, industry, the AI analysis); a metrics page with three tables ([lines 351-377](tools/pdf_tools.py#L351-L377)); a charts page; a sentiment page with the sentiment chart and top 5 headlines ([lines 400-439](tools/pdf_tools.py#L400-L439)); recommendations; and a fixed disclaimer ([lines 448-462](tools/pdf_tools.py#L448-L462)). It saves to `output/reports/<TICKER>_Financial_Report_<timestamp>.pdf` and returns that path ([lines 465-475](tools/pdf_tools.py#L465-L475)).

One detail: in the price table, values are built as `f"${key_metrics.get('current_price', 'N/A')}"`. If the price is missing this gives `"$N/A"`, which is not equal to `"N/A"`, so the row is *not* skipped.

### 6.7 Agent 1: agents/market_researcher.py

Imports: `config.llm_client`, `config.settings`, `tools.news_tools`.

All three agents share the same skeleton, so learn it once here:

- `__init__`: read role/goal from `AGENT_SETTINGS`, create an `LLMClient`, start an empty `conversation_history`, write a **system prompt**.
- `log(message)`: print a timestamped line and keep it in `conversation_history`.
- one public "do the job" method.
- `_analyze_with_llm`: build a **user prompt**, call the LLM, split the answer into sections.
- `_extract_section`: find one numbered section in the LLM's text.

An LLM chat request is a list of *messages*. The **system** message sets the role and rules ("You are a Market Research Analyst… be objective"). The **user** message carries the actual task and data.

**`MarketResearcherAgent.__init__`** [agents/market_researcher.py:52-84](agents/market_researcher.py#L52-L84). Notice `self.client = LLMClient()`: each agent has its own client, and creating it raises `ValueError` if no keys are set.

**`log`** [agents/market_researcher.py:86-91](agents/market_researcher.py#L86-L91). The entries look like `[10:15:02] MarketResearcher: Found 9 news articles`. The orchestrator later splits these strings back into parts.

**`research(ticker, company_name)`** [agents/market_researcher.py:93-142](agents/market_researcher.py#L93-L142). The public method, in four labelled steps: search news (10 articles), format them as text, ask the LLM, return a results dict that includes the raw `news_data`, the `overall_sentiment` and the `ai_analysis`.

**`_format_news_for_analysis(news_data)`** [agents/market_researcher.py:144-159](agents/market_researcher.py#L144-L159). Turns the article list into numbered text lines with `[POSITIVE]`-style labels and 200-character snippets. LLMs read text, not Python dicts, so data is always converted to a readable layout first.

**`_analyze_with_llm(...)`** [agents/market_researcher.py:161-233](agents/market_researcher.py#L161-L233). The prompt asks for six numbered sections: SENTIMENT ASSESSMENT, KEY THEMES, NOTABLE EVENTS, RISKS AND CONCERNS, OPPORTUNITIES, SUMMARY. The call:

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.3,
    max_tokens=1500
)
```

`temperature=0.3` keeps the writing fairly consistent; `max_tokens` caps the answer length. The answer is stored whole (`full_analysis`) and section by section. If the call fails, it returns a short error dict instead of raising ([lines 228-233](agents/market_researcher.py#L228-L233)), so the run continues.

**`_extract_section(text, section_name)`** [agents/market_researcher.py:235-269](agents/market_researcher.py#L235-L269). Looks for `"SUMMARY:"`, `"SUMMARY\n"` or `"**SUMMARY**"` (case-insensitive), then takes the text up to the next line that starts with a number and a capital letter (`\n\d+\.\s+[A-Z]`), or up to a blank line. *Why so many markers?* Different LLMs format headings differently (some add Markdown bold). This is a heuristic: if the LLM changes its format, a section may come back empty.

**`get_conversation_log`** [agents/market_researcher.py:271-273](agents/market_researcher.py#L271-L273). Joins the log into one string. Not called by the app.

### 6.8 Agent 2: agents/data_analyst.py

Imports: `config.llm_client`, `config.settings`, `tools.finance_tools`, `tools.chart_tools`.

**`__init__`** [agents/data_analyst.py:60-93](agents/data_analyst.py#L60-L93) and **`log`** [agents/data_analyst.py:95-100](agents/data_analyst.py#L95-L100): same pattern as agent 1, with a numbers-focused system prompt ("Be precise with numbers… explain what the numbers mean in plain English").

**`analyze(ticker, days_back, sentiment_data)`** [agents/data_analyst.py:102-188](agents/data_analyst.py#L102-L188). Seven labelled steps:

1. company info; 2. key metrics; 3. price history **and** statistics ([lines 141-142](agents/data_analyst.py#L141-L142)). `get_price_statistics` downloads the history a second time internally;
4. charts, passing the researcher's sentiment so the sentiment chart can be drawn:

```python
chart_paths = create_all_charts(
    ticker=ticker,
    price_data=price_history,
    metrics=key_metrics,
    sentiment_data=sentiment_data.get('overall_sentiment', {}) if sentiment_data else {}
)
```

5. format everything as text; 6. ask the LLM; 7. return a big dict ([lines 172-185](agents/data_analyst.py#L172-L185)) that also includes the raw `price_history` DataFrame.

**`_format_data_for_analysis(...)`** [agents/data_analyst.py:190-256](agents/data_analyst.py#L190-L256). Lays the numbers out under headings (COMPANY OVERVIEW, CURRENT PRICE DATA, VALUATION METRICS…). Here the market cap *is* formatted correctly with `format_large_number` ([line 213](agents/data_analyst.py#L213)), and margins are converted to percentages ([lines 241-251](agents/data_analyst.py#L241-L251)).

**`_analyze_with_llm(...)`** [agents/data_analyst.py:258-333](agents/data_analyst.py#L258-L333). Seven sections: VALUATION ASSESSMENT, PERFORMANCE ANALYSIS, RISK ASSESSMENT, FINANCIAL HEALTH, KEY STRENGTHS, KEY CONCERNS, DATA SUMMARY. The prompt gives the LLM a reference point, "typical market volatility (~15-20% annualized)", so it can judge whether the stock is risky.

**`_extract_section`** [agents/data_analyst.py:335-367](agents/data_analyst.py#L335-L367) and **`get_conversation_log`** [agents/data_analyst.py:369-371](agents/data_analyst.py#L369-L371). Copies of agent 1's methods. A shared base class would remove this duplication ([exercise 6](#9-exercises)).

### 6.9 Agent 3: agents/report_writer.py

Imports: `config.llm_client`, `config.settings`, `tools.pdf_tools`.

The header comment says it plainly: **one** LLM call writes all three text sections. *Why?* Each call takes seconds and uses up rate limit; one call with clear section markers is faster and cheaper than three.

**`__init__`** [agents/report_writer.py:60-106](agents/report_writer.py#L60-L106). Adds retry settings (3 attempts, 2-second base delay) and a system prompt with formatting rules. Because the output goes into a PDF, Markdown would show up as literal `**` and `##`, hence the rules "never use asterisks" and "no markdown formatting" ([lines 100-101](agents/report_writer.py#L100-L101)).

**`_call_llm_with_retry(messages)`** [agents/report_writer.py:115-146](agents/report_writer.py#L115-L146). Wraps the call in a retry loop **on top of** the provider fallback: if the error text contains `"429"` or `"rate"`, wait 2 s, then 4 s, and try the whole provider chain again. Any other error, or running out of attempts, returns `None`.

**`write_report(ticker, market_research, financial_analysis)`** [agents/report_writer.py:148-211](agents/report_writer.py#L148-L211). Compiles the inputs, generates the text, then calls `generate_report` with data from both earlier agents ([lines 184-193](agents/report_writer.py#L184-L193)). The executive summary and detailed analysis are joined into the PDF's "AI Analysis" section; recommendations get their own page.

**`_compile_research_data(...)`** [agents/report_writer.py:213-265](agents/report_writer.py#L213-L265). Picks about 25 fields from the two big result dicts into one flat dict for the prompt: price, P/E, sentiment, and the other agents' **summaries** (not their full text). This keeps the prompt short. The market cap comes from `key_metrics.get('market_cap_formatted', 'N/A')` ([line 239](agents/report_writer.py#L239)), the field nobody sets, so it is always `"N/A"`.

**`_generate_all_content(...)`** [agents/report_writer.py:267-353](agents/report_writer.py#L267-L353). The prompt lists the data, then asks for three sections separated by exact markers ([lines 309-331](agents/report_writer.py#L309-L331)):

```text
---EXECUTIVE_SUMMARY---
...
---DETAILED_ANALYSIS---
...
---RECOMMENDATIONS---
```

Unusual markers like `---EXECUTIVE_SUMMARY---` are easy to find with a regex and unlikely to appear by accident. If the LLM call fails completely, the method uses template text instead ([lines 346-353](agents/report_writer.py#L346-L353)).

**`_parse_sections(...)`** [agents/report_writer.py:355-407](agents/report_writer.py#L355-L407). Three regexes cut the text at the markers ([lines 369-380](agents/report_writer.py#L369-L380)). `(.*?)` captures as little as possible, and `(?=---DETAILED_ANALYSIS---|$)` is a *lookahead*: it stops before the next marker without consuming it. Any section shorter than 100 characters is treated as a failure and replaced with the template text ([lines 387-392](agents/report_writer.py#L387-L392)). That means a single report can mix AI-written and template paragraphs.

**`_clean_content(text)`** [agents/report_writer.py:409-421](agents/report_writer.py#L409-L421). A belt-and-braces clean-up in case the LLM ignored the "no Markdown" rule: `* ` bullets become `- `, `**bold**` and `*italic*` markers are removed, `#` headings stripped, and runs of blank lines collapsed.

**`_get_fallback_content(...)`** [agents/report_writer.py:423-469](agents/report_writer.py#L423-L469). Template paragraphs filled in with real numbers. The report is always produced, even with no working LLM at this step.

### 6.10 The conductor: agents/orchestrator.py

Imports: `config.settings` and the three agents.

**`AgentOrchestrator.__init__(progress_callback)`** [agents/orchestrator.py:55-72](agents/orchestrator.py#L55-L72). Stores the optional callback and leaves the agents as `None` until needed.

**`log`** [agents/orchestrator.py:74-87](agents/orchestrator.py#L74-L87). Unlike the agents, it stores log entries as dicts (`timestamp, stage, message`).

**`_report_progress(stage, message, progress)`** [agents/orchestrator.py:89-96](agents/orchestrator.py#L89-L96). Logs, then calls the UI's callback with a progress fraction from 0.0 to 1.0. Errors inside the callback are caught, so a UI bug can't break the analysis.

**`run_analysis(ticker, company_name, days_back)`** [agents/orchestrator.py:98-262](agents/orchestrator.py#L98-L262). The pipeline:

```python
if not validate_config():
    raise ValueError("Configuration validation failed. Check your .env file.")
self._initialize_agents()
market_research = self.market_researcher.research(ticker=ticker, company_name=company_name)
...
financial_analysis = self.data_analyst.analyze(
    ticker=ticker,
    days_back=days_back,
    sentiment_data=market_research  # Pass sentiment for chart
)
...
report = self.report_writer.write_report(
    ticker=ticker,
    market_research=market_research,
    financial_analysis=financial_analysis
)
```

Things worth seeing:

- A `result` dict is created up front with `success: False` ([lines 136-147](agents/orchestrator.py#L136-L147)) and filled in as steps finish. Even on failure, the caller gets everything completed so far plus an `error` message.
- [Lines 172-174](agents/orchestrator.py#L172-L174) try to learn the company name from the research result. But the researcher only echoes back what it was given, so if you left the name blank, it stays blank until the Data Analyst finds it from Yahoo ([lines 197-198](agents/orchestrator.py#L197-L198)). By then the news search has already run with just the ticker.
- Any exception lands in `except` ([lines 230-237](agents/orchestrator.py#L230-L237)), which logs the full traceback. `finally` ([lines 239-260](agents/orchestrator.py#L239-L260)) always computes the run time and gathers the logs.

**`_initialize_agents()`** [agents/orchestrator.py:264-275](agents/orchestrator.py#L264-L275). Creates the three agents (three `LLMClient`s).

**`_compile_conversation_logs()`** [agents/orchestrator.py:277-324](agents/orchestrator.py#L277-L324). Merges the orchestrator's dict logs with each agent's string logs into one list of dicts, splitting strings like `"[10:15:02] MarketResearcher: Found 9 articles"` at `"]"` and `": "`. The list is grouped by agent, not sorted by time.

**`get_conversation_log_formatted()`** [agents/orchestrator.py:326-346](agents/orchestrator.py#L326-L346) and **`analyze_stock(...)`** [agents/orchestrator.py:351-380](agents/orchestrator.py#L351-L380). A text version of the log and a one-line convenience wrapper. Neither is used by the app, but `analyze_stock("AAPL")` is the easiest way to run everything from a Python shell.

### 6.11 The web UI: app.py

Imports: `agents.orchestrator`, `tools.finance_tools` (unused).

Remember: Streamlit runs this whole file again on every click. Reading it top to bottom *is* reading what happens on each interaction.

**Path and imports** [app.py:19-23](app.py#L19-L23). Adds the project folder to `sys.path`. `get_company_info` is imported but never used.

**Page set-up and CSS** [app.py:29-331](app.py#L29-L331). `st.set_page_config` must be the first Streamlit call. Then about 300 lines of CSS injected with `st.markdown(..., unsafe_allow_html=True)` give the dark "glass" look. `unsafe_allow_html=True` tells Streamlit to render raw HTML instead of escaping it. Several class names it styles (`.css-1d391kg`, `.streamlit-expanderHeader`) are Streamlit internals that change between versions, so some of these rules may quietly do nothing.

**Helper functions.**
- **`render_header`** [app.py:335-338](app.py#L335-L338): the gradient title.
- **`render_agent_console(logs, is_running)`** [app.py:341-442](app.py#L341-L442): draws a fake terminal from the last 25 log entries. It **hides** messages containing error-ish keywords like `"Error code: 429"` or `"Rate limited"` ([lines 358-378](app.py#L358-L378)) so visitors don't see provider noise, and cuts long messages to 100 characters. Its body is indented with 6 spaces instead of 4. Python allows that, as long as it's consistent within the block.
- **`render_metric_card`** [app.py:444-451](app.py#L444-L451) and **`render_agent_status`** [app.py:513-537](app.py#L513-L537): small HTML cards.
- **`format_logs_for_export`** [app.py:454-489](app.py#L454-L489): the text for the "Download Log" button.
- **`save_logs_to_file`** [app.py:492-510](app.py#L492-L510): writes that text to disk. Never called.

**Sidebar** [app.py:542-599](app.py#L542-L599). Ticker (upper-cased and trimmed), optional company name, a period of 7–90 days, agent status cards inside an `st.empty()` placeholder (so they can be redrawn later), and the **Run Analysis** button. `st.button` returns `True` only on the re-run caused by clicking it.

**Main layout** [app.py:608-643](app.py#L608-L643). Two columns: console on the left, "Quick Stats" on the right, each in a placeholder. Session state keys are created on first load ([lines 616-621](app.py#L616-L621)).

**When Run is clicked** [app.py:648-851](app.py#L648-L851):

1. Defines `progress_callback`, which appends each message to `st.session_state.logs` ([lines 658-669](app.py#L658-L669)).
2. Marks the researcher "Running…" and shows an "Initializing" console.
3. Runs the whole analysis inside `st.spinner` ([lines 686-692](app.py#L686-L692)). **This blocks**: nothing on the page changes until it returns, because the callback only stores messages and never redraws a placeholder.
4. Saves the result in session state ([lines 695-696](app.py#L695-L696)), so a later click (like Download) can show it again.
5. On success, fills Quick Stats (price, sentiment, P/E, time), reads the PDF bytes for `st.download_button`, and shows the summary, charts, recommendations and full log in expanders ([lines 714-836](app.py#L714-L836)). On failure, shows the error ([lines 838-851](app.py#L838-L851)).

**Showing a previous result** [app.py:857-1000](app.py#L857-L1000). The `elif` branch. Clicking a download button re-runs the script with `run_analysis == False`, so without this branch the results would vanish. It redraws everything from `st.session_state.analysis_result`. It is a near-copy of the success branch above: about 140 duplicated lines ([exercise 4](#9-exercises)). The download buttons here have `key=` arguments because Streamlit needs unique keys when the same widget could appear twice.

**Footer** [app.py:1004-1009](app.py#L1004-L1009).

### 6.12 test_config.py

[test_config.py:1-16](test_config.py#L1-L16). A script, not a pytest test: it imports settings, prints whether the Gemini and News keys are set, and runs `validate_config()`. Run it with `python test_config.py` to check your `.env`. It only reports the Gemini key, even though Mistral is first in the default order.

### 6.13 Running and deploying: Dockerfile and workflow

- **[Dockerfile](Dockerfile)**: Python 3.11 slim; a user with UID 1000 because Hugging Face Spaces requires it ([line 9](Dockerfile#L9)); install requirements; copy the code; `MPLCONFIGDIR=/tmp/matplotlib` gives matplotlib a writable cache folder ([line 20](Dockerfile#L20)); start Streamlit on port 7860 with CORS/XSRF checks off so it works behind the Space's proxy ([line 23](Dockerfile#L23)). API keys are **not** in the image (`.dockerignore` excludes `.env`); on Hugging Face they are set as Space secrets, which become environment variables.
- **[.github/workflows/deploy-hf.yml](.github/workflows/deploy-hf.yml)**: on every push to `main`, force-push the repo to the Hugging Face Space ([line 29](.github/workflows/deploy-hf.yml#L29)), which rebuilds from the Dockerfile. Every 12 hours ([line 9](.github/workflows/deploy-hf.yml#L9)) it pings the demo URL so the free Space doesn't go to sleep.
- **[README.md:1-10](README.md#L1-L10)**: the block between the `---` lines is the Space's configuration (Docker SDK, port 7860).

---

## 7. One run traced from start to finish

You leave the defaults (ticker **AAPL**, no company name, 30 days) and click **🚀 Run Analysis**. Assume `.env` has `LLM_PROVIDERS=mistral,groq,gemini` and only a Groq key, and no NewsAPI key.

**1. Streamlit re-runs app.py.** Settings are imported first, which calls `load_dotenv()`: [config/settings.py:21](config/settings.py#L21). This time `run_analysis` (the button value) is `True`: [app.py:586](app.py#L586), [app.py:648](app.py#L648).

**2. The UI starts the orchestrator** with its progress callback, and waits: [app.py:686-692](app.py#L686-L692).

**3. Configuration check.** `validate_config()` finds `["groq"]` and prints "Configuration loaded successfully!": [agents/orchestrator.py:152-153](agents/orchestrator.py#L152-L153) → [config/settings.py:55-71](config/settings.py#L55-L71).

**4. Agents are created**, each with an `LLMClient` holding one OpenAI-compatible client for Groq. Mistral and Gemini are skipped because they have no key: [agents/orchestrator.py:264-275](agents/orchestrator.py#L264-L275) → [config/llm_client.py:120-128](config/llm_client.py#L120-L128).

**5. Market research.** `research("AAPL", "")` → `search_stock_news` builds `"AAPL stock news"` and, with no NewsAPI key, calls DuckDuckGo: [agents/market_researcher.py:113-117](agents/market_researcher.py#L113-L117) → [tools/news_tools.py:278-300](tools/news_tools.py#L278-L300).
Each of up to 10 articles gets a keyword sentiment; the average gives, say, score 0.21 → "positive": [tools/news_tools.py:306-326](tools/news_tools.py#L306-L326).

**6. LLM call #1.** The news is formatted as text and sent with the six-section prompt. `_Completions.create` tries Groq, gets an answer, records `last_provider = "groq"`, and returns: [agents/market_researcher.py:204-212](agents/market_researcher.py#L204-L212) → [config/llm_client.py:88-98](config/llm_client.py#L88-L98). The sections are cut out with `_extract_section`.

**7. Data analysis.** `analyze("AAPL", 30, sentiment_data=market_research)`: [agents/orchestrator.py:189-193](agents/orchestrator.py#L189-L193).
- Yahoo is asked for company info (→ name "Apple Inc."), metrics, and the price history twice: [agents/data_analyst.py:130-142](agents/data_analyst.py#L130-L142).
- Three PNGs are written to `output/reports/charts/`: [agents/data_analyst.py:151-156](agents/data_analyst.py#L151-L156) → [tools/chart_tools.py:369-401](tools/chart_tools.py#L369-L401).
- **LLM call #2** interprets the numbers: [agents/data_analyst.py:303-311](agents/data_analyst.py#L303-L311).
- Back in the orchestrator, the company name is updated to "Apple Inc.": [agents/orchestrator.py:197-198](agents/orchestrator.py#L197-L198).

**8. Report writing.** `write_report` flattens both results into one dict (`market_cap` = "N/A", see section 8), then **LLM call #3** asks for the three marked sections: [agents/report_writer.py:166-170](agents/report_writer.py#L166-L170) → [agents/report_writer.py:346](agents/report_writer.py#L346).
The answer is split at the markers, checked for length and cleaned of Markdown: [agents/report_writer.py:369-397](agents/report_writer.py#L369-L397).

**9. The PDF.** `generate_report` builds the pages, loads the three PNGs and saves `output/reports/AAPL_Financial_Report_<time>.pdf`: [agents/report_writer.py:184-193](agents/report_writer.py#L184-L193) → [tools/pdf_tools.py:288-475](tools/pdf_tools.py#L288-L475).

**10. Wrap-up.** `success = True`; `finally` computes about 40–70 seconds of run time and merges all logs: [agents/orchestrator.py:228-260](agents/orchestrator.py#L228-L260).

**11. The UI shows it.** The result is saved in session state, the status cards turn "Complete", Quick Stats fill in, and the PDF bytes go into a download button: [app.py:695-785](app.py#L695-L785).

**12. You click Download PDF.** Streamlit re-runs the script once more. `run_analysis` is now `False`, so the `elif` branch redraws the stored result and the browser receives the file: [app.py:857-949](app.py#L857-L949).

Total: four Yahoo requests for prices/info (more inside yfinance), one news search, three LLM calls, three charts and one PDF, all in one Python thread, one after another.

---

## 8. Things to notice

Real issues found while reading and running the code. Each one is a small lesson.

### Bugs

1. **Market Cap is always missing from the PDF and the report text.** `market_cap_formatted` is only added by `get_full_stock_analysis` ([tools/finance_tools.py:293-296](tools/finance_tools.py#L293-L296)), which the Data Analyst never calls. So the PDF's "Market Cap" row ([tools/pdf_tools.py:356](tools/pdf_tools.py#L356)) is `"N/A"` and gets skipped, and the Report Writer's prompt says "Market Cap: N/A" ([agents/report_writer.py:239](agents/report_writer.py#L239)). Only the Data Analyst's own prompt sees the real value, because it formats it itself ([agents/data_analyst.py:213](agents/data_analyst.py#L213)). Fix: set `key_metrics["market_cap_formatted"]` in `analyze()`.

2. **Keyword sentiment matches parts of words.** `word in text_lower` ([tools/news_tools.py:92-93](tools/news_tools.py#L92-L93)) is a substring test, so `up` matches "update" and "supply", `low` matches "follow", `cut` matches "execute", `gain` matches "against", `rise` matches "enterprise", and `deal` matches "ideal". Running it confirms this: *"Firm will execute against enterprise ideal"*, a sentence with no opinion in it, scores **+0.5, positive**. Matching whole words with `re.findall(r"\b\w+\b", text)` would fix it ([exercise 3](#9-exercises)).

3. **Two different defaults for `LLM_PROVIDERS`.** `config/settings.py` defaults to `"mistral,groq,gemini"` ([config/settings.py:29](config/settings.py#L29)); `LLMClient` defaults to `"groq"` ([config/llm_client.py:118](config/llm_client.py#L118)). If `LLM_PROVIDERS` isn't set (for example, you forgot it in the Hugging Face secrets) and you only have a Mistral key, `validate_config` says "OK" but every agent then crashes with *"No API key set for any provider in LLM_PROVIDERS=groq"*. Confirmed by running both with only `MISTRAL_API_KEY` set. Fix: import one constant in both places.

4. **The agent test blocks can't run as documented.** `agents/market_researcher.py` imports `config.llm_client` on [line 20](agents/market_researcher.py#L20), *before* adding the project root to `sys.path` on [line 29](agents/market_researcher.py#L29). Running `python agents/market_researcher.py` therefore fails with `ModuleNotFoundError: No module named 'config'`. Same in [agents/data_analyst.py:20](agents/data_analyst.py#L20) and [agents/report_writer.py:27](agents/report_writer.py#L27). The orchestrator and tools put the path fix first, so they work. Workaround: run `python -m agents.market_researcher` from the project root.

5. **The "live" console isn't live.** The UI and its docstring promise real-time progress ([app.py:5-8](app.py#L5-L8)), but `progress_callback` only appends to a list ([app.py:658-669](app.py#L658-L669)); it never redraws `console_placeholder`. The screen shows "Initializing…" for the whole run, then everything at once.

6. **Company names with unusual characters can crash the PDF.** `sanitize_text` is used for paragraphs, but not for the company name in `header()` ([tools/pdf_tools.py:97](tools/pdf_tools.py#L97)) and `add_title_page()` ([tools/pdf_tools.py:136](tools/pdf_tools.py#L136)). A name containing a character outside Latin-1 would make fpdf2 raise an encoding error.

7. **`"rate"` matches more than rate limits.** The retry check `"rate" in error_str.lower()` ([agents/report_writer.py:133](agents/report_writer.py#L133)) also matches words like "generate" or "accurate", so unrelated errors can trigger pointless waits.

### Design quirks

8. **News is searched before the company name is known** when you leave it blank ([agents/orchestrator.py:165-174](agents/orchestrator.py#L165-L174)). "AAPL stock news" gives worse results than "Apple Inc. (AAPL) stock news". Running the Data Analyst's `get_company_info` first would fix it.

9. **Duplicate downloads.** Yahoo's `info` is fetched twice and price history twice per run ([agents/data_analyst.py:130-142](agents/data_analyst.py#L130-L142)). Yahoo is quick to rate-limit, so fewer calls means fewer failures.

10. **`"$N/A"` rows** appear in the PDF tables when a price is missing, because the `$` is added before the "N/A" check ([tools/pdf_tools.py:351-355](tools/pdf_tools.py#L351-L355)).

11. **Unescaped HTML.** Log messages, the executive summary and the recommendations are pasted into HTML with `unsafe_allow_html=True` ([app.py:407-411](app.py#L407-L411), [app.py:791-795](app.py#L791-L795)). If an LLM answer contained `<` or HTML tags, it would be rendered rather than shown as text. `html.escape()` is the standard fix.

12. **Matplotlib's global state** (`plt.subplots`, `plt.savefig`, `plt.close`) is shared by the whole process. With two visitors running analyses at once, Streamlit runs them in parallel threads, and charts could mix. The object-oriented form (`fig.savefig`, `plt.close(fig)`) is safer.

13. **Output files are never deleted.** Every run adds three PNGs and a PDF under `output/reports/`. On Hugging Face this resets on restart; on your own machine the folder just grows.

14. **The model name is ignored.** Agents pass `model=self.model` (the first provider's model) to every call, but `_Completions.create` ignores it ([config/llm_client.py:80-86](config/llm_client.py#L80-L86)).

15. **`ln=True` in fpdf2 calls** (e.g. [tools/pdf_tools.py:102](tools/pdf_tools.py#L102)) is deprecated in recent fpdf2 versions in favour of `new_x`/`new_y`; it still works but prints warnings.

### Unused code

- `plotly` and `beautifulsoup4` in [requirements.txt](requirements.txt) are never imported.
- `import json` in all three agents; `analyze_sentiment` imported in [agents/market_researcher.py:32](agents/market_researcher.py#L32); `get_full_stock_analysis` imported in [agents/data_analyst.py:37](agents/data_analyst.py#L37); `get_company_info` imported in [app.py:23](app.py#L23).
- `get_news_summary` ([tools/news_tools.py:347-394](tools/news_tools.py#L347-L394)), `save_logs_to_file` ([app.py:492-510](app.py#L492-L510)), `progress_data` ([app.py:656](app.py#L656)), `get_conversation_log_formatted`, `analyze_stock`, every agent's `get_conversation_log`, `LLMClient.last_provider` (set, never read) and `provider_names`.
- `DEFAULT_DAYS_BACK` and the three `*_API_KEY` constants in [config/settings.py](config/settings.py#L30-L49) are only read by `test_config.py`.
- The CSS classes `.console-container`, `.console-line` and friends ([app.py:96-151](app.py#L96-L151)) are never used; the console uses inline styles instead.

### Setup gotchas

- **Keep `LLM_PROVIDERS` in your `.env`** (and in Hugging Face secrets), or see bug 3.
- **Run from the project folder**, and use `python -m agents.orchestrator` (not `python agents/orchestrator.py` for the three agents) when testing modules directly.
- **DuckDuckGo and Yahoo can rate-limit you** after a few quick runs. Errors become empty results and "N/A" in the report rather than crashes, which can look like the app "worked" with no data.
- **Inline comments in `.env`**: lines like `MISTRAL_API_KEY=   # https://...` in [.env.example:9](.env.example#L9) are read as empty by python-dotenv. Put your key right after `=`, and the comment is ignored.
- **The README's folder diagram** doesn't show `config/llm_client.py` or `test_config.py`.

---

## 9. Exercises

From easy to advanced. Each says which file to change. Test by running the app or `python -m agents.orchestrator`.

1. **Add an analysis period.** Offer 180 days in the dropdown. *File:* [app.py:563-568](app.py#L563-L568). Then check that the price chart's date labels are still readable ([tools/chart_tools.py:154-155](tools/chart_tools.py#L154-L155)).

2. **Fix the market cap.** In `DataAnalystAgent.analyze`, add `market_cap_formatted` to `key_metrics` so the PDF and the Report Writer get it. *File:* [agents/data_analyst.py:134-137](agents/data_analyst.py#L134-L137). Open the PDF and check the Price Information table.

3. **Whole-word sentiment.** Make `analyze_sentiment` match whole words only, and count every occurrence instead of just whether a word appears. *File:* [tools/news_tools.py:89-93](tools/news_tools.py#L89-L93). Check with `"Firm will execute against enterprise ideal"` (should be neutral) and the test sentences in [tools/news_tools.py:410-416](tools/news_tools.py#L410-L416).

4. **Remove the duplicated results code.** Move the results display into one function `render_results(result, key_suffix)` and call it from both branches. *File:* [app.py:714-836](app.py#L714-L836) and [app.py:857-1000](app.py#L857-L1000).

5. **One default for providers.** Make `LLMClient` use `config.settings.LLM_PROVIDERS` as its default, so bug 3 can't happen. *Files:* [config/llm_client.py:117-118](config/llm_client.py#L117-L118), [config/llm_client.py:151](config/llm_client.py#L151). Watch out for a circular import: `settings` imports `llm_client` inside a function for a reason.

6. **A base agent class.** Create `agents/base.py` with a `BaseAgent` holding `__init__` (client, history), `log`, `_extract_section` and `get_conversation_log`, and make the three agents inherit from it. *Files:* the three agents, e.g. [agents/market_researcher.py:52-91](agents/market_researcher.py#L52-L91).

7. **Show which provider answered.** After each LLM call, log `self.client.last_provider` and show it in the console. *Files:* the `_analyze_with_llm` methods and [agents/report_writer.py:115-128](agents/report_writer.py#L115-L128).

8. **Make the console really live.** Pass `console_placeholder` into the callback and call `render_agent_console(st.session_state.logs, is_running=True)` inside it. *File:* [app.py:658-669](app.py#L658-L669). Notice how the experience changes during the minute-long wait.

9. **Write real tests.** Create `tests/test_news_tools.py` with pytest tests for `analyze_sentiment` and `format_large_number`, and a test for `ReportWriterAgent._parse_sections` with a hand-written LLM answer. These need no network. *Files:* [tools/news_tools.py:67-116](tools/news_tools.py#L67-L116), [tools/finance_tools.py:247-269](tools/finance_tools.py#L247-L269), [agents/report_writer.py:355-407](agents/report_writer.py#L355-L407).

10. **Run research and data fetching in parallel.** The news search and the Yahoo downloads don't depend on each other. Use `concurrent.futures.ThreadPoolExecutor` in the orchestrator to start both at once, then draw the sentiment chart after both finish. *Files:* [agents/orchestrator.py:159-205](agents/orchestrator.py#L159-L205) and [agents/data_analyst.py:149-156](agents/data_analyst.py#L149-L156). Measure the time saved.

---

## 10. Glossary

**Agent.** Here, a Python class with one job, its own LLM instructions, and the tools it needs.

**Annualised volatility.** Daily volatility × √252, an estimate of yearly price variation.

**API key.** A secret string that proves to a service (Groq, NewsAPI…) who is calling.

**Callback.** A function passed to other code to be called later, e.g. to report progress.

**DataFrame.** A pandas table with named columns and an index (here, dates).

**Environment variable.** A named value set outside the program (`GROQ_API_KEY=...`), read with `os.getenv`.

**Fallback.** A second option used automatically when the first fails, here the next LLM provider.

**LLM (Large Language Model).** An AI model that generates text, like Mistral, Gemini or `gpt-oss` on Groq.

**Market capitalisation (market cap).** Share price × number of shares; the market value of the whole company.

**Moving average (SMA).** The average closing price over the last N days, used to show the trend.

**OpenAI-compatible API.** A service that accepts the same request format as OpenAI's chat API, so the `openai` library can talk to it.

**Orchestrator.** The code that runs agents in order and passes data between them.

**P/E ratio (price-to-earnings).** Share price ÷ earnings per share. Higher means investors pay more for each pound or dollar of profit.

**Placeholder (Streamlit).** A spot on the page created with `st.empty()` that can be redrawn later.

**Prompt (system / user).** The instructions sent to an LLM. The system message sets the role and rules; the user message gives the task and data.

**Rate limit.** A cap on requests per time period. Exceeding it returns HTTP 429.

**Session state (Streamlit).** A dict that survives the script re-running on each click.

**Sentiment analysis.** Judging whether text sounds positive, negative or neutral.

**Temperature.** An LLM setting for randomness: low is consistent, high is creative.

**Ticker.** A short stock symbol, e.g. AAPL for Apple.

**Token.** A chunk of text (roughly ¾ of a word) that LLMs read and write; `max_tokens` limits answer length.

**Volatility.** How much a price moves around; the standard deviation of daily returns.
