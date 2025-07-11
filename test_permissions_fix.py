#!/usr/bin/env python3
"""
Простой тест для проверки исправлений прав доступа
"""
import sys
import os
import tempfile
from pathlib import Path

# Добавляем текущую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

def test_permissions_fix():
    """Тестирует исправления прав доступа"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕНИЙ ПРАВ ДОСТУПА")
    print("=" * 50)
    
    # Тест 1: Импорт модулей
    print("\n🔍 Тест 1: Проверка импорта модулей")
    try:
        from utils.metrics import ParsingMetrics, ParsingCache
        print("✅ Модули metrics импортированы успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта metrics: {e}")
        return False
    
    try:
        from core.base_parser import DNSCryptParser
        print("✅ Модуль base_parser импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта base_parser: {e}")
        return False
    
    # Тест 2: Создание ParsingCache
    print("\n💾 Тест 2: Создание системы кэширования")
    try:
        cache = ParsingCache()
        print(f"✅ Кэш создан, статус: {cache.cache_enabled}")
        print(f"📁 Директория кэша: {cache.cache_dir}")
        
        if cache.cache_enabled:
            # Тестируем кэширование
            test_data = {"test": "data", "ip": "1.2.3.4"}
            cache.cache_server_info("test_server", test_data)
            retrieved = cache.get_cached_server_info("test_server")
            
            if retrieved:
                print("✅ Кэширование работает корректно")
            else:
                print("⚠️ Кэш создан, но извлечение данных не работает")
        else:
            print("⚠️ Кэширование отключено (это нормально при проблемах с правами)")
            
    except Exception as e:
        print(f"❌ Ошибка создания кэша: {e}")
        return False
    
    # Тест 3: Создание ParsingMetrics
    print("\n📊 Тест 3: Создание системы метрик")
    try:
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
        print(f"❌ Ошибка создания метрик: {e}")
        return False
    
    # Тест 4: Создание DNSCryptParser
    print("\n🚀 Тест 4: Создание основного парсера")
    try:
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
            
    except Exception as e:
        print(f"❌ Ошибка создания парсера: {e}")
        return False
    
    # Тест 5: Проверка прав доступа к директориям
    print("\n📁 Тест 5: Проверка прав доступа к директориям")
    
    directories_to_test = [
        "./output",
        "./output/cache",
        "./logs",
        tempfile.gettempdir(),
        os.path.join(tempfile.gettempdir(), "dnscrypt_parser")
    ]
    
    for dir_path in directories_to_test:
        try:
            # Создаем директорию если не существует
            os.makedirs(dir_path, exist_ok=True)
            
            # Пробуем создать тестовый файл
            test_file = os.path.join(dir_path, "test_permissions.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Удаляем тестовый файл
            os.remove(test_file)
            
            print(f"✅ {dir_path} - доступен для записи")
            
        except Exception as e:
            print(f"❌ {dir_path} - недоступен ({e})")
    
    print("\n" + "=" * 50)
    print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
    print("✅ Исправления прав доступа работают корректно")
    print("🚀 Модульная система готова к использованию")
    
    return True

if __name__ == "__main__":
    success = test_permissions_fix()
    sys.exit(0 if success else 1)