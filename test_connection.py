import psycopg2
from psycopg2 import Error
from config import DB_CONFIG

def test_db_connection():
    """Проверка подключения к PostgreSQL"""
    
    # Настройки подключения из конфигурационного файла
    server = DB_CONFIG['host']
    database = DB_CONFIG['database']
    username = DB_CONFIG['username']
    password = DB_CONFIG['password']
    port = DB_CONFIG['port']
    
    print("=== Проверка подключения к PostgreSQL ===")
    print(f"Сервер: {server}")
    print(f"База данных: {database}")
    print(f"Пользователь: {username}")
    print(f"Порт: {port}")
    print("-" * 40)
    
    try:
        # Подключаемся к базе данных
        conn_str = f"host={server} port={port} dbname={database} user={username} password={password}"
        connection = psycopg2.connect(conn_str)
        print("✅ Подключение к базе данных успешно!")
        
        cursor = connection.cursor()
        
        # Проверяем версию PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Версия PostgreSQL: {version[0]}")
        
        # Проверяем существование таблицы inspections
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'inspections'
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Таблица 'inspections' существует")
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM inspections")
            count = cursor.fetchone()[0]
            print(f"Количество записей в таблице: {count}")
            
            # Показываем структуру таблицы
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'inspections'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("Структура таблицы inspections:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        else:
            print("⚠️  Таблица 'inspections' не существует")
        
        cursor.close()
        connection.close()
        print("✅ Соединение закрыто")
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("\nВозможные причины:")
        print("1. PostgreSQL не запущен")
        print("2. Неправильные настройки подключения")
        print("3. База данных не существует")
        print("4. Неправильные учетные данные")
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    test_db_connection() 