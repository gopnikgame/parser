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

# Исправляем импорт на абсолютный
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
                
               