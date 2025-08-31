
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

EXPOSE 8000

CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]