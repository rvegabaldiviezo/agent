FROM python:3.11-slim

WORKDIR /agent

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

CMD ["adk", "web"]
