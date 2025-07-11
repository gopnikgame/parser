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

# Используем относительный импорт для лучшей совместимости
try:
    from ..core.config import ParserConfig
except ImportError:
    # Fallback для случаев когда относительный импорт не работает
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import ParserConfig

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
                
                # Клик через Space
                lambda: element.send_keys(Keys.SPACE)
            ]
            
            # Пробуем разные методы клика
            for i, click_method in enumerate(click_methods):
                try:
                    click_method()
                    time.sleep(random.uniform(0.5, 1.5))
                    return True
                except Exception as e:
                    if i == len(click_methods) - 1:
                        self.extraction_stats['click_failures'] += 1
                        print(f"⚠️ Все методы клика не сработали для элемента: {e}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Критическая ошибка при клике: {e}")
            self.extraction_stats['click_failures'] += 1
            return False
    
    def _human_like_click(self, element):
        """Человекоподобный клик с движением мыши"""
        actions = ActionChains(self.driver)
        
        # Двигаемся к элементу с задержкой
        actions.move_to_element(element)
        time.sleep(random.uniform(0.1, 0.3))
        
        # Небольшое смещение для имитации человеческого поведения
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-3, 3)
        actions.move_by_offset(offset_x, offset_y)
        
        time.sleep(random.uniform(0.1, 0.2))
        actions.click()
        actions.perform()
    
    def _click_with_offset(self, element):
        """Клик с случайным смещением"""
        actions = ActionChains(self.driver)
        size = element.size
        
        # Рассчитываем случайные координаты внутри элемента
        offset_x = random.randint(-size['width']//4, size['width']//4)
        offset_y = random.randint(-size['height']//4, size['height']//4)
        
        actions.move_to_element_with_offset(element, offset_x, offset_y).click().perform()
    
    def _extract_dialog_content(self) -> Optional[str]:
        """Извлечение содержимого диалога с множественными стратегиями"""
        try:
            # Ждем появления диалога
            dialog_selectors = [
                ".v-dialog .v-card",
                ".v-overlay__content",
                ".modal-content",
                ".dialog",
                "[role='dialog']",
                ".popup",
                ".overlay-content"
            ]
            
            dialog = None
            for selector in dialog_selectors:
                try:
                    dialog = WebDriverWait(self.driver, self.config.DIALOG_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if dialog and dialog.is_displayed():
                        break
                except TimeoutException:
                    continue
            
            if not dialog:
                self.extraction_stats['dialog_failures'] += 1
                print("⚠️ Диалог не найден")
                return None
            
            # Ждем загрузки содержимого
            time.sleep(random.uniform(1, 2))
            
            # Извлекаем текст
            dialog_text = dialog.text
            if not dialog_text or len(dialog_text.strip()) < 10:
                # Пробуем извлечь через innerHTML
                dialog_text = self.driver.execute_script("return arguments[0].innerHTML;", dialog)
            
            return dialog_text
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения диалога: {e}")
            self.extraction_stats['dialog_failures'] += 1
            return None
    
    def _close_dialog(self):
        """Закрытие диалога с множественными стратегиями"""
        try:
            # Стратегии закрытия диалога
            close_strategies = [
                # Кнопки закрытия
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".v-btn[aria-label*='close']").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".close").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, "[aria-label='Close']").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".modal-close").click(),
                
                # Клавиши
                lambda: ActionChains(self.driver).send_keys(Keys.ESCAPE).perform(),
                
                # Клик по оверлею
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".v-overlay").click(),
                lambda: self.driver.find_element(By.CSS_SELECTOR, ".modal-backdrop").click()
            ]
            
            for strategy in close_strategies:
                try:
                    strategy()
                    time.sleep(random.uniform(0.5, 1))
                    
                    # Проверяем, закрылся ли диалог
                    try:
                        WebDriverWait(self.driver, 2).until_not(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".v-dialog"))
                        )
                        return True
                    except TimeoutException:
                        continue
                        
                except Exception:
                    continue
            
            print("⚠️ Не удалось закрыть диалог")
            return False
            
        except Exception as e:
            print(f"⚠️ Ошибка закрытия диалога: {e}")
            return False
    
    def _parse_server_info(self, dialog_content: str, server_name: str) -> Optional[Dict[str, Any]]:
        """Парсинг информации о сервере из содержимого диалога"""
        try:
            import re
            
            info = {
                'name': server_name,
                'ip': None,
                'port': None,
                'protocol': None,
                'location': None,
                'provider': None,
                'dnssec': None,
                'logs': None,
                'filter': None
            }
            
            # Регулярные выражения для поиска информации
            patterns = {
                'ip': [
                    r'(?:IP|Address|Server)[\s:]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                    r'IP[\s\w]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                ],
                'port': [
                    r'(?:Port|:)[\s]*(\d{2,5})',
                    r':(\d{2,5})\b'
                ],
                'protocol': [
                    r'(DNSCrypt(?:\s+relay)?)',
                    r'(DoH|DoT|DNS-over-HTTPS|DNS-over-TLS)'
                ],
                'location': [
                    r'(?:Location|Country|Region)[\s:]*([A-Za-z\s,]+)',
                    r'Flag[\s]*([A-Za-z\s]+)'
                ],
                'provider': [
                    r'(?:Provider|Organization)[\s:]*([^\n\r]+)',
                    r'Provided by[\s:]*([^\n\r]+)'
                ]
            ]
            
            # Очищаем содержимое от HTML тегов
            clean_content = re.sub(r'<[^>]+>', ' ', dialog_content)
            
            # Извлекаем информацию по паттернам
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, clean_content, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value and value not in ['N/A', 'Unknown', '-']:
                            info[field] = value
                            break
            
            # Дополнительные проверки и очистка
            if info['ip']:
                # Проверяем валидность IP
                ip_parts = info['ip'].split('.')
                if len(ip_parts) == 4 and all(0 <= int(part) <= 255 for part in ip_parts):
                    # Определяем протокол по имени сервера, если не найден
                    if not info['protocol']:
                        if 'relay' in server_name.lower():
                            info['protocol'] = 'DNSCrypt relay'
                        else:
                            info['protocol'] = 'DNSCrypt'
                    
                    return info
            
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга информации о сервере: {e}")
            return None
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Получение статистики извлечения"""
        stats = self.extraction_stats.copy()
        if stats['attempts'] > 0:
            stats['success_rate'] = (stats['successes'] / stats['attempts']) * 100
        else:
            stats['success_rate'] = 0
        return stats
    
    def reset_stats(self):
        """Сброс статистики"""
        self.extraction_stats = {
            'attempts': 0,
            'successes': 0,
            'timeouts': 0,
            'click_failures': 0,
            'dialog_failures': 0
        }