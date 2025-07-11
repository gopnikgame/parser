#!/usr/bin/env python3
"""
Скрипт для проверки и исправления импортов в модульной системе
Проверяет все модули на наличие ошибок импорта
"""

import sys
import os
from pathlib import Path

def test_module_imports():
    """Тестирование импортов всех модулей"""
    print("🔍 ПРОВЕРКА ИМПОРТОВ МОДУЛЬНОЙ СИСТЕМЫ")
    print("=" * 60)
    
    # Добавляем текущую директорию в путь
    current_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(current_dir))
    
    modules_to_test = [
        ("core", ["DNSCryptParser", "SmartDriverManager", "ParserConfig"]),
        ("extractors", ["AdvancedDialogExtractor"]),
        ("strategies", ["SmartErrorRecovery"]),
        ("utils", ["ParsingMetrics"]),
        ("page_handlers", ["PageNavigator", "PaginationManager"]),
        ("file_handlers", ["ConfigFileParser", "FileUpdater"]),
        ("github", ["GitHubManager"]),
        ("data_handlers", ["ServerProcessor"])
    ]
    
    all_passed = True
    failed_modules = []
    
    for module_name, classes in modules_to_test:
        print(f"\n📦 Тестирование модуля: {module_name}")
        print("-" * 40)
        
        try:
            # Пытаемся импортировать модуль
            module = __import__(module_name)
            print(f"✅ Модуль {module_name} импортирован успешно")
            
            # Проверяем доступность классов
            for class_name in classes:
                try:
                    if hasattr(module, class_name):
                        print(f"  ✅ {class_name} доступен")
                    else:
                        print(f"  ❌ {class_name} недоступен в модуле")
                        all_passed = False
                except Exception as e:
                    print(f"  ❌ Ошибка проверки {class_name}: {e}")
                    all_passed = False
                    
        except ImportError as e:
            print(f"❌ Ошибка импорта модуля {module_name}: {e}")
            failed_modules.append((module_name, str(e)))
            all_passed = False
        except Exception as e:
            print(f"❌ Неожиданная ошибка в модуле {module_name}: {e}")
            failed_modules.append((module_name, str(e)))
            all_passed = False
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    if all_passed:
        print("🎉 ВСЕ МОДУЛИ ПРОШЛИ ПРОВЕРКУ УСПЕШНО!")
        print("✅ Модульная система готова к использованию")
    else:
        print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С ИМПОРТАМИ")
        print(f"❌ Проблемных модулей: {len(failed_modules)}")
        
        if failed_modules:
            print("\n🔍 Детали ошибок:")
            for module_name, error in failed_modules:
                print(f"  📦 {module_name}: {error}")
        
        print("\n🛠️ Рекомендации по исправлению:")
        print("  1. Проверьте наличие всех файлов __init__.py")
        print("  2. Убедитесь в корректности относительных импортов")
        print("  3. Проверьте зависимости в requirements.txt")
        print("  4. Перезапустите из корневой директории проекта")
    
    return all_passed

def test_individual_imports():
    """Детальное тестирование отдельных импортов"""
    print("\n🔬 ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ ИМПОРТОВ")
    print("=" * 60)
    
    test_imports = [
        "from core import DNSCryptParser, SmartDriverManager, ParserConfig",
        "from extractors import AdvancedDialogExtractor",
        "from strategies import SmartErrorRecovery", 
        "from utils import ParsingMetrics",
        "from page_handlers import PageNavigator, PaginationManager",
        "from file_handlers import ConfigFileParser, FileUpdater",
        "from github import GitHubManager",
        "from data_handlers import ServerProcessor"
    ]
    
    success_count = 0
    
    for import_statement in test_imports:
        try:
            exec(import_statement)
            print(f"✅ {import_statement}")
            success_count += 1
        except Exception as e:
            print(f"❌ {import_statement}")
            print(f"   Ошибка: {e}")
    
    print(f"\n📊 Успешных импортов: {success_count}/{len(test_imports)}")
    return success_count == len(test_imports)

def check_file_structure():
    """Проверка структуры файлов"""
    print("\n📁 ПРОВЕРКА СТРУКТУРЫ ФАЙЛОВ")
    print("=" * 60)
    
    required_files = [
        "core/__init__.py",
        "core/base_parser.py",
        "core/config.py", 
        "core/driver_manager.py",
        "extractors/__init__.py",
        "extractors/dialog_extractor.py",
        "strategies/__init__.py",
        "strategies/error_recovery.py",
        "utils/__init__.py",
        "utils/metrics.py",
        "page_handlers/__init__.py",
        "page_handlers/page_navigator.py",
        "page_handlers/pagination_manager.py",
        "file_handlers/__init__.py",
        "file_handlers/config_parser.py",
        "file_handlers/file_updater.py",
        "github/__init__.py",
        "github/github_manager.py",
        "data_handlers/__init__.py",
        "data_handlers/server_processor.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - ОТСУТСТВУЕТ")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Отсутствует файлов: {len(missing_files)}")
        print("🛠️ Создайте недостающие файлы для корректной работы модульной системы")
        return False
    else:
        print("\n✅ Все необходимые файлы присутствуют")
        return True

def main():
    """Главная функция проверки"""
    print("🔧 ДИАГНОСТИКА МОДУЛЬНОЙ СИСТЕМЫ DNSCrypt Parser v2.0")
    print("=" * 70)
    
    # Проверяем структуру файлов
    structure_ok = check_file_structure()
    
    # Проверяем импорты модулей
    modules_ok = test_module_imports()
    
    # Детальное тестирование
    imports_ok = test_individual_imports()
    
    print("\n" + "=" * 70)
    print("🎯 ОБЩИЙ РЕЗУЛЬТАТ ДИАГНОСТИКИ")
    print("=" * 70)
    
    overall_status = structure_ok and modules_ok and imports_ok
    
    if overall_status:
        print("🎉 МОДУЛЬНАЯ СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К РАБОТЕ!")
        print("✅ Все компоненты инициализированы корректно")
        print("🚀 Можно запускать parser_new.py")
    else:
        print("⚠️ МОДУЛЬНАЯ СИСТЕМА ТРЕБУЕТ ИСПРАВЛЕНИЯ")
        print("❌ Обнаружены проблемы инициализации")
        print("🛠️ Исправьте указанные проблемы перед запуском")
        
        if not structure_ok:
            print("  📁 Проблемы со структурой файлов")
        if not modules_ok:
            print("  📦 Проблемы с импортами модулей")
        if not imports_ok:
            print("  🔗 Проблемы с детальными импортами")
    
    return overall_status

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)