"""
Извлечение данных из диалогов - ПОЛНОСТЬЮ ПЕРЕПИСАН для Vue.js v2.1
"""
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

class DialogExtractor:
    """Извлечение данных из диалогов - ОБНОВЛЕННАЯ ВЕРСИЯ v2.1 для Vue.js"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        
        # Обновленные селекторы для Vue.js/Vuetify приложения
        self.selectors = {
            # Кнопки и триггеры для открытия диалогов
            'dialog_triggers': [
                'button[data-testid*="dialog"]',
                '.v-btn[aria-haspopup="dialog"]',
                'button[aria-label*="info" i]',
                'button[aria-label*="detail" i]',
                'button[title*="info" i]',
                'button[title*="detail" i]',
                '.v-btn[data-action="show-details"]',
                '.server-info-btn',
                '.details-btn',
                'button.info-button',
                '[role="button"][aria-describedby]',
                '.v-data-table__expand-icon',
                '.expand-btn'
            ],
            
            # Диалоги и модальные окна
            'dialogs': [
                '.v-dialog',
                '.v-overlay__content',
                '.v-menu__content',
                '.modal',
                '.dialog',
                '[role="dialog"]',
                '.v-card[aria-modal="true"]',
                '.popup',
                '.overlay'
            ],
            
            # Содержимое диалогов
            'dialog_content': [
                '.v-dialog .v-card-text',
                '.v-dialog .v-card__text',
                '.v-overlay__content .v-card-text',
                '.v-menu__content .v-list',
                '.modal-body',
                '.dialog-content',
                '.popup-content'
            ],
            
            # Строки таблицы данных
            'table_rows': [
                '.v-data-table tbody tr',
                '.v-datatable tbody tr',
                'table tbody tr',
                '.data-table tbody tr',
                'tr[data-item]',
                'tr[class*="row"]'
            ],
            
            # Ячейки с серверными данными
            'server_cells': [
                'td[data-label*="server" i]',
                'td[data-field*="name" i]',
                'td.server-name',
                'td.name-cell',
                'td:first-child',
                'td[class*="name"]'
            ],
            
            # Закрытие диалогов
            'dialog_close': [
                '.v-dialog .v-btn[aria-label*="close" i]',
                '.v-overlay .v-btn[data-dismiss]',
                '.v-dialog .v-icon[aria-label*="close" i]',
                '.modal .close',
                '.dialog .close-btn',
                '[aria-label="Close"]',
                '.v-overlay__scrim'
            ]
        }
        
        # Паттерны для извлечения данных
        self.data_patterns = {
            'server_name': [
                r'Server:\s*([^\n\r]+)',
                r'Name:\s*([^\n\r]+)',
                r'Hostname:\s*([^\n\r]+)',
                r'^([a-zA-Z0-9\-_.]+)(?:\s|$)',
                r'([a-zA-Z0-9\-_.]+\.(?:com|org|net|info|io|me|co))',
            ],
            'ip_address': [
                r'IP:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
                r'Address:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
                r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
            ],
            'protocol': [
                r'Protocol:\s*(DNSCrypt|DoH|DoT)',
                r'Type:\s*(DNSCrypt|DoH|DoT)',
                r'(DNSCrypt|DNS-over-HTTPS|DNS-over-TLS)',
            ]
        }
    
    def extract_all_servers(self, max_servers: int = 200) -> list:
        """Извлечение всех серверов с улучшенным алгоритмом"""
        print("🔍 Начинаем извлечение серверов (улучшенная версия v2.1)...")
        
        servers_data = []
        processed_servers = set()
        
        try:
            # Метод 1: Прямое извлечение из таблицы
            table_servers = self._extract_from_table()
            for server in table_servers:
                server_key = f"{server.get('name', '')}_{server.get('ip', '')}"
                if server_key not in processed_servers:
                    servers_data.append(server)
                    processed_servers.add(server_key)
            
            print(f"📊 Извлечено из таблицы: {len(table_servers)} серверов")
            
            # Метод 2: Извлечение через диалоги/попапы
            if len(servers_data) < 50:  # Если мало данных, пробуем диалоги
                dialog_servers = self._extract_via_dialogs(max_servers - len(servers_data))
                for server in dialog_servers:
                    server_key = f"{server.get('name', '')}_{server.get('ip', '')}"
                    if server_key not in processed_servers:
                        servers_data.append(server)
                        processed_servers.add(server_key)
                
                print(f"📊 Извлечено через диалоги: {len(dialog_servers)} серверов")
            
            # Метод 3: JavaScript извлечение из Vue данных
            if len(servers_data) < 50:
                js_servers = self._extract_via_javascript()
                for server in js_servers:
                    server_key = f"{server.get('name', '')}_{server.get('ip', '')}"
                    if server_key not in processed_servers:
                        servers_data.append(server)
                        processed_servers.add(server_key)
                
                print(f"📊 Извлечено через JavaScript: {len(js_servers)} серверов")
            
            print(f"✅ Общее количество извлеченных серверов: {len(servers_data)}")
            return servers_data[:max_servers]
            
        except Exception as e:
            print(f"❌ Критическая ошибка извлечения серверов: {e}")
            return []
    
    def _extract_from_table(self) -> list:
        """Прямое извлечение данных из таблицы"""
        servers = []
        
        try:
            # Находим все строки таблицы
            rows = []
            for selector in self.selectors['table_rows']:
                try:
                    found_rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_rows:
                        rows.extend(found_rows)
                        break
                except:
                    continue
            
            if not rows:
                print("⚠️ Строки таблицы не найдены")
                return []
            
            print(f"📊 Найдено {len(rows)} строк в таблице")
            
            for i, row in enumerate(rows[:200]):  # Ограничиваем обработку
                try:
                    if not row.is_displayed():
                        continue
                    
                    server_data = self._extract_server_from_row(row, i)
                    if server_data and server_data.get('name'):
                        servers.append(server_data)
                        
                except Exception as e:
                    print(f"⚠️ Ошибка обработки строки {i}: {e}")
                    continue
            
            return servers
            
        except Exception as e:
            print(f"❌ Ошибка извлечения из таблицы: {e}")
            return []
    
    def _extract_server_from_row(self, row, row_index: int) -> dict:
        """Извлечение данных сервера из строки таблицы"""
        try:
            row_text = row.text.strip()
            if not row_text or 'loading' in row_text.lower():
                return None
            
            # Получаем все ячейки
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                return None
            
            server_data = {
                'name': '',
                'ip': '',
                'protocol': 'DNSCrypt',
                'row_index': row_index,
                'extraction_method': 'table_direct'
            }
            
            # Пытаемся извлечь данные из первой ячейки (обычно название)
            if len(cells) > 0:
                first_cell = cells[0]
                cell_text = first_cell.text.strip()
                
                # Извлекаем имя сервера
                name_match = None
                for pattern in self.data_patterns['server_name']:
                    match = re.search(pattern, cell_text)
                    if match:
                        name_match = match.group(1).strip()
                        break
                
                if name_match:
                    server_data['name'] = name_match
                elif cell_text and len(cell_text) < 100:  # Простое имя
                    server_data['name'] = cell_text
            
            # Ищем IP адрес во всех ячейках
            for cell in cells:
                cell_text = cell.text.strip()
                for pattern in self.data_patterns['ip_address']:
                    match = re.search(pattern, cell_text)
                    if match:
                        server_data['ip'] = match.group(1)
                        break
                if server_data['ip']:
                    break
            
            # Определяем протокол
            full_row_text = row_text.lower()
            if 'doh' in full_row_text or 'dns-over-https' in full_row_text:
                server_data['protocol'] = 'DoH'
            elif 'dot' in full_row_text or 'dns-over-tls' in full_row_text:
                server_data['protocol'] = 'DoT'
            elif 'relay' in full_row_text:
                server_data['protocol'] = 'DNSCrypt relay'
            
            # Если нет имени, используем любой доступный текст
            if not server_data['name'] and row_text:
                clean_text = row_text.split('\n')[0].strip()
                if clean_text and len(clean_text) < 50:
                    server_data['name'] = clean_text
            
            return server_data if server_data['name'] else None
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения из строки {row_index}: {e}")
            return None
    
    def _extract_via_dialogs(self, max_count: int = 100) -> list:
        """Извлечение данных через открытие диалогов"""
        servers = []
        
        try:
            print("🔍 Пробуем извлечение через диалоги...")
            
            # Находим все возможные триггеры диалогов
            triggers = []
            for selector in self.selectors['dialog_triggers']:
                try:
                    found_triggers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    triggers.extend(found_triggers)
                except:
                    continue
            
            print(f"📊 Найдено {len(triggers)} потенциальных триггеров диалогов")
            
            for i, trigger in enumerate(triggers[:max_count]):
                try:
                    if not trigger.is_displayed():
                        continue
                    
                    # Пробуем открыть диалог
                    server_data = self._extract_from_trigger(trigger, i)
                    if server_data:
                        servers.append(server_data)
                    
                    # Ограничиваем время обработки
                    if i > 0 and i % 20 == 0:
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"⚠️ Ошибка с триггером {i}: {e}")
                    continue
            
            return servers
            
        except Exception as e:
            print(f"❌ Ошибка извлечения через диалоги: {e}")
            return []
    
    def _extract_from_trigger(self, trigger, index: int) -> dict:
        """Извлечение данных из одного триггера диалога"""
        try:
            # Скроллим к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", trigger)
            time.sleep(0.5)
            
            # Пробуем кликнуть
            actions = ActionChains(self.driver)
            actions.move_to_element(trigger).click().perform()
            time.sleep(1)
            