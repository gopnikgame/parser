#!/bin/bash

# Скрипт для исправления относительных импортов в модульной системе
echo "🔧 Исправление относительных импортов в модульной системе..."

# Функция для исправления импортов в файле
fix_imports_in_file() {
    local file="$1"
    echo "📝 Исправляем $file..."
    
    # Создаем временный файл
    temp_file="${file}.tmp"
    
    # Исправляем относительные импорты
    sed 's/from \.\.core\./from core./g' "$file" | \
    sed 's/from \.\.extractors\./from extractors./g' | \
    sed 's/from \.\.strategies\./from strategies./g' | \
    sed 's/from \.\.utils\./from utils./g' | \
    sed 's/from \.\.page_handlers\./from page_handlers./g' | \
    sed 's/from \.\.file_handlers\./from file_handlers./g' | \
    sed 's/from \.\.github\./from github./g' | \
    sed 's/from \.\.data_handlers\./from data_handlers./g' > "$temp_file"
    
    # Заменяем оригинальный файл
    mv "$temp_file" "$file"
    echo "✅ $file исправлен"
}

# Исправляем все Python файлы в модульных директориях
echo "🔍 Поиск файлов с относительными импортами..."

# Список файлов для исправления
files_to_fix=(
    "utils/metrics.py"
    "page_handlers/page_navigator.py"
    "page_handlers/pagination_manager.py"
    "file_handlers/config_parser.py"
    "file_handlers/file_updater.py"
    "github/github_manager.py"
)

# Исправляем каждый файл
for file in "${files_to_fix[@]}"; do
    if [ -f "$file" ]; then
        fix_imports_in_file "$file"
    else
        echo "⚠️ Файл $file не найден"
    fi
done

echo "🎉 Исправление импортов завершено!"
echo "🚀 Теперь модульная система должна работать корректно в Docker"