#!/bin/bash

echo "Ожидание запуска PostgreSQL..."
sleep 15

echo "Запуск планировщика в фоновом режиме..."
python scheduler.py &
SCHEDULER_PID=$!

echo "Инициализация базы данных..."
python init_db.py

echo "Запуск Flask приложения..."
python app.py

# Если Flask приложение завершится, остановим планировщик
kill $SCHEDULER_PID 