#!/usr/bin/env python3
"""
Скрипт для обновления данных через парсер
Используется для периодического обновления данных в базе
"""

import os
import subprocess
import sys
from datetime import datetime

def update_data():
    """Обновление данных через парсер и перезагрузка в базу"""
    print(f"[{datetime.now()}] Начинаем обновление данных...")
    
    try:
        # Запускаем парсер
        print("Запуск парсера...")
        result = subprocess.run([sys.executable, "parser_v3.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("Парсер успешно завершил работу")
            print(result.stdout)
        else:
            print(f"Ошибка в парсере: {result.stderr}")
            return False
        
        # Очищаем базу данных и загружаем новые данные
        print("Обновление базы данных...")
        result = subprocess.run([sys.executable, "init_db.py", "--force"], 
                              capture_output=True, text=True, timeout=60)
        
        # Если файл был сохранен в /tmp, копируем его в основную директорию
        try:
            import shutil
            if os.path.exists('/tmp/inspections.json'):
                shutil.copy('/tmp/inspections.json', 'inspections.json')
                print("Файл скопирован из временной директории")
        except Exception as e:
            print(f"Ошибка при копировании файла: {e}")
        
        if result.returncode == 0:
            print("База данных успешно обновлена")
            print(result.stdout)
            return True
        else:
            print(f"Ошибка обновления базы: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Превышено время ожидания выполнения")
        return False
    except Exception as e:
        print(f"Ошибка при обновлении данных: {e}")
        return False

if __name__ == "__main__":
    success = update_data()
    sys.exit(0 if success else 1) 