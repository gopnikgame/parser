FROM python:3.11-slim

# Устанавливаем переменные среды для неинтерактивной установки
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Обновляем систему и устанавливаем базовые зависимости
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

# Добавляем ключ Google Chrome через новый метод (без использования apt-key)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > \
    /etc/apt/sources.list.d/google-chrome.list

# Устанавливаем Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем ChromeDriver используя новый Chrome for Testing API
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1-3) && \
    echo "🔍 Установленная версия Chrome: $CHROME_VERSION" && \
    # Пробуем найти совместимую версию ChromeDriver через новый API
    AVAILABLE_VERSIONS=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json") && \
    # Находим ближайшую доступную версию ChromeDriver
    CHROMEDRIVER_VERSION=$(echo "$AVAILABLE_VERSIONS" | jq -r ".versions[] | select(.version | startswith(\"$CHROME_VERSION\")) | .version" | head -1) && \
    # Если точной версии нет, берем последнюю стабильную
    if [ -z "$CHROMEDRIVER_VERSION" ]; then \
        echo "⚠️ Точная версия не найдена, используем последнюю стабильную"; \
        CHROMEDRIVER_VERSION=$(echo "$AVAILABLE_VERSIONS" | jq -r '.versions[-1].version'); \
    fi && \
    echo "📥 Скачиваем ChromeDriver версии: $CHROMEDRIVER_VERSION" && \
    # Формируем URL для скачивания
    DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" && \
    echo "🔗 URL для скачивания: $DOWNLOAD_URL" && \
    # Скачиваем и устанавливаем ChromeDriver
    wget -O /tmp/chromedriver.zip "$DOWNLOAD_URL" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver* && \
    # Проверяем установку
    chromedriver --version && \
    echo "✅ ChromeDriver успешно установлен"

# Создаем рабочую директорию
WORKDIR /app

# Создаем непривилегированного пользователя заранее
RUN useradd -m -u 1000 parser && \
    chown -R parser:parser /app

# Копируем requirements.txt и устанавливаем зависимости как root
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем скрипты и устанавливаем права доступа
COPY parser.py scheduler.py ./
RUN chown -R parser:parser /app

# Переключаемся на непривилегированного пользователя
USER parser

# Команда по умолчанию - запуск scheduler'а
CMD ["python", "scheduler.py"]