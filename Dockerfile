# Dockerfile
FROM python:3.11-slim

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    chromium libnss3-tools ca-certificates fonts-liberation \
    wget unzip gnupg && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV UCGUI=0

WORKDIR /app
COPY brightdata_proxy_headless.py ./brightdata_proxy_headless.py
COPY brightdata_ca.crt ./brightdata_ca.crt

RUN pip install --no-cache-dir selenium-wire undetected-chromedriver python-dotenv

# Non-root user
RUN useradd -m appuser
USER appuser

CMD ["python", "brightdata_proxy_headless.py"]
