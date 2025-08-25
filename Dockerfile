# Multi-stage build pre Claims AI aplikáciu
FROM python:3.9-slim as base

# Nastavenie pracovného priečinka
WORKDIR /app

# Inštalácia systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Kopírovanie requirements a inštalácia Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírovanie aplikačného kódu
COPY . .

# Vytvorenie potrebných priečinkov
RUN mkdir -p poistne_udalosti anonymized_output general_output raw_ocr_output analysis_output

# Nastavenie environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

# Exponovanie portov
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Spustenie aplikácie (Streamlit + FastAPI)
CMD ["sh", "-c", "streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0 & uvicorn api:app --host 0.0.0.0 --port 8000"]
