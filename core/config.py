# Конфигурация парсера с возможностью тонкой настройки
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class ParserConfig:
    """Централизованная конфигурация парсера"""
    
    # Таймауты (в секундах)
    PAGE_LOAD_TIMEOUT: int = 120
    ELEMENT_WAIT_TIMEOUT: int = 30
    DIALOG_WAIT_TIMEOUT: int = 15
    NETWORK_IDLE_TIMEOUT: int = 10
    
    # Повторные попытки
    MAX_RETRIES: int = 5
    RETRY_DELAY_BASE: float = 2.0
    DIALOG_CLICK_RETRIES: int = 3
    
    # Селекторы для различных версий Vuetify
    TABLE_ROW_SELECTORS: List[str] = field(default_factory=lambda: [
        # Vuetify 3.x селекторы
        ".v-table tbody tr:not(.v-table__progress)",
        ".v-data-table tbody tr:not(.v-data-table__progress)",
        
        # Vuetify 2.x селекторы  
        ".v-datatable tbody tr",
        ".v-data-table .v-data-table__wrapper tbody tr",
        
        # Стандартные HTML селекторы
        "table tbody tr",
        "tbody tr",
        
        # Общие селекторы
        "tr[role='row']:not([role='columnheader'])",
        "div[role='row']"
    ])
    
    DIALOG_SELECTORS: List[str] = field(default_factory=lambda: [
        # Современные Vuetify 3.x
        ".v-overlay__content .v-card",
        ".v-dialog--active .v-card", 
        ".v-menu--active .v-card",
        
        # Vuetify 2.x
        ".v-dialog.v-dialog--active .v-card",
        ".v-menu__content--active .v-card",
        
        # Fallback селекторы
        "[role='dialog'][aria-hidden='false'] .v-card",
        "[role='dialog'][aria-hidden='false']",
        ".modal.show .modal-content",
        ".popup-content.active",
        
        # XPath селекторы
        "//div[contains(@class, 'v-dialog') and contains(@style, 'display') and not(contains(@style, 'none'))]//div[contains(@class, 'v-card')]"
    ])
    
    PAGINATION_SELECTORS: List[str] = field(default_factory=lambda: [
        # Vuetify 3.x
        ".v-data-table__footer .v-select",
        ".v-table__footer .v-select",
        
        # Vuetify 2.x
        ".v-datatable__actions .v-select",
        ".v-data-table-footer .v-select",
        
        # Общие
        ".v-pagination .v-select",
        "select[aria-label*='per page']",
        "select[aria-label*='rows']",
        ".per-page-select",
        ".rows-per-page select"
    ])
    
    # Настройки Chrome
    CHROME_OPTIONS: List[str] = field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-dev-shm-usage", 
        "--disable-gpu",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",
        "--remote-debugging-port=9222",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--max_old_space_size=4096",
        "--window-size=1920,1080"
    ])
    
    # Антибот настройки
    STEALTH_OPTIONS: List[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions-except",
        "--disable-plugins-discovery",
        "--lang=en-US,en",
        "--accept-lang=en-US,en;q=0.9"
    ])
    
    # Человекоподобные задержки
    HUMAN_DELAYS: Dict[str, tuple] = field(default_factory=lambda: {
        'click': (0.5, 2.0),
        'scroll': (1.0, 3.0), 
        'type': (0.1, 0.3),
        'page_load': (3.0, 8.0)
    })
    
    @classmethod
    def from_env(cls) -> 'ParserConfig':
        """Загрузка конфигурации из переменных окружения"""
        config = cls()
        
        # Загружаем таймауты
        config.PAGE_LOAD_TIMEOUT = int(os.getenv('PARSER_PAGE_TIMEOUT', 120))
        config.ELEMENT_WAIT_TIMEOUT = int(os.getenv('PARSER_ELEMENT_TIMEOUT', 30))
        config.DIALOG_WAIT_TIMEOUT = int(os.getenv('PARSER_DIALOG_TIMEOUT', 15))
        
        # Загружаем retry настройки
        config.MAX_RETRIES = int(os.getenv('PARSER_MAX_RETRIES', 5))
        config.RETRY_DELAY_BASE = float(os.getenv('PARSER_RETRY_DELAY', 2.0))
        
        # Chrome настройки
        if os.getenv('CHROME_HEADLESS', 'true').lower() == 'true':
            config.CHROME_OPTIONS.append("--headless=new")
            
        return config
    
    def get_click_delay(self) -> tuple:
        """Получить случайную задержку для кликов"""
        return self.HUMAN_DELAYS['click']
    
    def get_scroll_delay(self) -> tuple:
        """Получить случайную задержку для прокрутки"""
        return self.HUMAN_DELAYS['scroll']