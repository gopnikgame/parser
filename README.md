# 🔍 DNSCrypt Parser with Scheduler

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)
![Selenium](https://img.shields.io/badge/Selenium-4.15.2-orange.svg)
![Scheduler](https://img.shields.io/badge/Scheduler-7%20days-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Автоматизированный парсер для сбора публичных данных DNSCrypt серверов с поддержкой расписания**

🌐 Источник: [dnscrypt.info/public-servers](https://dnscrypt.info/public-servers)
⏰ **НОВОЕ**: Автоматическое обновление каждые 7 дней!

</div>

---

## 📖 Описание

DNSCrypt Parser — это полностью автоматизированное решение для сбора информации о публичных DNSCrypt серверах и релеях с встроенным планировщиком. Проект использует Selenium для парсинга веб-страницы, Docker для изоляции среды выполнения и GitHub API для автоматического обновления конфигурационных файлов.

### ⭐ Ключевые возможности

- 🤖 **Полная автоматизация** — парсинг, обработка и отправка в GitHub
- ⏰ **Встроенный scheduler** — автоматический запуск каждые 7 дней
- 🔄 **Умный перезапуск** — отсчет начинается заново при перезапуске контейнера
- 🐳 **Docker контейнеризация** — изолированная среда выполнения
- 🔄 **Обновление в реальном времени** — актуальные данные с dnscrypt.info
- 📤 **GitHub интеграция** — автоматические коммиты через API
- 💾 **Резервное копирование** — сохранение оригинальных файлов
- 📊 **Детальная отчетность** — подробные логи работы парсера и scheduler'а
- 🛡️ **Безопасность** — работа под непривилегированным пользователем

---

## 🚀 Быстрый старт

### 🎯 Автоматическая установка (рекомендуется)# Скачайте и запустите launcher
wget -O launcher_parser.sh https://raw.githubusercontent.com/gopnikgame/parser/main/launcher_parser.sh
chmod +x launcher_parser.sh
sudo ./launcher_parser.sh
### 🔧 Ручная установка# Клонируйте репозиторий
git clone https://github.com/gopnikgame/parser.git
cd parser

# Создайте .env файл из примера
cp .env.example .env
nano .env  # Настройте GitHub токен

# Запустите скрипт управления
chmod +x manage_parser.sh
./manage_parser.sh
---

## ⏰ Новая функция: Scheduler

### 🔄 Как работает scheduler

1. **Первый запуск** — парсер выполняется сразу после запуска контейнера
2. **Автоматический интервал** — следующий запуск через 7 дней
3. **Умный перезапуск** — при перезапуске контейнера отсчет начинается заново
4. **Логирование** — все действия scheduler'а записываются в лог
5. **Мониторинг** — возможность проверить статус и время следующего запуска

### 📋 Файлы scheduler'а

| 📄 Файл | 📝 Описание |
|---------|-------------|
| `output/scheduler.log` | 📊 Лог работы scheduler'а |
| `output/last_run.txt` | ⏰ Время последнего запуска парсера |

---

## ⚙️ Конфигурация

### 📝 Настройка .env файла

Создайте файл `.env` на основе `.env.example`:
# GitHub настройки
GITHUB_TOKEN=your_github_token_here
GITHUB_OWNER=gopnikgame
GITHUB_REPO=Installer_dnscypt
GITHUB_BRANCH=main

# Настройки Chrome (опционально)
CHROME_HEADLESS=true
CHROME_NO_SANDBOX=true
### 🔑 Получение GitHub токена

1. 🌐 Перейдите на https://github.com/settings/tokens
2. 🎫 Нажмите **"Generate new token (classic)"**
3. ✅ Установите права доступа:
   - **repo** (full control of private repositories)
   - **workflow** (update GitHub Action workflows)
4. 📋 Скопируйте токен и добавьте в файл `.env`

---

## 🎮 Использование

### 📱 Интерактивное меню./manage_parser.sh
Новые опции в меню:

- 🔄 **Запустить scheduler** — автоматические обновления каждые 7 дней
- ⏹️ **Остановить scheduler** — остановка автоматических обновлений
- 📊 **Статус scheduler'а** — информация о работе и следующем запуске
- 📄 **Логи scheduler'а** — просмотр логов планировщика

### 🐳 Прямой запуск Docker

#### Запуск с scheduler'ом (рекомендуется)# Построение образа
docker build -t dnscrypt-parser .

# Запуск с scheduler'ом
docker run -d \
    --name dnscrypt-parser-scheduler \
    -v "$(pwd)/output:/app/output" \
    --env-file .env \
    dnscrypt-parser
#### Одноразовый запуск без scheduler'а# Запуск парсера один раз
docker run --rm \
    -v "$(pwd)/output:/app/output" \
    --env-file .env \
    dnscrypt-parser python parser.py
### 🔄 Через Docker Compose

#### Запуск scheduler'а# Запуск scheduler'а в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f
#### Одноразовый запуск# Запуск парсера без scheduler'а
docker-compose --profile manual run --rm dnscrypt-parser-once
---

## 📁 Структура проекта
parser/
├── 🐳 Dockerfile              # Конфигурация Docker образа
├── 🔧 docker-compose.yml      # Docker Compose конфигурация
├── 📦 requirements.txt        # Python зависимости
├── 🐍 parser.py               # Основной скрипт парсера
├── ⏰ scheduler.py            # Планировщик автоматических запусков
├── ⚙️ .env.example            # Пример конфигурации
├── 🛠️ manage_parser.sh        # Скрипт управления
├── 🚀 launcher_parser.sh      # Скрипт автоматической установки
├── 📊 output/                 # Результаты парсинга
│   ├── 🔗 DNSCrypt_relay.txt     # Обновленные релеи
│   ├── 🖥️ DNSCrypt_servers.txt   # Обновленные серверы
│   ├── 📄 update_report.txt      # Отчет о работе
│   ├── ⏰ last_run.txt           # Время последнего запуска
│   └── 📊 scheduler.log          # Лог scheduler'а
└── 📋 logs/                   # Логи работы
    ├── 📝 parser.log             # Основные логи
    └── ❌ error.log              # Логи ошибок
---

## 📊 Результаты работы

После успешного выполнения парсера в директории `output/` создаются:

| 📄 Файл | 📝 Описание |
|---------|-------------|
| `DNSCrypt_relay.txt` | 🔗 Обновленный список релеев |
| `DNSCrypt_servers.txt` | 🖥️ Обновленный список серверов |
| `update_report.txt` | 📊 Подробный отчет о работе |
| `scheduler.log` | ⏰ Лог работы scheduler'а |
| `last_run.txt` | 🕐 Время последнего запуска |
| `*.original_backup` | 💾 Резервные копии оригинальных файлов |

### 📋 Пример отчета# Отчет об обновлении DNSCrypt серверов (Docker)
# Дата: 2024-01-15 14:30:22

Всего серверов обработано: 150
Успешно обновлено: 142

РЕЛЕИ:
anon-cs-fr              -> 51.15.70.167 (DNSCrypt relay)
anon-cs-ireland         -> 94.130.135.131 (DNSCrypt relay)

СЕРВЕРЫ:
cloudflare              -> 1.1.1.1 (DNSCrypt)
quad9-dnscrypt-ip4      -> 9.9.9.9 (DNSCrypt)
---

## ⏰ Управление Scheduler'ом

### 📊 Проверка статуса# Через manage_parser.sh
./manage_parser.sh
# Выберите пункт "6. 📊 Статус scheduler'а"

# Или напрямую через Docker
docker logs dnscrypt-parser-scheduler
### 🔄 Перезапуск scheduler'а# Перезапуск с сохранением отсчета времени
docker-compose restart

# Полный перезапуск (отсчет времени сбрасывается)
docker-compose down
docker-compose up -d
### 📄 Просмотр логов# Логи scheduler'а
tail -f output/scheduler.log

# Логи контейнера
docker-compose logs -f
---

## 🔄 Автоматизация

### ⏰ Встроенный Scheduler

Scheduler автоматически:
- 🔥 Запускает парсер сразу после старта контейнера
- ⏰ Повторяет запуск каждые 7 дней
- 📊 Ведет лог всех операций
- 💾 Сохраняет время последнего запуска
- 🔄 Сбрасывает отсчет при перезапуске контейнера

### 📋 Настройка системного автозапуска

Для автоматического запуска при загрузке системы:
# Создайте systemd service
sudo tee /etc/systemd/system/dnscrypt-parser.service > /dev/null << EOF
[Unit]
Description=DNSCrypt Parser Scheduler
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dnscrypt-parser
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Включите автозапуск
sudo systemctl enable dnscrypt-parser.service
sudo systemctl start dnscrypt-parser.service
---

## 🛠️ Устранение неполадок

### ⏰ Проблемы с Scheduler'ом
# Проверка статуса контейнера
docker ps | grep dnscrypt-parser

# Просмотр логов scheduler'а
docker logs dnscrypt-parser-scheduler

# Проверка файла времени последнего запуска
cat output/last_run.txt

# Перезапуск с сбросом таймера
docker-compose down && docker-compose up -d
### 🐳 Docker проблемы# Проверка Docker
docker --version
docker-compose --version

# Очистка Docker
docker system prune -f

# Просмотр логов
docker-compose logs -f
### 🌐 Chrome/Selenium проблемы# Проверка логов контейнера
docker-compose logs dnscrypt-parser

# Запуск с отладкой (показать браузер)
CHROME_HEADLESS=false ./manage_parser.sh

# Проверка ChromeDriver
docker run --rm dnscrypt-parser chromedriver --version
### 🔑 GitHub API проблемы# Проверка токена
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Проверка прав доступа
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/gopnikgame/Installer_dnscypt
---

## 💻 Системные требования

| Компонент | Требование |
|-----------|------------|
| 🐧 **ОС** | Linux (Ubuntu/Debian рекомендуется) |
| 🐳 **Docker** | 20.10+ |
| 🔧 **Docker Compose** | 1.29+ |
| 🌐 **Интернет** | Стабильное соединение |
| 🔑 **GitHub Token** | Personal Access Token (для автоотправки) |
| 💾 **Диск** | 2GB свободного места |
| 🧠 **RAM** | 1GB минимум |
| ⏰ **Время** | Контейнер должен работать постоянно для scheduler'а |

---

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

### 📋 Как внести вклад:

1. 🍴 **Fork** репозитория
2. 🌿 Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. 💾 Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. 📤 Отправьте в ветку (`git push origin feature/amazing-feature`)
5. 🎯 Создайте **Pull Request**

### 🐛 Сообщение об ошибках

Нашли баг? Создайте [Issue](https://github.com/gopnikgame/parser/issues) с описанием:
- 📝 Подробное описание проблемы
- 🔄 Шаги для воспроизведения
- 🖥️ Информация о системе
- 📋 Логи (если доступны)

---

## 📋 TODO

- [x] ⏰ Встроенный scheduler для автоматических обновлений
- [x] 🔄 Умный перезапуск с сбросом таймера
- [x] 📊 Мониторинг статуса scheduler'а
- [ ] 🔔 Уведомления в Telegram/Discord при ошибках
- [ ] 📊 Web-интерфейс для мониторинга scheduler'а
- [ ] 🔄 Поддержка IPv6 адресов
- [ ] 📈 Метрики и аналитика работы
- [ ] 🌍 Поддержка других источников DNS серверов
- [ ] 🔐 Шифрование конфигурационных файлов

---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT**. Подробности в файле [LICENSE](LICENSE).

---

## 🙏 Благодарности

- 🌐 **DNSCrypt.info** — за предоставление открытых данных
- 🔧 **Selenium** — за мощный инструмент веб-автоматизации
- 🐳 **Docker** — за платформу контейнеризации
- 🐍 **Python** — за простоту и мощь языка
- ⏰ **Cron** — за вдохновение для создания scheduler'а

---

## 📞 Поддержка

<div align="center">

**Нужна помощь?**

📧 [Создать Issue](https://github.com/gopnikgame/parser/issues) • 
💬 [Обсуждения](https://github.com/gopnikgame/parser/discussions) • 
📖 [Wiki](https://github.com/gopnikgame/parser/wiki)

**Сделано с ❤️ для сообщества DNSCrypt**

</div>

---

<div align="center">

![DNSCrypt](https://img.shields.io/badge/DNSCrypt-Powered-blue.svg)
![Open Source](https://img.shields.io/badge/Open%20Source-❤️-red.svg)
![Scheduler](https://img.shields.io/badge/Auto%20Updates-Every%207%20Days-green.svg)

⭐ **Если проект помог вам, поставьте звездочку!** ⭐

</div>
