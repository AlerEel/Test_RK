import json
import psycopg2
from config import DB_CONFIG

JSON_FILE = 'inspections.json'

# Чтение данных из JSON
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Подключение к PostgreSQL
conn = psycopg2.connect(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    dbname=DB_CONFIG['database'],
    user=DB_CONFIG['username'],
    password=DB_CONFIG['password']
)
cur = conn.cursor()

# Удалить старую таблицу, если есть
cur.execute('DROP TABLE IF EXISTS inspections')

# Создание таблицы, если не существует
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

conn.commit()
cur.close()
conn.close()
print('Данные успешно перенесены в базу данных PostgreSQL.') 