FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY docs/ ./docs/
COPY README.md .
COPY .env.example .env

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

EXPOSE 8000

CMD ["python", "-m", "src.api.server"]
