"""
Основной класс парсера DNSCrypt - заменяет функцию main() из parser.py
"""
import time
import os
import sys
from typing import Dict, List, Optional, Any

# Исправляем импорты на абсолютные для работы в Docker
from core.config import ParserConfig
from core.driver_manager import SmartDriverManager
from extractors.dialog_extractor import AdvancedDialogExtractor
from strategies.error_recovery import SmartErrorRecovery
from utils.metrics import ParsingMetrics, ParsingCache
from file_handlers.config_parser import ConfigFileParser
from file_handlers.file_updater import FileUpdater
from github.github_manager import GitHubManager
from page_handlers.page_navigator import PageNavigator
from page_handlers.pagination_manager import PaginationManager
from data_handlers.server_processor import ServerProcessor

class DNSCryptParser:
    """Главный класс парсера DNSCrypt с полной модульной архитектурой"""
    
    def __init__(self):
        """Инициализация парсера с загрузкой конфигурации"""
        try:
            self.config = ParserConfig.from_env()
            self.driver_manager = SmartDriverManager(self.config)
            self.driver = None
            
            # Основные модули
            self.dialog_extractor = None
            self.error_recovery = None
            self.page_navigator = None
            self.pagination_manager = None
            self.server_processor = None
            
            # Файловые модули
            self.config_parser = ConfigFileParser()
            self.file_updater = FileUpdater()
            self.github_manager = GitHubManager()
            
            # Метрики и кэширование с обработкой ошибок
            print("📊 Инициализация системы метрик...")
            self.metrics = ParsingMetrics()
            
            print("💾 Инициализация системы кэширования...")
            self.cache = ParsingCache()
            
            if not self.cache.cache_enabled:
                print("⚠️ Кэширование отключено, парсинг будет работать без кэша")
            
            # Статистика сессии
            self.session_stats = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'cache_hits': 0,
                'recovery_attempts': 0,
                'start_time': None,
                'end_time': None
            }
            
            print("🚀 DNSCrypt Parser v2.0 инициализирован")
            
        except Exception as e:
            print(f"❌ Критическая ошибка инициализации DNSCryptParser: {e}")
            # Создаем fallback объекты для продолжения работы
            self.metrics = None
            self.cache = None
            print("⚠️ Парсер будет работать без метрик и кэширования")
            raise
    
    def initialize(self) -> bool:
        """Полная инициализация всех компонентов парсера"""
        try:
            print("🔧 Инициализация компонентов парсера...")
            
            # Создаем драйвер
            self.driver = self.driver_manager.create_stealth_driver()
            if not self.driver:
                print("❌ Не удалось создать драйвер")
                return False
            
            # Инициализируем основные модули
            self.dialog_extractor = AdvancedDialogExtractor(self.driver, self.config)
            self.error_recovery = SmartErrorRecovery(self.driver, self.config)
            self.page_navigator = PageNavigator(self.driver, self.config)
            self.pagination_manager = PaginationManager(self.driver, self.config)
            self.server_processor = ServerProcessor(self.driver, self.config, self.dialog_extractor)
            
            # Очищаем устаревший кэш (если доступен)
            if self.cache and self.cache.cache_enabled:
                self.cache.clear_expired_cache()
            
            print("✅ Все компоненты успешно инициализированы")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def run_full_parsing(self) -> Dict[str, Any]:
        """Запуск полного цикла парсинга"""
        try:
            self.session_stats['start_time'] = time.time()
            
            # Запускаем сессию метрик если доступна
            session_id = None
            if self.metrics:
                session_id = self.metrics.start_session()
            
            print("🎯 Запуск полного цикла парсинга DNSCrypt серверов")
            print("=" * 70)
            
            # Этап 1: Скачивание и парсинг конфигурационных файлов
            print("\n📥 ЭТАП 1: Загрузка конфигурационных файлов")
            print("-" * 50)
            
            target_servers = self._download_and_parse_configs()
            if not target_servers:
                return self._create_error_result("Не удалось загрузить конфигурационные файлы")
            
            print(f"✅ Загружено {len(target_servers)} серверов для обработки")
            
            # Этап 2: Навигация и загрузка страницы
            print("\n🌐 ЭТАП 2: Навигация на страницу")
            print("-" * 50)
            
            if not self.page_navigator.navigate_to_page("https://dnscrypt.info/public-servers"):
                return self._create_error_result("Не удалось загрузить страницу")
            
            # Этап 3: Настройка пагинации
            print("\n🔧 ЭТАП 3: Настройка пагинации")
            print("-" * 50)
            
            pagination_success = self.pagination_manager.setup_pagination()
            if pagination_success:
                print("✅ Пагинация настроена успешно")
            else:
                print("⚠️ Пагинация не настроена, продолжаем с ограниченными данными")
            
            # Этап 4: Извлечение и обработка данных
            print("\n🔍 ЭТАП 4: Извлечение данных серверов")
            print("-" * 50)
            
            parsing_result = self.server_processor.process_servers(target_servers)
            
            # Этап 5: Обновление файлов
            print("\n📝 ЭТАП 5: Обновление конфигурационных файлов")
            print("-" * 50)
            
            update_result = self._update_config_files(parsing_result, target_servers)
            
            # Этап 6: Отправка в GitHub
            print("\n🚀 ЭТАП 6: Отправка в GitHub")
            print("-" * 50)
            
            github_result = self._push_to_github(update_result['total_updated'])
            
            # Финализация сессии
            self.session_stats['end_time'] = time.time()
            
            # Завершаем сессию метрик если доступна
            session = None
            if self.metrics:
                session = self.metrics.end_session()
            
            # Подготовка итогового результата
            result = {
                'success': True,
                'parsing_result': parsing_result,
                'update_result': update_result,
                'github_result': github_result,
                'session_stats': self.session_stats,
                'metrics': self.metrics.generate_detailed_report() if self.metrics else "Метрики недоступны",
                'duration': self.session_stats['end_time'] - self.session_stats['start_time']
            }
            
            self._print_final_summary(result)
            return result
            
        except Exception as e:
            print(f"❌ Критическая ошибка в цикле парсинга: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(str(e))
    
    def _download_and_parse_configs(self) -> List[Dict[str, Any]]:
        """Скачивание и парсинг конфигурационных файлов"""
        try:
            # Формируем URLs для скачивания
            github_config = self.github_manager.get_config()
            github_urls = {
                'DNSCrypt_relay.txt': f'https://github.com/{github_config["owner"]}/{github_config["repo"]}/blob/{github_config["branch"]}/lib/DNSCrypt_relay.txt',
                'DNSCrypt_servers.txt': f'https://github.com/{github_config["owner"]}/{github_config["repo"]}/blob/{github_config["branch"]}/lib/DNSCrypt_servers.txt'
            }
            
            # Скачиваем файлы
            temp_files = []
            for filename, url in github_urls.items():
                temp_filename = f"temp_{filename}"
                if self.config_parser.download_file(url, temp_filename):
                    temp_files.append(temp_filename)
                else:
                    print(f"❌ Не удалось скачать {filename}")
                    return []
            
            # Парсим файлы
            relay_servers = self.config_parser.parse_config_file('temp_DNSCrypt_relay.txt')
            dnscrypt_servers = self.config_parser.parse_config_file('temp_DNSCrypt_servers.txt')
            
            # Объединяем все серверы
            all_servers = relay_servers + dnscrypt_servers
            
            print(f"📋 Релеев: {len(relay_servers)}")
            print(f"📋 Серверов: {len(dnscrypt_servers)}")
            print(f"📋 Всего: {len(all_servers)}")
            
            return all_servers
            
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигураций: {e}")
            return []
    
    def _update_config_files(self, parsing_result: Dict[str, Any], target_servers: List[Dict]) -> Dict[str, Any]:
        """Обновление конфигурационных файлов"""
        try:
            servers_data = parsing_result.get('servers_data', {})
            
            # Разделяем данные по типам
            relay_data = {name: info for name, info in servers_data.items() 
                         if info.get('protocol') == 'DNSCrypt relay'}
            server_data = {name: info for name, info in servers_data.items() 
                          if info.get('protocol') == 'DNSCrypt'}
            
            total_updated = 0
            
            # Обновляем файл релеев
            if relay_data:
                print(f"📝 Обновление файла релеев ({len(relay_data)} серверов)...")
                if os.path.exists('temp_DNSCrypt_relay.txt'):
                    os.rename('temp_DNSCrypt_relay.txt', 'DNSCrypt_relay.txt')
                
                updated_count = self.file_updater.update_config_file(
                    'DNSCrypt_relay.txt', relay_data, is_relay_file=True
                )
                total_updated += updated_count
                print(f"✅ Обновлено релеев: {updated_count}")
            
            # Обновляем файл серверов
            if server_data:
                print(f"📝 Обновление файла серверов ({len(server_data)} серверов)...")
                if os.path.exists('temp_DNSCrypt_servers.txt'):
                    os.rename('temp_DNSCrypt_servers.txt', 'DNSCrypt_servers.txt')
                
                updated_count = self.file_updater.update_config_file(
                    'DNSCrypt_servers.txt', server_data, is_relay_file=False
                )
                total_updated += updated_count
                print(f"✅ Обновлено серверов: {updated_count}")
            
            return {
                'total_updated': total_updated,
                'relay_updated': len(relay_data),
                'server_updated': len(server_data),
                'relay_data': relay_data,
                'server_data': server_data
            }
            
        except Exception as e:
            print(f"❌ Ошибка обновления файлов: {e}")
            return {'total_updated': 0, 'error': str(e)}
    
    def _push_to_github(self, total_updated: int) -> Dict[str, Any]:
        """Отправка обновленных файлов в GitHub"""
        try:
            if total_updated == 0:
                print("⚠️ Нет изменений для отправки в GitHub")
                return {'success': False, 'reason': 'no_changes'}
            
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                print("⚠️ GitHub token не найден, отправка пропущена")
                return {'success': False, 'reason': 'no_token'}
            
            print(f"🚀 Отправка {total_updated} обновлений в GitHub...")
            
            success = self.github_manager.push_updates(total_updated)
            
            if success:
                print("✅ Успешно отправлено в GitHub")
                return {'success': True, 'files_updated': total_updated}
            else:
                print("❌ Ошибка отправки в GitHub")
                return {'success': False, 'reason': 'push_failed'}
                
        except Exception as e:
            print(f"❌ Ошибка GitHub операции: {e}")
            return {'success': False, 'reason': 'exception', 'error': str(e)}
    
    def _print_final_summary(self, result: Dict[str, Any]):
        """Печать финального отчета"""
        print("\n" + "=" * 70)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ ПАРСИНГА")
        print("=" * 70)
        
        parsing_result = result.get('parsing_result', {})
        update_result = result.get('update_result', {})
        duration = result.get('duration', 0)
        
        print(f"⏱️ Общее время выполнения: {duration:.1f} секунд")
        print(f"🎯 Обработано серверов: {parsing_result.get('successful', 0)}/{parsing_result.get('total_processed', 0)}")
        print(f"📈 Процент успеха: {parsing_result.get('success_rate', 0):.1f}%")
        print(f"💾 Кэш хиты: {parsing_result.get('cache_hits', 0)}")
        print(f"🔄 Восстановления: {parsing_result.get('recovery_attempts', 0)}")
        print(f"📝 Обновлено файлов: {update_result.get('total_updated', 0)}")
        
        github_result = result.get('github_result', {})
        if github_result.get('success'):
            print("🚀 GitHub: Успешно отправлено")
        else:
            print(f"⚠️ GitHub: {github_result.get('reason', 'неизвестная ошибка')}")
        
        print("=" * 70)
        
        # Выводим метрики
        metrics_report = result.get('metrics', '')
        if metrics_report and metrics_report != "Метрики недоступны":
            print("\n📈 ДЕТАЛЬНЫЕ МЕТРИКИ:")
            print(metrics_report)
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'success': False,
            'error': error_message,
            'parsing_result': {
                'servers_data': {},
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
            },
            'session_stats': self.session_stats
        }
    
    def cleanup(self):
        """Очистка всех ресурсов"""
        try:
            print("🧹 Очистка ресурсов...")
            
            # Закрываем драйвер
            if self.driver_manager:
                self.driver_manager.quit_driver()
            
            # Сохраняем финальные метрики если доступны
            if self.metrics:
                try:
                    self.metrics.export_csv_report()
                except Exception as e:
                    print(f"⚠️ Не удалось экспортировать метрики: {e}")
            
            # Очистка временных файлов
            temp_files = ['temp_DNSCrypt_relay.txt', 'temp_DNSCrypt_servers.txt']
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            print("✅ Ресурсы очищены")
            
        except Exception as e:
            print(f"⚠️ Ошибка при очистке: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        if self.initialize():
            return self
        else:
            raise RuntimeError("Не удалось инициализировать парсер")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()