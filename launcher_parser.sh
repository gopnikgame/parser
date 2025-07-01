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
    
    # Проверяем, что мы запущены в интерактивном режиме
    if [ ! -t 0 ]; then
        log "RED" "❌ Скрипт не запущен в интерактивном режиме. Невозможно запросить токен."
        return 1
    fi
    
    echo -n "🔑 Введите ваш GitHub Personal Access Token (символы не будут отображаться): "
    read -s token
    echo ""  # Переход на новую строку после скрытого ввода
    
    if [ -z "$token" ]; then
        log "RED" "❌ Токен не может быть пустым"
        return 1
    fi
    
    echo "$token"
    return 0
}

# Функция для проверки валидности GitHub токена
validate_github_token() {
    local token=$1
    log "BLUE" "🔍 Проверка валидности GitHub токена..."
    
    local response
    local http_code
    
    # Проверяем доступность GitHub API
    if ! curl -s --connect-timeout 10 https://api.github.com > /dev/null; then
        log "RED" "❌ Нет доступа к GitHub API. Проверьте интернет-соединение."
        return 1
    fi
    
    response=$(curl -s -w "%{http_code}" --connect-timeout 10 \
                    -H "Authorization: token $token" \
                    https://api.github.com/user)
    
    if [ $? -ne 0 ]; then
        log "RED" "❌ Ошибка при выполнении запроса к GitHub API"
        return 1
    fi
    
    http_code="${response: -3}"
    
    case "$http_code" in
        "200")
            log "GREEN" "✅ GitHub токен валиден"
            return 0
            ;;
        "401")
            log "RED" "❌ GitHub токен невалиден или истек срок действия"
            return 1
            ;;
        "403")
            log "RED" "❌ Токен валиден, но недостаточно прав доступа"
            return 1
            ;;
        *)
            log "RED" "❌ Неожиданный ответ от GitHub API (HTTP $http_code)"
            return 1
            ;;
    esac
}

# Функция для проверки доступа к репозиторию
check_repo_access() {
    local token=$1
    log "BLUE" "🔍 Проверка доступа к репозиторию $REPO_OWNER/$REPO_NAME..."
    
    local response
    local http_code
    
    response=$(curl -s -w "%{http_code}" --connect-timeout 10 \
                    -H "Authorization: token $token" \
                    "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME")
    
    if [ $? -ne 0 ]; then
        log "RED" "❌ Ошибка при проверке доступа к репозиторию"
        return 1
    fi
    
    http_code="${response: -3}"
    
    case "$http_code" in
        "200")
            log "GREEN" "✅ Доступ к репозиторию подтвержден"
            return 0
            ;;
        "404")
            log "RED" "❌ Репозиторий не найден или нет доступа"
            log "YELLOW" "⚠️ Убедитесь, что токен имеет права доступа к приватным репозиториям"
            return 1
            ;;
        "403")
            log "RED" "❌ Доступ к репозиторию запрещен"
            return 1
            ;;
        *)
            log "RED" "❌ Неожиданный ответ при проверке репозитория (HTTP $http_code)"
            return 1
            ;;
    esac
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
    
    # Выполняем клонирование с более подробным выводом
    if git clone --progress "$repo_url" "$temp_dir/$PROJECT_DIR" 2>&1; then
        log "GREEN" "✅ Репозиторий успешно клонирован"
        return 0
    else
        log "RED" "❌ Ошибка клонирования репозитория"
        log "YELLOW" "⚠️ Проверьте права доступа токена к репозиторию"
        return 1
    fi
}

# Функция для запроса и настройки GitHub токена
setup_github_token() {
    local token
    local attempts=0
    local max_attempts=3
    
    echo ""
    log "YELLOW" "⚠️ Для работы с приватным репозиторием необходим GitHub Personal Access Token"
    echo ""
    log "BLUE" "📋 Инструкция по получению токена:"
    echo "   1. Перейдите на https://github.com/settings/tokens"
    echo "   2. Нажмите 'Generate new token (classic)'"
    echo "   3. Выберите права доступа: repo, workflow"
    echo "   4. Скопируйте созданный токен"
    echo ""
    
    # Проверяем интерактивность
    if [ ! -t 0 ]; then
        log "RED" "❌ Скрипт запущен не в интерактивном режиме"
        log "YELLOW" "⚠️ Создайте файл .env вручную или запустите скрипт в интерактивном терминале"
        return 1
    fi
    
    while [ $attempts -lt $max_attempts ]; do
        log "BLUE" "🔄 Попытка $((attempts + 1)) из $max_attempts"
        
        if ! token=$(read_token); then
            ((attempts++))
            continue
        fi
        
        # Показываем первые и последние символы токена для подтверждения
        local token_preview="${token:0:8}...${token: -8}"
        log "BLUE" "🔍 Проверяем токен: $token_preview"
        
        if validate_github_token "$token" && check_repo_access "$token"; then
            log "GREEN" "✅ Токен принят и готов к использованию"
            echo "$token"
            return 0
        fi
        
        ((attempts++))
        if [ $attempts -lt $max_attempts ]; then
            echo ""
            log "YELLOW" "⚠️ Попробуйте еще раз ($attempts/$max_attempts)"
            echo ""
        fi
    done
    
    log "RED" "❌ Превышено количество попыток ввода токена"
    log "YELLOW" "⚠️ Убедитесь что:"
    echo "   - Токен скопирован полностью"
    echo "   - Токен имеет права доступа 'repo'"
    echo "   - Интернет-соединение стабильно"
    return 1
}

# Функция проверки интернет-соединения
check_internet() {
    log "BLUE" "🌐 Проверка интернет-соединения..."
    
    if ping -c 1 google.com &> /dev/null || ping -c 1 github.com &> /dev/null; then
        log "GREEN" "✅ Интернет-соединение активно"
        return 0
    else
        log "RED" "❌ Нет интернет-соединения"
        return 1
    fi
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

# Проверяем интернет-соединение
if ! check_internet; then
    log "RED" "❌ Для работы скрипта необходимо интернет-соединение"
    exit 1
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
    else
        log "GREEN" "✅ Файл .env найден"
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
                if git pull origin main; then
                    log "GREEN" "✅ Репозиторий обновлен"
                else
                    log "YELLOW" "⚠️ Не удалось обновить репозиторий, продолжаем с текущей версией"
                fi
            fi
        fi
    fi
    
    # Добавляем права на выполнение скрипта manage_parser.sh
    if [ -f "manage_parser.sh" ]; then
        chmod +x manage_parser.sh
        
        # Запускаем скрипт manage_parser.sh с именем экземпляра
        log "BLUE" "🚀 Запуск основного скрипта управления парсером для экземпляра $PROJECT_DIR..."
        ./manage_parser.sh "$INSTANCE_NAME"
    else
        log "RED" "❌ Файл manage_parser.sh не найден в $INSTALL_DIR"
        exit 1
    fi
    
else
    log "BLUE" "⬇️ Первоначальная установка парсера для экземпляра $PROJECT_DIR..."
    
    # Запрашиваем GitHub токен
    log "BLUE" "📋 Настройка GitHub токена для работы с приватным репозиторием..."
    if ! github_token=$(setup_github_token); then
        log "RED" "❌ Не удалось настроить GitHub токен"
        exit 1
    fi
    
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    log "BLUE" "📁 Создана временная директория: $TEMP_DIR"
    
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
    if [ -f "manage_parser.sh" ]; then
        chmod +x manage_parser.sh
        
        # Запускаем скрипт manage_parser.sh с именем экземпляра
        log "BLUE" "🚀 Запуск основного скрипта управления парсером..."
        ./manage_parser.sh "$INSTANCE_NAME"
    else
        log "RED" "❌ Файл manage_parser.sh не найден в клонированном репозитории"
        exit 1
    fi
    
    # Удаляем временную директорию
    rm -rf "$TEMP_DIR"
    log "BLUE" "🗑️ Временная директория удалена"
fi

log "GREEN" "✅ Установка/обновление парсера $PROJECT_DIR завершено"