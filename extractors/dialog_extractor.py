"""
Извлечение данных из диалогов - для Vue.js v2.1
"""
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

class AdvancedDialogExtractor:
    """Извлечение данных из диалогов - ОБНОВЛЕННАЯ ВЕРСИЯ v2.1 для Vue.js"""
    
    def __init__(self, driver: webdriver.Chrome, config=None):
        self.driver = driver
        self.config = config
        
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
                r'sdns:\/\/([^\n\r"\'<]+)',  # More specific to avoid grabbing unrelated text
            ],
            'ip_address': [
                r'Address:[^:]*?\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
                r'IP\sAddress:[^:]*?\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
                r'IP:[^:]*?\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
                r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b',
            ],
            'protocol': [
                r'Protocol:\s*(DNSCrypt|DoH|DoT|DNSCrypt relay)',
                r'Type:\s*(DNSCrypt|DoH|DoT|DNSCrypt relay)',
                r'(DNSCrypt relay|DNSCrypt|DNS-over-HTTPS|DNS-over-TLS)',
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
                except Exception:
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
                        ip = match.group(1).strip()
                        # Простая валидация IP
                        ip_parts = ip.split('.')
                        if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                            server_data['ip'] = ip
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
                except Exception:
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

            # Ждем появления диалога
            dialog_element = self._wait_for_dialog()
            if not dialog_element:
                self._close_dialog_if_present()
                return None

            # Извлекаем текст
            dialog_text = self._get_dialog_text(dialog_element)
            if not dialog_text:
                print(f"   ⚠️ Пустой диалог для триггера {index}")
                self._close_dialog_if_present()
                return None
            
            print(f"   📄 Диалог получен, {len(dialog_text)} символов.")

            # Парсим данные
            server_data = self._parse_dialog_text(dialog_text, index)

            # Закрываем диалог
            self._close_dialog_if_present()

            return server_data

        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            print(f"⚠️ Ошибка при обработке триггера {index}: {e}")
            self._close_dialog_if_present()
            return None
        except Exception as e:
            print(f"❌ Непредвиденная ошибка с триггером {index}: {e}")
            self._close_dialog_if_present()
            return None

    def _wait_for_dialog(self):
        """Ожидание появления диалогового окна"""
        combined_selector = ", ".join(self.selectors['dialogs'])
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, combined_selector))
            )
        except TimeoutException:
            return None

    def _get_dialog_text(self, dialog_element) -> str:
        """Извлечение текста из диалогового окна с несколькими стратегиями."""
        text = ""
        try:
            # Strategy 1: Standard .text attribute
            text = dialog_element.text.strip()
            if text:
                return text

            # Strategy 2: textContent via JavaScript
            text = self.driver.execute_script("return arguments[0].textContent;", dialog_element).strip()
            if text:
                return text

            # Strategy 3: innerText via JavaScript
            text = self.driver.execute_script("return arguments[0].innerText;", dialog_element).strip()
            if text:
                return text

            # Strategy 4: innerHTML via JavaScript (less clean, but sometimes necessary)
            html = self.driver.execute_script("return arguments[0].innerHTML;", dialog_element)
            # Простая очистка HTML
            clean_html = re.sub('<[^<]+?>', ' ', html)
            text = ' '.join(clean_html.split()).strip()
            if text:
                return text
        except Exception as e:
            print(f"      ⚠️ Ошибка при извлечении текста диалога: {e}")
        
        return text

    def _parse_dialog_text(self, text: str, index: int) -> dict:
        """Парсинг текста диалога для извлечения данных сервера (v2.1, legacy compatible)"""
        server_data = {
            'name': '',
            'ip': None,
            'protocol': None,
            'dnssec': False,
            'no_filters': False,
            'no_logs': False,
            'row_index': index,
            'extraction_method': 'dialog'
        }

        if not text:
            return server_data

        # Извлекаем имя сервера
        for pattern in self.data_patterns['server_name']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                server_data['name'] = match.group(1).strip()
                break
        
        # Ищем IP адрес (логика из старого парсера)
        ip_patterns = [
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'Address[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'IP[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        ]
        for pattern in ip_patterns:
            matches = re.findall(pattern, text)
            for ip in matches:
                octets = ip.split('.')
                if all(0 <= int(octet) <= 255 for octet in octets):
                    server_data['ip'] = ip
                    break
            if server_data['ip']:
                break

        # Ищем протокол
        if 'DNSCrypt relay' in text:
            server_data['protocol'] = 'DNSCrypt relay'
        elif 'DNSCrypt' in text:
            server_data['protocol'] = 'DNSCrypt'
        elif 'DoH' in text or 'DNS-over-HTTPS' in text:
            server_data['protocol'] = 'DoH'
        elif 'DoT' in text or 'DNS-over-TLS' in text:
            server_data['protocol'] = 'DoT'

        # Ищем флаги
        text_lower = text.lower()
        # Более надежная проверка флагов
        server_data['dnssec'] = 'dnssec' in text_lower and 'true' in text_lower
        server_data['no_filters'] = ('no filter' in text_lower or 'no filtering' in text_lower) and 'true' in text_lower
        server_data['no_logs'] = ('no log' in text_lower or 'no logging' in text_lower) and 'true' in text_lower

        return server_data if server_data['name'] and server_data['ip'] else None

    def _close_dialog_if_present(self):
        """Закрытие диалогового окна, если оно присутствует"""
        for selector in self.selectors['dialog_close']:
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if close_button.is_displayed():
                    actions = ActionChains(self.driver)
                    actions.move_to_element(close_button).click().perform()
                    time.sleep(0.5)
                    return
            except (NoSuchElementException, WebDriverException):
                continue
        # Fallback: click outside if no close button found
        try:
            actions = ActionChains(self.driver)
            actions.move_by_offset(10, 10).click().perform()
            time.sleep(0.5)
        except Exception:
            pass

    def _extract_via_javascript(self) -> list:
        """Извлечение данных из Vue.js компонента через JavaScript"""
        print("🔍 Пробуем извлечение через JavaScript...")
        servers = []
        try:
            # Этот скрипт предполагает, что данные хранятся в свойстве `items` или `servers`
            # корневого Vue-компонента. Его нужно адаптировать под конкретную структуру.
            script = """
            const app = document.querySelector('#app') || document.body;
            if (app && app.__vue__) {
                const vueInstance = app.__vue__;
                // Ищем данные в разных местах
                const dataSources = [
                    vueInstance.servers,
                    vueInstance.items,
                    vueInstance.$data.servers,
                    vueInstance.$data.items,
                    vueInstance.$children[0].servers,
                    vueInstance.$children[0].items
                ];
                for (const source of dataSources) {
                    if (source && Array.isArray(source) && source.length > 0) {
                        return source;
                    }
                }
            }
            return [];
            """
            raw_servers = self.driver.execute_script(script)
            
            for i, item in enumerate(raw_servers):
                if isinstance(item, dict):
                    server_data = {
                        'name': item.get('name', item.get('server', '')),
                        'ip': item.get('ip', item.get('address', '')),
                        'protocol': item.get('protocol', 'DNSCrypt'),
                        'row_index': i,
                        'extraction_method': 'javascript'
                    }
                    if server_data['name']:
                        servers.append(server_data)

            return servers
        except Exception as e:
            print(f"⚠️ Ошибка при извлечении через JavaScript: {e}")
            return []

    def extract_server_info_smart(self, row, server_name):
        """
        Умное извлечение информации о сервере из строки таблицы
        Добавлено для обратной совместимости с legacy кодом
        """
        try:
            print(f"🔍 Извлекаем информацию о сервере: {server_name}")
            
            # Пытаемся извлечь данные прямо из строки
            server_data = self._extract_server_from_row(row, server_name)
            
            # Если данных мало, пытаемся открыть диалог для этой строки
            if not server_data or not server_data.get('ip'):
                print(f"   🔄 Пытаемся извлечь через диалог...")
                dialog_data = self._try_extract_via_row_dialog(row, server_name)
                if dialog_data:
                    # Объединяем данные
                    if server_data:
                        server_data.update(dialog_data)
                    else:
                        server_data = dialog_data
            
            # Проверяем и нормализуем данные
            if server_data:
                server_data = self._normalize_server_data(server_data, server_name)
                if server_data.get('ip'):
                    print(f"   ✅ Успешно извлечено: {server_data.get('name', 'N/A')} -> {server_data.get('ip', 'N/A')}")
                else:
                    print(f"   ⚠️  Извлечено имя, но не IP: {server_data.get('name', 'N/A')}")
                return server_data
            else:
                print(f"   ❌ Не удалось извлечь данные для {server_name}")
                return None
                
        except Exception as e:
            print(f"   ❌ Ошибка извлечения данных для {server_name}: {e}")
            return None
    
    def _try_extract_via_row_dialog(self, row, server_name):
        """Попытка извлечь данные через диалог конкретной строки"""
        try:
            # Ищем кнопки или кликабельные элементы в строке
            clickable_elements = []
            
            for selector in self.selectors['dialog_triggers']:
                try:
                    elements = row.find_elements(By.CSS_SELECTOR, selector)
                    clickable_elements.extend(elements)
                except Exception:
                    continue
            
            # Если кнопок не найдено, попробуем кликнуть по самой строке
            if not clickable_elements:
                clickable_elements = [row]
            
            for element in clickable_elements[:2]:  # Максимум 2 попытки
                try:
                    # Скроллим к элементу
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                    
                    # Кликаем
                    if element.is_displayed() and element.is_enabled():
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        time.sleep(1)
                        
                        # Ждем диалог
                        dialog_element = self._wait_for_dialog()
                        if dialog_element:
                            dialog_text = self._get_dialog_text(dialog_element)
                            self._close_dialog_if_present()
                            
                            if dialog_text:
                                print(f"      📄 Диалог для '{server_name}' получен, {len(dialog_text)} символов.")
                                return self._parse_dialog_text(dialog_text, server_name)
                            else:
                                print(f"      ⚠️ Пустой диалог для '{server_name}'.")
                    
                except Exception as e:
                    print(f"      ⚠️ Ошибка клика/обработки диалога: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"      ⚠️ Ошибка при попытке открыть диалог: {e}")
            return None
    
    def _normalize_server_data(self, server_data, original_name):
        """Нормализация и проверка данных сервера"""
        if not server_data:
            return None
        
        # Если нет имени, используем оригинальное
        if not server_data.get('name') and original_name:
            server_data['name'] = original_name
        
        # Проверяем валидность IP
        ip = server_data.get('ip', '')
        if ip:
            # Простая валидация IP
            ip_parts = ip.split('.')
            if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                server_data['ip'] = ip
            else:
                # Если IP невалидный, убираем его
                server_data['ip'] = ''
        
        # Устанавливаем протокол по умолчанию
        if not server_data.get('protocol'):
            server_data['protocol'] = 'DNSCrypt'
        
        return server_data