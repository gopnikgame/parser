#!/bin/bash

# Скрипт для исправления прав доступа и тестирования модульной системы
echo "🔧 Скрипт исправления прав доступа DNSCrypt Parser"
echo "======================================================================="

# Проверяем, что мы в корректной директории
if [ ! -f "parser_new.py" ]; then
    echo "❌ Ошибка: файл parser_new.py не найден!"
    echo "Убедитесь, что вы находитесь в корневой директории проекта"
    exit 1
fi

echo "📁 Текущая директория: $(pwd)"
echo "👤 Текущий пользователь: $(whoami)"
echo "🆔 UID: $(id -u), GID: $(id -g)"

echo ""
echo "🔍 ПРОВЕРКА СТРУКТУРЫ ДИРЕКТОРИЙ"
echo "---------------------------------------"

# Список необходимых директорий
REQUIRED_DIRS=(
    "output"
    "output/cache"
    "logs"
    "core"
    "extractors"
    "strategies"
    "utils"
    "file_handlers"
    "github"
    "page_handlers"
    "data_handlers"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir - существует"
        ls -ld "$dir" 2>/dev/null || echo "  ⚠️ Не удалось проверить права доступа"
    else
        echo "❌ $dir - не существует, создаем..."
        mkdir -p "$dir" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Директория $dir создана"
        else
            echo "  ❌ Не удалось создать директорию $dir"
        fi
    fi
done

echo ""
echo "🔧 ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА"
echo "---------------------------------------"

# Устанавливаем права доступа
echo "🔨 Установка прав доступа для директорий..."

# Пытаемся установить права доступа
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "🔨 Настройка прав для $dir..."
        
        # Пытаемся различные методы установки прав
        chmod 755 "$dir" 2>/dev/null || \
        chmod 777 "$dir" 2>/dev/null || \
        echo "  ⚠️ Не удалось изменить права для $dir"
        
        # Проверяем, можем ли мы создать файл в директории
        TEST_FILE="$dir/test_permissions_$(date +%s).tmp"
        if touch "$TEST_FILE" 2>/dev/null; then
            rm "$TEST_FILE" 2>/dev/null
            echo "  ✅ Права доступа для $dir - ОК"
        else
            echo "  ⚠️ Ограниченные права доступа для $dir"
        fi
    fi
done

echo ""
echo "🐍 ПРОВЕРКА PYTHON МОДУЛЕЙ"
echo "---------------------------------------"

# Проверяем основные модули
MODULES=(
    "core"
    "core.base_parser"
    "core.config"
    "core.driver_manager"
    "extractors.dialog_extractor"
    "strategies.error_recovery"
    "utils.metrics"
    "file_handlers.config_parser"
    "github.github_manager"
    "page_handlers.page_navigator"
    "data_handlers.server_processor"
)

for module in "${MODULES[@]}"; do
    echo -n "🔍 Проверка модуля $module... "
    if python3 -c "import $module" 2>/dev/null; then
        echo "✅"
    else
        echo "❌"
        echo "  Подробности ошибки:"
        python3 -c "import $module" 2>&1 | head -3 | sed 's/^/    /'
    fi
done

echo ""
echo "💾 ТЕСТИРОВАНИЕ КЭШИРОВАНИЯ"
echo "---------------------------------------"

# Тестируем возможность создания кэша
echo "🧪 Тестирование создания файлов кэша..."

python3 << 'EOF'
import sys
import os
sys.path.append('.')

try:
    from utils.metrics import ParsingCache
    print("✅ Импорт ParsingCache успешен")
    
    # Пытаемся создать кэш
    cache = ParsingCache()
    print(f"✅ Кэш создан, статус: {cache.cache_enabled}")
    
    if cache.cache_enabled:
        print(f"📁 Директория кэша: {cache.cache_dir}")
        
        # Тестируем кэширование
        test_data = {"test": "data", "ip": "1.2.3.4"}
        cache.cache_server_info("test_server", test_data)
        
        retrieved = cache.get_cached_server_info("test_server")
        if retrieved:
            print("✅ Кэширование работает корректно")
        else:
            print("⚠️ Проблемы с извлечением из кэша")
    else:
        print("⚠️ Кэширование отключено")
        
except Exception as e:
    print(f"❌ Ошибка тестирования кэша: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "📊 ТЕСТИРОВАНИЕ МЕТРИК"
echo "---------------------------------------"

echo "🧪 Тестирование системы метрик..."

python3 << 'EOF'
import sys
sys.path.append('.')

try:
    from utils.metrics import ParsingMetrics
    print("✅ Импорт ParsingMetrics успешен")
    
    # Пытаемся создать систему метрик
    metrics = ParsingMetrics()
    print("✅ Система метрик создана")
    
    # Тестируем базовую функциональность
    session_id = metrics.start_session("test_session")
    print(f"✅ Сессия создана: {session_id}")
    
    # Добавляем тестовую метрику
    metrics.record_server_extraction("test_server", True, 1.5, 1, None, "test_method")
    print("✅ Метрика записана")
    
    # Завершаем сессию
    session = metrics.end_session()
    if session:
        print("✅ Сессия завершена успешно")
    else:
        print("⚠️ Проблемы с завершением сессии")
        
except Exception as e:
    print(f"❌ Ошибка тестирования метрик: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "🏗️ ТЕСТИРОВАНИЕ ОСНОВНОГО ПАРСЕРА"
echo "---------------------------------------"

echo "🧪 Тестирование инициализации DNSCryptParser..."

python3 << 'EOF'
import sys
sys.path.append('.')

try:
    from core.base_parser import DNSCryptParser
    print("✅ Импорт DNSCryptParser успешен")
    
    # Пытаемся создать парсер (без полной инициализации)
    parser = DNSCryptParser()
    print("✅ DNSCryptParser создан успешно")
    
    # Проверяем компоненты
    if parser.metrics:
        print("✅ Система метрик инициализирована")
    else:
        print("⚠️ Система метрик недоступна")
    
    if parser.cache:
        print(f"✅ Система кэширования инициализирована (активна: {parser.cache.cache_enabled})")
    else:
        print("⚠️ Система кэширования недоступна")
    
    print("✅ Базовая инициализация парсера прошла успешно")
    
except Exception as e:
    print(f"❌ Ошибка инициализации парсера: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "📋 ИТОГОВЫЙ ОТЧЕТ"
echo "======================================================================="

# Финальная проверка
FINAL_CHECK=true

# Проверяем ключевые файлы
KEY_FILES=(
    "parser_new.py"
    "core/base_parser.py"
    "core/config.py"
    "utils/metrics.py"
)

echo "🔍 Проверка ключевых файлов:"
for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - НЕ НАЙДЕН!"
        FINAL_CHECK=false
    fi
done

# Проверяем возможность импорта
echo ""
echo "🐍 Проверка возможности импорта основных модулей:"
python3 -c "
import sys
sys.path.append('.')

modules = [
    'core',
    'core.base_parser', 
    'utils.metrics'
]

all_ok = True
for module in modules:
    try:
        __import__(module)
        print(f'  ✅ {module}')
    except Exception as e:
        print(f'  ❌ {module} - {e}')
        all_ok = False

if all_ok:
    print('🎉 Все основные модули импортируются успешно!')
    exit(0)
else:
    print('⚠️ Есть проблемы с импортом модулей')
    exit(1)
"

if [ $? -eq 0 ] && [ "$FINAL_CHECK" = true ]; then
    echo ""
    echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"
    echo "✅ Модульная система готова к работе"
    echo "✅ Права доступа настроены (где возможно)"
    echo "✅ Все компоненты доступны"
    echo ""
    echo "🚀 Теперь можно запускать парсер:"
    echo "   python parser_new.py"
    echo ""
else
    echo ""
    echo "⚠️ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ"
    echo "❌ Есть проблемы, требующие внимания"
    echo ""
    echo "📝 Рекомендации:"
    echo "1. Проверьте права доступа к директориям"
    echo "2. Убедитесь, что все модули доступны"
    echo "3. При необходимости запустите Docker контейнер с правами root"
    echo ""
fi

echo "======================================================================="