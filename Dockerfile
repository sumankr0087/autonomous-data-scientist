# Backend image — serves the FastAPI API.
# Works on Hugging Face Spaces (Docker SDK, port 7860) and any Docker host.
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Writable dirs for HF Spaces (which runs as a non-root user).
ENV HOME=/tmp
ENV DUCKDB_PATH=/tmp/warehouse.duckdb
ENV ADS_ARTIFACTS_DIR=/tmp/artifacts
ENV ADS_LOGS_DIR=/tmp/logs
ENV ADS_DATA_DIR=/tmp/data
ENV LOG_TO_FILE=false
RUN mkdir -p /tmp/artifacts /tmp/logs /tmp/data && chmod -R 777 /tmp

# Seed the sample warehouse at build so the API is usable immediately.
RUN DUCKDB_PATH=/tmp/warehouse.duckdb python main.py seed || true

EXPOSE 7860

# GOOGLE_API_KEY is provided at runtime (HF Space secret / docker -e).
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
