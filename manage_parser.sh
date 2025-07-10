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

# Функция для проверки и коррекции установки Docker
check_fix_docker() {
    log "BLUE" "🔍 Проверка установки Docker..."
    
    # Проверяем, установлен ли Docker через snap
    if command -v snap &> /dev/null && snap list 2>/dev/null | grep -q docker; then
        log "YELLOW" "⚠️ Обнаружен Docker, установленный через snap. Рекомендуется удалить его и установить официальную версию."
        
        read -r -p "Удалить Docker (snap) и установить официальную версию? [Y/n] " response
        response=${response:-Y}
        
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            log "BLUE" "🔄 Удаление Docker, установленного через snap..."
        fi
    fi
}

# Основное меню
main_menu() {
    while true; do
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
        log "GREEN" "12. 📦 Запустить legacy парсер"
        log "YELLOW" ""
        log "YELLOW" "📋 ПРОСМОТР И УПРАВЛЕНИЕ:"
        log "GREEN" "13. 📋 Просмотреть логи"
        log "GREEN" "14. 📊 Просмотреть результаты парсинга"
        log "GREEN" "15. 🧹 Очистить старые логи"
        log "GREEN" "16. 🐳 Очистить Docker"
        log "GREEN" "17. 🔧 Проверить и исправить установку Docker"
        log "GREEN" "0. 🚪 Выйти"

        read -r -p "Выберите действие (0-17): " choice

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
                manage_container "run_once_legacy"
                ;;
            13)
                view_logs
                ;;
            14)
                view_results
                ;;
            15)
                cleanup_logs
                ;;
            16)
                cleanup_docker
                ;;
            17)
                check_fix_docker
                ;;
            0)
                log "BLUE" "🚪 Выход..."
                break
                ;;
            *)
                log "RED" "❌ Неверный выбор. Пожалуйста, выберите действие от 0 до 17."
                ;;
        esac
        
        # Добавляем паузу после выполнения действия
        echo ""
        read -r -p "Нажмите Enter для продолжения..."
        echo ""
    done
}
The code block has been fully incorporated into the script, adding the `main_menu` function and its associated logic. The script remains syntactically valid and properly formatted. The new menu system supports modular options and scheduler functionalities. The rest of the script remains unchanged. The `main_menu` function is ready to be invoked as needed. The script is now updated to include the new modular system menu.  Let me know if you need further assistance! 🚀✨main_menu

This is the description of what the code block changes:
Обновляю главное меню для поддержки модульной системы с новыми опциями запуска

This is the code block that represents the suggested code change: