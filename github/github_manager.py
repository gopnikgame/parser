"""
Менеджер GitHub операций
"""
import os
import time
import base64
import json
import requests
from typing import Dict, Any

class GitHubManager:
    """Менеджер для работы с GitHub API"""
    
    def get_config(self) -> Dict[str, str]:
        """Получение конфигурации GitHub из переменных окружения"""
        return {
            'owner': os.getenv('GITHUB_OWNER', 'gopnikgame'),
            'repo': os.getenv('GITHUB_REPO', 'Installer_dnscypt'),
            'token': os.getenv('GITHUB_TOKEN'),
            'branch': os.getenv('GITHUB_BRANCH', 'main')
        }
    
    def create_github_commit(self, files_to_commit: Dict[str, str], commit_message: str) -> bool:
        """Создание коммита с несколькими файлами через GitHub API"""
        try:
            config = self.get_config()
            
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
    
    def push_updates(self, total_updated: int) -> bool:
        """Отправка обновленных файлов в GitHub"""
        if total_updated == 0:
            print("⚠️ Нет файлов для отправки в GitHub")
            return False
        
        print(f"\n🚀 ОТПРАВКА ОБНОВЛЕНИЙ В GITHUB")
        print("="*60)
        
        # Проверяем файлы в разных локациях
        possible_locations = [
            '/app/output',
            './output', 
            '.',  # Текущая директория
            '/app'
        ]
        
        files_to_commit = {}
        
        for location in possible_locations:
            relay_file = os.path.join(location, 'DNSCrypt_relay.txt')
            servers_file = os.path.join(location, 'DNSCrypt_servers.txt')
            
            if os.path.exists(relay_file) and relay_file not in files_to_commit.values():
                files_to_commit[relay_file] = 'lib/DNSCrypt_relay.txt'
                print(f"✅ Найден файл релеев: {relay_file}")
            
            if os.path.exists(servers_file) and servers_file not in files_to_commit.values():
                files_to_commit[servers_file] = 'lib/DNSCrypt_servers.txt'
                print(f"✅ Найден файл серверов: {servers_file}")
        
        if not files_to_commit:
            print("⚠️ Файлы не найдены в доступных локациях")
            # Выводим отладочную информацию
            print("🔍 Поиск файлов в:")
            for location in possible_locations:
                if os.path.exists(location):
                    try:
                        files = os.listdir(location)
                        dns_files = [f for f in files if 'DNSCrypt' in f]
                        print(f"   {location}: {dns_files}")
                    except:
                        pass
            return False
        
        # Создаем сообщение коммита
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"🤖 Автоматическое обновление списков серверов\n\n" \
                        f"- Обновлено серверов: {total_updated}\n" \
                        f"- Дата обновления: {timestamp}\n" \
                        f"- Источник: dnscrypt.info/public-servers\n\n" \
                        f"Автоматически сгенерировано модульным парсером v2.0"
        
        # Создаем коммит с несколькими файлами
        success = self.create_github_commit(files_to_commit, commit_message)
        
        if success:
            config = self.get_config()
            print(f"\n🎉 ФАЙЛЫ УСПЕШНО ОТПРАВЛЕНЫ В GITHUB!")
            print(f"📁 Обновлено файлов: {len(files_to_commit)}")
            print(f"🔗 Ссылка: https://github.com/{config['owner']}/{config['repo']}/tree/{config['branch']}/lib")
            return True
        else:
            print(f"\n❌ НЕ УДАЛОСЬ ОТПРАВИТЬ ФАЙЛЫ В GITHUB")
            return False