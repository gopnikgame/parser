#!/usr/bin/env python3
"""
DNSCrypt Parser v2.0 - Полностью модульная версия
Автоматизированный парсер для сбора публичных данных DNSCrypt серверов

🌐 Источник: https://dnscrypt.info/public-servers
🎯 Цель: Извлечение IP-адресов для обновления списков GitHub
📦 Архитектура: Полностью модульная система
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
    from core import DNSCryptParser
    MODULAR_AVAILABLE = True
    print("🚀 Модульная система DNSCrypt Parser v2.0 загружена")
except ImportError as e:
    print(f"⚠️ Модульная система недоступна: {e}")
    MODULAR_AVAILABLE = False

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

def main():
    """Главная функция"""
    start_time = time.time()
    
    # Показываем баннер
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    DNSCrypt Parser v2.0                          ║
    ║              🚀 Модульная система                                ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  🎯 Автоматический парсинг DNSCrypt серверов                     ║
    ║  🌐 Источник: https://dnscrypt.info/public-servers              ║
    ║  📦 Архитектура: Полностью модульная система                    ║
    ║  🚀 GitHub: Автоматическая отправка обновлений                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    # Показываем информацию о системе
    system_ready = show_system_info()
    
    if not system_ready:
        print("\n⚠️ Система не полностью готова, но продолжаем...")
        # Можно добавить sys.exit(1) если критичные компоненты отсутствуют
    
    if not MODULAR_AVAILABLE:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Модульная система не найдена.")
        print("📋 Проверьте установку зависимостей и целостность файлов.")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🚀 НАЧАЛО ВЫПОЛНЕНИЯ")
    print("="*70)
    
    success = run_modular_parser()
    
    # Финальный отчет
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ")
    print("="*70)
    
    if success:
        print("🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"⏱️ Общее время выполнения: {duration:.1f} секунд")
    else:
        print("❌ ПАРСИНГ ЗАВЕРШЕН С ОШИБКОЙ!")
        print("🔍 Проверьте логи выше для диагностики проблем")
        sys.exit(1)
    
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прерывание пользователем (Ctrl+C)")
        print("🧹 Выполняется очистка ресурсов...")
        # Здесь можно добавить логику для корректного завершения работы,
        # например, закрытие драйвера, если он был инициализирован.
        sys.exit(130)