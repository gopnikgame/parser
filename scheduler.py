#!/usr/bin/env python3
"""
Scheduler для автоматического запуска парсера DNSCrypt каждые 7 дней
Поддержка модульной системы v2.0
"""

import time
import subprocess
import sys
import os
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/output/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DNSCryptScheduler:
    def __init__(self):
        self.is_running = True
        self.last_run_file = '/app/output/last_run.txt'
        
        # Получаем интервал из переменных окружения или используем значение по умолчанию
        self.interval_days = int(os.getenv('SCHEDULER_INTERVAL_DAYS', '7'))
        self.interval_seconds = self.interval_days * 24 * 60 * 60
        
        # Отладочный режим
        self.debug_mode = os.getenv('SCHEDULER_DEBUG', 'false').lower() == 'true'
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
            logger.debug("🐛 Включен отладочный режим")
        
        # ИСПРАВЛЕНИЕ: Определяем парсер автоматически
        self.parser_mode = os.getenv('PARSER_MODE', 'auto')
        self.parser_script = self._determine_parser_script()
        
        # Обработчики сигналов для корректного завершения
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("🚀 Scheduler DNSCrypt v2.0 запущен")
        logger.info(f"📅 Интервал обновления: {self.interval_days} дней")
        logger.info(f"⚙️ Режим парсера: {self.parser_mode}")
        logger.info(f"📄 Скрипт парсера: {self.parser_script}")
        
        # Проверяем переменные окружения
        self.check_environment()
        
    def _determine_parser_script(self):
        """Автоматическое определение доступного парсера"""
        if self.parser_mode == 'legacy':
            return '/app/parser.py'
        elif self.parser_mode == 'modular':
            return '/app/parser_new.py'
        else:  # auto mode
            # Проверяем доступность модульной системы
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("core", "/app/core/__init__.py")
                if spec and os.path.exists('/app/parser_new.py'):
                    logger.info("✅ Модульная система доступна - используем parser_new.py")
                    return '/app/parser_new.py'
            except Exception as e:
                logger.debug(f"🔍 Модульная система недоступна: {e}")
            
            # Fallback на legacy версию
            if os.path.exists('/app/parser.py'):
                logger.info("📦 Используем legacy parser.py")
                return '/app/parser.py'
            elif os.path.exists('/app/auto_parser.sh'):
                logger.info("🔄 Используем auto_parser.sh")
                return '/app/auto_parser.sh'
            else:
                logger.error("❌ Ни один парсер не найден!")
                return None
        
    def check_environment(self):
        """Проверка переменных окружения"""
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token or github_token == 'your_github_token_here':
            logger.warning("⚠️ GitHub токен не настроен. Автоотправка будет недоступна.")
        else:
            logger.info("✅ GitHub токен найден")
            
        # Проверяем настройки Chrome
        chrome_headless = os.getenv('CHROME_HEADLESS', 'true')
        logger.info(f"🌐 Chrome headless: {chrome_headless}")
        
        # Проверяем доступность файлов
        logger.info("📁 Проверка файлов:")
        files_to_check = [
            '/app/parser.py',
            '/app/parser_new.py', 
            '/app/core/__init__.py',
            '/app/auto_parser.sh'
        ]
        
        for file_path in files_to_check:
            exists = os.path.exists(file_path)
            status = "✅" if exists else "❌"
            logger.info(f"   {status} {file_path}")
        
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"📨 Получен сигнал {signum}. Завершение работы...")
        self.is_running = False
        
    def get_last_run_time(self):
        """Получить время последнего запуска"""
        try:
            if os.path.exists(self.last_run_file):
                with open(self.last_run_file, 'r') as f:
                    timestamp = f.read().strip()
                    if timestamp:
                        return datetime.fromisoformat(timestamp)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось прочитать время последнего запуска: {e}")
        return None
        
    def save_last_run_time(self, run_time=None):
        """Сохранить время последнего запуска"""
        if run_time is None:
            run_time = datetime.now()
            
        try:
            os.makedirs(os.path.dirname(self.last_run_file), exist_ok=True)
            with open(self.last_run_file, 'w') as f:
                f.write(run_time.isoformat())
            logger.info(f"💾 Время последнего запуска сохранено: {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения времени последнего запуска: {e}")
            
    def should_run_parser(self):
        """Проверить, нужно ли запускать парсер"""
        last_run = self.get_last_run_time()
        
        if last_run is None:
            logger.info("🔥 Первый запуск - парсер будет выполнен немедленно")
            return True
            
        time_since_last_run = datetime.now() - last_run
        time_until_next_run = timedelta(seconds=self.interval_seconds) - time_since_last_run
        
        if time_since_last_run.total_seconds() >= self.interval_seconds:
            logger.info(f"⏰ Время запуска парсера (прошло {time_since_last_run.days} дней)")
            return True
        else:
            if time_until_next_run.days > 0:
                logger.debug(f"⏳ До следующего запуска: {time_until_next_run.days} дней {time_until_next_run.seconds // 3600} часов")
            else:
                hours_left = time_until_next_run.seconds // 3600
                minutes_left = (time_until_next_run.seconds % 3600) // 60
                logger.debug(f"⏳ До следующего запуска: {hours_left} ч {minutes_left} мин")
            return False
            
    def run_parser(self):
        """Запуск парсера с поддержкой модульной системы"""
        if not self.parser_script:
            logger.error("❌ Парсер не найден!")
            return False
            
        logger.info(f"🚀 Запуск парсера: {self.parser_script}")
        
        try:
            start_time = datetime.now()
            
            # Определяем команду запуска
            if self.parser_script.endswith('.sh'):
                # Bash скрипт
                cmd = ['bash', self.parser_script]
            else:
                # Python скрипт
                cmd = [sys.executable, self.parser_script]
            
            # Запускаем парсер
            result = subprocess.run(
                cmd,
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=3600  # Таймаут 1 час
            )
            
            duration = datetime.now() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Парсер завершен успешно за {duration}")
                
                # Анализируем вывод для получения статистики
                self._analyze_parser_output(result.stdout)
                
                if self.debug_mode:
                    logger.debug(f"📊 Полный вывод парсера:\n{result.stdout}")
                else:
                    # В обычном режиме показываем только последние строки
                    stdout_lines = result.stdout.split('\n')
                    if len(stdout_lines) > 10:
                        logger.info("📊 Последние строки вывода парсера:")
                        for line in stdout_lines[-10:]:
                            if line.strip():
                                logger.info(f"   {line}")
                    else:
                        logger.info(f"📊 Вывод парсера:\n{result.stdout}")
                
                # Сохраняем время успешного запуска
                self.save_last_run_time(start_time)
                
                # Создаем краткий отчет о работе scheduler'а
                self.create_scheduler_report(start_time, duration, True, result.stdout)
                
                return True
            else:
                logger.error(f"❌ Парсер завершился с ошибкой (код {result.returncode})")
                logger.error(f"📝 Stderr: {result.stderr}")
                if self.debug_mode:
                    logger.error(f"📝 Stdout: {result.stdout}")
                
                # Создаем отчет об ошибке
                self.create_scheduler_report(start_time, duration, False, result.stderr)
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Парсер превысил время ожидания (1 час)")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка запуска парсера: {e}")
            return False
    
    def _analyze_parser_output(self, output):
        """Анализ вывода парсера для извлечения статистики"""
        lines = output.split('\n')
        stats = {}
        
        for line in lines:
            # Ищем статистику в выводе
            if 'обработано' in line.lower() or 'processed' in line.lower():
                logger.info(f"📊 {line.strip()}")
            elif 'успешно' in line.lower() or 'successful' in line.lower():
                logger.info(f"✅ {line.strip()}")
            elif 'github' in line.lower() and ('успешно' in line.lower() or 'success' in line.lower()):
                logger.info(f"🚀 {line.strip()}")
            elif 'время выполнения' in line.lower() or 'duration' in line.lower():
                logger.info(f"⏱️ {line.strip()}")
            
    def create_scheduler_report(self, start_time, duration, success, output=None):
        """Создание отчета о работе scheduler'а"""
        try:
            report_file = '/app/output/scheduler_report.txt'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# Отчет о работе DNSCrypt Scheduler v2.0\n")
                f.write(f"# Дата: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Режим парсера: {self.parser_mode}\n")
                f.write(f"Скрипт парсера: {self.parser_script}\n")
                f.write(f"Интервал обновления: {self.interval_days} дней\n")
                f.write(f"Время запуска: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Длительность: {duration}\n")
                f.write(f"Статус: {'✅ Успешно' if success else '❌ Ошибка'}\n")
                
                if output:
                    f.write(f"\nВывод парсера:\n")
                    # Извлекаем важную информацию из вывода
                    lines = output.split('\n')
                    important_lines = []
                    
                    for line in lines:
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in [
                            'успешно', 'ошибка', 'обработано', 'github', 
                            'время выполнения', 'файлов обновлено', 
                            'парсер завершен', 'модульн', 'legacy'
                        ]):
                            important_lines.append(line)
                    
                    if important_lines:
                        f.write('\n'.join(important_lines))
                    else:
                        # Если важные строки не найдены, показываем последние 20 строк
                        f.write('\n'.join(lines[-20:]))
                
                # Информация о следующем запуске
                if success:
                    next_run = start_time + timedelta(days=self.interval_days)
                    f.write(f"\n\nСледующий запуск: {next_run.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка создания отчета scheduler'а: {e}")
            
    def log_status(self):
        """Вывести статус scheduler'а"""
        last_run = self.get_last_run_time()
        now = datetime.now()
        
        logger.info("=" * 60)
        logger.info("📊 СТАТУС SCHEDULER'А v2.0")
        logger.info("=" * 60)
        logger.info(f"🕐 Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⚙️ Режим парсера: {self.parser_mode}")
        logger.info(f"📄 Скрипт: {self.parser_script}")
        
        if last_run:
            time_since_last = now - last_run
            time_until_next = timedelta(seconds=self.interval_seconds) - time_since_last
            
            logger.info(f"🔄 Последний запуск: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️ Прошло времени: {time_since_last.days} дней {time_since_last.seconds // 3600} часов")
            
            if time_until_next.total_seconds() > 0:
                if time_until_next.days > 0:
                    logger.info(f"⏳ До следующего запуска: {time_until_next.days} дней {time_until_next.seconds // 3600} часов")
                else:
                    hours = time_until_next.seconds // 3600
                    minutes = (time_until_next.seconds % 3600) // 60
                    logger.info(f"⏳ До следующего запуска: {hours} ч {minutes} мин")
            else:
                logger.info("🔥 Время для запуска парсера!")
        else:
            logger.info("🔥 Парсер еще не запускался - будет запущен немедленно")
            
        logger.info(f"📅 Интервал: каждые {self.interval_days} дней")
        logger.info("=" * 60)
        
    def run(self):
        """Основной цикл scheduler'а"""
        logger.info("🔄 Запуск основного цикла scheduler'а v2.0")
        
        # Показываем статус при запуске
        self.log_status()
        
        # Проверяем, нужно ли запустить парсер сразу
        if self.should_run_parser():
            success = self.run_parser()
            if success:
                logger.info(f"😴 Следующий запуск через {self.interval_days} дней")
            else:
                logger.warning("⚠️ Парсер завершился с ошибкой, попробуем снова через час")
        
        # Основной цикл
        check_interval = 3600  # Проверяем каждый час
        status_interval = 6 * 3600  # Показываем статус каждые 6 часов
        last_status_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Показываем статус каждые 6 часов
                if current_time - last_status_time >= status_interval:
                    self.log_status()
                    last_status_time = current_time
                
                # Проверяем, нужно ли запускать парсер
                if self.should_run_parser():
                    success = self.run_parser()
                    if success:
                        logger.info(f"😴 Следующий запуск через {self.interval_days} дней")
                    else:
                        logger.warning("⚠️ Парсер завершился с ошибкой, попробуем снова через час")
                
                # Ждем перед следующей проверкой
                if self.debug_mode:
                    logger.debug(f"😴 Ожидание {check_interval} секунд до следующей проверки...")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("⌨️ Получен сигнал прерывания")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(60)  # Ждем минуту при ошибке
                
        logger.info("🛑 Scheduler v2.0 завершен")

def main():
    """Основная функция"""
    logger.info("🌟 Запуск DNSCrypt Scheduler v2.0")
    
    # Создаем директории если их нет
    os.makedirs('/app/output', exist_ok=True)
    os.makedirs('/app/logs', exist_ok=True)
    
    # Создаем и запускаем scheduler
    scheduler = DNSCryptScheduler()
    
    try:
        scheduler.run()
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())