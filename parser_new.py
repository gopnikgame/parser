#!/usr/bin/env python3
"""
DNSCrypt Parser v2.0 - Полностью модульная версия
Автоматизированный парсер для сбора публичных данных DNSCrypt серверов

🌐 Источник: https://dnscrypt.info/public-servers
🎯 Цель: Извлечение IP-адресов для обновления списков GitHub
📦 Архитектура: Полностью модульная система с обратной совместимостью

ИСПОЛЬЗОВАНИЕ:
  python parser_new.py  # Запуск модульной версии
"""

import sys
import os
import time
from pathlib import Path

# Добавляем текущую директорию в путь для импорта модулей
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Проверяем доступность модульной системы
try:
    # Импорты модульной системы
    from core import DNSCryptParser, ParserConfig
    from strategies.error_recovery import SmartErrorRecovery
    from utils.metrics import ParsingMetrics
    MODULAR_AVAILABLE = True
    print("🚀 Модульная система DNSCrypt Parser v2.0 загружена")
except ImportError as e:
    print(f"⚠️ Модульная система недоступна: {e}")
    MODULAR_AVAILABLE = False

# Импорт функций из старого parser.py для обратной совместимости
try:
    import parser as legacy_parser
    LEGACY_AVAILABLE = True
    print("📦 Legacy функции доступны для обратной совместимости")
except ImportError:
    LEGACY_AVAILABLE = False
    print("⚠️ Legacy функции недоступны")

def show_system_info():
    """Показать информацию о системе и доступных компонентах"""
    print("🔍 ИНФОРМАЦИЯ О СИСТЕМЕ:")
    print("-" * 50)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Платформа: {sys.platform}")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Проверяем доступность компонентов
    components = {
        "Модульная система v2.0": MODULAR_AVAILABLE,
        "Legacy функции": LEGACY_AVAILABLE,
        "Selenium": check_module('selenium'),
        "Requests": check_module('requests'),
        "PSUtil": check_module('psutil'),
        "DotEnv": check_module('dotenv')
    }
    
    print("\n📦 ДОСТУПНЫЕ КОМПОНЕНТЫ:")
    for component, available in components.items():
        status = "✅" if available else "❌"
        print(f"{status} {component}")
    
    # Проверяем конфигурацию
    github_token = os.getenv('GITHUB_TOKEN')
    chrome_headless = os.getenv('CHROME_HEADLESS', 'true')
    
    print("\n⚙️ КОНФИГУРАЦИЯ:")
    print(f"🔑 GitHub Token: {'✅ Настроен' if github_token else '❌ Отсутствует'}")
    print(f"🖥️ Chrome Headless: {chrome_headless}")
    
    return all(components.values())

def check_module(module_name):
    """Проверка доступности модуля"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def run_modular_parser():
    """Запуск модульного парсера v2.0"""
    if not MODULAR_AVAILABLE:
        print("❌ Модульная система недоступна")
        return False
    
    try:
        print("\n🎯 ЗАПУСК МОДУЛЬНОГО ПАРСЕРА v2.0")
        print("=" * 70)
        
        # Создаем и запускаем парсер с context manager
        with DNSCryptParser() as parser:
            # Запускаем полный цикл парсинга
            result = parser.run_full_parsing()
            
            if result['success']:
                print("\n🎉 МОДУЛЬНЫЙ ПАРСЕР ЗАВЕРШЕН УСПЕШНО!")
                
                # Выводим детальную статистику
                parsing_result = result.get('parsing_result', {})
                update_result = result.get('update_result', {})
                github_result = result.get('github_result', {})
                
                print(f"📊 Успешность парсинга: {parsing_result.get('success_rate', 0):.1f}%")
                print(f"📝 Обновлено файлов: {update_result.get('total_updated', 0)}")
                print(f"🚀 GitHub: {'✅' if github_result.get('success') else '❌'}")
                print(f"⏱️ Время выполнения: {result.get('duration', 0):.1f}с")
                
                return True
            else:
                print(f"\n❌ МОДУЛЬНЫЙ ПАРСЕР ЗАВЕРШЕН С ОШИБКОЙ:")
                print(f"   {result.get('error', 'Неизвестная ошибка')}")
                return False
                
    except Exception as e:
        print(f"❌ Критическая ошибка модульного парсера: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_legacy_parser():
    """Запуск legacy версии парсера"""
    if not LEGACY_AVAILABLE:
        print("❌ Legacy версия недоступна")
        return False
    
    try:
        print("\n🔄 ЗАПУСК LEGACY ПАРСЕРА")
        print("=" * 70)
        print("📦 Используется оригинальная версия parser.py")
        
        # Запускаем старую main функцию
        legacy_parser.main()
        
        print("✅ Legacy парсер завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка legacy парсера: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_hybrid_mode():
    """Гибридный режим - использует модульные компоненты с legacy логикой"""
    print("\n🔀 ЗАПУСК ГИБРИДНОГО РЕЖИМА")
    print("=" * 70)
    
    try:
        # Используем модульные компоненты, где возможно
        config = ParserConfig.from_env() if MODULAR_AVAILABLE else None
        metrics = ParsingMetrics() if MODULAR_AVAILABLE else None
        
        # Но используем legacy функции для основной логики
        if LEGACY_AVAILABLE:
            # Модифицируем legacy функции с улучшениями
            print("🔧 Применение модульных улучшений к legacy коду...")
            
            if config:
                print(f"✅ Конфигурация: таймауты {config.PAGE_LOAD_TIMEOUT}с")
            
            if metrics:
                session_id = metrics.start_session()
                print(f"📊 Метрики: сессия {session_id} начата")
            
            # Запускаем основную логику
            legacy_parser.main()
            
            if metrics:
                session = metrics.end_session()
                print(f"📊 Метрики: сессия завершена")
            
            return True
        else:
            print("❌ Legacy функции недоступны для гибридного режима")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка гибридного режима: {e}")
        return False

def choose_execution_mode():
    """Выбор режима выполнения на основе доступных компонентов"""
    print("\n🎯 ВЫБОР РЕЖИМА ВЫПОЛНЕНИЯ:")
    print("-" * 50)
    
    if MODULAR_AVAILABLE and LEGACY_AVAILABLE:
        print("🔀 Доступны все режимы:")
        print("   1. 🚀 Модульный парсер v2.0 (рекомендуется)")
        print("   2. 📦 Legacy парсер (обратная совместимость)")
        print("   3. 🔀 Гибридный режим (экспериментальный)")
        return "full"
    elif MODULAR_AVAILABLE:
        print("🚀 Доступен только модульный парсер v2.0")
        return "modular_only"
    elif LEGACY_AVAILABLE:
        print("📦 Доступен только legacy парсер")
        return "legacy_only"
    else:
        print("❌ Не доступен ни один режим выполнения")
        return "none"

def main():
    """Главная функция с интеллектуальным выбором режима"""
    start_time = time.time()
    
    # Показываем баннер
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    DNSCrypt Parser v2.0                          ║
    ║              🚀 Модульная + Legacy поддержка                     ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  🎯 Автоматический парсинг DNSCrypt серверов                     ║
    ║  🌐 Источник: https://dnscrypt.info/public-servers              ║
    ║  📦 Архитектура: Модульная система с обратной совместимостью    ║
    ║  🚀 GitHub: Автоматическая отправка обновлений                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    # Показываем информацию о системе
    system_ready = show_system_info()
    
    if not system_ready:
        print("\n⚠️ Система не полностью готова, но продолжаем...")
    
    # Определяем доступные режимы
    execution_mode = choose_execution_mode()
    
    if execution_mode == "none":
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Нет доступных режимов выполнения")
        print("📋 Проверьте установку зависимостей и целостность файлов")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🚀 НАЧАЛО ВЫПОЛНЕНИЯ")
    print("="*70)
    
    success = False
    
    # Выполняем парсинг в зависимости от доступного режима
    if execution_mode == "full":
        # Пытаемся все режимы по порядку приоритета
        print("🎯 Приоритет 1: Модульный парсер v2.0")
        success = run_modular_parser()
        
        if not success:
            print("\n🔄 Приоритет 2: Legacy парсер")
            success = run_legacy_parser()
            
        if not success:
            print("\n🔀 Приоритет 3: Гибридный режим")
            success = run_hybrid_mode()
            
    elif execution_mode == "modular_only":
        success = run_modular_parser()
        
    elif execution_mode == "legacy_only":
        success = run_legacy_parser()
    
    # Финальный отчет
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ")
    print("="*70)
    
    if success:
        print("🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"⏱️ Общее время выполнения: {duration:.1f} секунд")
        print(f"🎯 Использованный режим: {execution_mode}")
    else:
        print("❌ ПАРСИНГ ЗАВЕРШЕН С ОШИБКОЙ!")
        print("📋 Все доступные методы были испробованы")
        print("🔍 Проверьте логи выше для диагностики проблем")
        sys.exit(1)
    
    print("="*70)

# Функции для обратной совместимости
def enhanced_get_all_server_rows(driver):
    """Обертка для совместимости со старым кодом"""
    if MODULAR_AVAILABLE:
        from data_handlers.server_processor import ServerProcessor
        from core.config import ParserConfig
        from extractors.dialog_extractor import AdvancedDialogExtractor
        
        config = ParserConfig.from_env()
        dialog_extractor = AdvancedDialogExtractor(driver, config)
        processor = ServerProcessor(driver, config, dialog_extractor)
        return processor._get_server_rows_enhanced()
    elif LEGACY_AVAILABLE:
        return legacy_parser.enhanced_get_all_server_rows(driver)
    else:
        raise RuntimeError("Ни модульная, ни legacy версия недоступна")

def extract_server_info_from_row_enhanced(driver, row, server_name):
    """Улучшенная обертка для извлечения информации"""
    if MODULAR_AVAILABLE:
        from extractors.dialog_extractor import AdvancedDialogExtractor
        from core.config import ParserConfig
        
        config = ParserConfig.from_env()
        extractor = AdvancedDialogExtractor(driver, config)
        return extractor.extract_server_info_smart(row, server_name)
    elif LEGACY_AVAILABLE:
        return legacy_parser.extract_server_info_from_row(driver, row)
    else:
        raise RuntimeError("Ни модульная, ни legacy версия недоступны")

# Экспорт функций для обратной совместимости
if LEGACY_AVAILABLE:
    # Экспортируем все функции из legacy парсера
    globals().update({name: getattr(legacy_parser, name) 
                     for name in dir(legacy_parser) 
                     if not name.startswith('_') and callable(getattr(legacy_parser, name))})

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прерывание пользователем (Ctrl+C)")
        print("🧹 Выполняется очистка ресурсов...")
        
        # Пытаемся выполнить очистку
        try:
            if MODULAR_AVAILABLE:
                # Очистка через модульную систему
                pass
            elif LEGACY_AVAILABLE:
                # Очистка через legacy функции
                legacy_parser.kill_existing_chrome()
        except:
            pass
        