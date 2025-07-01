# Создаем временный файл scheduler для теста
log "BLUE" "📝 Создание тестовой версии scheduler'а..."

cat > test_scheduler.py << 'EOF'
#!/usr/bin/env python3
"""
Тестовая версия scheduler'а с коротким интервалом
"""

import time
import subprocess
import sys
import os
import signal
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/test_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestScheduler:
    def __init__(self):
        self.is_running = True
        self.last_run_file = 'output/test_last_run.txt'
        self.interval_minutes = 2  # Тестовый интервал: 2 минуты
        self.interval_seconds = self.interval_minutes * 60
        
        # Обработчики сигналов
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("🧪 Тестовый Scheduler запущен")
        logger.info(f"⏰ Тестовый интервал: {self.interval_minutes} минут")
        
    def signal_handler(self, signum, frame):
        logger.info(f"📨 Получен сигнал {signum}. Завершение...")
        self.is_running = False
        
    def get_last_run_time(self):
        try:
            if os.path.exists(self.last_run_file):
                with open(self.last_run_file, 'r') as f:
                    timestamp = f.read().strip()
                    if timestamp:
                        return datetime.fromisoformat(timestamp)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка чтения времени: {e}")
        return None
        
    def save_last_run_time(self, run_time=None):
        if run_time is None:
            run_time = datetime.now()
            
        try:
            os.makedirs(os.path.dirname(self.last_run_file), exist_ok=True)
            with open(self.last_run_file, 'w') as f:
                f.write(run_time.isoformat())
            logger.info(f"💾 Время сохранено: {run_time.strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            
    def should_run_parser(self):
        last_run = self.get_last_run_time()
        
        if last_run is None:
            logger.info("🔥 Первый запуск - немедленное выполнение")
            return True
            
        time_since_last_run = datetime.now() - last_run
        
        if time_since_last_run.total_seconds() >= self.interval_seconds:
            logger.info(f"⏰ Время запуска (прошло {int(time_since_last_run.total_seconds())} сек)")
            return True
        else:
            remaining = self.interval_seconds - time_since_last_run.total_seconds()
            logger.info(f"⏳ До запуска: {int(remaining)} секунд")
            return False
            
    def test_run_parser(self):
        """Имитация запуска парсера для теста"""
        logger.info("🧪 ТЕСТОВЫЙ запуск парсера...")
        
        try:
            start_time = datetime.now()
            
            # Имитируем работу парсера
            logger.info("📥 Имитация скачивания файлов...")
            time.sleep(2)
            
            logger.info("🔍 Имитация парсинга серверов...")
            time.sleep(3)
            
            logger.info("📤 Имитация отправки в GitHub...")
            time.sleep(1)
            
            duration = datetime.now() - start_time
            logger.info(f"✅ Тестовый парсер завершен за {duration}")
            
            # Создаем тестовый отчет
            with open('output/test_report.txt', 'w') as f:
                f.write(f"Тестовый запуск в {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Длительность: {duration}\n")
                f.write("Статус: Успешно (тест)\n")
            
            self.save_last_run_time(start_time)
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестового парсера: {e}")
            return False
            
    def run(self):
        logger.info("🔄 Запуск тестового цикла")
        logger.info("🛑 Для остановки нажмите Ctrl+C")
        
        # Первый запуск
        if self.should_run_parser():
            self.test_run_parser()
        
        # Основной цикл
        check_interval = 10  # Проверяем каждые 10 секунд
        
        while self.is_running:
            try:
                if self.should_run_parser():
                    self.test_run_parser()
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("⌨️ Получен Ctrl+C")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                time.sleep(5)
                
        logger.info("🛑 Тестовый scheduler завершен")

if __name__ == "__main__":
    scheduler = TestScheduler()
    scheduler.run()
EOF

log "GREEN" "✅ Тестовая версия создана"

# Запускаем тестовый scheduler
log "BLUE" "🚀 Запуск тестового scheduler'а..."
log "YELLOW" "⚠️ Парсер будет имитироваться каждые 2 минуты"
log "YELLOW" "⚠️ Для остановки нажмите Ctrl+C"
echo

python3 test_scheduler.py

# Очищаем после теста
log "BLUE" "🧹 Очистка тестовых файлов..."
rm -f test_scheduler.py
rm -f output/test_*.txt

log "GREEN" "✅ Тестирование завершено!"
log "BLUE" "💡 Для запуска настоящего scheduler'а используйте:"
log "BLUE" "   ./manage_parser.sh"
log "BLUE" "   Выберите пункт '4. 🔄 Запустить scheduler'"