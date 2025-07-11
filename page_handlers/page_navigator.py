"""
Навигатор для работы со страницами - ИСПРАВЛЕННАЯ ВЕРСИЯ v2.1
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Используем относительный импорт для лучшей совместимости
try:
    from ..core.config import ParserConfig
except ImportError:
    # Fallback для случаев когда относительный импорт не работает
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import ParserConfig

class PageNavigator:
    """Навигатор для работы со страницами - ИСПРАВЛЕННАЯ ВЕРСИЯ v2.1"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
        
        # Обновленные селекторы для Vue.js приложения
        self.selectors = {
            'vue_app': ['#app', '[data-app]', '.v-application'],
            'data_table': ['.v-data-table', 'table', '.v-datatable'],
            'loading': ['.v-progress-linear', '.v-skeleton-loader', '.loading'],
            'data_rows': ['table tbody tr', '.v-data-table tbody tr', 'tr[data-item]'],
            'server_rows': ['tbody tr:not(.v-data-table__empty-wrapper)']
        }
    
    def navigate_to_page(self, url: str, max_attempts: int = 3) -> bool:
        """Навигация на страницу с восстановлением после ошибок"""
        for attempt in range(max_attempts):
            try:
                print(f"🌐 Переход на страницу (попытка {attempt + 1}/{max_attempts})...")
                
                if attempt > 0:
                    self.driver.delete_all_cookies()
                
                self.driver.get(url)
                
                if self._wait_for_vue_app() and self._wait_for_data_load():
                    print("✅ Страница и данные успешно загружены")
                    return True
                else:
                    print("⚠️ Страница загрузилась с проблемами")
                    
            except Exception as e:
                print(f"❌ Ошибка загрузки страницы: {e}")
                
            time.sleep(5 * (attempt + 1))
        
        print("🔍 Финальная диагностика проблемы...")
        self.debug_page_structure()
        return False
    
    def _wait_for_vue_app(self, timeout: int = 30) -> bool:
        """Ожидание загрузки Vue.js приложения"""
        try:
            print("⏳ Ожидание загрузки Vue.js приложения...")
            wait = WebDriverWait(self.driver, timeout)
            
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            for selector in self.selectors['vue_app']:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Vue приложение найдено: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            print("⚠️ Vue приложение не найдено, используем стандартную логику")
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка ожидания Vue приложения: {e}")
            return False
    
    def _wait_for_data_load(self, timeout: int = 60) -> bool:
        """Ожидание загрузки данных"""
        try:
            print("⏳ Ожидание загрузки данных серверов...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                loading_active = self._check_loading_indicators()
                data_rows = self._find_data_rows()
                visible_rows = [row for row in data_rows if row.is_displayed() and row.text.strip()]
                
                print(f"📊 Найдено {len(visible_rows)} строк данных")
                
                if not loading_active and len(visible_rows) >= 10:
                    print(f"✅ Данные готовы: {len(visible_rows)} строк")
                    return True
                
                time.sleep(3)
            
            print("⚠️ Таймаут ожидания загрузки данных")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка ожидания данных: {e}")
            return False
    
    def _check_loading_indicators(self) -> bool:
        """Проверка активных загрузочных индикаторов"""
        try:
            for selector in self.selectors['loading']:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        return True
            return False
        except:
            return False
    
    def _find_data_rows(self) -> list:
        """Поиск строк данных"""
        all_rows = []
        
        for selector in self.selectors['data_rows']:
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_rows.extend(rows)
            except:
                continue
        
        # Удаляем дубликаты
        unique_rows = []
        seen = set()
        for row in all_rows:
            row_id = id(row)
            if row_id not in seen:
                seen.add(row_id)
                unique_rows.append(row)
        
        return unique_rows
    
    def wait_for_dynamic_content(self, timeout: int = 300) -> bool:
        """Ожидание динамического контента"""
        return self._wait_for_data_load(timeout)
    
    def debug_page_structure(self) -> bool:
        """Анализ структуры страницы"""
        try:
            print("🔍 АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ...")
            
            title = self.driver.title
            print(f"📄 Заголовок: {title}")
            
            # Проверяем Vue.js
            try:
                vue_info = self.driver.execute_script("""
                    return {
                        hasVue: typeof Vue !== 'undefined',
                        vueApp: document.querySelector('[data-app]') !== null
                    };
                """)
                print(f"⚙️ Vue.js статус: {vue_info}")
            except:
                print("⚠️ Не удалось проверить Vue.js")
            
            # Анализируем таблицы
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"📋 Найдено таблиц: {len(tables)}")
            
            for i, table in enumerate(tables):
                if table.is_displayed():
                    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                    print(f"  Таблица {i+1}: {len(rows)} строк")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка анализа страницы: {e}")
            return False