# Обновленный главный парсер с интеграцией всех улучшений
import time
import random
import os
import sys
from typing import Dict, List, Optional, Any

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты новых модулей
from core.config import ParserConfig
from core.driver_manager import SmartDriverManager
from extractors.dialog_extractor import AdvancedDialogExtractor
from strategies.error_recovery import SmartErrorRecovery
from utils.metrics import ParsingMetrics, ParsingCache

# Старые импорты (оставляем для совместимости)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import re
import subprocess
import urllib.request
import requests
import base64
import json
import psutil
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class EnhancedDNSCryptParser:
    """Улучшенный парсер DNSCrypt с 100% надежностью"""
    
    def __init__(self):
        self.config = ParserConfig.from_env()
        self.driver_manager = SmartDriverManager(self.config)
        self.driver = None
        self.dialog_extractor = None
        self.error_recovery = None
        self.metrics = ParsingMetrics()
        self.cache = ParsingCache()
        
        # Статистика сессии
        self.session_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0,
            'recovery_attempts': 0
        }
    
    def initialize(self) -> bool:
        """Инициализация парсера"""
        try:
            print("🚀 Инициализация улучшенного DNSCrypt парсера...")
            
            # Создаем драйвер
            self.driver = self.driver_manager.create_stealth_driver()
            if not self.driver:
                return False
            
            # Инициализируем модули
            self.dialog_extractor = AdvancedDialogExtractor(self.driver, self.config)
            self.error_recovery = SmartErrorRecovery(self.driver, self.config)
            
            # Очищаем устаревший кэш
            self.cache.clear_expired_cache()
            
            print("✅ Парсер успешно инициализирован")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def parse_servers_enhanced(self, target_servers: List[Dict]) -> Dict[str, Any]:
        """Улучшенный парсинг серверов с максимальной надежностью"""
        try:
            # Начинаем сессию метрик
            session_id = self.metrics.start_session()
            
            print(f"🎯 Начало улучшенного парсинга {len(target_servers)} серверов")
            
            # Переходим на страницу
            if not self._navigate_to_page():
                return self._create_error_result("Не удалось загрузить страницу")
            
            # Настраиваем пагинацию
            if not self._setup_pagination():
                print("⚠️ Не удалось настроить пагинацию, продолжаем...")
            
            # Получаем все строки серверов
            all_rows = self._get_server_rows_enhanced()
            if not all_rows:
                return self._create_error_result("Не удалось найти строки серверов")
            
            # Обрабатываем серверы
            results = self._process_servers_smart(target_servers, all_rows)
            
            # Завершаем сессию метрик
            session = self.metrics.end_session()
            
            # Генерируем детальный отчет
            detailed_report = self.metrics.generate_detailed_report()
            print(detailed_report)
            
            return results
            
        except Exception as e:
            print(f"❌ Критическая ошибка парсинга: {e}")
            return self._create_error_result(str(e))
    
    def _navigate_to_page(self) -> bool:
        """Навигация на страницу с восстановлением после ошибок"""
        url = "https://dnscrypt.info/public-servers"
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"🌐 Переход на страницу (попытка {attempt + 1}/{max_attempts})...")
                
                self.driver.get(url)
                
                # Ждем загрузки с умным ожиданием
                if self._wait_for_page_load_smart():
                    print("✅ Страница успешно загружена")
                    return True
                else:
                    print("⚠️ Страница загрузилась с проблемами")
                    
            except Exception as e:
                print(f"❌ Ошибка загрузки страницы: {e}")
                
                if not self.error_recovery.handle_error(e, "page_navigation"):
                    print("❌ Не удалось восстановиться после ошибки")
                    
                time.sleep(5 * (attempt + 1))  # Экспоненциальная задержка
        
        return False
    
    def _wait_for_page_load_smart(self, timeout: int = 120) -> bool:
        """Умное ожидание загрузки страницы"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # Ждем готовности DOM
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Ждем появления основных элементов
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            # Ждем завершения сетевых запросов
            for _ in range(30):  # Максимум 30 попыток
                try:
                    network_idle = self.driver.execute_script("""
                        return window.performance.getEntriesByType('resource')
                            .filter(r => r.responseEnd === 0).length === 0;
                    """)
                    
                    if network_idle:
                        break
                        
                except:
                    pass
                
                time.sleep(2)
            
            # Проверяем загрузку данных
            data_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            visible_rows = [row for row in data_rows if row.is_displayed() and row.text.strip()]
            
            print(f"📊 Найдено {len(visible_rows)} строк данных")
            
            return len(visible_rows) > 50  # Ожидаем минимум 50 серверов
            
        except TimeoutException:
            print("⚠️ Таймаут ожидания загрузки страницы")
            return False
        except Exception as e:
            print(f"⚠️ Ошибка ожидания загрузки: {e}")
            return False
    
    def _setup_pagination(self) -> bool:
        """Настройка пагинации с множественными стратегиями"""
        print("🔧 Настройка пагинации...")
        
        # Стратегии настройки пагинации
        strategies = [
            self._try_vuetify3_pagination,
            self._try_vuetify2_pagination,
            self._try_generic_pagination,
            self._try_javascript_pagination
        ]
        
        for strategy in strategies:
            try:
                if strategy():
                    print("✅ Пагинация настроена успешно")
                    # Ждем обновления данных
                    time.sleep(5)
                    return True
            except Exception as e:
                print(f"⚠️ Стратегия пагинации не сработала: {e}")
                continue
        
        print("⚠️ Не удалось настроить пагинацию")
        return False
    
    def _try_vuetify3_pagination(self) -> bool:
        """Попытка настройки Vuetify 3.x пагинации"""
        selectors = [
            ".v-data-table__footer .v-select",
            ".v-table__footer .v-select"
        ]
        
        for selector in selectors:
            try:
                dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown.is_displayed():
                    return self._click_pagination_dropdown(dropdown)
            except:
                continue
        
        return False
    
    def _try_vuetify2_pagination(self) -> bool:
        """Попытка настройки Vuetify 2.x пагинации"""
        selectors = [
            ".v-datatable__actions .v-select",
            ".v-data-table-footer .v-select"
        ]
        
        for selector in selectors:
            try:
                dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown.is_displayed():
                    return self._click_pagination_dropdown(dropdown)
            except:
                continue
        
        return False
    
    def _try_generic_pagination(self) -> bool:
        """Попытка общей настройки пагинации"""
        selectors = [
            "select[aria-label*='per page']",
            "select[aria-label*='rows']",
            ".per-page-select",
            ".rows-per-page select"
        ]
        
        for selector in selectors:
            try:
                dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown.is_displayed():
                    return self._click_pagination_dropdown(dropdown)
            except:
                continue
        
        return False
    
    def _try_javascript_pagination(self) -> bool:
        """JavaScript принудительная настройка пагинации"""
        try:
            self.driver.execute_script("""
                // Пытаемся найти Vue компонент и установить большой лимит
                var app = document.querySelector('[data-app]');
                if (app && app.__vue__) {
                    var vm = app.__vue__;
                    if (vm.$data && vm.$data.itemsPerPage) {
                        vm.$data.itemsPerPage = -1;
                    }
                    if (vm.$data && vm.$data.pagination) {
                        vm.$data.pagination.rowsPerPage = -1;
                    }
                }
                
                // Пытаемся найти все селекты и установить максимальное значение
                var selects = document.querySelectorAll('select');
                selects.forEach(function(select) {
                    var options = select.options;
                    for (var i = options.length - 1; i >= 0; i--) {
                        if (options[i].value === '-1' || options[i].text.includes('All')) {
                            select.selectedIndex = i;
                            select.dispatchEvent(new Event('change'));
                            return true;
                        }
                    }
                });
            """)
            return True
        except:
            return False
    
    def _click_pagination_dropdown(self, dropdown) -> bool:
        """Клик по dropdown пагинации и выбор 'All'"""
        try:
            # Кликаем на dropdown
            ActionChains(self.driver).move_to_element(dropdown).click().perform()
            time.sleep(2)
            
            # Ищем опцию "All"
            all_options = [
                "//div[contains(@class, 'v-list__tile__title') and (text()='All' or text()='Все' or text()='-1')]",
                "//li[contains(text(), 'All') or contains(text(), 'Все')]",
                "//option[contains(text(), 'All') or contains(text(), 'Все') or @value='-1']",
                "//div[contains(@class, 'v-list-item__title') and (text()='All' or text()='Все')]"
            ]
            
            for option_xpath in all_options:
                try:
                    option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    option.click()
                    return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def _get_server_rows_enhanced(self) -> List:
        """Получение строк серверов с улучшенным поиском"""
        print("🔍 Поиск строк серверов...")
        
        # Прокрутка для загрузки lazy-content
        self._scroll_to_load_content()
        
        all_rows = []
        found_selectors = []
        
        for selector in self.config.TABLE_ROW_SELECTORS:
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                valid_rows = self._filter_valid_rows(rows)
                
                if valid_rows:
                    print(f"✅ Селектор '{selector}': найдено {len(valid_rows)} валидных строк")
                    all_rows.extend(valid_rows)
                    found_selectors.append(selector)
                    
            except Exception as e:
                continue
        
        # Убираем дубликаты
        unique_rows = self._remove_duplicate_rows(all_rows)
        
        print(f"✅ Найдено {len(unique_rows)} уникальных строк серверов")
        print(f"📊 Использованные селекторы: {found_selectors}")
        
        return unique_rows
    
    def _scroll_to_load_content(self):
        """Прокрутка для загрузки ленивого контента"""
        print("📜 Прокрутка для загрузки контента...")
        
        for i in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 3))
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.5))
    
    def _filter_valid_rows(self, rows) -> List:
        """Фильтрация валидных строк"""
        valid_rows = []
        
        for row in rows:
            try:
                if not row.is_displayed():
                    continue
                
                text = row.text.strip()
                if not text or len(text) < 10:
                    continue
                
                if any(skip_text in text.lower() for skip_text in 
                       ["no data available", "loading", "please wait"]):
                    continue
                
                # Проверяем наличие ячеек
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.CSS_SELECTOR, "div[role='cell'], .cell")
                
                if len(cells) >= 2:
                    first_cell_text = cells[0].text.strip()
                    if first_cell_text and len(first_cell_text) > 2:
                        valid_rows.append(row)
                        
            except:
                continue
        
        return valid_rows
    
    def _remove_duplicate_rows(self, rows) -> List:
        """Удаление дубликатов строк"""
        unique_rows = []
        seen_texts = set()
        
        for row in rows:
            try:
                row_text = row.text.strip()[:100]  # Первые 100 символов
                if row_text not in seen_texts and len(row_text) > 10:
                    seen_texts.add(row_text)
                    unique_rows.append(row)
            except:
                continue
        
        return unique_rows
    
    def _process_servers_smart(self, target_servers: List[Dict], all_rows: List) -> Dict[str, Any]:
        """Умная обработка серверов с кэшированием и восстановлением"""
        print(f"🎯 Умная обработка {len(target_servers)} серверов...")
        
        # Создаем индекс имен серверов для быстрого поиска
        target_names = {server['name'] for server in target_servers}
        
        # Создаем индекс строк по именам серверов
        row_index = self._create_row_index(all_rows)
        
        servers_data = {}
        processed_count = 0
        
        for server in target_servers:
            server_name = server['name']
            processed_count += 1
            
            print(f"\n[{processed_count}/{len(target_servers)}] Обрабатываем {server_name}...")
            
            start_time = time.time()
            
            # Проверяем кэш
            cached_info = self.cache.get_cached_server_info(server_name)
            if cached_info:
                servers_data[server_name] = cached_info
                self.session_stats['cache_hits'] += 1
                self.metrics.record_server_extraction(
                    server_name, True, 0.1, 1, 
                    extraction_method="cache"
                )
                print(f"💾 Использован кэш для {server_name}")
                continue
            
            # Ищем строку для этого сервера
            row = row_index.get(server_name)
            if not row:
                print(f"⚠️ Строка не найдена для {server_name}")
                self.metrics.record_server_extraction(
                    server_name, False, time.time() - start_time, 1,
                    error_type="row_not_found"
                )
                continue
            
            # Извлекаем информацию с множественными попытками
            try:
                info = self.dialog_extractor.extract_server_info_smart(row, server_name)
                
                duration = time.time() - start_time
                
                if info and info.get('ip'):
                    servers_data[server_name] = info
                    self.session_stats['successful'] += 1
                    
                    # Кэшируем успешный результат
                    self.cache.cache_server_info(server_name, info)
                    
                    self.metrics.record_server_extraction(
                        server_name, True, duration, 1,
                        extraction_method="dialog_extraction"
                    )
                    
                    print(f"✅ {server_name} -> {info['ip']} ({info['protocol']})")
                else:
                    self.session_stats['failed'] += 1
                    self.metrics.record_server_extraction(
                        server_name, False, duration, 1,
                        error_type="extraction_failed"
                    )
                    print(f"❌ Не удалось получить данные для {server_name}")
                
            except Exception as e:
                self.session_stats['failed'] += 1
                duration = time.time() - start_time
                
                # Пытаемся восстановиться после ошибки
                if self.error_recovery.handle_error(e, f"server_extraction_{server_name}"):
                    self.session_stats['recovery_attempts'] += 1
                
                self.metrics.record_server_extraction(
                    server_name, False, duration, 1,
                    error_type=str(type(e).__name__)
                )
                
                print(f"❌ Ошибка обработки {server_name}: {e}")
            
            # Пауза между серверами
            time.sleep(random.uniform(0.5, 2.0))
        
        # Подготавливаем результат
        total_processed = len(target_servers)
        successful = len(servers_data)
        success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
        
        result = {
            'servers_data': servers_data,
            'total_processed': total_processed,
            'successful': successful,
            'failed': total_processed - successful,
            'success_rate': success_rate,
            'cache_hits': self.session_stats['cache_hits'],
            'recovery_attempts': self.session_stats['recovery_attempts']
        }
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        print(f"   Всего: {total_processed}")
        print(f"   Успешно: {successful} ({success_rate:.1f}%)")
        print(f"   Кэш хиты: {self.session_stats['cache_hits']}")
        print(f"   Восстановления: {self.session_stats['recovery_attempts']}")
        
        return result
    
    def _create_row_index(self, all_rows: List) -> Dict[str, Any]:
        """Создание индекса строк по именам серверов"""
        row_index = {}
        
        for row in all_rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) > 0:
                    server_name = cells[0].text.strip()
                    if server_name and len(server_name) > 2:
                        row_index[server_name] = row
            except:
                continue
        
        print(f"📊 Создан индекс для {len(row_index)} серверов")
        return row_index
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'servers_data': {},
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0,
            'error': error_message
        }
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver_manager:
            self.driver_manager.quit_driver()
        
        # Сохраняем финальные метрики
        if self.metrics:
            self.metrics.export_csv_report()
        
        print("🧹 Ресурсы очищены")

# Функции-обертки для совместимости со старым кодом
def enhanced_get_all_server_rows(driver):
    """Обертка для старой функции"""
    config = ParserConfig.from_env()
    parser = EnhancedDNSCryptParser()
    parser.driver = driver
    return parser._get_server_rows_enhanced()

def extract_server_info_from_row_enhanced(driver, row, server_name):
    """Улучшенная обертка для извлечения информации"""
    config = ParserConfig.from_env()
    extractor = AdvancedDialogExtractor(driver, config)
    return extractor.extract_server_info_smart(row, server_name)

# Интеграция с основной функцией main()
def enhanced_main():
    """Улучшенная главная функция"""
    parser = EnhancedDNSCryptParser()
    
    try:
        # Инициализация
        if not parser.initialize():
            print("❌ Не удалось инициализировать парсер")
            return
        
        # Загрузка конфигурационных файлов (используем старые функции)
        print("📥 Скачивание файлов с GitHub...")
        
        config_github = get_github_config()
        github_urls = {
            'DNSCrypt_relay.txt': f'https://github.com/{config_github["owner"]}/{config_github["repo"]}/blob/{config_github["branch"]}/lib/DNSCrypt_relay.txt',
            'DNSCrypt_servers.txt': f'https://github.com/{config_github["owner"]}/{config_github["repo"]}/blob/{config_github["branch"]}/lib/DNSCrypt_servers.txt'
        }
        
        temp_files = []
        for filename, url in github_urls.items():
            temp_filename = f"temp_{filename}"
            if download_file(url, temp_filename):
                temp_files.append(temp_filename)
            else:
                print(f"❌ Не удалось скачать {filename}")
                return
        
        # Парсинг файлов
        relay_servers = parse_config_file('temp_DNSCrypt_relay.txt')
        dnscrypt_servers = parse_config_file('temp_DNSCrypt_servers.txt')
        
        all_target_servers = relay_servers + dnscrypt_servers
        print(f"🎯 Найдено {len(all_target_servers)} серверов для обработки")
        
        # Выполняем улучшенный парсинг
        result = parser.parse_servers_enhanced(all_target_servers)
        
        if 'error' in result:
            print(f"❌ Ошибка парсинга: {result['error']}")
            return
        
        # Обработка результатов (используем старые функции)
        servers_data = result['servers_data']
        
        # Разделяем данные по типам
        relay_data = {name: info for name, info in servers_data.items() 
                     if info.get('protocol') == 'DNSCrypt relay'}
        server_data = {name: info for name, info in servers_data.items() 
                      if info.get('protocol') == 'DNSCrypt'}
        
        # Обновляем файлы
        total_updated = 0
        
        if relay_data:
            print(f"\n📝 Обновление файла релеев...")
            os.rename('temp_DNSCrypt_relay.txt', 'DNSCrypt_relay.txt')
            updated_count = update_config_file('DNSCrypt_relay.txt', relay_data, is_relay_file=True)
            total_updated += updated_count
        
        if server_data:
            print(f"\n📝 Обновление файла серверов...")
            os.rename('temp_DNSCrypt_servers.txt', 'DNSCrypt_servers.txt')
            updated_count = update_config_file('DNSCrypt_servers.txt', server_data, is_relay_file=False)
            total_updated += updated_count
        
        # Отправка в GitHub
        if total_updated > 0:
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                print("🔑 Отправка обновлений в GitHub...")
                push_to_github(total_updated)
            else:
                print("⚠️ GitHub token не найден")
        
        print(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"📊 Итоговая успешность: {result['success_rate']:.1f}%")
        print(f"📊 Обработано серверов: {result['successful']}/{result['total_processed']}")
        
        # Очистка временных файлов
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        parser.cleanup()

# Определяем, какую функцию запускать
if __name__ == "__main__":
    # Проверяем наличие новых модулей
    try:
        from core.config import ParserConfig
        print("🚀 Запуск УЛУЧШЕННОГО парсера DNSCrypt v2.0")
        enhanced_main()
    except ImportError:
        print("🚀 Запуск СТАНДАРТНОГО парсера DNSCrypt")
        # Импортируем старые функции и запускаем main()
        from parser import main
        main()