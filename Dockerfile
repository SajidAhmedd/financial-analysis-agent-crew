# Financial Analysis Agent Crew - Streamlit app
# Runs on Hugging Face Spaces (port 7860) or anywhere Docker runs.

FROM python:3.11-slim

WORKDIR /app

# Non-root user with UID 1000 (required by Hugging Face Spaces)
RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
RUN mkdir -p output/reports && chown -R appuser:appuser /app

USER appuser
ENV HOME=/home/appuser \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib

EXPOSE 7860
CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT:-7860} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --browser.gatherUsageStats false"]
