# Test_RK - Система отображения результатов проверок

Flask-приложение для отображения результатов проверок с использованием PostgreSQL и автоматическим парсингом данных с API Госуслуг.

## Структура проекта

### Основные файлы
- `app.py` - Flask-приложение с веб-интерфейсом
- `parser_v3.py` - парсер для получения данных с API Госуслуг
- `init_db.py` - инициализация базы данных и загрузка данных
- `scheduler.py` - планировщик для автоматического обновления данных
- `cookie_manager.py` - управление cookies для API запросов

### Конфигурация и запуск
- `start_with_scheduler.sh` - скрипт запуска с планировщиком
- `docker-compose.yml` - конфигурация Docker Compose
- `Dockerfile` - конфигурация Docker-образа
- `requirements.txt` - зависимости Python

### Шаблоны и данные
- `templates/index.html` - HTML-шаблон для отображения результатов
- `inspections.json` - данные для загрузки в базу (создается парсером)

## Запуск

### В Docker (рекомендуется)

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd Test_RK
   ```

2. **Запустите приложение:**
   ```bash
   docker-compose up --build
   ```

3. **Откройте браузер:**
   ```
   http://localhost:5000
   ```

**Примечание:** Первый запуск может занять несколько минут, пока парсер получит данные с API.

### Без Docker

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте PostgreSQL:**
   - Создайте базу данных `Test_RK`
   - Установите переменную окружения:
     ```bash
     export DATABASE_URL="postgresql://postgres:postgres@localhost/Test_RK"
     ```

3. **Запустите парсер и загрузите данные:**
   ```bash
   python parser_v3.py
   python init_db.py
   ```

4. **Запустите Flask-приложение:**
   ```bash
   python app.py
   ```

5. **Откройте браузер:**
   ```
   http://localhost:5000
   ```

## Управление контейнерами

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f app

# Пересборка
docker-compose up --build
```

## Автоматическое обновление

Приложение автоматически обновляет данные каждый день в 6:00 утра. Логи планировщика сохраняются в `/app/scheduler.log`.

## Конфигурация

### Переменные окружения
- `DATABASE_URL` - URL подключения к PostgreSQL
- `FLASK_ENV` - окружение Flask (production/development)
- `TZ` - временная зона (Europe/Moscow)

### База данных
- **База:** Test_RK_docker (в Docker) / Test_RK (локально)
- **Порт:** 5533 (в Docker) / 5432 (локально)
- **Пользователь:** postgres
- **Пароль:** postgres 