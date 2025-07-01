#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Аргумент для имени экземпляра (по умолчанию - пустая строка)
INSTANCE_NAME="${1:-}"

# Конфигурация
REPO_OWNER="gopnikgame"
REPO_NAME="parser"
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
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    local level=$1
    local message=$2
    echo -e "${!level}${message}${NC}" | tee -a "$LOG_FILE"
}

# Функция для безопасного ввода токена
read_token() {
    local token
    echo -n "🔑 Введите ваш GitHub Personal Access Token: "
    read -s token
    echo
    echo "$token"
}

# Функция для проверки валидности GitHub токена
validate_github_token() {
    local token=$1
    log "BLUE" "🔍 Проверка валидности GitHub токена..."
    
    local response
    response=$(curl -s -w "%{http_code}" -H "Authorization: token $token" https://api.github.com/user)
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        log "GREEN" "✅ GitHub токен валиден"
        return 0
    else
        log "RED" "❌ GitHub токен невалиден (HTTP $http_code)"
        return 1
    fi
}

# Функция для проверки доступа к репозиторию
check_repo_access() {
    local token=$1
    log "BLUE" "🔍 Проверка доступа к репозиторию $REPO_OWNER/$REPO_NAME..."
    
    local response
    response=$(curl -s -w "%{http_code}" -H "Authorization: token $token" \
               "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        log "GREEN" "✅ Доступ к репозиторию подтвержден"
        return 0
    else
        log "RED" "❌ Нет доступа к репозиторию (HTTP $http_code)"
        return 1
    fi
}

# Функция для создания .env файла
create_env_file() {
    local token=$1
    local env_file="$INSTALL_DIR/.env"
    
    log "BLUE" "📝 Создание .env файла..."
    
    cat > "$env_file" << EOF
# ==========================================
# GitHub настройки для автоматической отправки результатов
# ==========================================

# GitHub Personal Access Token
GITHUB_TOKEN=$token

# Настройки GitHub репозитория
GITHUB_OWNER=gopnikgame
GITHUB_REPO=Installer_dnscypt
GITHUB_BRANCH=main

# ==========================================
# Настройки Chrome для парсинга (опционально)
# ==========================================

# Запуск Chrome в headless режиме (без графического интерфейса)
CHROME_HEADLESS=true

# Отключение sandbox для Docker контейнеров
CHROME_NO_SANDBOX=true

# ==========================================
# Настройки Scheduler'а (опционально)
# ==========================================

# Интервал запуска парсера в днях (по умолчанию: 7 дней)
SCHEDULER_INTERVAL_DAYS=7

# Включение отладочных логов scheduler'а
SCHEDULER_DEBUG=false
EOF

    chmod 600 "$env_file"  # Ограничиваем доступ к файлу с токеном
    log "GREEN" "✅ Файл .env создан и настроен"
}

# Функция для клонирования репозитория с токеном
clone_repo_with_token() {
    local token=$1
    local temp_dir=$2
    
    log "BLUE" "⬇️ Клонирование приватного репозитория..."
    
    # Клонируем репозиторий с токеном
    local repo_url="https://$token@github.com/$REPO_OWNER/$REPO_NAME.git"
    
    if git clone "$repo_url" "$temp_dir/$PROJECT_DIR"; then
        log "GREEN" "✅ Репозиторий успешно клонирован"
        return 0
    else
        log "RED" "❌ Ошибка клонирования репозитория"
        return 1
    fi
}

# Функция для запроса и настройки GitHub токена
setup_github_token() {
    local token
    local attempts=0
    local max_attempts=3
    
    log "YELLOW" "⚠️ Для работы с приватным репозиторием необходим GitHub Personal Access Token"
    echo ""
    log "BLUE" "📋 Инструкция по получению токена:"
    echo "   1. Перейдите на https://github.com/settings/tokens"
    echo "   2. Нажмите 'Generate new token (classic)'"
    echo "   3. Выберите права доступа: repo, workflow"
    echo "   4. Скопируйте созданный токен"
    echo ""
    
    while [ $attempts -lt $max_attempts ]; do
        token=$(read_token)
        
        if [ -z "$token" ]; then
            log "RED" "❌ Токен не может быть пустым"
            ((attempts++))
            continue
        fi
        
        if validate_github_token "$token" && check_repo_access "$token"; then
            echo "$token"
            return 0
        fi
        
        ((attempts++))
        if [ $attempts -lt $max_attempts ]; then
            log "YELLOW" "⚠️ Попробуйте еще раз ($attempts/$max_attempts)"
        fi
    done
    
    log "RED" "❌ Превышено количество попыток ввода токена"
    return 1
}

# Проверка зависимостей
log "BLUE" "🔍 Проверка зависимостей..."
missing_deps=()

if ! command -v git &> /dev/null; then
    missing_deps+=("git")
fi
if ! command -v docker &> /dev/null; then
    missing_deps+=("docker.io")
fi
if ! command -v docker-compose &> /dev/null; then
    missing_deps+=("docker-compose")
fi
if ! command -v nano &> /dev/null; then
    missing_deps+=("nano")
fi
if ! command -v curl &> /dev/null; then
    missing_deps+=("curl")
fi

if [ ${#missing_deps[@]} -gt 0 ]; then
    log "YELLOW" "⚠️ Установка необходимых пакетов: ${missing_deps[*]}"
    apt-get update
    apt-get install -y "${missing_deps[@]}"
fi

# Проверка существования директории установки
if [ -d "$INSTALL_DIR" ]; then
    log "BLUE" "🚀 Директория установки существует: $INSTALL_DIR"
    
    # Проверяем наличие .env файла
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        log "YELLOW" "⚠️ Файл .env не найден, требуется настройка GitHub токена"
        
        if github_token=$(setup_github_token); then
            create_env_file "$github_token"
        else
            log "RED" "❌ Не удалось настроить GitHub токен"
            exit 1
        fi
    fi
    
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    
    # Обновляем репозиторий если есть .git
    if [ -d ".git" ]; then
        log "BLUE" "🔄 Обновление репозитория..."
        
        # Загружаем токен из .env
        if [ -f ".env" ]; then
            source .env
            if [ -n "${GITHUB_TOKEN:-}" ]; then
                # Обновляем remote URL с токеном
                git remote set-url origin "https://$GITHUB_TOKEN@github.com/$REPO_OWNER/$REPO_NAME.git"
                git pull origin main
                log "GREEN" "✅ Репозиторий обновлен"
            fi
        fi
    fi
    
    # Добавляем права на выполнение скрипта manage_parser.sh
    chmod +x manage_parser.sh
    
    # Запускаем скрипт manage_parser.sh с именем экземпляра
    log "BLUE" "🚀 Запуск основного скрипта управления парсером для экземпляра $PROJECT_DIR..."
    ./manage_parser.sh "$INSTANCE_NAME"
    
else
    log "BLUE" "⬇️ Первоначальная установка парсера для экземпляра $PROJECT_DIR..."
    
    # Запрашиваем GitHub токен
    if ! github_token=$(setup_github_token); then
        log "RED" "❌ Не удалось настроить GitHub токен"
        exit 1
    fi
    
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    
    # Клонируем репозиторий с токеном
    if ! clone_repo_with_token "$github_token" "$TEMP_DIR"; then
        log "RED" "❌ Не удалось клонировать репозиторий"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Переходим в директорию проекта
    cd "$TEMP_DIR/$PROJECT_DIR"
    
    # Создаем директорию установки, если она не существует
    mkdir -p "$INSTALL_DIR"
    
    # Копируем файлы в директорию установки
    log "BLUE" "📦 Копирование файлов в директорию установки..."
    cp -r . "$INSTALL_DIR"
    
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    
    # Создаем .env файл с токеном
    create_env_file "$github_token"
    
    # Добавляем права на выполнение скрипта manage_parser.sh
    chmod +x manage_parser.sh
    
    # Запускаем скрипт manage_parser.sh с именем экземпляра
    log "BLUE" "🚀 Запуск основного скрипта управления парсером..."
    ./manage_parser.sh "$INSTANCE_NAME"
    
    # Удаляем временную директорию
    rm -rf "$TEMP_DIR"
fi

log "GREEN" "✅ Установка/обновление парсера $PROJECT_DIR завершено"