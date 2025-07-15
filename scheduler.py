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

def run_parser_and_update_db():
    logging.info("Запуск парсера...")
    result = subprocess.run([sys.executable, "parser_v3.py"], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info("Парсер успешно завершил работу")
        logging.info(result.stdout)
    else:
        logging.error(f"Ошибка в парсере: {result.stderr}")
        return
    logging.info("Обновление базы данных...")
    db_result = subprocess.run([sys.executable, "init_db.py"], capture_output=True, text=True)
    if db_result.returncode == 0:
        logging.info("База данных успешно обновлена")
        logging.info(db_result.stdout)
    else:
        logging.error(f"Ошибка обновления базы: {db_result.stderr}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/app/scheduler.log'),
            logging.StreamHandler()
        ]
    )
    logging.info("Запуск планировщика...")
    # Запуск каждый день в 6:00 утра
    schedule.every().day.at("06:00").do(run_parser_and_update_db)
    # Для теста можно раскомментировать:
    # schedule.every().hour.do(run_parser_and_update_db)
    logging.info("Планировщик настроен. Следующий запуск парсера: 06:00")
    # run_parser_and_update_db()  # Удалено: первый запуск теперь только по расписанию
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 