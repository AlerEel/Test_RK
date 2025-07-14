#!/usr/bin/env python3
"""
Планировщик для периодического запуска парсера
"""

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_parser():
    """Запуск парсера и обновление базы данных"""
    try:
        logging.info("Запуск парсера...")
        
        # Запускаем парсер
        result = subprocess.run([sys.executable, "parser_v3.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logging.info("Парсер успешно завершил работу")
            logging.info(result.stdout)
            
            # Обновляем базу данных
            logging.info("Обновление базы данных...")
            db_result = subprocess.run([sys.executable, "init_db.py", "--force"], 
                                     capture_output=True, text=True, timeout=60)
            
            if db_result.returncode == 0:
                logging.info("База данных успешно обновлена")
                logging.info(db_result.stdout)
            else:
                logging.error(f"Ошибка обновления базы: {db_result.stderr}")
                
        else:
            logging.error(f"Ошибка в парсере: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logging.error("Превышено время ожидания выполнения")
    except Exception as e:
        logging.error(f"Ошибка при запуске парсера: {e}")

def main():
    """Основная функция планировщика"""
    logging.info("Запуск планировщика...")
    
    # Настройка расписания
    # Запуск каждый день в 6:00 утра
    #schedule.every().day.at("06:00").do(run_parser)
    
    # Запуск каждый час (для тестирования)
    schedule.every().hour.do(run_parser)
    
    # Запуск каждые 6 часов
    # schedule.every(6).hours.do(run_parser)
    
    # Запуск каждые 12 часов
    # schedule.every(12).hours.do(run_parser)
    
    logging.info("Планировщик настроен. Следующий запуск парсера: 06:00")
    
    # Запускаем парсер сразу при старте
    logging.info("Первоначальный запуск парсера...")
    run_parser()
    
    # Бесконечный цикл для выполнения запланированных задач
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == "__main__":
    main() 