import sqlite3

DB_NAME = 'inspections.db'
TABLE_NAME = 'inspections'

COLUMNS = [
    ('entity_name', 'TEXT'),
    ('ogrn', 'TEXT'),
    ('purpose', 'TEXT'),
    ('status', 'TEXT'),
    ('result', 'TEXT'),
    ('examStartDate', 'TEXT')
]

def create_table(conn):
    columns_sql = ', '.join([f'{name} {type_}' for name, type_ in COLUMNS])
    sql = f'''CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {columns_sql}
    )'''
    conn.execute(sql)
    print(f"[INFO] Таблица {TABLE_NAME} создана или уже существует.")

def insert_data_from_list(data):
    conn = sqlite3.connect(DB_NAME)
    create_table(conn)
    # Очищаем таблицу перед загрузкой новых данных
    conn.execute(f'DELETE FROM {TABLE_NAME}')
    print(f"[INFO] Старые данные удалены из таблицы {TABLE_NAME}.")
    placeholders = ', '.join(['?'] * len(COLUMNS))
    columns = ', '.join([name for name, _ in COLUMNS])
    sql = f'INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})'
    cur = conn.cursor()
    for item in data:
        values = tuple(item.get(name, '') for name, _ in COLUMNS)
        cur.execute(sql, values)
    conn.commit()
    print(f"[INFO] Вставлено {len(data)} записей в таблицу {TABLE_NAME}.")
    conn.close() 