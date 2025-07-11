# Стратегии восстановления после ошибок
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, List, Callable, Optional

# Используем относительный импорт для лучшей совместимости
try:
    from ..core.config import ParserConfig
except ImportError:
    # Fallback для случаев когда относительный импорт не работает
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import ParserConfig

class SmartErrorRecovery:
    """Система умного восстановления после ошибок"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
        self.error_patterns = {
            'cloudflare_protection': ['cloudflare', 'checking your browser', 'security check'],
            'rate_limiting': ['too many requests', 'rate limit', 'slow down'],
            'page_not_loaded': ['no data available', 'loading', 'please wait'],
            'network_error': ['network error', 'connection timeout', 'failed to load'],
            'javascript_error': ['script error', 'uncaught', 'undefined is not a function']
        }
        
        self.recovery_stats = {
            'total_errors': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'recovery_methods_used': {}
        }
    
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """Умная обработка ошибок с автовосстановлением"""
        self.recovery_stats['total_errors'] += 1
        
        error_text = str(error).lower()
        error_type = self._classify_error(error_text)
        
        print(f"🛠️ Обнаружена ошибка типа '{error_type}': {error}")
        
        recovery_strategies = {
            'cloudflare_protection': self._handle_cloudflare,
            'rate_limiting': self._handle_rate_limit,
            'page_not_loaded': self._handle_page_reload,
            'network_error': self._handle_network_error,
            'javascript_error': self._handle_javascript_error,
            'unknown': self._handle_generic_error
        }
        
        strategy = recovery_strategies.get(error_type, recovery_strategies['unknown'])
        
        try:
            success = strategy(context, error_text)
            
            if success:
                self.recovery_stats['successful_recoveries'] += 1
                method_name = strategy.__name__
                self.recovery_stats['recovery_methods_used'][method_name] = \
                    self.recovery_stats['recovery_methods_used'].get(method_name, 0) + 1
            else:
                self.recovery_stats['failed_recoveries'] += 1
                
            return success
            
        except Exception as recovery_error:
            print(f"❌ Ошибка во время восстановления: {recovery_error}")
            self.recovery_stats['failed_recoveries'] += 1
            return False
    
    def _classify_error(self, error_text: str) -> str:
        """Классификация типа ошибки"""
        for error_type, patterns in self.error_patterns.items():
            if any(pattern in error_text for pattern in patterns):
                return error_type
        return 'unknown'
    
    def _handle_cloudflare(self, context: str, error_text: str) -> bool:
        """Обработка Cloudflare защиты"""
        print("🛡️ Обнаружена Cloudflare защита...")
        
        try:
            wait_time = random.uniform(15, 30)
            print(f"⏳ Ожидание {wait_time:.1f}с для прохождения проверки...")
            time.sleep(wait_time)
            
            if self._check_page_accessibility():
                print("✅ Cloudflare проверка пройдена")
                return True
            
            print("🔄 Обновление страницы...")
            self.driver.refresh()
            time.sleep(random.uniform(10, 20))
            
            return self._check_page_accessibility()
            
        except Exception as e:
            print(f"❌ Ошибка обработки Cloudflare: {e}")
            return False
    
    def _handle_rate_limit(self, context: str, error_text: str) -> bool:
        """Обработка ограничений скорости"""
        print("⏳ Обнаружено ограничение скорости...")
        
        try:
            wait_time = random.uniform(30, 90)
            print(f"⏳ Пауза {wait_time:.1f}с для снятия ограничений...")
            time.sleep(wait_time)
            
            return self._check_page_accessibility()
            
        except Exception as e:
            print(f"❌ Ошибка обработки rate limit: {e}")
            return False
    
    def _handle_page_reload(self, context: str, error_text: str) -> bool:
        """Обработка проблем загрузки страницы"""
        print("🔄 Перезагрузка страницы...")
        
        try:
            self.driver.refresh()
            time.sleep(random.uniform(5, 10))
            return self._wait_for_page_ready()
        except Exception as e:
            print(f"❌ Ошибка перезагрузки: {e}")
            return False
    
    def _handle_network_error(self, context: str, error_text: str) -> bool:
        """Обработка сетевых ошибок"""
        print("🌐 Обработка сетевой ошибки...")
        
        try:
            current_url = self.driver.current_url
            time.sleep(random.uniform(10, 20))
            self.driver.get(current_url)
            return self._wait_for_page_ready()
            
        except Exception as e:
            print(f"❌ Ошибка обработки сетевой ошибки: {e}")
            return False
    
    def _handle_javascript_error(self, context: str, error_text: str) -> bool:
        """Обработка JavaScript ошибок"""
        print("🔧 Обработка JavaScript ошибки...")
        
        try:
            self.driver.refresh()
            time.sleep(random.uniform(5, 10))
            return self._wait_for_page_ready()
            
        except Exception as e:
            print(f"❌ Ошибка обработки JavaScript ошибки: {e}")
            return False
    
    def _handle_generic_error(self, context: str, error_text: str) -> bool:
        """Обработка общих ошибок"""
        print("🔧 Обработка общей ошибки...")
        
        try:
            time.sleep(random.uniform(5, 15))
            self.driver.refresh()
            return self._wait_for_page_ready()
            
        except Exception as e:
            print(f"❌ Ошибка обработки общей ошибки: {e}")
            return False
    
    def _check_page_accessibility(self) -> bool:
        """Проверка доступности страницы"""
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_text = self.driver.page_source.lower()
            blocking_patterns = ['cloudflare', 'checking your browser', 'security check']
            
            return not any(pattern in page_text for pattern in blocking_patterns)
            
        except Exception:
            return False
    
    def _wait_for_page_ready(self) -> bool:
        """Ожидание готовности страницы"""
        try:
            WebDriverWait(self.driver, self.config.PAGE_TIMEOUT).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            time.sleep(random.uniform(2, 5))
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return True
            except TimeoutException:
                return False
                
        except Exception:
            return False
    
    def get_recovery_stats(self) -> Dict[str, any]:
        """Получение статистики восстановления"""
        stats = self.recovery_stats.copy()
        if stats['total_errors'] > 0:
            stats['success_rate'] = (stats['successful_recoveries'] / stats['total_errors']) * 100
        else:
            stats['success_rate'] = 0
        return stats
    
    def reset_stats(self):
        """Сброс статистики восстановления"""
        self.recovery_stats = {
            'total_errors': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'recovery_methods_used': {}
        }