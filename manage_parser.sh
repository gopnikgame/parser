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
            
            # Останавливаем все контейнеры перед удалением Docker
            log "YELLOW" "⚠️ Останавливаем все запущенные контейнеры..."
            docker ps -q | xargs -r docker stop || true
            
            # Удаляем Docker через snap
            sudo snap remove docker || {
                log "RED" "❌ Не удалось удалить Docker через snap"
                return 1
            }
            
            log "GREEN" "✅ Docker (snap) удален"
            
            # Установка официальной версии Docker
            log "BLUE" "⬇️ Установка официальной версии Docker..."
            
            # Обновляем информацию о пакетах
            sudo apt-get update
            
            # Устанавливаем необходимые пакеты для добавления репозитория
            sudo apt-get install -y ca-certificates curl gnupg || {
                log "RED" "❌ Ошибка при установке необходимых пакетов"
                return 1
            }
            
            # Создаем директорию для ключей
            sudo install -m 0755 -d /etc/apt/keyrings
            
            # Скачиваем официальный ключ Docker и добавляем его в keyring
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            
            # Добавляем репозиторий Docker
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
                sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Обновляем информацию о пакетах после добавления репозитория
            sudo apt-get update
            
            # Устанавливаем Docker Engine, containerd и Docker Compose
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose || {
                log "RED" "❌ Ошибка при установке Docker"
                return 1
            }
            
            # Добавляем текущего пользователя в группу docker
            sudo usermod -aG docker "$CURRENT_USER"
            
            log "GREEN" "✅ Docker успешно установлен"
            log "YELLOW" "⚠️ Для применения изменений в группах пользователей может потребоваться перезайти в систему"
            
            # Проверяем установку
            if command -v docker &> /dev/null; then
                docker --version
                docker-compose --version
                log "GREEN" "✅ Docker и Docker Compose установлены и готовы к использованию"
            else
                log "RED" "❌ Возникла проблема с установкой Docker"
                return 1
            fi
            
            # Спрашиваем пользователя, хочет ли он перезайти в систему
            read -r -p "Изменения в группах требуют перезахода в систему. Выйти сейчас? [y/N] " response
            response=${response:-N}
            
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                log "YELLOW" "⚠️ Выход из системы. После повторного входа запустите скрипт снова."
                exit 0
            fi
        else
            log "YELLOW" "⚠️ Продолжение работы с Docker, установленным через snap. Возможны ограничения."
        fi
    else
        # Проверяем наличие Docker
        if ! command -v docker &> /dev/null; then
            log "YELLOW" "⚠️ Docker не установлен. Необходимо установить Docker для работы парсера."
            
            read -r -p "Установить официальную версию Docker? [Y/n] " response
            response=${response:-Y}
            
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                log "BLUE" "⬇️ Установка официальной версии Docker..."
                
                # Обновляем информацию о пакетах
                sudo apt-get update
                
                # Устанавливаем необходимые пакеты для добавления репозитория
                sudo apt-get install -y ca-certificates curl gnupg || {
                    log "RED" "❌ Ошибка при установке необходимых пакетов"
                    return 1
                }
                
                # Создаем директорию для ключей
                sudo install -m 0755 -d /etc/apt/keyrings
                
                # Скачиваем официальный ключ Docker и добавляем его в keyring
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                sudo chmod a+r /etc/apt/keyrings/docker.gpg
                
                # Определяем дистрибутив для репозитория
                DIST=$(lsb_release -cs)
                
                # Добавляем репозиторий Docker
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $DIST stable" | \
                    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                
                # Обновляем информацию о пакетах после добавления репозитория
                sudo apt-get update
                
                # Устанавливаем Docker Engine, containerd и Docker Compose
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose || {
                    log "RED" "❌ Ошибка при установке Docker"
                    return 1
                }
                
                # Добавляем текущего пользователя в группу docker
                sudo usermod -aG docker "$CURRENT_USER"
                
                log "GREEN" "✅ Docker успешно установлен"
                log "YELLOW" "⚠️ Для применения изменений в группах пользователей может потребоваться перезайти в систему"
                
                # Проверяем установку
                if command -v docker &> /dev/null; then
                    docker --version
                    docker-compose --version
                    log "GREEN" "✅ Docker и Docker Compose установлены и готовы к использованию"
                else
                    log "RED" "❌ Возникла проблема с установкой Docker"
                    return 1
                fi
                
                # Спрашиваем пользователя, хочет ли он перезайти в систему
                read -r -p "Изменения в группах требуют перезахода в систему. Выйти сейчас? [y/N] " response
                response=${response:-N}
                
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                    log "YELLOW" "⚠️ Выход из системы. После повторного входа запустите скрипт снова."
                    exit 0
                fi
            else
                log "RED" "❌ Docker требуется для работы парсера. Установка отменена."
                return 1
            fi
        else
            log "GREEN" "✅ Обнаружена стандартная установка Docker"
            docker --version
            
            # Проверяем Docker Compose
            if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
                log "YELLOW" "⚠️ Docker Compose не установлен"
                
                read -r -p "Установить Docker Compose? [Y/n] " response
                response=${response:-Y}
                
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                    log "BLUE" "⬇️ Установка Docker Compose..."
                    sudo apt-get update
                    sudo apt-get install -y docker-compose || {
                        log "RED" "❌ Ошибка при установке Docker Compose"
                        return 1
                    }
                    log "GREEN" "✅ Docker Compose успешно установлен"
                    docker-compose --version
                fi
            else
                log "GREEN" "✅ Docker Compose установлен"
                if command -v docker-compose &> /dev/null; then
                    docker-compose --version
                else
                    docker compose version
                fi
            fi
        fi
    fi
    
    return 0
}

# Функция для запуска docker-compose
docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose "$@"
    else
        log "RED" "❌ Не найден docker-compose или docker compose"
        return 1
    fi
}

# Функция для управления .env файлом
manage_env_file() {
    local env_file="$ROOT_DIR/.env"
    local env_example="$ROOT_DIR/.env.example"
    local created=false

    log "BLUE" "📝 Управление конфигурацией .env..."

    # Выводим текущую директорию
    log "BLUE" "📍 Корневая директория проекта: $ROOT_DIR"

    # Проверяем существование файлов
    if [ ! -f "$env_file" ]; then
        if [ -f "$env_example" ]; then
            cp "$env_example" "$env_file"
            created=true
            log "GREEN" "✅ Создан новый .env файл из примера"
        else
            log "YELLOW" "⚠️ Файл .env.example не найден, создаем базовый .env"
            cat > "$env_file" << EOL
# GitHub настройки
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=gopnikgame
GITHUB_REPO=Installer_dnscypt
GITHUB_BRANCH=main

# Настройки Chrome (опционально)
CHROME_HEADLESS=true
CHROME_NO_SANDBOX=true

# Настройки Scheduler (опционально)
SCHEDULER_INTERVAL_DAYS=7
SCHEDULER_DEBUG=false
EOL
            created=true
            log "YELLOW" "⚠️ Создан базовый .env файл. Пожалуйста, обновите GitHub токен!"
        fi
    fi

    # Предлагаем отредактировать файл
    read -r -p "Редактировать .env файл сейчас? [Y/n] " response
    response=${response:-Y}
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        # Добавляем логирование
        if command -v nano &> /dev/null; then
            log "BLUE" "🚀 Запускаем nano..."
            nano "$env_file"
            editor_result=$?
        else
            log "BLUE" "🚀 Запускаем vi..."
            vi "$env_file"
            editor_result=$?
        fi

        # Проверяем код возврата редактора
        if [ "$editor_result" -ne 0 ]; then
            log "RED" "❌ Редактор вернул код ошибки: $editor_result"
            log "YELLOW" "⚠️ Файл .env необходимо настроить для работы парсера."
            return 1
        fi
    else
        log "YELLOW" "⚠️ Файл .env необходимо настроить для работы парсера."
        return 1
    fi

    log "GREEN" "✅ Конфигурация .env завершена"
    return 0
}

# Функция для обновления репозитория
update_repo() {
    log "BLUE" "🔄 Обновление репозитория..."

    # Инициализация переменной STASHED
    STASHED="false"

    # Stash local changes to .env
    if ! git diff --quiet HEAD -- .env 2>/dev/null; then
        log "BLUE" "Сохранение локальных изменений в .env"
        git stash push -m "Автоматическое сохранение .env перед обновлением" -- .env
        STASHED="true"
    else
        log "BLUE" "Нет изменений в .env для сохранения"
    fi

    git fetch
    git reset --hard origin/main
    log "GREEN" "✅ Репозиторий обновлен"

    # Restore stashed changes to .env
    if [[ "$STASHED" == "true" ]]; then
        log "BLUE" "Восстановление локальных изменений .env"
        git stash pop
        if [ $? -ne 0 ]; then
            log "YELLOW" "⚠️ Возникли конфликты при восстановлении .env. Проверьте файл вручную."
        fi
    fi
}

# Функция для запуска scheduler'а
start_scheduler() {
    log "BLUE" "⏰ Запуск scheduler'а DNSCrypt..."
    
    # Проверяем и исправляем установку Docker
    check_fix_docker || {
        log "RED" "❌ Необходимо исправить установку Docker для продолжения."
        return 1
    }
    
    # Загружаем переменные окружения из файла .env
    if [ -f ".env" ]; then
        log "BLUE" "🔑 Загружаем переменные окружения из .env"
        export $(grep -v '^#' .env | xargs)
    else
        log "RED" "❌ Файл .env не найден. Создайте его и настройте переменные окружения."
        return 1
    fi

    # Останавливаем существующий scheduler, если он запущен
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "YELLOW" "⚠️ Останавливаем существующий scheduler..."
        docker_compose_cmd down
    fi

    # Экспортируем переменные для docker-compose
    export DOCKER_UID DOCKER_GID
    export CREATED_BY="$CURRENT_USER"
    export CREATED_AT="$CURRENT_TIME"

    # Запускаем scheduler в фоне
    log "BLUE" "🚀 Запуск scheduler'а в фоновом режиме..."
    docker_compose_cmd up -d

    # Ждем немного и проверяем статус
    sleep 3
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "GREEN" "✅ Scheduler запущен успешно"
        log "BLUE" "📊 Для просмотра логов используйте: docker logs -f $SCHEDULER_CONTAINER_NAME"
        log "BLUE" "📁 Логи scheduler'а: $SCHEDULER_LOG_FILE"
    else
        log "RED" "❌ Ошибка запуска scheduler'а"
        log "BLUE" "📋 Проверьте логи: docker logs $SCHEDULER_CONTAINER_NAME"
        return 1
    fi
}

# Функция для остановки scheduler'а
stop_scheduler() {
    log "BLUE" "⏹️ Остановка scheduler'а DNSCrypt..."
    
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        docker_compose_cmd down
        log "GREEN" "✅ Scheduler остановлен"
    else
        log "YELLOW" "⚠️ Scheduler не запущен"
    fi
}

# Функция для просмотра статуса scheduler'а
view_scheduler_status() {
    log "BLUE" "📊 Статус scheduler'а DNSCrypt..."
    
    # Проверяем статус контейнера
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "GREEN" "✅ Scheduler запущен"
        
        # Показываем информацию о контейнере
        docker ps --filter "name=$SCHEDULER_CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Показываем информацию из файлов scheduler'а
        echo ""
        log "BLUE" "📄 Информация из файлов scheduler'а:"
        
        # Время последнего запуска
        if [ -f "$OUTPUT_DIR/last_run.txt" ]; then
            last_run=$(cat "$OUTPUT_DIR/last_run.txt" 2>/dev/null || echo "Неизвестно")
            log "GREEN" "🕐 Время последнего запуска: $last_run"
        else
            log "YELLOW" "⚠️ Файл времени последнего запуска не найден"
        fi
        
        # Отчет scheduler'а
        if [ -f "$OUTPUT_DIR/scheduler_report.txt" ]; then
            log "GREEN" "📊 Найден отчет scheduler'а:"
            cat "$OUTPUT_DIR/scheduler_report.txt"
        else
            log "YELLOW" "⚠️ Отчет scheduler'а не найден"
        fi
        
        # Предлагаем показать логи
        echo ""
        read -r -p "Показать последние логи scheduler'а? [Y/n] " response
        response=${response:-Y}
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            if [ -f "$SCHEDULER_LOG_FILE" ]; then
                log "BLUE" "📋 Последние 20 строк логов scheduler'а:"
                tail -20 "$SCHEDULER_LOG_FILE"
            else
                log "YELLOW" "⚠️ Файл логов scheduler'а не найден"
            fi
        fi
        
    elif docker ps -a | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "YELLOW" "⚠️ Scheduler остановлен"
        docker ps -a --filter "name=$SCHEDULER_CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}"
        
        log "BLUE" "📋 Последние логи остановленного scheduler'а:"
        docker logs --tail 10 "$SCHEDULER_CONTAINER_NAME" 2>/dev/null || log "RED" "❌ Не удалось получить логи"
    else
        log "RED" "❌ Scheduler не найден"
    fi
}

# Функция для управления контейнером
manage_container() {
    local action=$1

    log "BLUE" "🐳 Управление контейнером парсера..."
    
    # Проверяем и исправляем установку Docker
    check_fix_docker || {
        log "RED" "❌ Необходимо исправить установку Docker для продолжения."
        return 1
    }
    
    # Выводим текущую директорию для отладки
    log "BLUE" "📍 Текущая директория: $(pwd)"
    log "BLUE" "🔍 Проверка наличия docker-compose.yml: $(ls -la | grep docker-compose.yml || echo 'Файл не найден')"

    # Загружаем переменные окружения из файла .env
    if [ -f ".env" ]; then
        log "BLUE" "🔑 Загружаем переменные окружения из .env"
        export $(grep -v '^#' .env | xargs)
    else
        log "RED" "❌ Файл .env не найден. Создайте его и настройте переменные окружения."
        return 1
    fi

    # Экспортируем переменные для docker-compose
    export DOCKER_UID DOCKER_GID
    export CREATED_BY="$CURRENT_USER"
    export CREATED_AT="$CURRENT_TIME"

    # Проверяем наличие docker-compose файла
    if [ ! -f "docker-compose.yml" ]; then
        log "RED" "❌ Файл docker-compose.yml не найден в текущей директории!"
        log "BLUE" "🔍 Содержимое директории:"
        ls -la
        return 1
    fi

    case $action in
        "restart_scheduler")
            log "BLUE" "🔄 Перезапуск scheduler'а..."
            docker_compose_cmd down --remove-orphans
            docker_compose_cmd build --no-cache
            docker_compose_cmd up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка всех контейнеров..."
            docker_compose_cmd down --remove-orphans
            ;;
        "start_scheduler")
            start_scheduler
            ;;
        "run_once")
            log "BLUE" "🔍 Одноразовый запуск парсера..."
            # Останавливаем scheduler если он запущен
            if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
                log "YELLOW" "⚠️ Останавливаем scheduler для одноразового запуска..."
                docker_compose_cmd down
            fi
            docker_compose_cmd build
            docker_compose_cmd --profile manual run --rm dnscrypt-parser-once
            ;;
    esac

    if [ "$action" = "start_scheduler" ] || [ "$action" = "restart_scheduler" ]; then
        log "GREEN" "✅ Scheduler запущен и работает в фоне"
        log "BLUE" "📁 Проверьте логи в файле: $SCHEDULER_LOG_FILE"
    elif [ "$action" = "run_once" ]; then
        log "GREEN" "✅ Парсер завершил работу"
        log "BLUE" "📁 Проверьте результаты в директории output/"
    fi
}

# Функция для принудительного удаления контейнера
force_remove_container() {
    local container_name=$1
    if docker ps -a | grep -q "$container_name"; then
        log "YELLOW" "⚠️ Принудительное удаление контейнера $container_name..."
        docker stop "$container_name" || true
        docker rm "$container_name" || true
    fi
}

# Функция для просмотра результатов парсинга
view_results() {
    log "BLUE" "📊 Просмотр результатов парсинга..."
    
    if [ -d "$OUTPUT_DIR" ]; then
        log "GREEN" "📁 Содержимое директории output:"
        ls -la "$OUTPUT_DIR"
        
        # Проверяем наличие отчета парсера
        if [ -f "$OUTPUT_DIR/update_report.txt" ]; then
            log "BLUE" "📄 Показать отчет о парсинге? [Y/n]"
            read -r response
            response=${response:-Y}
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                less "$OUTPUT_DIR/update_report.txt" || cat "$OUTPUT_DIR/update_report.txt"
            fi
        fi
        
        # Проверяем наличие отчета scheduler'а
        if [ -f "$OUTPUT_DIR/scheduler_report.txt" ]; then
            echo ""
            log "BLUE" "📄 Показать отчет scheduler'а? [Y/n]"
            read -r response
            response=${response:-Y}
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                cat "$OUTPUT_DIR/scheduler_report.txt"
            fi
        fi
        
        # Проверяем наличие файлов конфигурации
        echo ""
        if [ -f "$OUTPUT_DIR/DNSCrypt_relay.txt" ] || [ -f "$OUTPUT_DIR/DNSCrypt_servers.txt" ]; then
            log "GREEN" "✅ Найдены обновленные файлы конфигурации"
            if [ -f "$OUTPUT_DIR/DNSCrypt_relay.txt" ]; then
                log "GREEN" "📄 DNSCrypt_relay.txt: $(wc -l < "$OUTPUT_DIR/DNSCrypt_relay.txt") строк"
            fi
            if [ -f "$OUTPUT_DIR/DNSCrypt_servers.txt" ]; then
                log "GREEN" "📄 DNSCrypt_servers.txt: $(wc -l < "$OUTPUT_DIR/DNSCrypt_servers.txt") строк"
            fi
        else
            log "YELLOW" "⚠️ Файлы конфигурации не найдены"
        fi
        
        # Информация о времени последнего запуска
        if [ -f "$OUTPUT_DIR/last_run.txt" ]; then
            last_run=$(cat "$OUTPUT_DIR/last_run.txt" 2>/dev/null || echo "Неизвестно")
            log "BLUE" "🕐 Время последнего запуска парсера: $last_run"
        fi
    else
        log "RED" "❌ Директория output не найдена"
    fi
}

# Функция для просмотра логов
view_logs() {
    log "BLUE" "📋 Выберите тип логов для просмотра:"
    log "GREEN" "1. 📄 Логи парсера (parser.log)"
    log "GREEN" "2. ⏰ Логи scheduler'а (scheduler.log)"
    log "GREEN" "3. ❌ Логи ошибок (error.log)"
    log "GREEN" "4. 🐳 Логи контейнера scheduler'а"
    log "GREEN" "5. 📊 Все логи"
    log "GREEN" "0. 🔙 Назад"
    
    read -r -p "Выберите действие (0-5): " choice
    
    case "$choice" in
        1)
            if [ -f "$PARSER_LOG_FILE" ]; then
                log "MAGENTA" "📊 Логи парсера:"
                less "$PARSER_LOG_FILE" || cat "$PARSER_LOG_FILE"
            else
                log "RED" "❌ Файл логов парсера не найден: $PARSER_LOG_FILE"
            fi
            ;;
        2)
            if [ -f "$SCHEDULER_LOG_FILE" ]; then
                log "MAGENTA" "📊 Логи scheduler'а:"
                less "$SCHEDULER_LOG_FILE" || cat "$SCHEDULER_LOG_FILE"
            else
                log "RED" "❌ Файл логов scheduler'а не найден: $SCHEDULER_LOG_FILE"
            fi
            ;;
        3)
            if [ -f "$ERROR_LOG_FILE" ]; then
                log "MAGENTA" "📊 Логи ошибок:"
                less "$ERROR_LOG_FILE" || cat "$ERROR_LOG_FILE"
            else
                log "RED" "❌ Файл логов ошибок не найден: $ERROR_LOG_FILE"
            fi
            ;;
        4)
            if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
                log "MAGENTA" "📊 Логи контейнера scheduler'а:"
                docker logs -f "$SCHEDULER_CONTAINER_NAME"
            else
                log "RED" "❌ Контейнер scheduler'а не запущен"
            fi
            ;;
        5)
            log "MAGENTA" "📊 Показываем все доступные логи..."
            echo "==================== ЛОГИ ПАРСЕРА ===================="
            if [ -f "$PARSER_LOG_FILE" ]; then
                tail -50 "$PARSER_LOG_FILE"
            else
                echo "Файл не найден"
            fi
            echo ""
            echo "==================== ЛОГИ SCHEDULER'А ===================="
            if [ -f "$SCHEDULER_LOG_FILE" ]; then
                tail -50 "$SCHEDULER_LOG_FILE"
            else
                echo "Файл не найден"
            fi
            echo ""
            echo "==================== ЛОГИ ОШИБОК ===================="
            if [ -f "$ERROR_LOG_FILE" ]; then
                tail -50 "$ERROR_LOG_FILE"
            else
                echo "Файл не найден"
            fi
            ;;
        0)
            return 0
            ;;
        *)
            log "RED" "❌ Неверный выбор."
            ;;
    esac
}

# Функция для сброса таймера scheduler'а
reset_scheduler_timer() {
    log "BLUE" "🔄 Сброс таймера scheduler'а..."
    
    # Удаляем файл времени последнего запуска
    if [ -f "$OUTPUT_DIR/last_run.txt" ]; then
        rm "$OUTPUT_DIR/last_run.txt"
        log "GREEN" "✅ Файл времени последнего запуска удален"
    else
        log "YELLOW" "⚠️ Файл времени последнего запуска не найден"
    fi
    
    # Перезапускаем scheduler если он запущен
    if docker ps | grep -q "$SCHEDULER_CONTAINER_NAME"; then
        log "BLUE" "🔄 Перезапуск scheduler'а для применения изменений..."
        docker_compose_cmd restart
        log "GREEN" "✅ Scheduler перезапущен - парсер запустится немедленно"
    else
        log "YELLOW" "⚠️ Scheduler не запущен. При следующем запуске парсер выполнится немедленно."
    fi
}

# Функция для очистки временных файлов
cleanup() {
    log "BLUE" "🧹 Очистка временных файлов..."
    find /tmp -maxdepth 1 -type d -name "tmp.*" -user "$CURRENT_USER" -exec rm -rf {} \; 2>/dev/null || true
}

# Функция для очистки Docker
cleanup_docker() {
    log "BLUE" "🧹 Очистка Docker..."
    docker system prune -f
    log "GREEN" "✅ Docker очищен (удалены неиспользуемые образы, контейнеры и сети)"

    read -r -p "Очистить также все тома Docker? [y/N] " response
    response=${response:-N}
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker system prune -af --volumes
        log "GREEN" "✅ Docker очищен полностью (включая тома)"
    fi
}

# Функция для очистки логов
cleanup_logs() {
    log "BLUE" "🧹 Очистка старых логов..."
    
    if [ -d "$LOGS_DIR" ] || [ -f "$SCHEDULER_LOG_FILE" ]; then
        local backup_date=$(date +%Y%m%d-%H%M%S)
        local backup_dir="$ROOT_DIR/logs_backup"
        mkdir -p "$backup_dir"
        
        # Создаем архив всех логов
        log "BLUE" "📦 Создание архива логов..."
        tar -czf "$backup_dir/logs_$backup_date.tar.gz" \
            $([ -d "$LOGS_DIR" ] && echo "$LOGS_DIR") \
            $([ -f "$SCHEDULER_LOG_FILE" ] && echo "$SCHEDULER_LOG_FILE") \
            $([ -f "$OUTPUT_DIR/scheduler_report.txt" ] && echo "$OUTPUT_DIR/scheduler_report.txt") \
            2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "GREEN" "✅ Создан архив логов: logs_$backup_date.tar.gz"
            
            # Очищаем файлы логов
            [ -f "$PARSER_LOG_FILE" ] && echo "" > "$PARSER_LOG_FILE"
            [ -f "$ERROR_LOG_FILE" ] && echo "" > "$ERROR_LOG_FILE"
            [ -f "$SCHEDULER_LOG_FILE" ] && echo "" > "$SCHEDULER_LOG_FILE"
            
            log "GREEN" "✅ Логи очищены"
            
            # Удаляем старые архивы (старше 30 дней)
            find "$backup_dir" -name "logs_*.tar.gz" -type f -mtime +30 -delete
            log "GREEN" "✅ Старые архивы логов удалены"
        else
            log "RED" "❌ Ошибка при создании архива логов"
        fi
    else
        log "YELLOW" "⚠️ Файлы логов не найдены"
        mkdir -p "$LOGS_DIR"
        touch "$PARSER_LOG_FILE" "$ERROR_LOG_FILE" "$SCHEDULER_LOG_FILE"
        log "GREEN" "✅ Созданы пустые файлы логов"
    fi
}

# Функция проверки GitHub токена
check_github_token() {
    log "BLUE" "🔑 Проверка GitHub токена..."
    
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
        
        if [ -n "${GITHUB_TOKEN:-}" ] && [ "$GITHUB_TOKEN" != "your_github_token_here" ]; then
            log "GREEN" "✅ GitHub токен настроен"
            
            # Проверяем валидность токена
            if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user > /dev/null; then
                log "GREEN" "✅ GitHub токен валиден"
            else
                log "RED" "❌ GitHub токен невалиден"
            fi
        else
            log "YELLOW" "⚠️ GitHub токен не настроен или использует значение по умолчанию"
            log "YELLOW" "⚠️ Парсер будет работать без автоматической отправки в GitHub"
        fi
    else
        log "RED" "❌ Файл .env не найден"
    fi
}

# Основное меню
main_menu() {
    while true; do
        log "YELLOW" "🔍 DNSCrypt Parser with Scheduler"
        log "YELLOW" "===================================="
        log "GREEN" "1. ⬆️ Обновить из репозитория"
        log "GREEN" "2. 📝 Создать или редактировать .env файл"
        log "GREEN" "3. 🔑 Проверить GitHub токен"
        log "GREEN" "4. ⏰ Запустить scheduler (автоматические обновления)"
        log "GREEN" "5. ⏹️ Остановить scheduler"
        log "GREEN" "6. 📊 Статус scheduler'а"
        log "GREEN" "7. 🚀 Запустить парсер (одноразово)"
        log "GREEN" "8. 🔄 Перезапустить scheduler"
        log "GREEN" "9. ⏰ Сбросить таймер scheduler'а"
        log "GREEN" "10. 📋 Просмотреть логи"
        log "GREEN" "11. 📊 Просмотреть результаты парсинга"
        log "GREEN" "12. 🧹 Очистить старые логи"
        log "GREEN" "13. 🐳 Очистить Docker"
        log "GREEN" "14. 🔧 Проверить и исправить установку Docker"
        log "GREEN" "0. 🚪 Выйти"

        read -r -p "Выберите действие (0-14): " choice

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
                manage_container "start_scheduler"
                ;;
            5)
                stop_scheduler
                ;;
            6)
                view_scheduler_status
                ;;
            7)
                manage_container "run_once"
                ;;
            8)
                manage_container "restart_scheduler"
                ;;
            9)
                reset_scheduler_timer
                ;;
            10)
                view_logs
                ;;
            11)
                view_results
                ;;
            12)
                cleanup_logs
                ;;
            13)
                cleanup_docker
                ;;
            14)
                check_fix_docker
                ;;
            0)
                log "BLUE" "🚪 Выход..."
                break
                ;;
            *)
                log "RED" "❌ Неверный выбор. Пожалуйста, выберите действие от 0 до 14."
                ;;
        esac
        
        # Добавляем паузу после выполнения действия
        echo ""
        read -r -p "Нажмите Enter для продолжения..."
        echo ""
    done
}

# Проверка прав суперпользователя для управления Docker
if [ "$EUID" -ne 0 ] && ! groups | grep -q docker && ! sudo -n true 2>/dev/null; then
    log "YELLOW" "⚠️ Для управления Docker требуются права суперпользователя или членство в группе docker"
    log "YELLOW" "⚠️ Запустите скрипт с sudo или добавьте пользователя в группу docker и перезайдите в систему"
fi

# Запускаем основное меню
main_menu

# Очистка временных файлов перед выходом
cleanup