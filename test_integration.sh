#!/bin/bash

# Тест интеграции модульной системы с Docker и скриптами управления
# Версия: 2.0 - Полная проверка модульной архитектуры

echo "🧪 ТЕСТ ИНТЕГРАЦИИ DNSCRYPT PARSER V2.0"
echo "========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Счетчики
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Функция для логирования
test_log() {
    local level=$1
    local message=$2
    echo -e "${!level}${message}${NC}"
}

# Функция для проведения теста
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_log "BLUE" "🧪 Тест: $test_name"
    
    if eval "$test_command"; then
        test_log "GREEN" "  ✅ ПРОЙДЕН"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        test_log "RED" "  ❌ ПРОВАЛЕН"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo ""
test_log "YELLOW" "🔍 ПРОВЕРКА СТРУКТУРЫ МОДУЛЬНОЙ СИСТЕМЫ"
echo "================================================"

# Тест 1: Основные файлы парсера
run_test "Основные файлы парсера" "[ -f 'parser.py' ] && [ -f 'parser_new.py' ] && [ -f 'scheduler.py' ]"

# Тест 2: Структура core модуля
run_test "Core модуль" "[ -d 'core' ] && [ -f 'core/__init__.py' ] && [ -f 'core/base_parser.py' ] && [ -f 'core/config.py' ]"

# Тест 3: Файловые обработчики
run_test "File handlers" "[ -d 'file_handlers' ] && [ -f 'file_handlers/__init__.py' ] && [ -f 'file_handlers/config_parser.py' ]"

# Тест 4: GitHub интеграция
run_test "GitHub модуль" "[ -d 'github' ] && [ -f 'github/__init__.py' ] && [ -f 'github/github_manager.py' ]"

# Тест 5: Обработчики страниц
run_test "Page handlers" "[ -d 'page_handlers' ] && [ -f 'page_handlers/__init__.py' ] && [ -f 'page_handlers/page_navigator.py' ]"

# Тест 6: Извлекатели данных
run_test "Extractors" "[ -d 'extractors' ] && [ -f 'extractors/__init__.py' ] && [ -f 'extractors/dialog_extractor.py' ]"

# Тест 7: Стратегии восстановления
run_test "Strategies" "[ -d 'strategies' ] && [ -f 'strategies/__init__.py' ] && [ -f 'strategies/error_recovery.py' ]"

# Тест 8: Утилиты
run_test "Utils" "[ -d 'utils' ] && [ -f 'utils/__init__.py' ] && [ -f 'utils/metrics.py' ]"

echo ""
test_log "YELLOW" "🐳 ПРОВЕРКА DOCKER КОНФИГУРАЦИИ"
echo "====================================="

# Тест 9: Docker файлы
run_test "Docker файлы" "[ -f 'Dockerfile' ] && [ -f 'docker-compose.yml' ] && [ -f 'requirements.txt' ]"

# Тест 10: Проверка Dockerfile на модульную систему
run_test "Dockerfile содержит модульные копии" "grep -q 'COPY core/' Dockerfile && grep -q 'COPY file_handlers/' Dockerfile"

# Тест 11: Docker-compose профили
run_test "Docker-compose профили" "grep -q 'profiles:' docker-compose.yml && grep -q 'modular' docker-compose.yml && grep -q 'legacy' docker-compose.yml"

# Тест 12: Environment переменные
run_test "Environment переменные" "grep -q 'PARSER_MODE' docker-compose.yml"

echo ""
test_log "YELLOW" "📝 ПРОВЕРКА КОНФИГУРАЦИОННЫХ ФАЙЛОВ"
echo "======================================"

# Тест 13: .env.example обновлен
run_test ".env.example для v2.0" "grep -q 'PARSER_MODE' .env.example && grep -q 'modular' .env.example"

# Тест 14: Requirements для модульной системы
run_test "Requirements для модульной системы" "grep -q 'selenium-stealth' requirements.txt && grep -q 'pydantic' requirements.txt"

echo ""
test_log "YELLOW" "🛠️ ПРОВЕРКА СКРИПТОВ УПРАВЛЕНИЯ"
echo "=================================="

# Тест 15: manage_parser.sh обновлен
run_test "manage_parser.sh поддержка модульной системы" "grep -q 'run_modular_parser' manage_parser.sh && grep -q 'check_modular_system' manage_parser.sh"

# Тест 16: Новые функции в меню
run_test "Новые опции в меню" "grep -q 'модульный парсер v2.0' manage_parser.sh && grep -q 'legacy парсер' manage_parser.sh"

echo ""
test_log "YELLOW" "🐍 ПРОВЕРКА PYTHON ИНТЕГРАЦИИ"
echo "================================"

# Тест 17: parser_new.py импорты
run_test "parser_new.py импорты модулей" "grep -q 'from core import' parser_new.py && grep -q 'from strategies' parser_new.py"

# Тест 18: Обратная совместимость
run_test "Обратная совместимость в parser_new.py" "grep -q 'LEGACY_AVAILABLE' parser_new.py && grep -q 'import parser as legacy_parser' parser_new.py"

# Тест 19: scheduler.py поддержка модульной системы
run_test "scheduler.py поддержка модулей" "grep -q 'PARSER_MODE' scheduler.py && grep -q 'parser_new.py' scheduler.py"

echo ""
test_log "YELLOW" "⚙️ ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ"
echo "========================="

# Тест 20: Python синтаксис parser_new.py
run_test "Python синтаксис parser_new.py" "python -m py_compile parser_new.py 2>/dev/null"

# Тест 21: Python синтаксис scheduler.py
run_test "Python синтаксис scheduler.py" "python -m py_compile scheduler.py 2>/dev/null"

# Тест 22: Импорт модульной системы
if python -c "import sys; sys.path.append('.'); from core import DNSCryptParser" 2>/dev/null; then
    run_test "Импорт модульной системы" "true"
else
    run_test "Импорт модульной системы" "false"
fi

# Тест 23: Проверка автоматического выбора парсера
run_test "Автоматический выбор парсера" "grep -q 'choose_execution_mode' parser_new.py && grep -q 'MODULAR_AVAILABLE' parser_new.py"

echo ""
test_log "YELLOW" "📋 ПРОВЕРКА ДОКУМЕНТАЦИИ"
echo "=========================="

# Тест 24: README обновлен для v2.0
run_test "README.md обновлен для v2.0" "grep -q 'v2.0' README.md && grep -q 'модульная' README.md"

# Тест 25: Структура проекта в README
run_test "Структура проекта включает модули" "grep -q 'core/' README.md && grep -q 'strategies/' README.md"

echo ""
test_log "YELLOW" "🔄 ПРОВЕРКА ИНТЕГРАЦИОННЫХ СЦЕНАРИЕВ"
echo "========================================"

# Тест 26: Docker build проходит
if command -v docker &> /dev/null; then
    run_test "Docker build успешен" "docker build -t dnscrypt-parser-test . >/dev/null 2>&1"
    
    # Очистка тестового образа
    docker rmi dnscrypt-parser-test >/dev/null 2>&1 || true
else
    test_log "YELLOW" "⚠️ Docker не установлен, пропускаем тест сборки"
fi

# Тест 27: manage_parser.sh исполняется
run_test "manage_parser.sh исполняемый" "[ -x 'manage_parser.sh' ] || chmod +x manage_parser.sh"

# Тест 28: launcher_parser.sh исполняемый
run_test "launcher_parser.sh исполняемый" "[ -x 'launcher_parser.sh' ] || chmod +x launcher_parser.sh"

echo ""
test_log "YELLOW" "📊 ИТОГОВЫЙ ОТЧЕТ"
echo "=================="

test_log "BLUE" "Всего тестов: $TOTAL_TESTS"
test_log "GREEN" "Пройдено: $PASSED_TESTS"
test_log "RED" "Провалено: $FAILED_TESTS"

# Вычисляем процент успеха
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    test_log "YELLOW" "Процент успеха: $SUCCESS_RATE%"
    
    if [ $SUCCESS_RATE -ge 90 ]; then
        test_log "GREEN" "🎉 ОТЛИЧНО! Модульная система полностью интегрирована!"
        echo ""
        test_log "GREEN" "✅ Готово к использованию:"
        echo "   • Запустите: ./manage_parser.sh"
        echo "   • Выберите: '4. 🔍 Проверить модульную систему'"
        echo "   • Затем: '10. 🔄 Запустить парсер (авто-выбор)'"
    elif [ $SUCCESS_RATE -ge 75 ]; then
        test_log "YELLOW" "⚠️ ХОРОШО, но есть замечания. Проверьте провалившиеся тесты."
    else
        test_log "RED" "❌ ТРЕБУЕТСЯ ДОРАБОТКА. Множественные проблемы интеграции."
    fi
else
    test_log "RED" "❌ Не удалось выполнить тесты"
fi

echo ""
test_log "BLUE" "🔍 Для диагностики проблем:"
echo "   • Запустите: ./manage_parser.sh"
echo "   • Выберите: '4. 🔍 Проверить модульную систему'"
echo "   • Или проверьте логи: docker logs <container_name>"

# Возвращаем код ошибки если есть проваленные тесты
if [ $FAILED_TESTS -gt 0 ]; then
    exit 1
else
    exit 0
fi