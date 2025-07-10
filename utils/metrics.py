# Система метрик и мониторинга парсера
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

@dataclass
class ServerExtractionMetric:
    """Метрика извлечения одного сервера"""
    server_name: str
    success: bool
    duration: float
    attempt_count: int
    error_type: Optional[str] = None
    extraction_method: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class SessionMetrics:
    """Метрики сессии парсинга"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    total_servers: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    total_duration: float = 0.0
    
    # Детальная статистика по типам ошибок
    error_stats: Dict[str, int] = field(default_factory=dict)
    
    # Статистика по методам извлечения
    method_stats: Dict[str, int] = field(default_factory=dict)
    
    # Статистика по времени извлечения
    timing_stats: Dict[str, float] = field(default_factory=dict)
    
    # Список метрик серверов
    server_metrics: List[ServerExtractionMetric] = field(default_factory=list)
    
    def add_server_metric(self, metric: ServerExtractionMetric):
        """Добавление метрики сервера"""
        self.server_metrics.append(metric)
        self.total_servers += 1
        
        if metric.success:
            self.successful_extractions += 1
        else:
            self.failed_extractions += 1
            if metric.error_type:
                self.error_stats[metric.error_type] = self.error_stats.get(metric.error_type, 0) + 1
        
        if metric.extraction_method:
            self.method_stats[metric.extraction_method] = self.method_stats.get(metric.extraction_method, 0) + 1
        
        # Обновляем статистику времени
        self.timing_stats['total_duration'] = self.timing_stats.get('total_duration', 0) + metric.duration
        self.timing_stats['avg_duration'] = self.timing_stats['total_duration'] / self.total_servers
        
        if metric.success:
            self.timing_stats['avg_success_duration'] = (
                self.timing_stats.get('success_duration_sum', 0) + metric.duration
            ) / self.successful_extractions
            self.timing_stats['success_duration_sum'] = (
                self.timing_stats.get('success_duration_sum', 0) + metric.duration
            )
    
    def finalize(self):
        """Финализация метрик сессии"""
        self.end_time = datetime.now().isoformat()
        if self.server_metrics:
            start = datetime.fromisoformat(self.server_metrics[0].timestamp)
            end = datetime.now()
            self.total_duration = (end - start).total_seconds()
    
    def get_success_rate(self) -> float:
        """Получение процента успешности"""
        if self.total_servers == 0:
            return 0.0
        return (self.successful_extractions / self.total_servers) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Получение краткой сводки"""
        return {
            'session_id': self.session_id,
            'success_rate': self.get_success_rate(),
            'total_servers': self.total_servers,
            'successful': self.successful_extractions,
            'failed': self.failed_extractions,
            'duration': self.total_duration,
            'avg_duration_per_server': self.timing_stats.get('avg_duration', 0),
            'top_errors': dict(sorted(self.error_stats.items(), key=lambda x: x[1], reverse=True)[:5])
        }

class ParsingMetrics:
    """Система метрик парсера"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.metrics_file = os.path.join(output_dir, "parsing_metrics.json")
        self.current_session: Optional[SessionMetrics] = None
        self.historical_metrics: List[SessionMetrics] = []
        
        # Создаем директорию если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # Загружаем исторические метрики
        self._load_historical_metrics()
    
    def start_session(self, session_id: str = None) -> str:
        """Начало новой сессии метрик"""
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now().isoformat()
        )
        
        print(f"📊 Начата сессия метрик: {session_id}")
        return session_id
    
    def record_server_extraction(
        self, 
        server_name: str, 
        success: bool, 
        duration: float,
        attempt_count: int = 1,
        error_type: str = None,
        extraction_method: str = None
    ):
        """Запись метрики извлечения сервера"""
        if not self.current_session:
            self.start_session()
        
        metric = ServerExtractionMetric(
            server_name=server_name,
            success=success,
            duration=duration,
            attempt_count=attempt_count,
            error_type=error_type,
            extraction_method=extraction_method
        )
        
        self.current_session.add_server_metric(metric)
        
        # Выводим прогресс
        session = self.current_session
        print(f"📊 [{session.total_servers}] {server_name}: "
              f"{'✅' if success else '❌'} ({duration:.2f}s)")
    
    def end_session(self) -> Optional[SessionMetrics]:
        """Завершение текущей сессии"""
        if not self.current_session:
            return None
        
        self.current_session.finalize()
        self.historical_metrics.append(self.current_session)
        
        # Сохраняем метрики
        self._save_metrics()
        
        session = self.current_session
        self.current_session = None
        
        print(f"📊 Сессия завершена: {session.session_id}")
        print(f"📊 Успешность: {session.get_success_rate():.1f}% "
              f"({session.successful_extractions}/{session.total_servers})")
        
        return session
    
    def generate_detailed_report(self) -> str:
        """Генерация детального отчета"""
        if not self.current_session and not self.historical_metrics:
            return "📊 Нет данных для отчета"
        
        # Используем последнюю сессию если текущая не завершена
        session = self.current_session
        if not session and self.historical_metrics:
            session = self.historical_metrics[-1]
        
        if not session:
            return "📊 Нет данных для отчета"
        
        report = f"""
📊 ДЕТАЛЬНЫЙ ОТЧЕТ ПАРСИНГА
{'='*60}
🆔 Сессия: {session.session_id}
⏰ Время: {session.start_time} - {session.end_time or 'В процессе'}
⏱️ Длительность: {session.total_duration:.1f} сек

🎯 ОБЩАЯ СТАТИСТИКА:
   Всего серверов: {session.total_servers}
   Успешно: {session.successful_extractions} ({session.get_success_rate():.1f}%)
   Неудачно: {session.failed_extractions}
   
⏱️ ПРОИЗВОДИТЕЛЬНОСТЬ:
   Среднее время на сервер: {session.timing_stats.get('avg_duration', 0):.2f}с
   Среднее время успешного извлечения: {session.timing_stats.get('avg_success_duration', 0):.2f}с
   Общее время: {session.total_duration:.1f}с

❌ СТАТИСТИКА ОШИБОК:"""

        # Добавляем статистику ошибок
        if session.error_stats:
            for error_type, count in sorted(session.error_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / session.failed_extractions) * 100 if session.failed_extractions > 0 else 0
                report += f"\n   {error_type}: {count} ({percentage:.1f}%)"
        else:
            report += "\n   Ошибок не обнаружено ✅"

        # Добавляем статистику методов
        if session.method_stats:
            report += f"\n\n🔧 МЕТОДЫ ИЗВЛЕЧЕНИЯ:"
            for method, count in sorted(session.method_stats.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / session.total_servers) * 100
                report += f"\n   {method}: {count} ({percentage:.1f}%)"

        # Добавляем проблемные серверы
        failed_servers = [m for m in session.server_metrics if not m.success]
        if failed_servers:
            report += f"\n\n❌ ПРОБЛЕМНЫЕ СЕРВЕРЫ ({len(failed_servers)}):"
            for server in failed_servers[:10]:  # Показываем первые 10
                report += f"\n   {server.server_name}: {server.error_type or 'Unknown error'}"
            if len(failed_servers) > 10:
                report += f"\n   ... и еще {len(failed_servers) - 10} серверов"

        return report
    
    def get_historical_summary(self, days: int = 7) -> Dict[str, Any]:
        """Получение исторической сводки за последние дни"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_sessions = [
            s for s in self.historical_metrics 
            if datetime.fromisoformat(s.start_time) > cutoff_date
        ]
        
        if not recent_sessions:
            return {"message": "Нет данных за указанный период"}
        
        total_servers = sum(s.total_servers for s in recent_sessions)
        total_successful = sum(s.successful_extractions for s in recent_sessions)
        avg_success_rate = (total_successful / total_servers * 100) if total_servers > 0 else 0
        
        # Агрегируем ошибки
        all_errors = {}
        for session in recent_sessions:
            for error_type, count in session.error_stats.items():
                all_errors[error_type] = all_errors.get(error_type, 0) + count
        
        return {
            "period_days": days,
            "sessions_count": len(recent_sessions),
            "total_servers": total_servers,
            "total_successful": total_successful,
            "avg_success_rate": avg_success_rate,
            "top_errors": dict(sorted(all_errors.items(), key=lambda x: x[1], reverse=True)[:5]),
            "latest_session": recent_sessions[-1].get_summary() if recent_sessions else None
        }
    
    def _load_historical_metrics(self):
        """Загрузка исторических метрик"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.historical_metrics = []
                for session_data in data.get('sessions', []):
                    # Восстанавливаем SessionMetrics из JSON
                    session = SessionMetrics(**{
                        k: v for k, v in session_data.items() 
                        if k != 'server_metrics'
                    })
                    
                    # Восстанавливаем метрики серверов
                    for metric_data in session_data.get('server_metrics', []):
                        metric = ServerExtractionMetric(**metric_data)
                        session.server_metrics.append(metric)
                    
                    self.historical_metrics.append(session)
                
                print(f"📊 Загружено {len(self.historical_metrics)} исторических сессий")
                
            except Exception as e:
                print(f"⚠️ Не удалось загрузить исторические метрики: {e}")
                self.historical_metrics = []
    
    def _save_metrics(self):
        """Сохранение метрик в файл"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "sessions": [asdict(session) for session in self.historical_metrics]
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Метрики сохранены в {self.metrics_file}")
            
        except Exception as e:
            print(f"⚠️ Не удалось сохранить метрики: {e}")
    
    def export_csv_report(self, filename: str = None) -> str:
        """Экспорт отчета в CSV формат"""
        if filename is None:
            filename = os.path.join(self.output_dir, f"parsing_report_{int(time.time())}.csv")
        
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовки
                writer.writerow([
                    'Session ID', 'Server Name', 'Success', 'Duration (s)',
                    'Attempt Count', 'Error Type', 'Extraction Method', 'Timestamp'
                ])
                
                # Данные
                for session in self.historical_metrics:
                    for metric in session.server_metrics:
                        writer.writerow([
                            session.session_id,
                            metric.server_name,
                            metric.success,
                            metric.duration,
                            metric.attempt_count,
                            metric.error_type or '',
                            metric.extraction_method or '',
                            metric.timestamp
                        ])
            
            print(f"📊 CSV отчет экспортирован: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка экспорта CSV: {e}")
            return ""

class ParsingCache:
    """Система кэширования для парсера"""
    
    def __init__(self, cache_dir: str = "./output/cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "server_cache.json")
        self.cache_duration = 3600 * 24  # 24 часа
        self.cache = {}
        
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()
    
    def get_cached_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Получение кэшированной информации о сервере"""
        if server_name in self.cache:
            data, timestamp = self.cache[server_name]
            
            # Проверяем срок действия кэша
            if time.time() - timestamp < self.cache_duration:
                print(f"💾 Использован кэш для {server_name}")
                return data
            else:
                # Удаляем устаревший кэш
                del self.cache[server_name]
        
        return None
    
    def cache_server_info(self, server_name: str, info: Dict[str, Any]):
        """Кэширование информации о сервере"""
        self.cache[server_name] = (info, time.time())
        self._save_cache()
        print(f"💾 Кэширована информация для {server_name}")
    
    def clear_expired_cache(self):
        """Очистка устаревшего кэша"""
        current_time = time.time()
        expired_keys = []
        
        for server_name, (data, timestamp) in self.cache.items():
            if current_time - timestamp >= self.cache_duration:
                expired_keys.append(server_name)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            print(f"💾 Очищен устаревший кэш для {len(expired_keys)} серверов")
            self._save_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for server_name, (data, timestamp) in self.cache.items():
            if current_time - timestamp < self.cache_duration:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_hit_rate": 0,  # Будет обновляться во время использования
            "cache_duration_hours": self.cache_duration / 3600
        }
    
    def _load_cache(self):
        """Загрузка кэша из файла"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"💾 Загружен кэш с {len(self.cache)} записями")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить кэш: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Сохранение кэша в файл"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить кэш: {e}")