# Задача: автоматически собирать публичные данные с сайта https://dnscrypt.info/public-servers
# Поиск серверов по имени и извлечение IP-адресов для обновления списков GitHub
# Работаем только с IPv4 адресами и протоколами DNSCrypt/DNSCrypt relay

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import re
import time
import subprocess
import urllib.request
import os
import requests
import base64
import json
import signal
import psutil
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_default_chrome_options():
    """ИСПРАВЛЕННЫЕ опции Chrome для стабильной работы"""
    options = webdriver.ChromeOptions()
    
    # Базовые опции для Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    
    # КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ для Docker
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Настройки для стабильности
    options.add_argument("--max_old_space_size=4096")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    
    # Размер окна
    options.add_argument("--window-size=1920,1080")
    
    # User agent
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Headless режим
    if os.getenv('CHROME_HEADLESS', 'true').lower() == 'true':
        options.add_argument("--headless=new")
    
    # Отключаем автоматизацию
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return options

def kill_existing_chrome():
    """Убиваем все процессы Chrome перед запуском"""
    try:
        # Убиваем все процессы Chrome
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
        
        subprocess.run(['pkill', '-f', 'chrome'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'chromium'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ Существующие процессы Chrome завершены")
    except Exception as e:
        print(f"⚠️ Не удалось завершить процессы Chrome: {e}")

def setup_driver():
    """Настройка драйвера Chrome для Vue.js приложения"""
    kill_existing_chrome()
    
    try:
        options = get_default_chrome_options()
        driver = webdriver.Chrome(options=options)
        
        # Убираем автоматические свойства WebDriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome успешно запущен для Vue.js")
        return driver
        
    except WebDriverException as e:
        print(f"❌ Ошибка запуска Chrome: {str(e)}")
        return None

def wait_for_vue_app_ready(driver, timeout=60):
    """ИСПРАВЛЕННОЕ ожидание готовности Vue.js приложения"""
    try:
        print("⏳ Ожидание загрузки Vue.js приложения...")
        
        # Увеличенное время ожидания базовой загрузки
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Ждем загрузки Vue приложения с несколькими попытками
        vue_ready = False
        for attempt in range(5):
            try:
                # Проверяем различные признаки загрузки Vue
                vue_checks = [
                    "return typeof Vue !== 'undefined'",
                    "return document.querySelector('[data-app]') !== null",
                    "return document.querySelector('.v-application') !== null",
                    "return document.querySelector('table') !== null",
                    "return document.querySelector('.v-data-table') !== null"
                ]
                
                for check in vue_checks:
                    try:
                        if driver.execute_script(check):
                            vue_ready = True
                            break
                    except:
                        continue
                
                if vue_ready:
                    break
                    
                print(f"⏳ Попытка {attempt + 1}/5 загрузки Vue.js...")
                time.sleep(10)
                
            except Exception as e:
                print(f"⚠️ Ошибка проверки Vue.js (попытка {attempt + 1}): {e}")
                time.sleep(5)
        
        if vue_ready:
            print("✅ Vue.js приложение загружено")
            # Дополнительное ожидание для полной загрузки данных
            time.sleep(10)
            return True
        else:
            print("⚠️ Vue.js приложение не загрузилось полностью")
            return False
            
    except TimeoutException:
        print("⚠️ Таймаут загрузки Vue.js приложения")
        return False

def wait_for_datatable_load(driver, timeout=60):
    """ИСПРАВЛЕННОЕ ожидание загрузки данных в таблицу"""
    try:
        print("⏳ Ожидание загрузки данных в таблицу...")
        
        # Ждем появления таблицы
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .v-data-table, .v-table"))
            )
        except TimeoutException:
            print("⚠️ Таблица не найдена")
            return False
        
        # Ждем загрузки данных с множественными проверками
        for attempt in range(10):
            try:
                # Проверяем различные селекторы строк
                row_selectors = [
                    "table tbody tr",
                    ".v-data-table tbody tr",
                    ".v-table tbody tr", 
                    "tr[role='row']",
                    ".v-data-table__wrapper tbody tr"
                ]
                
                for selector in row_selectors:
                    rows = driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_rows = [row for row in rows if row.is_displayed() and row.text.strip()]
                    
                    if len(visible_rows) > 10:  # Если найдено достаточно строк
                        print(f"✅ Найдено {len(visible_rows)} строк данных")
                        return True
                
                print(f"⏳ Попытка {attempt + 1}/10 загрузки данных...")
                time.sleep(6)
                
            except Exception as e:
                print(f"⚠️ Ошибка проверки данных (попытка {attempt + 1}): {e}")
                time.sleep(3)
        
        print("⚠️ Данные в таблице не загрузились")
        return False
        
    except TimeoutException:
        print("⚠️ Данные в таблице не загрузились")
        return False
        
    except TimeoutException:
        print("⚠️ Данные в таблице не загрузились")
        return False

def set_pagination_to_all(driver):
    """Установка пагинации на 'All' для отображения всех серверов"""
    try:
        print("🔧 Установка пагинации на 'All'...")
        
        # Находим dropdown пагинации
        pagination_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".v-datatable__actions .v-select"))
        )
        
        # Кликаем на dropdown
        pagination_dropdown.click()
        time.sleep(2)
        
        # Ждем появления списка опций
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".v-menu__content .v-list"))
        )
        
        # Находим и кликаем на опцию "All"
        all_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='v-list__tile__title'][text()='All']"))
        )
        all_option.click()
        
        print("✅ Пагинация установлена на 'All'")
        
        # Ждем обновления таблицы
        time.sleep(3)
        wait_for_datatable_load(driver)
        
        return True
        
    except Exception as e:
        print(f"⚠️ Не удалось установить пагинацию: {e}")
        return False

def get_all_server_rows(driver):
    """ИСПРАВЛЕННОЕ получение всех строк серверов"""
    try:
        print("🔍 Поиск строк серверов...")
        
        # Ждем немного для стабилизации
        time.sleep(5)
        
        # Множественные селекторы для поиска строк
        row_selectors = [
            "table tbody tr",
            ".v-data-table tbody tr",
            ".v-table tbody tr",
            "tr[role='row']",
            ".v-data-table__wrapper tbody tr",
            ".datatable tbody tr",
            "tbody tr"
        ]
        
        all_rows = []
        
        for selector in row_selectors:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, selector)
                for row in rows:
                    if row.is_displayed() and row.text.strip() and "No data available" not in row.text:
                        # Проверяем что в строке есть имя сервера
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3 and cells[0].text.strip():
                            all_rows.append(row)
                
                if len(all_rows) > 50:  # Если нашли достаточно строк, останавливаемся
                    break
                    
            except Exception as e:
                continue
        
        # Убираем дубликаты
        unique_rows = []
        seen_texts = set()
        
        for row in all_rows:
            row_text = row.text.strip()
            if row_text not in seen_texts:
                seen_texts.add(row_text)
                unique_rows.append(row)
        
        print(f"✅ Найдено {len(unique_rows)} уникальных строк серверов")
        return unique_rows
        
    except Exception as e:
        print(f"❌ Ошибка получения строк серверов: {e}")
        return []

def extract_server_info_from_row(driver, row):
    """Улучшенное извлечение информации о сервере из строки таблицы"""
    try:
        # Получаем ячейки строки
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) < 3:
            return None
        
        # Извлекаем имя сервера (первая ячейка)
        name_cell = cells[0]
        server_name = name_cell.text.strip()
        
        if not server_name or server_name == "No data available":
            return None
        
        # УЛУЧШЕНИЕ: Множественные стратегии поиска кликабельного элемента
        clickable_element = None
        click_strategies = [
            lambda: name_cell.find_element(By.CSS_SELECTOR, "span"),
            lambda: name_cell.find_element(By.CSS_SELECTOR, "a"),
            lambda: name_cell.find_element(By.CSS_SELECTOR, "button"),
            lambda: name_cell.find_element(By.CSS_SELECTOR, "[role='button']"),
            lambda: name_cell.find_element(By.CSS_SELECTOR, "*[onclick]"),
            lambda: name_cell  # Если ничего не найдено, кликаем по ячейке
        ]
        
        for strategy in click_strategies:
            try:
                clickable_element = strategy()
                break
            except:
                continue
        
        if not clickable_element:
            return None
        
        # Прокручиваем к элементу и кликаем
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_element)
        time.sleep(1)
        
        # УЛУЧШЕНИЕ: Множественные попытки клика
        click_attempts = [
            lambda: clickable_element.click(),
            lambda: ActionChains(driver).move_to_element(clickable_element).click().perform(),
            lambda: driver.execute_script("arguments[0].click();", clickable_element),
            lambda: ActionChains(driver).move_to_element(clickable_element).pause(0.5).click().perform()
        ]
        
        dialog = None
        for i, click_method in enumerate(click_attempts):
            try:
                click_method()
                time.sleep(2 + i)  # Увеличиваем задержку с каждой попыткой
                
                # УЛУЧШЕНИЕ: Расширенный поиск диалогов
                dialog_selectors = [
                    ".v-dialog.v-dialog--active .v-card",
                    ".v-dialog.v-dialog--active",
                    ".v-menu__content--active .v-card",
                    ".v-menu__content--active",
                    ".v-tooltip__content--fixed",
                    "[role='dialog'] .v-card",
                    "[role='dialog']",
                    ".v-overlay--active .v-card",
                    ".v-overlay--active",
                    ".modal.show",
                    ".popup.active"
                ]
                
                for selector in dialog_selectors:
                    try:
                        dialog = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if dialog.is_displayed() and dialog.text.strip():
                            break
                    except:
                        continue
                
                if dialog and dialog.text.strip():
                    break
                    
            except Exception as e:
                continue
        
        if not dialog or not dialog.text.strip():
            print(f"⚠️ Диалог не найден для {server_name}")
            return None
        
        # Извлекаем текст из диалога
        dialog_text = dialog.text
        
        # УЛУЧШЕНИЕ: Множественные способы закрытия диалога
        close_methods = [
            lambda: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE),
            lambda: dialog.find_element(By.CSS_SELECTOR, "button[aria-label*='close']").click(),
            lambda: dialog.find_element(By.CSS_SELECTOR, ".v-btn--icon").click(),
            lambda: driver.execute_script("arguments[0].style.display = 'none';", dialog)
        ]
        
        for close_method in close_methods:
            try:
                close_method()
                time.sleep(1)
                break
            except:
                continue
        
        # Парсим информацию из диалога
        info = parse_server_info(dialog_text, server_name)
        
        return info
        
    except Exception as e:
        print(f"❌ Ошибка извлечения информации о сервере: {e}")
        return None

def parse_server_info(dialog_text, server_name):
    """Парсинг информации сервера из диалога"""
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
    
    # Ищем IP адрес
    ip_patterns = [
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        r'Address[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        r'IP[^:]*:?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    ]
    
    for pattern in ip_patterns:
        matches = re.findall(pattern, dialog_text)
        for ip in matches:
            octets = ip.split('.')
            if all(0 <= int(octet) <= 255 for octet in octets):
                info['ip'] = ip
                break
        if info['ip']:
            break
    
    # Ищем протокол
    if 'DNSCrypt relay' in dialog_text:
        info['protocol'] = 'DNSCrypt relay'
    elif 'DNSCrypt' in dialog_text:
        info['protocol'] = 'DNSCrypt'
    elif 'DoH' in dialog_text:
        info['protocol'] = 'DoH'
    
    # Ищем флаги
    text_lower = dialog_text.lower()
    info['dnssec'] = 'dnssec' in text_lower and ('true' in text_lower or 'yes' in text_lower)
    info['no_filters'] = 'no filter' in text_lower and ('true' in text_lower or 'yes' in text_lower)
    info['no_logs'] = 'no log' in text_lower and ('true' in text_lower or 'yes' in text_lower)
    
    return info

def download_file(url, filename):
    """Скачивание файла с GitHub"""
    try:
        print(f"📥 Скачиваем {filename} с GitHub...")
        
        # Преобразуем GitHub URL в raw URL
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        urllib.request.urlretrieve(raw_url, filename)
        print(f"✅ Файл {filename} успешно скачан")
        return True
    except Exception as e:
        print(f"❌ Ошибка скачивания {filename}: {e}")
        return False

def parse_config_file(filename):
    """Парсинг файлов конфигурации для извлечения имен серверов"""
    servers = []
    current_country = None
    current_city = None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith('#'):
                continue
                
            # Страна в квадратных скобках
            if line.startswith('[') and line.endswith(']'):
                current_country = line[1:-1]
                current_city = None
                continue
                
            # Город в кавычках
            if line.startswith('"') and line.endswith('"'):
                current_city = line[1:-1]
                continue
                
            # Имя сервера (не начинается с [ или ")
            if not line.startswith('[') and not line.startswith('"') and current_country:
                # Извлекаем имя сервера (до первого пробела или табуляции)
                server_name = line.split()[0] if line.split() else line
                
                servers.append({
                    'name': server_name,
                    'country': current_country,
                    'city': current_city,
                    'original_line': line
                })
                
        print(f"✅ Извлечено {len(servers)} серверов из {filename}")
        return servers
        
    except Exception as e:
        print(f"❌ Ошибка парсинга {filename}: {e}")
        return []

def process_servers_from_website(driver, target_servers):
    """Обработка серверов прямо с сайта по списку целевых серверов"""
    print(f"\n🔍 Поиск {len(target_servers)} серверов на сайте...")
    
    # Получаем все строки серверов с сайта
    all_rows = get_all_server_rows(driver)
    if not all_rows:
        print("❌ Не удалось получить строки серверов")
        return {}, 0
    
    # Создаем список имен целевых серверов для быстрого поиска
    target_names = {server['name'] for server in target_servers}
    
    servers_data = {}
    successful_count = 0
    
    for i, row in enumerate(all_rows, 1):
        try:
            # Получаем имя сервера из первой ячейки
            first_cell = row.find_element(By.TAG_NAME, "td")
            server_name = first_cell.text.strip()
            
            # Проверяем, нужен ли нам этот сервер
            if server_name not in target_names:
                continue
            
            print(f"\n[{successful_count + 1}] Обрабатываем {server_name}...")
            
            # Извлекаем информацию о сервере
            info = extract_server_info_from_row(driver, row)
            
            if info and info['ip']:
                servers_data[server_name] = info
                successful_count += 1
                print(f"✅ {server_name} -> {info['ip']} ({info['protocol']})")
            else:
                print(f"⚠️ Не удалось получить данные для {server_name}")
            
            # Пауза между запросами
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Ошибка обработки строки {i}: {e}")
            continue
    
    print(f"\n📊 Успешно обработано: {successful_count}/{len(target_servers)} серверов")
    return servers_data, successful_count


def format_relay_line(server_info):
    """Форматирование строки релея"""
    if not server_info['ip']:
        return None
    
    name = server_info['name']
    protocol = server_info['protocol']
    ip = server_info['ip']
    
    return f"{name:<30} Anonymized DNS relay | {protocol} | {ip}"

def format_server_line(server_info):
    """Форматирование строки обычного сервера"""
    if not server_info['ip']:
        return None
    
    name = server_info['name']
    no_filter = "no filter" if server_info['no_filters'] else "filter"
    no_logs = "no logs" if server_info['no_logs'] else "logs"
    dnssec = "DNSSEC" if server_info['dnssec'] else "-----"
    protocol = server_info['protocol']
    ip = server_info['ip']
    
    return f"{name:<30} {no_filter} | {no_logs} | {dnssec} | IPv4 server | {protocol} | {ip}"

def update_config_file(filename, servers_data, is_relay_file=False):
    """Обновление файла конфигурации с новыми данными"""
    try:
        print(f"📝 Обновляем файл {filename}...")
        
        # Читаем оригинальный файл
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated_lines = []
        updated_count = 0
        
        for line in lines:
            original_line = line.rstrip()
            
            # Пропускаем комментарии, пустые строки, страны и города
            if (not original_line or original_line.startswith('#') or 
                (original_line.startswith('[') and original_line.endswith(']')) or
                (original_line.startswith('"') and original_line.endswith('"'))):
                updated_lines.append(line)
                continue
            
            # Ищем имя сервера в данных
            server_name = original_line.split()[0] if original_line.split() else ""
            
            if server_name in servers_data:
                # Форматируем строку в зависимости от типа файла
                if is_relay_file:
                    new_line = format_relay_line(servers_data[server_name])
                else:
                    new_line = format_server_line(servers_data[server_name])
                
                if new_line:
                    updated_lines.append(new_line + '\n')
                    updated_count += 1
                    print(f"✅ Обновлен: {server_name} -> {servers_data[server_name]['ip']}")
                else:
                    updated_lines.append(line)
            else:
                # Оставляем оригинальную строку
                updated_lines.append(line)
        
        output_dir = '/app/output' if os.path.exists('/app') else './output'
        
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, mode=0o755, exist_ok=True)
        except PermissionError:
            print(f"⚠️ Не удалось создать директорию {output_dir}, используем текущую")
            output_dir = '.'
        
        backup_filename = os.path.join(output_dir, f"{os.path.basename(filename)}.original_backup")
        try:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"💾 Резервная копия создана: {backup_filename}")
        except PermissionError:
            print(f"⚠️ Не удалось создать резервную копию, продолжаем без неё")
        
        output_filename = os.path.join(output_dir, os.path.basename(filename))
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            print(f"✅ Файл {output_filename} обновлен. Обновлено серверов: {updated_count}")
        except PermissionError:
            # Пробуем записать в альтернативную директорию
            alt_filename = f"./{os.path.basename(filename)}"
            try:
                with open(alt_filename, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
                print(f"✅ Файл {alt_filename} обновлен в текущей директории. Обновлено серверов: {updated_count}")
            except Exception as e:
                print(f"❌ Критическая ошибка записи файла: {e}")
                return 0
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Ошибка обновления файла {filename}: {e}")
        return 0


# GitHub функции (остаются без изменений)
def get_github_config():
    """Настройки GitHub репозитория из переменных окружения"""
    return {
        'owner': os.getenv('GITHUB_OWNER', 'gopnikgame'),
        'repo': os.getenv('GITHUB_REPO', 'Installer_dnscypt'),
        'token': os.getenv('GITHUB_TOKEN'),
        'branch': os.getenv('GITHUB_BRANCH', 'main')
    }

def create_github_commit(files_to_commit, commit_message):
    """Создание коммита с несколькими файлами через GitHub API"""
    try:
        config = get_github_config()
        
        if not config['token']:
            print("❌ GitHub token не найден в переменных окружения")
            return False
        
        headers = {
            'Authorization': f"token {config['token']}",
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Получаем последний коммит
        url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/refs/heads/{config['branch']}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Не удалось получить последний коммит: {response.status_code}")
            return False
        
        last_commit_sha = response.json()['object']['sha']
        
        # Получаем дерево последнего коммита
        url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/commits/{last_commit_sha}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Не удалось получить дерево коммита: {response.status_code}")
            return False
        
        base_tree_sha = response.json()['tree']['sha']
        
        # Создаем новые blob'ы для файлов
        tree_items = []
        
        for local_file, github_path in files_to_commit.items():
            print(f"📤 Подготовка {local_file} -> {github_path}")
            
            # Читаем файл
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Создаем blob
            blob_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/blobs"
            blob_data = {
                'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                'encoding': 'base64'
            }
            
            response = requests.post(blob_url, headers=headers, data=json.dumps(blob_data))
            if response.status_code != 201:
                print(f"❌ Не удалось создать blob для {local_file}: {response.status_code}")
                return False
            
            blob_sha = response.json()['sha']
            
            tree_items.append({
                'path': github_path,
                'mode': '100644',
                'type': 'blob',
                'sha': blob_sha
            })
        
        # Создаем новое дерево
        tree_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/trees"
        tree_data = {
            'base_tree': base_tree_sha,
            'tree': tree_items
        }
        
        response = requests.post(tree_url, headers=headers, data=json.dumps(tree_data))
        if response.status_code != 201:
            print(f"❌ Не удалось создать дерево: {response.status_code}")
            return False
        
        new_tree_sha = response.json()['sha']
        
        # Создаем коммит
        commit_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/commits"
        commit_data = {
            'message': commit_message,
            'tree': new_tree_sha,
            'parents': [last_commit_sha]
        }
        
        response = requests.post(commit_url, headers=headers, data=json.dumps(commit_data))
        if response.status_code != 201:
            print(f"❌ Не удалось создать коммит: {response.status_code}")
            return False
        
        new_commit_sha = response.json()['sha']
        
        # Обновляем ссылку на ветку
        ref_url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/git/refs/heads/{config['branch']}"
        ref_data = {
            'sha': new_commit_sha
        }
        
        response = requests.patch(ref_url, headers=headers, data=json.dumps(ref_data))
        if response.status_code != 200:
            print(f"❌ Не удалось обновить ветку: {response.status_code}")
            return False
        
        print(f"✅ Коммит успешно создан: {new_commit_sha[:7]}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания коммита: {e}")
        return False

def push_to_github(total_updated):
    """Отправка обновленных файлов в GitHub"""
    if total_updated == 0:
        print("⚠️ Нет файлов для отправки в GitHub")
        return False
    
    print(f"\n🚀 ОТПРАВКА ОБНОВЛЕНИЙ В GITHUB")
    print("="*60)
    
    # Определяем пути к файлам
    output_dir = '/app/output' if os.path.exists('/app') else './output'
    
    # Подготавливаем список файлов для коммита
    files_to_commit = {}
    
    relay_file = os.path.join(output_dir, 'DNSCrypt_relay.txt')
    if os.path.exists(relay_file):
        files_to_commit[relay_file] = 'lib/DNSCrypt_relay.txt'
        print(f"✅ Добавлен в коммит: DNSCrypt_relay.txt")
    
    servers_file = os.path.join(output_dir, 'DNSCrypt_servers.txt')
    if os.path.exists(servers_file):
        files_to_commit[servers_file] = 'lib/DNSCrypt_servers.txt'
        print(f"✅ Добавлен в коммит: DNSCrypt_servers.txt")
    
    if not files_to_commit:
        print("⚠️ Нет обновленных файлов для отправки")
        return False
    
    # Создаем сообщение коммита
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    commit_message = f"🤖 Автоматическое обновление списков серверов (Vue.js парсер)\n\n" \
                    f"- Обновлено серверов: {total_updated}\n" \
                    f"- Дата обновления: {timestamp}\n" \
                    f"- Источник: dnscrypt.info/public-servers\n" \
                    f"- Версия: Улучшенная для Vue.js\n\n" \
                    f"Автоматически сгенерировано парсером"
    
    # Создаем коммит с несколькими файлами
    success = create_github_commit(files_to_commit, commit_message)
    
    if success:
        config = get_github_config()
        print(f"\n🎉 ФАЙЛЫ УСПЕШНО ОТПРАВЛЕНЫ В GITHUB!")
        print(f"📁 Обновлено файлов: {len(files_to_commit)}")
        print(f"🔗 Ссылка: https://github.com/{config['owner']}/{config['repo']}/tree/{config['branch']}/lib")
        return True
    else:
        print(f"\n❌ НЕ УДАЛОСЬ ОТПРАВИТЬ ФАЙЛЫ В GITHUB")
        return False

def main():
    """Главная функция с улучшенной обработкой Vue.js"""
    print("🚀 Запуск ИСПРАВЛЕННОГО парсера DNSCrypt серверов (Vue.js)")
    print("=" * 70)
    
    # Создаем директорию output
    output_dir = '/app/output' if os.path.exists('/app') else './output'
    os.makedirs(output_dir, exist_ok=True)
    
    # URLs файлов на GitHub
    config_github = get_github_config()
    github_urls = {
        'DNSCrypt_relay.txt': f'https://github.com/{config_github["owner"]}/{config_github["repo"]}/blob/{config_github["branch"]}/lib/DNSCrypt_relay.txt',
        'DNSCrypt_servers.txt': f'https://github.com/{config_github["owner"]}/{config_github["repo"]}/blob/{config_github["branch"]}/lib/DNSCrypt_servers.txt'
    }
    
    # Скачиваем файлы во временную папку
    temp_files = []
    print("📥 Скачивание файлов с GitHub...")
    for filename, url in github_urls.items():
        temp_filename = f"temp_{filename}"
        if download_file(url, temp_filename):
            temp_files.append(temp_filename)
        else:
            print(f"❌ Не удалось скачать {filename}. Завершение работы.")
            return
    
    # Парсим временные файлы для получения списка серверов
    print("\n📋 Парсинг файлов конфигурации...")
    
    relay_servers = parse_config_file('temp_DNSCrypt_relay.txt')
    dnscrypt_servers = parse_config_file('temp_DNSCrypt_servers.txt')
    
    if not relay_servers and not dnscrypt_servers:
        print("❌ Не найдено серверов в файлах конфигурации")
        return
    
    print(f"✅ Найдено релеев: {len(relay_servers)}")
    print(f"✅ Найдено серверов: {len(dnscrypt_servers)}")
    
    # Запускаем браузер
    driver = setup_driver()
    if not driver:
        print("❌ Не удалось запустить браузер")
        return
    
    try:
        total_start_time = time.time()
        
        print("\n🔄 Переход на страницу dnscrypt.info...")
        driver.get("https://dnscrypt.info/public-servers")
        
        print("⏳ Ожидание полной загрузки страницы (может занять до 2 минут)...")

        # Ждем Vue.js с большим таймаутом
        vue_loaded = wait_for_vue_app_ready(driver, timeout=120)
        if not vue_loaded:
            print("⚠️ Vue.js не загрузился, но продолжаем...")
        
        # Ждем загрузки данных в таблицу
        data_loaded = wait_for_datatable_load(driver, timeout=120)
        if not data_loaded:
            print("⚠️ Данные не загрузились полностью, но продолжаем...")
        
        # Попытка установить пагинацию "All"
        try:
            set_pagination_to_all(driver)
        except Exception as e:
            print(f"⚠️ Ошибка установки пагинации: {e}")

        print("⏳ Дополнительное ожидание загрузки всех данных...")
        time.sleep(30)
        
        # Объединяем все целевые серверы
        all_target_servers = relay_servers + dnscrypt_servers
        
        # Обрабатываем серверы с сайта
        all_servers_data, total_successful = process_servers_from_website(driver, all_target_servers)
        
        # Разделяем данные по типам
        relay_data = {name: info for name, info in all_servers_data.items() 
                     if info['protocol'] == 'DNSCrypt relay'}
        server_data = {name: info for name, info in all_servers_data.items() 
                      if info['protocol'] == 'DNSCrypt'}
        
        # Статистика с временем
        total_time = time.time() - total_start_time
        total_processed = len(all_target_servers)
        
        print(f"\n{'='*70}")
        print("📊 ИТОГОВАЯ СТАТИСТИКА (Vue.js парсер)")
        print('='*70)
        print(f"Всего серверов для поиска: {total_processed}")
        print(f"  - Релеев: {len(relay_servers)} (найдено: {len(relay_data)})")
        print(f"  - Серверов: {len(dnscrypt_servers)} (найдено: {len(server_data)})")
        print(f"Общий успех: {total_successful}/{total_processed}")
        if total_processed > 0:
            print(f"Процент успеха: {total_successful/total_processed*100:.1f}%")
        print(f"⏱️ Общее время: {total_time:.1f}с")
        
        # Создаем итоговые файлы с обновленными данными
        total_updated = 0
        
        if relay_data:
            print(f"\n📝 Создание обновленного файла релеев...")
            os.rename('temp_DNSCrypt_relay.txt', 'DNSCrypt_relay.txt')
            updated_count = update_config_file('DNSCrypt_relay.txt', relay_data, is_relay_file=True)
            total_updated += updated_count
        
        if server_data:
            print(f"\n📝 Создание обновленного файла серверов...")
            os.rename('temp_DNSCrypt_servers.txt', 'DNSCrypt_servers.txt')
            updated_count = update_config_file('DNSCrypt_servers.txt', server_data, is_relay_file=False)
            total_updated += updated_count
        
        # Создаем сводный отчет в output директории
        if total_updated > 0:
            report_file = os.path.join(output_dir, "update_report.txt")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("# Отчет об обновлении DNSCrypt серверов - Vue.js парсер\n")
                f.write(f"# Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Общее время: {total_time:.1f}с\n\n")
                f.write(f"Всего серверов обработано: {total_processed}\n")
                f.write(f"Успешно обновлено: {total_updated}\n\n")
                
                if relay_data:
                    f.write("РЕЛЕИ:\n")
                    for name, info in relay_data.items():
                        f.write(f"{name:<30} -> {info['ip']} ({info['protocol']})\n")
                    f.write("\n")
                
                if server_data:
                    f.write("СЕРВЕРЫ:\n")
                    for name, info in server_data.items():
                        f.write(f"{name:<30} -> {info['ip']} ({info['protocol']})\n")
            
            print(f"✅ Отчет сохранен в {report_file}")
            print(f"\n🎉 УСПЕШНО ЗАВЕРШЕНО!")
            print(f"📁 Созданы обновленные файлы в {output_dir}:")
            print(f"   - DNSCrypt_relay.txt ({len(relay_data)} релеев)")
            print(f"   - DNSCrypt_servers.txt ({len(server_data)} серверов)")
            print(f"   - update_report.txt (отчет)")
            
            # Отправка в GitHub
            print(f"\n{'='*70}")
            print("🚀 ОТПРАВКА ОБНОВЛЕНИЙ В GITHUB")
            print('='*70)
            
            # Проверяем наличие токена
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                print("⚠️ GitHub token не найден в переменных окружения")
                print("⚠️ Отправка в GitHub пропущена")
            else:
                print("🔑 GitHub token найден, начинаем отправку...")
                push_to_github(total_updated)
        else:
            print("❌ Нет данных для обновления файлов")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            driver.quit()
            print("\n🚪 Браузер закрыт")
        except:
            pass
        
        kill_existing_chrome()
        
        # Очистка временных файлов
        print("🧹 Очистка временных файлов...")
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ Удален временный файл: {temp_file}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить {temp_file}: {e}")
        
        print("\n✅ ПАРСИНГ ЗАВЕРШЕН! (Vue.js версия)")
        config_github = get_github_config()
        print(f"🔗 Репозиторий: https://github.com/{config_github['owner']}/{config_github['repo']}")

if __name__ == "__main__":
    main()