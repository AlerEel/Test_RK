import sqlite3
from typing import List, Dict, Any

class SqliteLoader:
    def __init__(self, db_name: str = 'data/inspections.db', table_name: str = 'inspections'):
        self.db_name = db_name
        self.table_name = table_name
        self.columns = [
            ('entity_name', 'TEXT'),
            ('ogrn', 'TEXT'),
            ('purpose', 'TEXT'),
            ('status', 'TEXT'),
            ('result', 'TEXT'),
            ('examStartDate', 'TEXT')
        ]

    def create_table(self, conn):
        columns_sql = ', '.join([f'{name} {type_}' for name, type_ in self.columns])
        sql = f'''CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns_sql}
        )'''
        conn.execute(sql)
        print(f"[INFO] Таблица {self.table_name} создана или уже существует.")

    def insert_data_from_list(self, data: List[Dict[str, Any]]):
        conn = sqlite3.connect(self.db_name)
        self.create_table(conn)
        # Очищаем таблицу перед загрузкой новых данных
        conn.execute(f'DELETE FROM {self.table_name}')
        print(f"[INFO] Старые данные удалены из таблицы {self.table_name}.")
        placeholders = ', '.join(['?'] * len(self.columns))
        columns = ', '.join([name for name, _ in self.columns])
        sql = f'INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})'
        cur = conn.cursor()
        for item in data:
            values = tuple(item.get(name, '') for name, _ in self.columns)
            cur.execute(sql, values)
        conn.commit()
        print(f"[INFO] Вставлено {len(data)} записей в таблицу {self.table_name}.")
        conn.close() 