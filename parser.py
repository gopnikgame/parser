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
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_default_chrome_options():
    """Базовые опции Chrome согласно документации Selenium"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    
    # Headless режим
    if os.getenv('CHROME_HEADLESS', 'true').lower() == 'true':
        options.add_argument("--headless")
    
    return options

def kill_existing_chrome():
    """Убиваем все процессы Chrome перед запуском"""
    try:
        subprocess.run(['pkill', '-f', 'chrome'], check=False)
        subprocess.run(['pkill', '-f', 'chromium'], check=False)
        time.sleep(2)
        print("✅ Существующие процессы Chrome завершены")
    except Exception as e:
        print(f"⚠️ Не удалось завершить процессы Chrome: {e}")

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

def setup_driver():
    """Простая настройка драйвера Chrome"""
    kill_existing_chrome()
    
    try:
        options = get_default_chrome_options()
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome успешно запущен")
        return driver
        
    except WebDriverException as e:
        print(f"❌ Ошибка запуска Chrome: {str(e)}")
        return None

def wait_for_page_load(driver, timeout=30):
    """Ожидание полной загрузки страницы"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("✅ Страница загружена")
        return True
    except TimeoutException:
        print("⚠️ Таймаут загрузки страницы")
        return False

def expand_all_rows(driver):
    """Попытка показать все строки в таблице"""
    try:
        print("🔧 Попытка показать все строки...")
        
        # Прокручиваем вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Ищем элементы пагинации разными способами
        pagination_selectors = [
            "//div[contains(text(), 'Rows per page')]//following::div[contains(@class, 'v-select')]",
            "//div[contains(@class, 'v-data-table__pagination')]//div[contains(@class, 'v-select')]",
            "//*[contains(text(), '50')]//parent::div[contains(@class, 'v-select')]",
            "//div[@role='combobox']"
        ]
        
        for selector in pagination_selectors:
            try:
                dropdown = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"✅ Найден dropdown: {selector}")
                dropdown.click()
                time.sleep(2)
                
                # Ищем опцию "All"
                all_options = [
                    "//div[contains(text(), 'All')]",
                    "//*[text()='All']",
                    "//div[contains(@class, 'v-list-item')]//div[contains(text(), 'All')]"
                ]
                
                for option_selector in all_options:
                    try:
                        all_option = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, option_selector))
                        )
                        all_option.click()
                        print("✅ Выбрана опция 'All'")
                        time.sleep(5)  # Ждем загрузки всех данных
                        return True
                    except TimeoutException:
                        continue
                
            except TimeoutException:
                continue
        
        print("⚠️ Не удалось найти элементы пагинации")
        return False
        
    except Exception as e:
        print(f"⚠️ Ошибка при попытке показать все строки: {e}")
        return False

def close_any_overlays(driver):
    """Закрытие любых overlay/модальных окон"""
    try:
        # Пробуем найти и закрыть overlay
        overlays = [
            "//div[contains(@class, 'v-overlay')]",
            "//div[contains(@class, 'v-dialog')]",
            "//div[contains(@class, 'modal')]"
        ]
        
        for overlay_selector in overlays:
            try:
                overlays_elements = driver.find_elements(By.XPATH, overlay_selector)
                for overlay in overlays_elements:
                    if overlay.is_displayed():
                        # Пробуем ESC
                        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        
                        # Если overlay все еще есть, кликаем вне его
                        if overlay.is_displayed():
                            driver.execute_script("arguments[0].click();", overlay)
                            time.sleep(1)
                        break
            except:
                continue
                
    except Exception as e:
        print(f"⚠️ Ошибка закрытия overlay: {e}")

def find_server_element(driver, server_name):
    """Улучшенный поиск элемента сервера"""
    try:
        # Закрываем любые overlay перед поиском
        close_any_overlays(driver)
        
        # Множественные стратегии поиска
        search_strategies = [
            # Точное совпадение в span
            f"//span[text()='{server_name}']",
            f"//span[contains(text(), '{server_name}')]",
            
            # Поиск в таблице
            f"//td[text()='{server_name}']",
            f"//td[contains(text(), '{server_name}')]",
            
            # Поиск в ссылках
            f"//a[text()='{server_name}']", 
            f"//a[contains(text(), '{server_name}')]",
            
            # Поиск в любых элементах
            f"//*[text()='{server_name}']",
            f"//*[contains(text(), '{server_name}')]",
            
            # Поиск в строках таблицы
            f"//tr[.//span[contains(text(), '{server_name}')]]//span[contains(text(), '{server_name}')]",
            f"//table//span[contains(text(), '{server_name}')]"
        ]
        
        for i, strategy in enumerate(search_strategies):
            try:
                elements = driver.find_elements(By.XPATH, strategy)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
                        
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка поиска сервера: {e}")
        return None

def click_server_and_get_dialog(driver, server_element, server_name):
    """Клик по серверу и получение диалога"""
    try:
        # Закрываем overlay перед кликом
        close_any_overlays(driver)
        
        # Прокручиваем к элементу
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", server_element)
        time.sleep(2)
        
        # Пробуем разные способы клика
        click_methods = [
            lambda: server_element.click(),
            lambda: ActionChains(driver).move_to_element(server_element).click().perform(),
            lambda: driver.execute_script("arguments[0].click();", server_element),
            lambda: ActionChains(driver).move_to_element(server_element).pause(1).click().perform()
        ]
        
        for i, click_method in enumerate(click_methods):
            try:
                # Убеждаемся что нет overlay
                close_any_overlays(driver)
                
                click_method()
                time.sleep(3)
                
                # Ищем диалог с расширенными селекторами
                dialog_selectors = [
                    "//div[contains(@class, 'v-dialog') and @role='dialog']",
                    "//div[contains(@class, 'v-dialog')]",
                    "//div[contains(@class, 'v-card')]", 
                    "//div[contains(@class, 'modal')]",
                    "//*[contains(@class, 'dialog')]",
                    "//div[@role='dialog']"
                ]
                
                for selector in dialog_selectors:
                    try:
                        dialogs = driver.find_elements(By.XPATH, selector)
                        for dialog in dialogs:
                            if dialog.is_displayed() and dialog.text.strip():
                                return dialog
                    except:
                        continue
                        
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка клика: {e}")
        return None

def extract_dialog_info(driver, dialog):
    """Извлечение информации из диалога"""
    try:
        time.sleep(2)  # Ждем полной загрузки
        
        # Пробуем получить текст разными способами
        dialog_text = ""
        
        # Способ 1: обычный text
        if dialog.text.strip():
            dialog_text = dialog.text
        
        # Способ 2: innerHTML через JavaScript
        if not dialog_text.strip():
            dialog_text = driver.execute_script("return arguments[0].innerHTML;", dialog)
        
        # Способ 3: textContent через JavaScript
        if not dialog_text.strip():
            dialog_text = driver.execute_script("return arguments[0].textContent;", dialog)
        
        # Способ 4: ищем конкретные элементы внутри диалога
        if not dialog_text.strip():
            try:
                inner_elements = dialog.find_elements(By.XPATH, ".//*[text()]")
                texts = [elem.text for elem in inner_elements if elem.text.strip()]
                dialog_text = "\n".join(texts)
            except:
                pass
        
        # Закрываем диалог
        try:
            # ESC
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            # Кнопка закрытия
            try:
                close_buttons = dialog.find_elements(By.XPATH, ".//button | .//i[@class*='close'] | .//*[@aria-label='close']")
                if close_buttons:
                    close_buttons[0].click()
                    time.sleep(1)
            except:
                pass
        
        return dialog_text if dialog_text.strip() else None
        
    except Exception as e:
        print(f"❌ Ошибка извлечения диалога: {e}")
        return None

def parse_server_info(dialog_text, server_name):
    """Парсинг информации сервера"""
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
    info['dnssec'] = 'dnssec' in text_lower and 'true' in text_lower
    info['no_filters'] = 'no filter' in text_lower and 'true' in text_lower
    info['no_logs'] = 'no log' in text_lower and 'true' in text_lower
    
    return info

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
        
        # Создаем директорию output если её нет
        output_dir = '/app/output' if os.path.exists('/app') else './output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Создаем резервную копию ОРИГИНАЛЬНОГО файла
        backup_filename = os.path.join(output_dir, f"{os.path.basename(filename)}.original_backup")
        try:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"💾 Резервная копия создана: {backup_filename}")
        except Exception as e:
            print(f"⚠️ Не удалось создать резервную копию: {e}")
        
        # Записываем обновленный файл в output
        output_filename = os.path.join(output_dir, os.path.basename(filename))
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Файл {output_filename} обновлен. Обновлено серверов: {updated_count}")
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Ошибка обновления файла {filename}: {e}")
        return 0

def process_servers(driver, servers, file_type):
    """Обработка списка серверов"""
    print(f"\n🔍 Обработка {len(servers)} серверов ({file_type})...")
    
    servers_data = {}
    successful_count = 0
    
    for i, server in enumerate(servers, 1):
        print(f"\n[{i}/{len(servers)}] {server['name']}", end=" ")
        
        # Ищем элемент сервера
        server_element = find_server_element(driver, server['name'])
        if server_element:
            print("✓", end=" ")
            
            # Кликаем и получаем диалог
            dialog = click_server_and_get_dialog(driver, server_element, server['name'])
            if dialog:
                print("🔍", end=" ")
                
                dialog_text = extract_dialog_info(driver, dialog)
                if dialog_text:
                    info = parse_server_info(dialog_text, server['name'])
                    
                    # Проверяем что протокол соответствует типу файла
                    expected_protocol = 'DNSCrypt relay' if file_type == 'relay' else 'DNSCrypt'
                    
                    if info['ip'] and info['protocol'] == expected_protocol:
                        servers_data[server['name']] = info
                        successful_count += 1
                        print(f"✅ -> {info['ip']}")
                    else:
                        print(f"⚠️ Неподходящий протокол: {info['protocol']}")
                else:
                    print("❌ Пустой диалог")
            else:
                print("❌ Диалог не открылся")
        else:
            print("❌ Не найден")
        
        # Пауза между запросами
        time.sleep(1)
        
        # Прогресс каждые 10 серверов
        if i % 10 == 0:
            print(f"\n📊 Прогресс {file_type}: {i}/{len(servers)} ({successful_count} успешных)")
    
    return servers_data, successful_count

# GitHub функции
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
    commit_message = f"🤖 Автоматическое обновление списков серверов\n\n" \
                    f"- Обновлено серверов: {total_updated}\n" \
                    f"- Дата обновления: {timestamp}\n" \
                    f"- Источник: dnscrypt.info/public-servers\n" \
                    f"- Версия: Стабильная (исправленная)\n\n" \
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
    """Главная функция"""
    print("🚀 Запуск автоматизированного парсера DNSCrypt серверов")
    print("=" * 60)
    
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
        
        if not wait_for_page_load(driver):
            print("⚠️ Продолжаем несмотря на проблемы с загрузкой...")
        
        time.sleep(5)
        
        # Показываем все строки
        expand_all_rows(driver)
        
        # Обрабатываем релеи
        relay_data = {}
        relay_successful = 0
        if relay_servers:
            relay_data, relay_successful = process_servers(driver, relay_servers, 'relay')
        
        # Обрабатываем обычные серверы
        server_data = {}
        server_successful = 0
        if dnscrypt_servers:
            server_data, server_successful = process_servers(driver, dnscrypt_servers, 'server')
        
        # Статистика с временем
        total_time = time.time() - total_start_time
        total_processed = len(relay_servers) + len(dnscrypt_servers)
        total_successful = relay_successful + server_successful
        
        print(f"\n{'='*60}")
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print('='*60)
        print(f"Всего серверов обработано: {total_processed}")
        print(f"  - Релеев: {len(relay_servers)} (успешно: {relay_successful})")
        print(f"  - Серверов: {len(dnscrypt_servers)} (успешно: {server_successful})")
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
                f.write("# Отчет об обновлении DNSCrypt серверов - ИСПРАВЛЕННАЯ ВЕРСИЯ\n")
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
            print(f"   - DNSCrypt_relay.txt ({relay_successful} серверов)")
            print(f"   - DNSCrypt_servers.txt ({server_successful} серверов)")
            print(f"   - update_report.txt (отчет)")
            
            # Отправка в GitHub
            print(f"\n{'='*60}")
            print("🚀 ОТПРАВКА ОБНОВЛЕНИЙ В GITHUB")
            print('='*60)
            
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
        
        print("\n✅ ПАРСИНГ ЗАВЕРШЕН!")
        config_github = get_github_config()
        print(f"🔗 Репозиторий: https://github.com/{config_github['owner']}/{config_github['repo']}")

if __name__ == "__main__":
    main()