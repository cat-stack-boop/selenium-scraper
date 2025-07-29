# ---------- build stage ----------------------------------------------------
ARG CHROME_CHANNEL=stable          # overridden by CI matrix
FROM ubuntu:24.04 AS build
RUN apt-get update -qq && \
    apt-get install -y curl unzip ca-certificates python3 python3-pip
# Chrome + driver matching the requested channel
RUN curl -fsSL https://dl.google.com/linux/direct/google-chrome-${CHROME_CHANNEL}_current_amd64.deb -o /tmp/chrome.deb && \
    apt-get install -y /tmp/chrome.deb && \
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    curl -fsSL "$DRIVER_URL" -o /tmp/driver.zip && unzip -q /tmp/driver.zip -d /opt && \
    mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/ && chmod +x /usr/local/bin/chromedriver
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# ---------- final stage ----------------------------------------------------
FROM python:3.11-slim as final
COPY --from=build /usr/local/bin/chromedriver /usr/local/bin/chromedriver
COPY --from=build /usr/bin/google-chrome /usr/bin/google-chrome
COPY --from=build /opt/google /opt/google
WORKDIR /app
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 \
    CHROME_DRIVER_PATH=/usr/local/bin/chromedriver \
    CHROME_BINARY_PATH=/usr/bin/google-chrome
CMD ["python", "-m", "scrape_chatgpt"]
