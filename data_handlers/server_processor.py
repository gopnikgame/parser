"""
Процессор серверов для извлечения и обработки данных
"""
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Dict, List, Any, Optional, Tuple

# Используем относительные импорты для лучшей совместимости
try:
    from ..core.config import ParserConfig
    from ..extractors.dialog_extractor import AdvancedDialogExtractor
except ImportError:
    # Fallback для случаев когда относительный импорт не работает
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import ParserConfig
    from extractors.dialog_extractor import AdvancedDialogExtractor

class ServerProcessor:
    """Обработчик данных серверов - ОБНОВЛЕННАЯ ВЕРСИЯ v2.1"""
    
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
        
        # Регулярные выражения для очистки и валидации данных
        self.patterns = {
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'server_name': re.compile(r'^[a-zA-Z0-9\-_.]+$'),
            'domain_name': re.compile(r'[a-zA-Z0-9\-_.]+\.[a-zA-Z]{2,}'),
            'clean_text': re.compile(r'[^\w\-_.]'),
            'protocol_indicators': {
                'relay': re.compile(r'relay|анонимайзер', re.IGNORECASE),
                'doh': re.compile(r'doh|dns-over-https|https', re.IGNORECASE),
                'dot': re.compile(r'dot|dns-over-tls|tls', re.IGNORECASE),
                'dnscrypt': re.compile(r'dnscrypt|криптование', re.IGNORECASE)
            }
        }
        
        # Списки известных серверов для лучшей классификации
        self.known_servers = {
            'cloudflare': ['1.1.1.1', '1.0.0.1'],
            'quad9': ['9.9.9.9', '149.112.112.112'],
            'google': ['8.8.8.8', '8.8.4.4'],
            'opendns': ['208.67.222.222', '208.67.220.220']
        }
        
        # Счетчики для статистики
        self.stats = {
            'processed': 0,
            'valid': 0,
            'duplicates': 0,
            'errors': 0,
            'protocols': {}
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
    
    def process_servers_batch(self, servers_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Обработка партии серверов с разделением на серверы и релеи"""
        print(f"🔄 Обработка партии из {len(servers_data)} серверов...")
        
        processed_servers = []
        processed_relays = []
        seen_items = set()
        
        for i, server_data in enumerate(servers_data):
            try:
                self.stats['processed'] += 1
                
                # Очищаем и валидируем данные
                cleaned_server = self._clean_server_data(server_data)
                if not cleaned_server:
                    self.stats['errors'] += 1
                    continue
                
                # Проверяем на дубликаты
                server_key = self._generate_server_key(cleaned_server)
                if server_key in seen_items:
                    self.stats['duplicates'] += 1
                    continue
                
                seen_items.add(server_key)
                
                # Определяем тип (сервер или релей)
                if self._is_relay(cleaned_server):
                    processed_relays.append(cleaned_server)
                else:
                    processed_servers.append(cleaned_server)
                
                self.stats['valid'] += 1
                
                # Обновляем статистику протоколов
                protocol = cleaned_server.get('protocol', 'Unknown')
                self.stats['protocols'][protocol] = self.stats['protocols'].get(protocol, 0) + 1
                
            except Exception as e:
                print(f"⚠️ Ошибка обработки сервера {i}: {e}")
                self.stats['errors'] += 1
                continue
        
        print(f"✅ Обработано: {len(processed_servers)} серверов, {len(processed_relays)} релеев")
        self._print_processing_stats()
        
        return processed_servers, processed_relays
    
    def _clean_server_data(self, raw_data: Dict) -> Optional[Dict]:
        """Очистка и нормализация данных сервера"""
        try:
            if not isinstance(raw_data, dict):
                return None
            
            cleaned = {
                'name': '',
                'ip': '',
                'protocol': 'DNSCrypt',
                'description': '',
                'source_method': raw_data.get('extraction_method', 'unknown')
            }
            
            # Очищаем имя сервера
            raw_name = str(raw_data.get('name', '')).strip()
            if raw_name:
                cleaned['name'] = self._clean_server_name(raw_name)
            
            # Извлекаем и валидируем IP адрес
            raw_ip = str(raw_data.get('ip', '')).strip()
            if raw_ip:
                cleaned['ip'] = self._extract_ip_address(raw_ip)
            
            # Если нет IP, пытаемся извлечь из имени или других полей
            if not cleaned['ip']:
                for field_name, field_value in raw_data.items():
                    if isinstance(field_value, str):
                        ip_match = self.patterns['ip_address'].search(field_value)
                        if ip_match:
                            cleaned['ip'] = ip_match.group()
                            break
            
            # Определяем протокол
            cleaned['protocol'] = self._determine_protocol(raw_data)
            
            # Формируем описание
            cleaned['description'] = self._generate_description(raw_data, cleaned)
            
            # Валидация финального результата
            if not cleaned['name'] and not cleaned['ip']:
                return None
            
            # Если нет имени, генерируем его из IP или других данных
            if not cleaned['name']:
                if cleaned['ip']:
                    cleaned['name'] = f"server_{cleaned['ip'].replace('.', '_')}"
                else:
                    return None
            
            return cleaned
            
        except Exception as e:
            print(f"⚠️ Ошибка очистки данных сервера: {e}")
            return None
    
    def _clean_server_name(self, raw_name: str) -> str:
        """Очистка имени сервера"""
        try:
            # Убираем лишние символы и пробелы
            name = raw_name.strip()
            
            # Удаляем специальные символы кроме разрешенных
            name = re.sub(r'[^\w\-_.]', '', name)
            
            # Убираем множественные подчеркивания и точки
            name = re.sub(r'[_]{2,}', '_', name)
            name = re.sub(r'[.]{2,}', '.', name)
            
            # Убираем начальные и конечные спецсимволы
            name = name.strip('._-')
            
            # Ограничиваем длину
            if len(name) > 50:
                name = name[:50]
            
            return name
            
        except Exception:
            return raw_name[:50] if raw_name else ''
    
    def _extract_ip_address(self, text: str) -> str:
        """Извлечение IP адреса из текста"""
        try:
            match = self.patterns['ip_address'].search(text)
            if match:
                ip = match.group()
                # Простая валидация IP
                parts = ip.split('.')
                if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
                    return ip
            return ''
        except Exception:
            return ''
    
    def _determine_protocol(self, raw_data: Dict) -> str:
        """Определение протокола сервера"""
        try:
            # Проверяем явно указанный протокол
            explicit_protocol = raw_data.get('protocol', '').strip()
            if explicit_protocol:
                return explicit_protocol
            
            # Анализируем все текстовые поля на наличие индикаторов протокола
            all_text = ' '.join(str(value) for value in raw_data.values() if isinstance(value, str)).lower()
            
            # Проверяем паттерны в порядке приоритета
            if self.patterns['protocol_indicators']['relay'].search(all_text):
                return 'DNSCrypt relay'
            elif self.patterns['protocol_indicators']['doh'].search(all_text):
                return 'DoH'
            elif self.patterns['protocol_indicators']['dot'].search(all_text):
                return 'DoT'
            elif self.patterns['protocol_indicators']['dnscrypt'].search(all_text):
                return 'DNSCrypt'
            
            # Дефолтный протокол
            return 'DNSCrypt'
            
        except Exception:
            return 'DNSCrypt'
    
    def _is_relay(self, server_data: Dict) -> bool:
        """Определение является ли сервер релеем"""
        try:
            protocol = server_data.get('protocol', '').lower()
            name = server_data.get('name', '').lower()
            description = server_data.get('description', '').lower()
            
            # Явные индикаторы релея
            relay_indicators = ['relay', 'релей', 'анонимайзер', 'anonymizer']
            
            for indicator in relay_indicators:
                if (indicator in protocol or 
                    indicator in name or 
                    indicator in description):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _generate_server_key(self, server_data: Dict) -> str:
        """Генерация уникального ключа сервера для проверки дубликатов"""
        try:
            name = server_data.get('name', '').lower().strip()
            ip = server_data.get('ip', '').strip()
            
            # Используем комбинацию имени и IP как ключ
            if name and ip:
                return f"{name}_{ip}"
            elif ip:
                return f"ip_{ip}"
            elif name:
                return f"name_{name}"
            else:
                return f"unknown_{hash(str(server_data))}"
                
        except Exception:
            return f"error_{hash(str(server_data))}"
    
    def _generate_description(self, raw_data: Dict, cleaned_data: Dict) -> str:
        """Генерация описания сервера"""
        try:
            parts = []
            
            # Добавляем IP если есть
            if cleaned_data.get('ip'):
                parts.append(f"IP: {cleaned_data['ip']}")
            
            # Добавляем протокол
            protocol = cleaned_data.get('protocol', 'DNSCrypt')
            if protocol != 'DNSCrypt':
                parts.append(f"Protocol: {protocol}")
            
            # Добавляем метод извлечения
            method = raw_data.get('extraction_method', '')
            if method:
                parts.append(f"Source: {method}")
            
            # Добавляем дополнительную информацию из исходных данных
            for key, value in raw_data.items():
                if (key not in ['name', 'ip', 'protocol', 'extraction_method'] and 
                    isinstance(value, str) and 
                    value.strip() and 
                    len(value.strip()) < 100):
                    parts.append(f"{key}: {value.strip()}")
            
            return ' | '.join(parts) if parts else 'DNSCrypt server'
            
        except Exception:
            return 'DNSCrypt server'
    
    def format_for_config(self, servers: List[Dict], is_relay: bool = False) -> List[str]:
        """Форматирование серверов для конфигурационного файла"""
        try:
            formatted_lines = []
            server_type = "relay" if is_relay else "server"
            
            for server in servers:
                try:
                    name = server.get('name', 'unknown')
                    ip = server.get('ip', '')
                    protocol = server.get('protocol', 'DNSCrypt')
                    
                    # Формируем строку в зависимости от наличия IP
                    if ip:
                        if is_relay:
                            line = f"{name:<30} -> {ip} (DNSCrypt relay)"
                        else:
                            line = f"{name:<30} -> {ip} ({protocol})"
                    else:
                        # Если нет IP, используем только имя
                        if is_relay:
                            line = f"{name:<30} (DNSCrypt relay)"
                        else:
                            line = f"{name:<30} ({protocol})"
                    
                    formatted_lines.append(line)
                    
                except Exception as e:
                    print(f"⚠️ Ошибка форматирования сервера: {e}")
                    continue
            
            # Сортируем для лучшей читаемости
            formatted_lines.sort()
            
            print(f"📝 Отформатировано {len(formatted_lines)} {server_type}(s)")
            return formatted_lines
            
        except Exception as e:
            print(f"❌ Ошибка форматирования списка серверов: {e}")
            return []
    
    def _print_processing_stats(self):
        """Вывод статистики обработки"""
        try:
            print("\n📊 СТАТИСТИКА ОБРАБОТКИ:")
            print(f"   Обработано: {self.stats['processed']}")
            print(f"   Валидных: {self.stats['valid']}")
            print(f"   Дубликатов: {self.stats['duplicates']}")
            print(f"   Ошибок: {self.stats['errors']}")
            
            if self.stats['protocols']:
                print(f"   Протоколы:")
                for protocol, count in sorted(self.stats['protocols'].items()):
                    print(f"     {protocol}: {count}")
            
        except Exception as e:
            print(f"⚠️ Ошибка вывода статистики: {e}")
    
    def validate_server_data(self, server: Dict) -> bool:
        """Валидация данных сервера"""
        try:
            # Проверяем обязательные поля
            if not server.get('name'):
                return False
            
            # Проверяем IP если есть
            ip = server.get('ip', '')
            if ip and not self.patterns['ip_address'].match(ip):
                return False
            
            # Проверяем имя сервера
            name = server.get('name', '')
            if len(name) < 1 or len(name) > 100:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_statistics(self) -> Dict:
        """Получение статистики обработки"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Сброс статистики"""
        self.stats = {
            'processed': 0,
            'valid': 0,
            'duplicates': 0,
            'errors': 0,
            'protocols': {}
        }
    
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