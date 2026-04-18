# Telegram-бот для записи к мастеру маникюра

## Возможности

- Запись клиента на свободный слот (1 активная запись на пользователя).
- Выбор даты и времени через inline-кнопки.
- Прайс и портфолио в главном меню.
- Проверка подписки на канал перед доступом к записи.
- Отмена записи клиентом (слот снова становится свободным).
- Уведомления администратору и в канал при создании/отмене записи.
- Напоминание за 24 часа до визита через APScheduler.
- Восстановление задач напоминаний после перезапуска бота.
- Админ-панель (`/admin`) для управления расписанием.

## Установка и запуск

### Локальный запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/manicure_bot.git
   cd manicure_bot
   ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте `.env` файл на основе `.env.example` и заполните значения.

5. Запустите бота:
   ```bash
   python bot.py
   ```

### Запуск на VPS с Docker

1. Установите Docker и Docker Compose на сервере.

2. Клонируйте репозиторий и перейдите в папку.

3. Создайте `.env` файл.

4. Запустите с Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Запуск на VPS без Docker

1. Установите Python 3.11+.

2. Клонируйте репозиторий.

3. Установите зависимости: `pip install -r requirements.txt`

4. Создайте `.env` файл.

5. Запустите: `python bot.py`

### Автозапуск с systemd (Linux)

1. Скопируйте `manicure-bot.service` в `/etc/systemd/system/`.

2. Отредактируйте пути в файле сервиса.

3. Включите и запустите:
   ```bash
   sudo systemctl enable manicure-bot
   sudo systemctl start manicure-bot
   ```

## Конфигурация

Все настройки в `.env` файле:
- `BOT_TOKEN`: Токен Telegram бота
- `ADMIN_ID`: ID администратора
- `CHANNEL_ID`: ID канала (опционально)
- `CHANNEL_LINK`: Ссылка на канал (опционально)
