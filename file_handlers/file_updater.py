"""
Модуль для обновления конфигурационных файлов
"""
import os
from typing import Dict, Any

class FileUpdater:
    """Обновлятор конфигурационных файлов"""
    
    def format_relay_line(self, server_info: Dict[str, Any]) -> str:
        """Форматирование строки релея"""
        if not server_info['ip']:
            return None
        
        name = server_info['name']
        protocol = server_info['protocol']
        ip = server_info['ip']
        
        return f"{name:<30} Anonymized DNS relay | {protocol} | {ip}"
    
    def format_server_line(self, server_info: Dict[str, Any]) -> str:
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
    
    def update_config_file(self, filename: str, servers_data: Dict[str, Any], is_relay_file: bool = False) -> int:
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
                        new_line = self.format_relay_line(servers_data[server_name])
                    else:
                        new_line = self.format_server_line(servers_data[server_name])
                    
                    if new_line:
                        updated_lines.append(new_line + '\n')
                        updated_count += 1
                        print(f"✅ Обновлен: {server_name} -> {servers_data[server_name]['ip']}")
                    else:
                        updated_lines.append(line)
                else:
                    # Оставляем оригинальную строку
                    updated_lines.append(line)
            
            # Определяем выходную директорию
            output_dir = '/app/output' if os.path.exists('/app') else './output'
            
            try:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, mode=0o755, exist_ok=True)
            except PermissionError:
                print(f"⚠️ Не удалось создать директорию {output_dir}, используем текущую")
                output_dir = '.'
            
            # Создаем резервную копию
            backup_filename = os.path.join(output_dir, f"{os.path.basename(filename)}.original_backup")
            try:
                with open(backup_filename, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"💾 Резервная копия создана: {backup_filename}")
            except PermissionError:
                print(f"⚠️ Не удалось создать резервную копию, продолжаем без неё")
            
            # Записываем обновленный файл
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