"""
Навигатор для работы со страницами
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..core.config import ParserConfig

class PageNavigator:
    """Навигатор для работы со страницами"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
    
    def navigate_to_page(self, url: str, max_attempts: int = 3) -> bool:
        """Навигация на страницу с восстановлением после ошибок"""
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
                time.sleep(5 * (attempt + 1))  # Экспоненциальная задержка
        
        return False
    
    def _wait_for_page_load_smart(self, timeout: int = None) -> bool:
        """Умное ожидание загрузки страницы"""
        if timeout is None:
            timeout = self.config.PAGE_LOAD_TIMEOUT
            
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
    
    def wait_for_dynamic_content(self, timeout: int = 300) -> bool:
        """Интеллектуальное ожидание динамического контента"""
        try:
            print("⏳ Интеллектуальное ожидание динамического контента...")
            
            start_time = time.time()
            last_content_length = 0
            stable_count = 0
            
            while time.time() - start_time < timeout:
                try:
                    # Проверяем различные индикаторы загрузки
                    current_content_length = len(self.driver.page_source)
                    
                    # Ждем завершения всех сетевых запросов
                    network_idle = self.driver.execute_script("""
                        return window.performance.getEntriesByType('resource')
                            .filter(r => r.responseEnd === 0).length === 0;
                    """)
                    
                    # Проверяем отсутствие загрузочных элементов
                    loading_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        ".v-progress-linear, .loading, .spinner, [role='progressbar'], .v-skeleton-loader")
                    loading_active = any(elem.is_displayed() for elem in loading_elements)
                    
                    # Проверяем наличие данных в таблице
                    data_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .v-data-table tbody tr")
                    visible_rows = [row for row in data_rows if row.is_displayed() and row.text.strip() and "loading" not in row.text.lower()]
                    
                    print(f"⏳ Проверка: сеть={network_idle}, загрузка={not loading_active}, строк={len(visible_rows)}, размер={current_content_length}")
                    
                    # Условия готовности
                    if (network_idle and not loading_active and len(visible_rows) > 10):
                        print(f"✅ Контент готов: {len(visible_rows)} строк данных")
                        return True
                    
                    # Проверяем стабильность контента
                    if current_content_length == last_content_length:
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_content_length = current_content_length
                    
                    # Если контент стабилен более 30 секунд, считаем загруженным
                    if stable_count > 10:
                        print(f"✅ Контент стабилизировался ({len(visible_rows)} строк)")
                        return len(visible_rows) > 0
                    
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"⚠️ Ошибка во время ожидания: {e}")
                    time.sleep(5)
            
            print("⚠️ Таймаут ожидания динамического контента")
            return False
            
        except Exception as e:
            print(f"❌ Критическая ошибка ожидания: {e}")
            return False
    
    def debug_page_structure(self) -> bool:
        """Глубокий анализ структуры страницы для отладки"""
        try:
            print("🔍 ГЛУБОКИЙ АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ...")
            
            # 1. Проверяем заголовок страницы
            title = self.driver.title
            print(f"📄 Заголовок страницы: {title}")
            
            # 2. Ищем все возможные контейнеры с данными
            containers = [
                "#app", "[data-app]", ".v-application", ".v-main", 
                ".container", ".v-data-table", "table", ".datatable",
                ".servers", ".server-list", "#servers", "#server-list"
            ]
            
            for container in containers:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, container)
                    if elements:
                        print(f"✅ Найден контейнер: {container} ({len(elements)} элементов)")
                        for i, elem in enumerate(elements[:3]):
                            if elem.is_displayed():
                                text_preview = elem.text[:100].replace('\n', ' ')
                                print(f"   [{i+1}] Видимый: {text_preview}...")
                except:
                    continue
            
            # 3. Ищем все таблицы и их содержимое
            print("\n📊 АНАЛИЗ ТАБЛИЦ:")
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Найдено таблиц: {len(tables)}")
            
            for i, table in enumerate(tables):
                if table.is_displayed():
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"  Таблица {i+1}: {len(rows)} строк, видима: {table.is_displayed()}")
                    
                    # Показываем первые несколько строк
                    for j, row in enumerate(rows[:5]):
                        if row.text.strip():
                            print(f"    Строка {j+1}: {row.text[:80]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка анализа страницы: {e}")
            return False