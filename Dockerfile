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

# ИСПРАВЛЕНИЕ X11: Создаем правильную структуру X11
RUN mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix && \
    mkdir -p /var/run/dbus

# Установка Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > \
    /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Установка ChromeDriver (исправленная версия)
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

# Создаем пользователя parser
RUN useradd -m -u 1000 parser

# ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА: Создаем директории с правильными правами
RUN mkdir -p /app/output && \
    mkdir -p /app/output/cache && \
    mkdir -p /app/logs && \
    chmod -R 755 /app && \
    chown -R parser:parser /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ИСПРАВЛЕНИЕ: Копируем модульную систему без удаленного parser.py
COPY scheduler.py parser_new.py ./
COPY core/ ./core/
COPY file_handlers/ ./file_handlers/
COPY github/ ./github/
COPY page_handlers/ ./page_handlers/
COPY data_handlers/ ./data_handlers/
COPY extractors/ ./extractors/
COPY strategies/ ./strategies/
COPY utils/ ./utils/

# Создаем script для автоматического выбора парсера
RUN echo '#!/bin/bash\n\
# Автоматический выбор парсера: модульный или legacy\n\
echo "🚀 Docker Container: Автоматический выбор парсера"\n\
echo "========================================"\n\
\n\
# Проверяем доступность модульной системы\n\
if [ -f "parser_new.py" ] && python -c "from core import DNSCryptParser" 2>/dev/null; then\n\
    echo "✅ Модульная система доступна - используем parser_new.py"\n\
    exec python parser_new.py "$@"\n\
else\n\
    echo "❌ Модульная система недоступна!"\n\
    exit 1\n\
fi' > /app/auto_parser.sh && \
    chmod +x /app/auto_parser.sh

# ИСПРАВЛЕНИЕ: Устанавливаем окончательные права доступа
RUN chown -R parser:parser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/output && \
    chmod -R 777 /app/logs

# Переключаемся на пользователя parser
USER parser

# Проверяем права доступа перед запуском
RUN echo "🔍 Проверка прав доступа:" && \
    ls -la /app/ && \
    echo "📁 Проверка директории output:" && \
    ls -la /app/output/ || echo "Директория output пуста" && \
    echo "🛠️ Тестируем создание файла в output:" && \
    touch /app/output/test_permissions.txt && \
    rm /app/output/test_permissions.txt && \
    echo "✅ Права доступа корректны!"

# Используем scheduler с модульной системой
CMD ["python", "scheduler.py"]