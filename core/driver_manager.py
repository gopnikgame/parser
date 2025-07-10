# Умный менеджер драйвера с антибот защитой и восстановлением
import time
import random
import psutil
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from typing import Optional
from .config import ParserConfig

class SmartDriverManager:
    """Интеллектуальный менеджер Chrome драйвера"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self._session_id = None
        
    def create_stealth_driver(self) -> webdriver.Chrome:
        """Создание скрытого драйвера с антибот защитой"""
        self._kill_existing_chrome()
        
        options = webdriver.ChromeOptions()
        
        # Добавляем базовые опции
        for option in self.config.CHROME_OPTIONS:
            options.add_argument(option)
            
        # Добавляем stealth опции
        for option in self.config.STEALTH_OPTIONS:
            options.add_argument(option)
            
        # Антибот настройки
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Реалистичный User-Agent
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Удаляем webdriver свойства
            self._inject_stealth_scripts(driver)
            
            self.driver = driver
            self._session_id = driver.session_id
            
            print("✅ Stealth Chrome драйвер успешно создан")
            return driver
            
        except WebDriverException as e:
            print(f"❌ Ошибка создания драйвера: {e}")
            raise
    
    def _inject_stealth_scripts(self, driver: webdriver.Chrome):
        """Внедрение stealth скриптов"""
        stealth_script = """
        // Удаляем webdriver свойства
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Подделываем геолокацию
        Object.defineProperty(navigator, 'geolocation', {
            get: () => ({
                getCurrentPosition: () => {},
                watchPosition: () => {},
                clearWatch: () => {}
            }),
        });
        
        // Подделываем языки
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Подделываем плагины
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Chrome PDF Plugin"},
                    description: "Chrome PDF Plugin",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            ],
        });
        
        // Подделываем разрешения
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Скрываем автоматизацию в Chrome объекте
        if (window.chrome) {
            Object.defineProperty(window.chrome, 'runtime', {
                get: () => ({
                    onConnect: undefined,
                    onMessage: undefined
                }),
            });
        }
        """
        
        try:
            driver.execute_script(stealth_script)
        except Exception as e:
            print(f"⚠️ Не удалось внедрить stealth скрипты: {e}")
    
    def _kill_existing_chrome(self):
        """Завершение всех процессов Chrome"""
        try:
            # Завершаем процессы через psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except:
                        try:
                            proc.kill()
                        except:
                            pass
            
            # Backup метод через системные команды
            subprocess.run(['pkill', '-f', 'chrome'], check=False, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'chromium'], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(2)
            print("✅ Существующие процессы Chrome завершены")
            
        except Exception as e:
            print(f"⚠️ Не удалось завершить процессы Chrome: {e}")
    
    def is_driver_alive(self) -> bool:
        """Проверка жизни драйвера"""
        if not self.driver:
            return False
            
        try:
            # Проверяем заголовок страницы
            _ = self.driver.title
            return True
        except:
            return False
    
    def recover_driver(self) -> bool:
        """Восстановление драйвера после сбоя"""
        print("🔄 Попытка восстановления драйвера...")
        
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            self.driver = self.create_stealth_driver()
            return True
            
        except Exception as e:
            print(f"❌ Не удалось восстановить драйвер: {e}")
            return False
    
    def quit_driver(self):
        """Безопасное завершение драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Драйвер безопасно завершен")
            except:
                pass
            finally:
                self.driver = None
                self._session_id = None
        
        self._kill_existing_chrome()
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Получение текущего драйвера"""
        return self.driver