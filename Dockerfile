# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем пользователя для безопасности и разрешаем запись
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
RUN chmod 755 /app
USER appuser

# Открываем порт
EXPOSE 5000

# Переменные окружения
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Создаем скрипты запуска
RUN echo '#!/bin/bash\n\
echo "Ожидание запуска PostgreSQL..."\n\
sleep 15\n\
echo "Запуск парсера для получения данных..."\n\
python parser_v3.py\n\
echo "Инициализация базы данных..."\n\
python init_db.py\n\
echo "Запуск Flask приложения..."\n\
python app.py' > /app/start.sh && chmod +x /app/start.sh

RUN echo '#!/bin/bash\n\
echo "Ожидание запуска PostgreSQL..."\n\
sleep 15\n\
echo "Запуск планировщика в фоновом режиме..."\n\
python scheduler.py &\n\
SCHEDULER_PID=$!\n\
echo "Инициализация базы данных..."\n\
python init_db.py\n\
echo "Запуск Flask приложения..."\n\
python app.py\n\
kill $SCHEDULER_PID' > /app/start_with_scheduler.sh && chmod +x /app/start_with_scheduler.sh

# Команда запуска (по умолчанию без планировщика)
CMD ["/app/start.sh"] 