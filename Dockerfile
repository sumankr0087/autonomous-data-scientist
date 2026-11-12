FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; wheels cover the rest.
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed the sample warehouse at build time so the app is usable immediately.
RUN python main.py seed || true

EXPOSE 8501

# GOOGLE_API_KEY must be provided at runtime:  docker run -e GOOGLE_API_KEY=...
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
