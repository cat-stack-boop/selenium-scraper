FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver \
    CHROME_BINARY_PATH=/usr/bin/chromium

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "scrape_chatgpt.py"]
