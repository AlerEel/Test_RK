import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Конфигурация базы данных
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/Test_RK')

def init_database():
    """Инициализация базы данных и загрузка данных из JSON"""
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Создание таблицы
        cur.execute('''
            CREATE TABLE IF NOT EXISTS inspections (
                id SERIAL PRIMARY KEY,
                entity_name TEXT,
                ogrn TEXT,
                purpose TEXT,
                status TEXT,
                result TEXT,
                inspection_date TEXT
            )
        ''')
        
        # Проверяем, есть ли уже данные в таблице
        cur.execute('SELECT COUNT(*) FROM inspections')
        count = cur.fetchone()[0]
        
        # Всегда очищаем таблицу и загружаем новые данные
        if count > 0:
            print("Очистка таблицы...")
            cur.execute('DELETE FROM inspections')
            cur.execute('ALTER SEQUENCE inspections_id_seq RESTART WITH 1')
        
        print("Загрузка новых данных...")
        # Загружаем данные из JSON файла
        try:
            # Пытаемся найти файл в разных местах
            json_files = ['inspections.json', '/tmp/inspections.json']
            data = None
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f'Файл найден: {json_file}')
                        break
                except FileNotFoundError:
                    continue
            
            if data is None:
                raise FileNotFoundError('Файл inspections.json не найден ни в одной из директорий')
            
            print(f'Найдено {len(data)} записей в inspections.json')
            
            # Вставка данных
            for item in data:
                cur.execute('''
                    INSERT INTO inspections (entity_name, ogrn, purpose, status, result, inspection_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    item.get('entity_name', ''),
                    item.get('ogrn', ''),
                    item.get('purpose', ''),
                    item.get('status', ''),
                    item.get('result', ''),
                    item.get('inspection_date', '')
                ))
            
            print(f'Загружено {len(data)} записей в базу данных.')
            # Очищаем файл после загрузки
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f'Файл {json_file} очищен после загрузки данных.')
            except Exception as e:
                print(f'Ошибка при очистке файла {json_file}: {e}')
        except FileNotFoundError:
            print('Файл inspections.json не найден. База данных будет пустой.')
        
        conn.commit()
        cur.close()
        conn.close()
        print('База данных успешно инициализирована.')
        
    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {e}')

if __name__ == '__main__':
    init_database() 