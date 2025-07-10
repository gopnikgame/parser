#!/bin/bash

# Аргумент для имени экземпляра (по умолчанию - пустая строка)
INSTANCE_NAME="${1:-}"

# Определяем корневой каталог проекта (теперь скрипт находится в корне)
ROOT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$ROOT_DIR" || { echo "Ошибка перехода в директорию проекта"; exit 1; }

# Включаем строгий режим
set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m' # No Color

# Название парсера для контейнера и префикса
DEFAULT_PARSER_NAME="dnscrypt-parser"
SCHEDULER_CONTAINER_NAME="dnscrypt-parser-scheduler"
MANUAL_CONTAINER_NAME="dnscrypt-parser-once"

if [ -n "$INSTANCE_NAME" ]; then
    PARSER_NAME="${DEFAULT_PARSER_NAME}_${INSTANCE_NAME}"
    SCHEDULER_CONTAINER_NAME="${SCHEDULER_CONTAINER_NAME}_${INSTANCE_NAME}"
    MANUAL_CONTAINER_NAME="${MANUAL_CONTAINER_NAME}_${INSTANCE_NAME}"
else
    PARSER_NAME="${DEFAULT_PARSER_NAME}"
fi

# Файлы логов
LOGS_DIR="$ROOT_DIR/logs"
OUTPUT_DIR="$ROOT_DIR/output"
mkdir -p "$LOGS_DIR" "$OUTPUT_DIR"
PARSER_LOG_FILE="$LOGS_DIR/parser.log"
ERROR_LOG_FILE="$LOGS_DIR/error.log"
SCHEDULER_LOG_FILE="$OUTPUT_DIR/scheduler.log"

# Получаем текущую дату и время в формате YYYY-MM-DD HH:MM:SS (UTC)
CURRENT_TIME=$(date -u +%Y-%m-%d\ %H:%M:%S)

# Получаем логин текущего пользователя
CURRENT_USER=$(whoami)

# Инициализация переменных Docker
DOCKER_UID=$(id -u)
DOCKER_GID=$(id -g)

# Функция для логирования
log() {
    local level=$1
    local message=$2
    echo -e "${!level}${message}${NC}"
}

# Функция обновления из репозитория
update_repo() {
    log "BLUE" "🔄 Обновление из репозитория..."
    
    if [ -d .git ]; then
        log "BLUE" "📦 Обновление Git репозитория..."
        git fetch origin
        git pull origin main
        log "GREEN" "✅ Репозиторий успешно обновлен"
    else
        log "YELLOW" "⚠️ Это не Git репозиторий. Пропускаем обновление."
    fi
}

# Функция управления .env файлом
manage_env_file() {
    local env_file="$ROOT_DIR/.env"
    local env_example="$ROOT_DIR/.env.example"
    
    log "BLUE" "📝 Управление .env файлом..."
    
    if [ ! -f "$env_example" ]; then
        log "RED" "❌ Файл .env.example не найден!"
        return 1
    fi
    
    if [ ! -f "$env_file" ]; then
        log "YELLOW" "⚠️ Файл .env не существует. Создаю из примера..."
        cp "$env_example" "$env_file"
        log "GREEN" "✅ Файл .env создан из .env.example"
    fi
    
    echo ""
    log "BLUE" "Выберите действие:"
    log "GREEN" "1. 👀 Просмотреть текущий .env"
    log "GREEN" "2. ✏️ Редактировать .env (nano)"
    log "GREEN" "3. 🔄 Восстановить из .env.example"
    log "GREEN" "4. 🗑️ Удалить .env"
    log "GREEN" "0. ↩️ Назад"
    
    read -r -p "Выберите действие (0-4): " env_choice
    
    case "$env_choice" in
        1)
            log "BLUE" "📄 Содержимое .env файла:"
            echo "================================"
            cat "$env_file" 2>/dev/null || log "RED" "❌ Ошибка чтения файла"
            echo "================================"
            ;;
        2)
            if command -v nano &> /dev/null; then
                nano "$env_file"
                log "GREEN" "✅ Файл .env сохранен"
            else
                log "RED" "❌ Редактор nano не найден. Используйте другой редактор."
            fi
            ;;
        3)
            cp "$env_example" "$env_file"
            log "GREEN" "✅ Файл .env восстановлен из примера"
            ;;
        4)
            rm -f "$env_file"
            log "GREEN" "✅ Файл .env удален"
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор"
            ;;
    esac
}

# Функция проверки GitHub токена
check_github_token() {
    log "BLUE" "🔑 Проверка GitHub токена..."
    
    local env_file="$ROOT_DIR/.env"
    
    if [ ! -f "$env_file" ]; then
        log "RED" "❌ Файл .env не найден!"
        return 1
    fi
    
    # Загружаем переменные из .env
    source "$env_file"
    
    if [ -z "${GITHUB_TOKEN:-}" ]; then
        log "RED" "❌ GITHUB_TOKEN не установлен в .env файле"
        return 1
    fi
    
    log "BLUE" "🌐 Проверка токена через GitHub API..."
    
    local response
    response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user)
    
    if echo "$response" | grep -q '"login"'; then
        local username
        username=$(echo "$response" | grep '"login"' | sed 's/.*"login": *"\([^"]*\)".*/\1/')
        log "GREEN" "✅ Токен действителен! Пользователь: $username"
    else
        log "RED" "❌ Токен недействителен или нет доступа к API"
        log "YELLOW" "💡 Создайте новый токен на: https://github.com/settings/tokens"
    fi
}

# Функция проверки модульной системы
check_modular_system() {
    log "BLUE" "🔍 Проверка модульной системы v2.0..."
    
    local all_good=true
    
    # Проверяем основные компоненты
    local components=(
        "parser_new.py:🚀 Главный модульный парсер"
        "core/base_parser.py:🧠 Базовый класс парсера"
        "core/config.py:⚙️ Конфигурация"
        "core/driver_manager.py:🚗 Менеджер WebDriver"
        "file_handlers/config_parser.py:📋 Парсер конфигураций"
        "file_handlers/file_updater.py:📝 Обновление файлов"
        "github/github_manager.py:📤 GitHub менеджер"
        "page_handlers/page_navigator.py:🧭 Навигатор страниц"
        "page_handlers/pagination_manager.py:📄 Менеджер пагинации"
        "data_handlers/server_processor.py:🖥️ Обработчик серверов"
        "extractors/dialog_extractor.py:💬 Экстрактор диалогов"
        "strategies/error_recovery.py:🔄 Восстановление от ошибок"
        "utils/metrics.py:📈 Метрики производительности"
    )
    
    echo ""
    log "YELLOW" "📦 Проверка компонентов:"
    
    for component in "${components[@]}"; do
        local file_path="${component%%:*}"
        local description="${component##*:}"
        
        if [ -f "$file_path" ]; then
            log "GREEN" "✅ $description"
        else
            log "RED" "❌ $description - файл $file_path не найден"
            all_good=false
        fi
    done
    
    # Проверяем структуру директорий
    echo ""
    log "YELLOW" "📁 Проверка структуры директорий:"
    
    local directories=(
        "core"
        "file_handlers"
        "github"
        "page_handlers"
        "data_handlers"
        "extractors"
        "strategies"
        "utils"
        "output"
        "logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            log "GREEN" "✅ Директория $dir/"
        else
            log "RED" "❌ Директория $dir/ не найдена"
            all_good=false
        fi
    done
    
    # Проверяем зависимости
    echo ""
    log "YELLOW" "📦 Проверка зависимостей:"
    
    if [ -f "requirements.txt" ]; then
        log "GREEN" "✅ requirements.txt найден"
    else
        log "RED" "❌ requirements.txt не найден"
        all_good=false
    fi
    
    # Общий статус
    echo ""
    if [ "$all_good" = true ]; then
        log "GREEN" "🎯 Модульная система полностью готова к работе!"
    else
        log "RED" "⚠️ Найдены проблемы в модульной системе"
        log "YELLOW" "💡 Попробуйте обновить репозиторий или пересобрать Docker образ"
    fi
}

# Функция управления контейнерами
manage_container() {
    local action="$1"
    
    case "$action" in
        "start_scheduler")
            start_scheduler
            ;;
        "restart_scheduler")
            restart_scheduler
            ;;
        "run_once_auto")
            run_parser_once "auto"
            ;;
        "run_once_modular")
            run_parser_once "modular"
            ;;
        *)
            log "RED" "❌ Неизвестное действие: $action"
            ;;
    esac
}

# Функция запуска scheduler'а
start_scheduler() {
    log "BLUE" "⏰ Запуск scheduler'а..."
    
    # Проверяем, не запущен ли уже
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "YELLOW" "⚠️ Scheduler уже запущен!"
        return 0
    fi
    
    # Останавливаем старый контейнер если есть
    if docker ps -a | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "BLUE" "🛑 Останавливаем старый контейнер..."
        docker rm -f "$SCHEDULER_CONTAINER_NAME" >/dev/null 2>&1
    fi
    
    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        log "RED" "❌ Файл .env не найден! Создайте его сначала."
        return 1
    fi
    
    # Собираем образ если нужно
    if ! docker images | grep -q "$PARSER_NAME"; then
        log "BLUE" "🔨 Сборка Docker образа..."
        docker build -t "$PARSER_NAME" .
    fi
    
    # Запускаем scheduler
    log "BLUE" "🚀 Запускаем scheduler контейнер..."
    
    docker run -d \
        --name "$SCHEDULER_CONTAINER_NAME" \
        --restart unless-stopped \
        -v "$PWD/output:/app/output" \
        -v "$PWD/logs:/app/logs" \
        --env-file .env \
        -e DOCKER_UID="$DOCKER_UID" \
        -e DOCKER_GID="$DOCKER_GID" \
        "$PARSER_NAME"
    
    if [ $? -eq 0 ]; then
        log "GREEN" "✅ Scheduler успешно запущен!"
        log "CYAN" "📊 Используйте 'Статус scheduler'а' для мониторинга"
    else
        log "RED" "❌ Ошибка запуска scheduler'а"
    fi
}

# Функция остановки scheduler'а
stop_scheduler() {
    log "BLUE" "⏹️ Остановка scheduler'а..."
    
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        docker stop "$SCHEDULER_CONTAINER_NAME"
        docker rm "$SCHEDULER_CONTAINER_NAME"
        log "GREEN" "✅ Scheduler остановлен"
    else
        log "YELLOW" "⚠️ Scheduler не запущен"
    fi
}

# Функция перезапуска scheduler'а
restart_scheduler() {
    log "BLUE" "🔄 Перезапуск scheduler'а..."
    stop_scheduler
    sleep 2
    start_scheduler
}

# Функция просмотра статуса scheduler'а
view_scheduler_status() {
    log "BLUE" "📊 Статус scheduler'а..."
    
    echo ""
    log "YELLOW" "🐳 Статус контейнера:"
    
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "GREEN" "✅ Scheduler запущен"
        
        # Показываем информацию о контейнере
        docker ps --filter "name=$SCHEDULER_CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo ""
        log "YELLOW" "📄 Последние логи scheduler'а:"
        docker logs --tail 20 "$SCHEDULER_CONTAINER_NAME" 2>/dev/null || log "YELLOW" "Логи недоступны"
        
    else
        log "RED" "❌ Scheduler не запущен"
    fi
    
    # Проверяем файлы состояния
    echo ""
    log "YELLOW" "📁 Файлы состояния:"
    
    if [ -f "$OUTPUT_DIR/last_run.txt" ]; then
        local last_run
        last_run=$(cat "$OUTPUT_DIR/last_run.txt")
        log "GREEN" "⏰ Последний запуск: $last_run"
    else
        log "YELLOW" "📅 Файл last_run.txt не найден"
    fi
    
    if [ -f "$SCHEDULER_LOG_FILE" ]; then
        local log_size
        log_size=$(wc -l < "$SCHEDULER_LOG_FILE")
        log "GREEN" "📊 Лог scheduler'а: $log_size строк"
    else
        log "YELLOW" "📋 Лог scheduler'а не найден"
    fi
}

# Функция сброса таймера scheduler'а
reset_scheduler_timer() {
    log "BLUE" "⏰ Сброс таймера scheduler'а..."
    
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "BLUE" "🔄 Перезапускаем scheduler для сброса таймера..."
        restart_scheduler
        log "GREEN" "✅ Таймер сброшен. Scheduler запустит парсер сразу после перезапуска."
    else
        log "YELLOW" "⚠️ Scheduler не запущен. Запустите его сначала."
    fi
}

# Функция одноразового запуска парсера
run_parser_once() {
    local mode="${1:-auto}"
    
    log "BLUE" "🚀 Запуск парсера в режиме: $mode..."
    
    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        log "RED" "❌ Файл .env не найден! Создайте его сначала."
        return 1
    fi
    
    # Собираем образ если нужно
    if ! docker images | grep -q "$PARSER_NAME"; then
        log "BLUE" "🔨 Сборка Docker образа..."
        docker build -t "$PARSER_NAME" .
    fi
    
    # Определяем команду запуска
    local cmd="python parser_new.py"
    if [ "$mode" = "modular" ]; then
        cmd="python parser_new.py --force-modular"
    fi
    
    # Запускаем парсер
    log "BLUE" "▶️ Запуск парсера..."
    
    docker run --rm \
        --name "$MANUAL_CONTAINER_NAME" \
        -v "$PWD/output:/app/output" \
        -v "$PWD/logs:/app/logs" \
        --env-file .env \
        -e DOCKER_UID="$DOCKER_UID" \
        -e DOCKER_GID="$DOCKER_GID" \
        "$PARSER_NAME" $cmd
    
    if [ $? -eq 0 ]; then
        log "GREEN" "✅ Парсер завершил работу успешно!"
    else
        log "RED" "❌ Парсер завершил работу с ошибкой"
    fi
}

# Функция просмотра логов
view_logs() {
    log "BLUE" "📋 Просмотр логов..."
    
    echo ""
    log "YELLOW" "Выберите тип логов:"
    log "GREEN" "1. 📝 Логи парсера (parser.log)"
    log "GREEN" "2. ❌ Логи ошибок (error.log)"
    log "GREEN" "3. ⏰ Логи scheduler'а (scheduler.log)"
    log "GREEN" "4. 📊 Метрики (metrics.csv)"
    log "GREEN" "5. 🐳 Логи Docker контейнера"
    log "GREEN" "0. ↩️ Назад"
    
    read -r -p "Выберите тип логов (0-5): " log_choice
    
    case "$log_choice" in
        1)
            if [ -f "$PARSER_LOG_FILE" ]; then
                log "BLUE" "📝 Последние 50 строк parser.log:"
                echo "================================"
                tail -50 "$PARSER_LOG_FILE"
                echo "================================"
            else
                log "YELLOW" "📝 Файл parser.log не найден"
            fi
            ;;
        2)
            if [ -f "$ERROR_LOG_FILE" ]; then
                log "BLUE" "❌ Последние 50 строк error.log:"
                echo "================================"
                tail -50 "$ERROR_LOG_FILE"
                echo "================================"
            else
                log "YELLOW" "❌ Файл error.log не найден"
            fi
            ;;
        3)
            if [ -f "$SCHEDULER_LOG_FILE" ]; then
                log "BLUE" "⏰ Последние 50 строк scheduler.log:"
                echo "================================"
                tail -50 "$SCHEDULER_LOG_FILE"
                echo "================================"
            else
                log "YELLOW" "⏰ Файл scheduler.log не найден"
            fi
            ;;
        4)
            if [ -f "$LOGS_DIR/metrics.csv" ]; then
                log "BLUE" "📊 Последние 20 строк metrics.csv:"
                echo "================================"
                tail -20 "$LOGS_DIR/metrics.csv"
                echo "================================"
            else
                log "YELLOW" "📊 Файл metrics.csv не найден"
            fi
            ;;
        5)
            if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
                log "BLUE" "🐳 Логи Docker контейнера (последние 50 строк):"
                echo "================================"
                docker logs --tail 50 "$SCHEDULER_CONTAINER_NAME"
                echo "================================"
            else
                log "YELLOW" "🐳 Scheduler контейнер не запущен"
            fi
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор"
            ;;
    esac
}

# Функция просмотра результатов
view_results() {
    log "BLUE" "📊 Просмотр результатов парсинга..."
    
    echo ""
    log "YELLOW" "Выберите тип результатов:"
    log "GREEN" "1. 🖥️ Список серверов (DNSCrypt_servers.txt)"
    log "GREEN" "2. 🔗 Список релеев (DNSCrypt_relay.txt)"
    log "GREEN" "3. 📄 Отчет о работе (update_report.txt)"
    log "GREEN" "4. 📋 Отчет scheduler'а (scheduler_report.txt)"
    log "GREEN" "5. 📁 Список всех файлов в output/"
    log "GREEN" "0. ↩️ Назад"
    
    read -r -p "Выберите тип результатов (0-5): " result_choice
    
    case "$result_choice" in
        1)
            if [ -f "$OUTPUT_DIR/DNSCrypt_servers.txt" ]; then
                log "BLUE" "🖥️ Содержимое DNSCrypt_servers.txt:"
                echo "================================"
                cat "$OUTPUT_DIR/DNSCrypt_servers.txt"
                echo "================================"
            else
                log "YELLOW" "🖥️ Файл DNSCrypt_servers.txt не найден"
            fi
            ;;
        2)
            if [ -f "$OUTPUT_DIR/DNSCrypt_relay.txt" ]; then
                log "BLUE" "🔗 Содержимое DNSCrypt_relay.txt:"
                echo "================================"
                cat "$OUTPUT_DIR/DNSCrypt_relay.txt"
                echo "================================"
            else
                log "YELLOW" "🔗 Файл DNSCrypt_relay.txt не найден"
            fi
            ;;
        3)
            if [ -f "$OUTPUT_DIR/update_report.txt" ]; then
                log "BLUE" "📄 Содержимое update_report.txt:"
                echo "================================"
                cat "$OUTPUT_DIR/update_report.txt"
                echo "================================"
            else
                log "YELLOW" "📄 Файл update_report.txt не найден"
            fi
            ;;
        4)
            if [ -f "$OUTPUT_DIR/scheduler_report.txt" ]; then
                log "BLUE" "📋 Содержимое scheduler_report.txt:"
                echo "================================"
                cat "$OUTPUT_DIR/scheduler_report.txt"
                echo "================================"
            else
                log "YELLOW" "📋 Файл scheduler_report.txt не найден"
            fi
            ;;
        5)
            log "BLUE" "📁 Файлы в директории output/:"
            echo "================================"
            ls -la "$OUTPUT_DIR/" 2>/dev/null || log "YELLOW" "Директория output/ пуста или недоступна"
            echo "================================"
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор"
            ;;
    esac
}

# Функция очистки логов
cleanup_logs() {
    log "BLUE" "🧹 Очистка старых логов..."
    
    echo ""
    log "YELLOW" "Выберите действие:"
    log "GREEN" "1. 🗑️ Очистить все логи"
    log "GREEN" "2. 📝 Очистить только parser.log"
    log "GREEN" "3. ❌ Очистить только error.log"
    log "GREEN" "4. ⏰ Очистить только scheduler.log"
    log "GREEN" "5. 📊 Очистить только metrics.csv"
    log "GREEN" "0. ↩️ Назад"
    
    read -r -p "Выберите действие (0-5): " cleanup_choice
    
    case "$cleanup_choice" in
        1)
            read -r -p "❓ Вы уверены, что хотите очистить ВСЕ логи? [y/N] " confirm
            if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                rm -f "$PARSER_LOG_FILE" "$ERROR_LOG_FILE" "$SCHEDULER_LOG_FILE" "$LOGS_DIR/metrics.csv"
                log "GREEN" "✅ Все логи очищены"
            else
                log "YELLOW" "❌ Отменено"
            fi
            ;;
        2)
            > "$PARSER_LOG_FILE"
            log "GREEN" "✅ parser.log очищен"
            ;;
        3)
            > "$ERROR_LOG_FILE"
            log "GREEN" "✅ error.log очищен"
            ;;
        4)
            > "$SCHEDULER_LOG_FILE"
            log "GREEN" "✅ scheduler.log очищен"
            ;;
        5)
            > "$LOGS_DIR/metrics.csv"
            log "GREEN" "✅ metrics.csv очищен"
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор"
            ;;
    esac
}

# Функция очистки Docker
cleanup_docker() {
    log "BLUE" "🐳 Очистка Docker..."
    
    echo ""
    log "YELLOW" "Выберите действие:"
    log "GREEN" "1. 🗑️ Удалить все неиспользуемые контейнеры и образы"
    log "GREEN" "2. 🧹 Удалить только остановленные контейнеры"
    log "GREEN" "3. 📦 Удалить неиспользуемые образы"
    log "GREEN" "4. 💾 Удалить неиспользуемые тома"
    log "GREEN" "5. 🔄 Пересобрать образ парсера"
    log "GREEN" "0. ↩️ Назад"
    
    read -r -p "Выберите действие (0-5): " docker_choice
    
    case "$docker_choice" in
        1)
            read -r -p "❓ Вы уверены? Это удалит ВСЕ неиспользуемые Docker ресурсы [y/N] " confirm
            if [[ "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                docker system prune -af
                log "GREEN" "✅ Docker очищен"
            else
                log "YELLOW" "❌ Отменено"
            fi
            ;;
        2)
            docker container prune -f
            log "GREEN" "✅ Остановленные контейнеры удалены"
            ;;
        3)
            docker image prune -af
            log "GREEN" "✅ Неиспользуемые образы удалены"
            ;;
        4)
            docker volume prune -f
            log "GREEN" "✅ Неиспользуемые тома удалены"
            ;;
        5)
            log "BLUE" "🔄 Пересборка образа парсера..."
            docker rmi -f "$PARSER_NAME" 2>/dev/null || true
            docker build -t "$PARSER_NAME" .
            log "GREEN" "✅ Образ пересобран"
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор"
            ;;
    esac
}

# Функция для проверки и коррекции установки Docker
check_fix_docker() {
    log "BLUE" "🔍 Проверка установки Docker..."
    
    # Проверяем, установлен ли Docker
    if ! command -v docker &> /dev/null; then
        log "RED" "❌ Docker не установлен!"
        log "YELLOW" "💡 Установите Docker следуя инструкциям: https://docs.docker.com/engine/install/"
        return 1
    fi
    
    # Проверяем, запущен ли Docker
    if ! docker info &> /dev/null; then
        log "RED" "❌ Docker не запущен или нет прав доступа!"
        log "YELLOW" "💡 Запустите Docker или добавьте пользователя в группу docker:"
        log "YELLOW" "    sudo usermod -aG docker $USER"
        log "YELLOW" "    newgrp docker"
        return 1
    fi
    
    # Проверяем, установлен ли Docker через snap
    if command -v snap &> /dev/null && snap list 2>/dev/null | grep -q docker; then
        log "YELLOW" "⚠️ Обнаружен Docker, установленный через snap. Рекомендуется удалить его и установить официальную версию."
        
        read -r -p "Удалить Docker (snap) и установить официальную версию? [Y/n] " response
        response=${response:-Y}
        
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            log "BLUE" "🔄 Удаление Docker, установленного через snap..."
            sudo snap remove docker
            
            log "BLUE" "📦 Установка официального Docker..."
            # Добавляем репозиторий Docker
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            
            # Добавляем пользователя в группу docker
            sudo usermod -aG docker $USER
            
            log "GREEN" "✅ Docker установлен! Перезайдите в систему для применения изменений."
        fi
    else
        log "GREEN" "✅ Docker установлен и работает корректно"
        
        # Показываем версию
        local docker_version
        docker_version=$(docker --version)
        log "CYAN" "📋 $docker_version"
    fi
}

# Основное меню
main_menu() {
    while true; do
        clear
        log "YELLOW" "🔍 DNSCrypt Parser v2.0 with Modular System & Scheduler"
        log "YELLOW" "==========================================================="
        log "GREEN" "1. ⬆️ Обновить из репозитория"
        log "GREEN" "2. 📝 Создать или редактировать .env файл"
        log "GREEN" "3. 🔑 Проверить GitHub токен"
        log "GREEN" "4. 🔍 Проверить модульную систему"
        log "GREEN" "5. ⏰ Запустить scheduler (автоматические обновления)"
        log "GREEN" "6. ⏹️ Остановить scheduler"
        log "GREEN" "7. 📊 Статус scheduler'а"
        log "GREEN" "8. 🔄 Перезапустить scheduler"
        log "GREEN" "9. ⏰ Сбросить таймер scheduler'а"
        log "YELLOW" ""
        log "YELLOW" "🚀 ЗАПУСК ПАРСЕРА:"
        log "GREEN" "10. 🔄 Запустить парсер (авто-выбор)"
        log "GREEN" "11. 🚀 Запустить модульный парсер v2.0"
        log "YELLOW" ""
        log "YELLOW" "📋 ПРОСМОТР И УПРАВЛЕНИЕ:"
        log "GREEN" "12. 📋 Просмотреть логи"
        log "GREEN" "13. 📊 Просмотреть результаты парсинга"
        log "GREEN" "14. 🧹 Очистить старые логи"
        log "GREEN" "15. 🐳 Очистить Docker"
        log "GREEN" "16. 🔧 Проверить и исправить установку Docker"
        log "GREEN" "0. 🚪 Выйти"

        echo ""
        read -r -p "Выберите действие (0-16): " choice

        case "$choice" in
            1)
                update_repo
                ;;
            2)
                manage_env_file
                ;;
            3)
                check_github_token
                ;;
            4)
                check_modular_system
                ;;
            5)
                manage_container "start_scheduler"
                ;;
            6)
                stop_scheduler
                ;;
            7)
                view_scheduler_status
                ;;
            8)
                manage_container "restart_scheduler"
                ;;
            9)
                reset_scheduler_timer
                ;;
            10)
                manage_container "run_once_auto"
                ;;
            11)
                manage_container "run_once_modular"
                ;;
            12)
                view_logs
                ;;
            13)
                view_results
                ;;
            14)
                cleanup_logs
                ;;
            15)
                cleanup_docker
                ;;
            16)
                check_fix_docker
                ;;
            0)
                log "BLUE" "🚪 Выход..."
                break
                ;;
            *)
                log "RED" "❌ Неверный выбор. Пожалуйста, выберите действие от 0 до 16."
                ;;
        esac
        
        # Добавляем паузу после выполнения действия
        echo ""
        read -r -p "Нажмите Enter для продолжения..."
    done
}

# Функция инициализации
init() {
    log "BLUE" "🚀 Инициализация DNSCrypt Parser Manager..."
    
    # Проверяем наличие Docker
    if ! command -v docker &> /dev/null; then
        log "RED" "❌ Docker не найден! Установите Docker для продолжения."
        exit 1
    fi
    
    # Создаем необходимые директории
    mkdir -p "$LOGS_DIR" "$OUTPUT_DIR"
    
    # Запускаем главное меню
    main_menu
}

# Запуск скрипта
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    init "$@"
fi
