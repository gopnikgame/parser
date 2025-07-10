# Продвинутый экстрактор диалогов с множественными стратегиями
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Optional, Dict, Any, List
from ..core.config import ParserConfig

class AdvancedDialogExtractor:
    """Продвинутый экстрактор диалогов с множественными стратегиями"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
        self.extraction_stats = {
            'attempts': 0,
            'successes': 0,
            'timeouts': 0,
            'click_failures': 0,
            'dialog_failures': 0
        }
    
    def extract_server_info_smart(self, row, server_name: str, retry_count: int = None) -> Optional[Dict[str, Any]]:
        """Умное извлечение информации о сервере с множественными попытками"""
        if retry_count is None:
            retry_count = self.config.MAX_RETRIES
            
        self.extraction_stats['attempts'] += 1
        
        for attempt in range(retry_count):
            try:
                print(f"🔄 Попытка {attempt + 1}/{retry_count} для {server_name}")
                
                # Проверяем видимость строки
                if not self._ensure_row_visible(row):
                    continue
                
                # Находим кликабельный элемент  
                clickable_element = self._find_clickable_element(row)
                if not clickable_element:
                    continue
                
                # Выполняем умный клик
                if not self._smart_click(clickable_element, attempt):
                    continue
                
                # Ищем и извлекаем диалог
                dialog_content = self._extract_dialog_content()
                if dialog_content:
                    self._close_dialog()
                    
                    # Парсим информацию
                    info = self._parse_server_info(dialog_content, server_name)
                    if info and info.get('ip'):
                        self.extraction_stats['successes'] += 1
                        return info
                
                # Если не получилось - делаем экспоненциальную задержку
                delay = self.config.RETRY_DELAY_BASE * (2 ** attempt) + random.uniform(0.5, 1.5)
                time.sleep(delay)
                
            except Exception as e:
                print(f"⚠️ Ошибка на попытке {attempt + 1} для {server_name}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(self.config.RETRY_DELAY_BASE * (attempt + 1))
        
        print(f"❌ Все попытки исчерпаны для {server_name}")
        return None
    
    def _ensure_row_visible(self, row) -> bool:
        """Обеспечение видимости строки"""
        try:
            if not row.is_displayed():
                # Прокручиваем к элементу
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                    row
                )
                time.sleep(random.uniform(1, 2))
                
                # Проверяем еще раз
                if not row.is_displayed():
                    return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка обеспечения видимости: {e}")
            return False
    
    def _find_clickable_element(self, row):
        """Поиск кликабельного элемента с множественными стратегиями"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 1:
                return None
            
            name_cell = cells[0]
            server_name = name_cell.text.strip()
            
            if not server_name or server_name in ["No data available", "loading"]:
                return None
            
            # Стратегии поиска кликабельного элемента
            click_strategies = [
                # Vuetify компоненты
                lambda: name_cell.find_element(By.CSS_SELECTOR, ".v-btn"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "[role='button']"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, ".v-chip"),
                
                # HTML элементы
                lambda: name_cell.find_element(By.CSS_SELECTOR, "span[title]"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "span"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "a"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "button"),
                
                # Атрибуты
                lambda: name_cell.find_element(By.CSS_SELECTOR, "*[onclick]"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "*[data-toggle]"),
                lambda: name_cell.find_element(By.CSS_SELECTOR, "*[aria-expanded]"),
                
                # Fallback - сама ячейка
                lambda: name_cell
            ]
            
            for strategy in click_strategies:
                try:
                    element = strategy()
                    if element and element.is_displayed():
                        return element
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска кликабельного элемента: {e}")
            return None
    
    def _smart_click(self, element, attempt: int = 0) -> bool:
        """Умный клик с человекоподобным поведением"""
        try:
            # Добавляем случайную задержку перед кликом
            delay_range = self.config.get_click_delay()
            time.sleep(random.uniform(*delay_range))
            
            # Стратегии клика в порядке предпочтения
            click_methods = [
                # Человекоподобный клик с движением мыши
                lambda: self._human_like_click(element),
                
                # Стандартный Selenium клик
                lambda: element.click(),
                
                # ActionChains клик
                lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                
                # JavaScript клик
                lambda: self.driver.execute_script("arguments[0].click();", element),
                
                # Клик с координатами
                lambda: self._click_with_offset(element),
                
                # Клик через Enter
                lambda: element.send_keys(Keys.ENTER),
                
                # Последняя попытка - принудительный JavaScript
                lambda: self.driver.execute_script("""
                    arguments[0].dispatchEvent(new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    }));
                """, element)
            ]
            
            for i, click_method in enumerate(click_methods):
                try:
                    click_method()
                    
                    # Ждем появления диалога с увеличивающейся задержкой
                    wait_time = 2 + (attempt * 0.5) + (i * 0.5)
                    time.sleep(wait_time)
                    
                    # Проверяем появление диалога
                    if self._check_dialog_appeared():
                        return True
                        
                except Exception as e:
                    continue
            
            self.extraction_stats['click_failures'] += 1
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка умного клика: {e}")
            return False
    
    def _human_like_click(self, element):
        """Человекоподобный клик с естественным движением мыши"""
        actions = ActionChains(self.driver)
        
        # Случайное смещение для более естественного клика
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        
        # Движение к элементу с паузой
        actions.move_to_element(element)
        actions.pause(random.uniform(0.1, 0.3))
        
        # Клик со смещением
        actions.move_to_element_with_offset(element, offset_x, offset_y)
        actions.pause(random.uniform(0.05, 0.15))
        actions.click()
        
        actions.perform()
    
    def _click_with_offset(self, element):
        """Клик с случайным смещением"""
        actions = ActionChains(self.driver)
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        actions.move_to_element_with_offset(element, offset_x, offset_y).click().perform()
    
    def _check_dialog_appeared(self) -> bool:
        """Проверка появления диалога"""
        for selector in self.config.DIALOG_SELECTORS[:5]:  # Проверяем только первые 5 для скорости
            try:
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        return True
            except:
                continue
        
        return False
    
    def _extract_dialog_content(self) -> Optional[str]:
        """Извлечение содержимого диалога с расширенным поиском"""
        try:
            # Ждем появления диалога с динамическим таймаутом
            wait = WebDriverWait(self.driver, self.config.DIALOG_WAIT_TIMEOUT)
            
            for selector in self.config.DIALOG_SELECTORS:
                try:
                    if selector.startswith("//"):
                        dialog = wait.until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        dialog = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    if dialog and dialog.is_displayed():
                        content = dialog.text.strip()
                        if content and len(content) > 20:  # Минимальная длина контента
                            return content
                            
                except TimeoutException:
                    continue
                except Exception as e:
                    continue
            
            self.extraction_stats['dialog_failures'] += 1
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения диалога: {e}")
            return None
    
    def _close_dialog(self):
        """Закрытие диалога множественными способами"""
        close_methods = [
            # ESC ключ
            lambda: self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE),
            
            # Поиск кнопки закрытия
            lambda: self._find_and_click_close_button(),
            
            # Клик вне диалога
            lambda: self._click_outside_dialog(),
            
            # Принудительное скрытие через JavaScript
            lambda: self._force_hide_dialogs()
        ]
        
        for close_method in close_methods:
            try:
                close_method()
                time.sleep(0.5)
                
                # Проверяем, закрылся ли диалог
                if not self._check_dialog_appeared():
                    break
                    
            except:
                continue
    
    def _find_and_click_close_button(self):
        """Поиск и клик по кнопке закрытия"""
        close_selectors = [
            "button[aria-label*='close']",
            "button[aria-label*='Close']", 
            ".v-btn--icon[aria-label*='close']",
            ".v-dialog__close",
            ".close-btn",
            ".modal-close",
            "button.close",
            "[data-dismiss='modal']"
        ]
        
        for selector in close_selectors:
            try:
                close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if close_btn.is_displayed():
                    close_btn.click()
                    return
            except:
                continue
    
    def _click_outside_dialog(self):
        """Клик вне диалога для его закрытия"""
        try:
            # Кликаем в левый верхний угол страницы
            actions = ActionChains(self.driver)
            actions.move_by_offset(10, 10).click().perform()
        except:
            pass
    
    def _force_hide_dialogs(self):
        """Принудительное скрытие всех диалогов"""
        try:
            self.driver.execute_script("""
                // Скрываем все возможные диалоги
                var dialogs = document.querySelectorAll('.v-dialog, .v-menu, .modal, .popup');
                dialogs.forEach(function(dialog) {
                    dialog.style.display = 'none';
                    dialog.style.visibility = 'hidden';
                });
                
                // Удаляем overlay
                var overlays = document.querySelectorAll('.v-overlay, .modal-backdrop');
                overlays.forEach(function(overlay) {
                    overlay.remove();
                });
            """)
        except:
            pass
    
    def _parse_server_info(self, dialog_text: str, server_name: str) -> Dict[str, Any]:
        """Улучшенный парсинг информации сервера"""
        import re
        
        info = {
            'name': server_name,
            'ip': None,
            'protocol': None,
            'dnssec': False,
            'no_filters': False,
            'no_logs': False
        }
        
        if not dialog_text:
            return info
        
        # Расширенные паттерны для поиска IP
        ip_patterns = [
            r'(?:Address|IP|Server)[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'(?:IPv4)[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        ]
        
        # Поиск IP адреса
        for pattern in ip_patterns:
            matches = re.findall(pattern, dialog_text, re.IGNORECASE)
            for ip in matches:
                if self._validate_ip(ip):
                    info['ip'] = ip
                    break
            if info['ip']:
                break
        
        # Улучшенное определение протокола
        text_lower = dialog_text.lower()
        if 'dnscrypt relay' in text_lower or 'anonymized dns relay' in text_lower:
            info['protocol'] = 'DNSCrypt relay'
        elif 'dnscrypt' in text_lower and 'doh' not in text_lower:
            info['protocol'] = 'DNSCrypt'
        elif 'doh' in text_lower or 'dns-over-https' in text_lower:
            info['protocol'] = 'DoH'
        elif 'dot' in text_lower or 'dns-over-tls' in text_lower:
            info['protocol'] = 'DoT'
        
        # Поиск флагов с более точными паттернами
        info['dnssec'] = bool(re.search(r'dnssec[^:]*:?\s*(true|yes|✓|enabled)', text_lower))
        info['no_filters'] = bool(re.search(r'no.?filter[^:]*:?\s*(true|yes|✓|enabled)', text_lower))
        info['no_logs'] = bool(re.search(r'no.?log[^:]*:?\s*(true|yes|✓|enabled)', text_lower))
        
        return info
    
    def _validate_ip(self, ip: str) -> bool:
        """Валидация IP адреса"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False
            
            # Исключаем локальные и служебные адреса
            first_octet = int(parts[0])
            if first_octet in [0, 10, 127] or (first_octet == 172 and 16 <= int(parts[1]) <= 31) or (first_octet == 192 and int(parts[1]) == 168):
                return False
                
            return True
            
        except (ValueError, IndexError):
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики работы"""
        return self.extraction_stats.copy()