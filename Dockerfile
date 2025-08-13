## Dockerfile
#FROM python:3.11-slim
#
#RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#    chromium libnss3-tools ca-certificates fonts-liberation \
#    wget unzip gnupg && rm -rf /var/lib/apt/lists/*
#
#ENV CHROME_BIN=/usr/bin/chromium
#ENV UCGUI=0
#
#WORKDIR /app
## Copy all necessary files
#COPY requirements.txt ./requirements.txt
#COPY brightdata_proxy_headless.py ./brightdata_proxy_headless.py
#COPY browser_setup.py ./browser_setup.py
#COPY dom_extractor.py ./dom_extractor.py
#COPY actions.py ./actions.py
#COPY search_agent.py ./search_agent.py
#COPY main.py ./main.py
#
#
## Install from requirements.txt with specific versions
#RUN pip install --no-cache-dir -r requirements.txt
#
## Create non-root user and give them ownership of /app
#RUN useradd -m appuser && chown -R appuser:appuser /app
#
#USER appuser
#
## Default to running the agent in headless mode
## Can be overridden with custom task via docker run
#CMD ["python", "main.py", "--headless"]
