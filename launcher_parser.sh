#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Аргумент для имени экземпляра (по умолчанию - пустая строка)
INSTANCE_NAME="${1:-}"

# Конфигурация
REPO_URL="https://github.com/gopnikgame/parser.git"
PROJECT_DIR="dnscrypt-parser"

# Если указано имя экземпляра, добавляем суффикс к PROJECT_DIR
if [ -n "$INSTANCE_NAME" ]; then
    PROJECT_DIR="${PROJECT_DIR}_${INSTANCE_NAME}"
fi

INSTALL_DIR="/opt/$PROJECT_DIR" # Постоянная директория для установки
LOG_FILE="/var/log/$PROJECT_DIR.log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    local level=$1
    local message=$2
    echo -e "${!level}${message}${NC}" | tee -a "$LOG_FILE"
}

# Проверка зависимостей
log "BLUE" "🔍 Проверка зависимостей..."
if ! command -v git &> /dev/null || ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null || ! command -v nano &> /dev/null; then
    log "YELLOW" "⚠️ Установка необходимых пакетов..."
    apt-get update
    apt-get install -y git docker.io docker-compose nano
fi

# Проверка существования директории установки
if [ -d "$INSTALL_DIR" ]; then
    log "BLUE" "🚀 Директория установки существует: $INSTALL_DIR"
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    # Добавляем права на выполнение скрипта manage_parser.sh
    chmod +x manage_parser.sh
    # Запускаем скрипт manage_parser.sh с именем экземпляра
    log "BLUE" "🚀 Запуск основного скрипта управления парсером для экземпляра $PROJECT_DIR..."
    ./manage_parser.sh "$INSTANCE_NAME"
else
    log "BLUE" "⬇️ Клонирование репозитория парсера для экземпляра $PROJECT_DIR..."
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    # Переходим во временную директорию
    cd "$TEMP_DIR"
    # Клонируем репозиторий
    git clone "$REPO_URL" "$PROJECT_DIR"
    # Переходим в директорию проекта
    cd "$PROJECT_DIR"
    # Создаем директорию установки, если она не существует
    mkdir -p "$INSTALL_DIR"
    # Копируем файлы в директорию установки
    log "BLUE" "📦 Копирование файлов в директорию установки..."
    cp -r . "$INSTALL_DIR"
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    # Добавляем права на выполнение скрипта manage_parser.sh
    chmod +x manage_parser.sh
    # Запускаем скрипт manage_parser.sh с именем экземпляра
    log "BLUE" "🚀 Запуск основного скрипта управления парсером..."
    ./manage_parser.sh "$INSTANCE_NAME"
    # Удаляем временную директорию
    rm -rf "$TEMP_DIR"
fi

log "GREEN" "✅ Установка/обновление парсера $PROJECT_DIR завершено"