"""
Процессор серверов для извлечения и обработки данных
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Dict, List, Any
from ..core.config import ParserConfig
from ..extractors.dialog_extractor import AdvancedDialogExtractor

class ServerProcessor:
    """Процессор для обработки серверов с сайта"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig, dialog_extractor: AdvancedDialogExtractor):
        self.driver = driver
        self.config = config
        self.dialog_extractor = dialog_extractor
        self.processing_stats = {
            'total_found_rows': 0,
            'target_servers_found': 0,
            'successful_extractions': 0,
            'failed_extractions': 0
        }
    
    def process_servers(self, target_servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Основная функция обработки серверов"""
        print(f"🎯 Начало обработки {len(target_servers)} целевых серверов")
        
        # Получаем все строки серверов с сайта
        all_rows = self._get_server_rows_enhanced()
        if not all_rows:
            print("❌ Не удалось получить строки серверов")
            return self._create_empty_result("Не удалось найти строки серверов")
        
        print(f"✅ Найдено {len(all_rows)} строк на сайте")
        self.processing_stats['total_found_rows'] = len(all_rows)
        
        # Создаем индекс имен целевых серверов
        target_names = {server['name'] for server in target_servers}
        print(f"🎯 Ищем {len(target_names)} целевых серверов")
        
        # Создаем индекс строк по именам серверов
        row_index = self._create_row_index(all_rows)
        
        # Обрабатываем каждый целевой сервер
        servers_data = {}
        processed_count = 0
        
        for server in target_servers:
            server_name = server['name']
            processed_count += 1
            
            print(f"\n[{processed_count}/{len(target_servers)}] Обрабатываем {server_name}...")
            
            # Ищем строку для этого сервера
            row = row_index.get(server_name)
            if not row:
                print(f"⚠️ Строка не найдена для {server_name}")
                self.processing_stats['failed_extractions'] += 1
                continue
            
            self.processing_stats['target_servers_found'] += 1
            
            # Извлекаем информацию о сервере
            try:
                start_time = time.time()
                info = self.dialog_extractor.extract_server_info_smart(row, server_name)
                duration = time.time() - start_time
                
                if info and info.get('ip'):
                    servers_data[server_name] = info
                    self.processing_stats['successful_extractions'] += 1
                    print(f"✅ {server_name} -> {info['ip']} ({info['protocol']}) [{duration:.1f}s]")
                else:
                    self.processing_stats['failed_extractions'] += 1
                    print(f"❌ Не удалось получить данные для {server_name} [{duration:.1f}s]")
                
            except Exception as e:
                self.processing_stats['failed_extractions'] += 1
                print(f"❌ Ошибка обработки {server_name}: {e}")
            
            # Пауза между серверами для человекоподобного поведения
            time.sleep(random.uniform(0.5, 2.0))
        
        # Подготавливаем результат
        return self._create_result(servers_data, target_servers)
    
    def _get_server_rows_enhanced(self) -> List:
        """Улучшенное получение всех строк серверов с множественными стратегиями"""
        print("🔍 УЛУЧШЕННЫЙ поиск строк серверов...")
        
        # Прокрутка страницы для загрузки lazy-loading контента
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
        
        # Выводим примеры найденных строк
        self._print_row_examples(unique_rows[:5])
        
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
    
    def _print_row_examples(self, example_rows):
        """Вывод примеров найденных строк"""
        for i, row in enumerate(example_rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.CSS_SELECTOR, "div[role='cell'], .cell")
                
                if cells:
                    first_cell = cells[0].text.strip()
                    print(f"   Пример {i+1}: {first_cell}")
            except:
                continue
    
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
    
    def _create_result(self, servers_data: Dict[str, Any], target_servers: List[Dict]) -> Dict[str, Any]:
        """Создание результата обработки"""
        total_processed = len(target_servers)
        successful = len(servers_data)
        success_rate = (successful / total_processed * 100) if total_processed > 0 else 0
        
        result = {
            'servers_data': servers_data,
            'total_processed': total_processed,
            'successful': successful,
            'failed': total_processed - successful,
            'success_rate': success_rate,
            'processing_stats': self.processing_stats.copy(),
            'cache_hits': 0,  # Будет заполнено в dialog_extractor
            'recovery_attempts': 0  # Будет заполнено в error_recovery
        }
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        print(f"   Всего строк найдено: {self.processing_stats['total_found_rows']}")
        print(f"   Целевых серверов найдено: {self.processing_stats['target_servers_found']}")
        print(f"   Успешно извлечено: {self.processing_stats['successful_extractions']}")
        print(f"   Неудачных попыток: {self.processing_stats['failed_extractions']}")
        print(f"   Общий процент успеха: {success_rate:.1f}%")
        
        return result
    
    def _create_empty_result(self, error_message: str) -> Dict[str, Any]:
        """Создание пустого результата с ошибкой"""
        return {
            'servers_data': {},
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0,
            'error': error_message,
            'processing_stats': self.processing_stats.copy()
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики обработки"""
        return self.processing_stats.copy()