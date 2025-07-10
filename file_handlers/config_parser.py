"""
Модуль для работы с конфигурационными файлами DNSCrypt
"""
import urllib.request
from typing import List, Dict, Any

class ConfigFileParser:
    """Парсер конфигурационных файлов DNSCrypt"""
    
    def download_file(self, url: str, filename: str) -> bool:
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
    
    def parse_config_file(self, filename: str) -> List[Dict[str, Any]]:
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