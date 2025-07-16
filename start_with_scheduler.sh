#!/bin/bash
set -e  # Скрипт завершится при любой ошибке

echo "Ожидание запуска PostgreSQL..."
sleep 15

echo "Получение заголовков через parser.py..."
if ! python parser.py; then
    echo "ОШИБКА: Не удалось получить заголовки. Останавливаем процесс."
    exit 1
fi

# Проверяем, что файл заголовков создан
if [ ! -f "real_headers.json" ]; then
    echo "ОШИБКА: Файл real_headers.json не найден. Останавливаем процесс."
    exit 1
fi

echo "Запуск парсера данных..."
if ! python parser_v3.py; then
    echo "ОШИБКА: Не удалось получить данные. Останавливаем процесс."
    exit 1
fi

echo "Загрузка данных в базу..."
if ! python init_db.py; then
    echo "ОШИБКА: Не удалось загрузить данные в БД. Останавливаем процесс."
    exit 1
fi

# Проверяем, что данные загружены в БД
echo "Проверка наличия данных в БД..."
if ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM inspections')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    if count == 0:
        print('ОШИБКА: В базе данных нет записей')
        exit(1)
    print(f'Найдено {count} записей в БД')
except Exception as e:
    print(f'ОШИБКА при проверке БД: {e}')
    exit(1)
"; then
    echo "ОШИБКА: Проверка БД не прошла. Останавливаем процесс."
    exit 1
fi

echo "Запуск Flask приложения..."
python app.py &

echo "Запуск планировщика..."
python scheduler.py 