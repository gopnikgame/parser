FROM python:3.11-slim

# Переменные окружения
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    apt-utils \
    ca-certificates \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    jq \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Добавить в секцию с установкой зависимостей
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > \
    /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Установка ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1-3) && \
    echo "🔍 Установленная версия Chrome: $CHROME_VERSION" && \
    AVAILABLE_VERSIONS=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json") && \
    CHROMEDRIVER_VERSION=$(echo "$AVAILABLE_VERSIONS" | jq -r ".versions[] | select(.version | startswith(\"$CHROME_VERSION\")) | .version" | head -1) && \
    if [ -z "$CHROMEDRIVER_VERSION" ]; then \
        echo "⚠️ Точная версия не найдена, используем последнюю стабильную"; \
        CHROMEDRIVER_VERSION=$(echo "$AVAILABLE_VERSIONS" | jq -r '.versions[-1].version'); \
    fi && \
    echo "📥 Скачиваем ChromeDriver версии: $CHROMEDRIVER_VERSION" && \
    DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" && \
    echo "🔗 URL для скачивания: $DOWNLOAD_URL" && \
    wget -O /tmp/chromedriver.zip "$DOWNLOAD_URL" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver* && \
    chromedriver --version && \
    echo "✅ ChromeDriver успешно установлен"

WORKDIR /app

# Создаем пользователя parser с правильными правами
RUN useradd -m -u 1000 parser

# Создаем директорию output и устанавливаем права ПЕРЕД копированием файлов
RUN mkdir -p /app/output && \
    chown -R parser:parser /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY parser.py scheduler.py ./

# ВАЖНО: Устанавливаем права ПОСЛЕ копирования всех файлов
RUN chown -R parser:parser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/output

USER parser

CMD ["python", "scheduler.py"]