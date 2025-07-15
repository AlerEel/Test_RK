#!/bin/bash
set -e  # Скрипт завершится при любой ошибке

echo "Ожидание запуска PostgreSQL..."
sleep 15

echo "Запуск парсера..."
python parser_v3.py

echo "Загрузка данных в базу..."
python init_db.py

echo "Запуск Flask приложения..."
python app.py &

echo "Запуск планировщика..."
python scheduler.py 