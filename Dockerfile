# Dockerfile
FROM python:3.11-slim

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    chromium libnss3-tools ca-certificates fonts-liberation \
    wget unzip gnupg && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV UCGUI=0

WORKDIR /app
# Copy all necessary files
COPY requirements.txt ./requirements.txt
COPY brightdata_proxy_headless.py ./brightdata_proxy_headless.py
COPY brightdata_ca.crt ./brightdata_ca.crt

# Install from requirements.txt with specific versions
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user and give them ownership of /app
RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser

CMD ["python", "brightdata_proxy_headless.py"]
