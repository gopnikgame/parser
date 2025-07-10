# Стратегии восстановления после ошибок
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, List, Callable, Optional
from ..core.config import ParserConfig

class SmartErrorRecovery:
    """Система умного восстановления после ошибок"""
    
    def __init__(self, driver: webdriver.Chrome, config: ParserConfig):
        self.driver = driver
        self.config = config
        self.error_patterns = {
            'cloudflare_protection': [
                'cloudflare', 'checking your browser', 'security check',
                'ddos protection', 'bot protection'
            ],
            'rate_limiting': [
                'too many requests', 'rate limit', 'slow down',
                'temporarily blocked', 'throttled'
            ],
            'page_not_loaded': [
                'no data available', 'loading', 'please wait',
                'still loading', 'fetching data'
            ],
            'network_error': [
                'network error', 'connection timeout', 'failed to load',
                'dns error', 'connection refused'
            ],
            'javascript_error': [
                'script error', 'uncaught', 'undefined is not a function',
                'cannot read property', 'vue is not defined'
            ]
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
            # Ждем прохождения проверки
            wait_time = random.uniform(15, 30)
            print(f"⏳ Ожидание {wait_time:.1f}с для прохождения проверки...")
            time.sleep(wait_time)
            
            # Проверяем, прошла ли проверка
            if self._check_page_accessibility():
                print("✅ Cloudflare проверка пройдена")
                return True
            
            # Если не прошла - пробуем обновить страницу
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
            # Экспоненциальная задержка
            wait_time = random.uniform(30, 90)
            print(f"⏳ Пауза {wait_time:.1f}с для снятия ограничений...")
            time.sleep(wait_time)
            
            # Проверяем доступность
            return self._check_page_accessibility()
            
        except Exception as e:
            print(f"❌ Ошибка обработки rate limit: {e}")
            return False
    
    def _handle_page_reload(self, context: str, error_text: str) -> bool:
        """Обработка проблем загрузки страницы"""
        print("🔄 Перезагрузка страницы...")
        
        reload_strategies = [
            self._soft_reload,
            self._hard_reload, 
            self._navigate_fresh,
            self._clear_cache_reload
        ]
        
        for strategy in reload_strategies:
            try:
                print(f"🔄 Применяем стратегию: {strategy.__name__}")
                
                if strategy():
                    # Ждем загрузки и проверяем готовность
                    if self._wait_for_page_ready():
                        return True
                        
            except Exception as e:
                print(f"⚠️ Стратегия {strategy.__name__} не сработала: {e}")
                continue
        
        return False
    
    def _handle_network_error(self, context: str, error_text: str) -> bool:
        """Обработка сетевых ошибок"""
        print("🌐 Обработка сетевой ошибки...")
        
        try:
            # Проверяем соединение
            if not self._check_internet_connection():
                print("❌ Нет интернет соединения")
                return False
            
            # Пробуем переподключиться
            current_url = self.driver.current_url
            
            # Пауза перед повторным подключением
            time.sleep(random.uniform(10, 20))
            
            # Переход на страницу заново
            self.driver.get(current_url)
            
            return self._wait_for_page_ready()
            
        except Exception as e:
            print(f"❌ Ошибка обработки сетевой ошибки: {e}")
            return False
    
    def _handle_javascript_error(self, context: str, error_text: str) -> bool:
        """Обработка JavaScript ошибок"""
        print("🔧 Обработка JavaScript ошибки...")
        
        try:
            # Очищаем console errors
            try:
                self.driver.get_log('browser')
            except:
                pass
            
            # Перезагружаем страницу для сброса состояния JS
            self.driver.refresh()
            
            # Ждем полной загрузки
            if self._wait_for_page_ready():
                # Проверяем, что Vue.js загружен
                vue_ready = self._check_vue_ready()
                if vue_ready:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка обработки JS ошибки: {e}")
            return False
    
    def _handle_generic_error(self, context: str, error_text: str) -> bool:
        """Обработка общих ошибок"""
        print("🔧 Обработка общей ошибки...")
        
        try:
            # Базовая стратегия восстановления
            time.sleep(random.uniform(5, 10))
            
            # Проверяем состояние драйвера
            if not self._check_driver_health():
                return False
            
            # Обновляем страницу
            self.driver.refresh()
            
            return self._wait_for_page_ready()
            
        except Exception as e:
            print(f"❌ Ошибка общего восстановления: {e}")
            return False
    
    def _soft_reload(self) -> bool:
        """Мягкая перезагрузка"""
        try:
            self.driver.refresh()
            time.sleep(5)
            return True
        except:
            return False
    
    def _hard_reload(self) -> bool:
        """Жесткая перезагрузка"""
        try:
            self.driver.execute_script("location.reload(true);")
            time.sleep(8)
            return True
        except:
            return False
    
    def _navigate_fresh(self) -> bool:
        """Свежий переход на URL"""
        try:
            current_url = self.driver.current_url
            self.driver.get(current_url)
            time.sleep(10)
            return True
        except:
            return False
    
    def _clear_cache_reload(self) -> bool:
        """Очистка кэша и перезагрузка"""
        try:
            # Очищаем localStorage и sessionStorage
            self.driver.execute_script("""
                localStorage.clear();
                sessionStorage.clear();
                location.reload(true);
            """)
            time.sleep(10)
            return True
        except:
            return False
    
    def _check_page_accessibility(self) -> bool:
        """Проверка доступности страницы"""
        try:
            # Проверяем заголовок
            title = self.driver.title
            if not title or 'error' in title.lower():
                return False
            
            # Проверяем наличие основных элементов
            table = self.driver.find_elements(By.TAG_NAME, "table")
            if not table:
                return False
            
            return True
            
        except:
            return False
    
    def _wait_for_page_ready(self, timeout: int = 60) -> bool:
        """Ожидание готовности страницы"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # Ждем готовности DOM
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Ждем появления таблицы
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            # Дополнительное время для загрузки данных
            time.sleep(5)
            
            return True
            
        except TimeoutException:
            return False
        except Exception:
            return False
    
    def _check_vue_ready(self) -> bool:
        """Проверка готовности Vue.js"""
        try:
            vue_checks = [
                "return typeof Vue !== 'undefined'",
                "return document.querySelector('[data-app]') !== null",
                "return document.querySelector('.v-application') !== null"
            ]
            
            for check in vue_checks:
                try:
                    if self.driver.execute_script(check):
                        return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def _check_driver_health(self) -> bool:
        """Проверка состояния драйвера"""
        try:
            _ = self.driver.current_url
            return True
        except:
            return False
    
    def _check_internet_connection(self) -> bool:
        """Проверка интернет соединения"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except:
            return False
    
    def get_recovery_stats(self) -> Dict:
        """Получение статистики восстановления"""
        stats = self.recovery_stats.copy()
        if stats['total_errors'] > 0:
            stats['success_rate'] = (stats['successful_recoveries'] / stats['total_errors']) * 100
        else:
            stats['success_rate'] = 0
        return stats