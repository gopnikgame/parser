"""
Менеджер пагинации для настройки отображения всех элементов
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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

class PaginationManager:
    """Менеджер пагинации для настройки отображения всех элементов"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
    
    def setup_pagination(self) -> bool:
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
    
    def try_multiple_pagination_strategies(self) -> bool:
        """Множественные стратегии работы с пагинацией"""
        try:
            print("🔧 Попытка различных стратегий пагинации...")
            
            # Стратегия 1: Vuetify пагинация
            for selector in self.config.PAGINATION_SELECTORS:
                try:
                    dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if dropdown.is_displayed():
                        print(f"✅ Найден dropdown пагинации: {selector}")
                        
                        # Кликаем на dropdown
                        ActionChains(self.driver).move_to_element(dropdown).click().perform()
                        time.sleep(2)
                        
                        # Ищем опцию "All" или максимальное значение
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
                                print(f"✅ Выбрана опция 'All'")
                                time.sleep(5)
                                return True
                            except:
                                continue
                        
                        # Если "All" не найдено, ищем максимальное число
                        try:
                            max_options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'v-list__tile__title') and text() > '50']")
                            if max_options:
                                max_option = max(max_options, key=lambda x: int(x.text) if x.text.isdigit() else 0)
                                max_option.click()
                                print(f"✅ Выбрана максимальная опция: {max_option.text}")
                                time.sleep(5)
                                return True
                        except:
                            pass
                        
                        # Закрываем dropdown
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        
                except Exception as e:
                    continue
            
            # Стратегия 2: Проверяем наличие кнопок пагинации и кликаем "последняя страница"
            try:
                last_page_selectors = [
                    ".v-pagination__navigation--end",
                    ".pagination .last",
                    "[aria-label*='last page']",
                    "[aria-label*='последняя']"
                ]
                
                for selector in last_page_selectors:
                    try:
                        last_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if last_button.is_displayed() and last_button.is_enabled():
                            last_button.click()
                            print(f"✅ Переход на последнюю страницу")
                            time.sleep(5)
                            return True
                    except:
                        continue
            except:
                pass
            
            # Стратегия 3: JavaScript принудительная загрузка всех данных
            try:
                print("🔧 Попытка JavaScript принудительной