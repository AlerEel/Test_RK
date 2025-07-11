import requests
import json
import psycopg2
from psycopg2 import Error
from config import DB_CONFIG, API_CONFIG

def test_connection():
    """Тест подключения к PostgreSQL"""
    try:
        # Подключаемся к базе данных PostgreSQL
        conn_str = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['username']} password={DB_CONFIG['password']}"
        print(f"Подключение к PostgreSQL: {conn_str}")
        
        connection = psycopg2.connect(conn_str)
        print("✅ Подключение к PostgreSQL успешно!")
        
        cursor = connection.cursor()
        
        # Проверяем версию PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Версия PostgreSQL: {version[0]}")
        
        # Создаем таблицу для сохранения результатов проверок
        create_table_query = """
        CREATE TABLE IF NOT EXISTS inspections (
            id SERIAL PRIMARY KEY,
            company_name TEXT,
            ogrn VARCHAR(15),
            inspection_purpose TEXT,
            inspection_status TEXT,
            inspection_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
        print("✅ Таблица 'inspections' создана/проверена")
        
        cursor.close()
        connection.close()
        print("✅ Соединение закрыто")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("\nВозможные причины:")
        print("1. PostgreSQL не установлен или не запущен")
        print("2. Неправильные настройки подключения")
        print("3. База данных не существует")
        print("4. Неправильные учетные данные")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def fetch_data():
    """Получение данных с API"""
    # Адрес API из конфигурации
    api_url = API_CONFIG['url']
    
    try:
        print(f"Запрос к API: {api_url}")
        response = requests.get(api_url, timeout=API_CONFIG['timeout'])
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Ошибка при получении данных: {response.status_code}")
            print("Возможно, API недоступен или URL изменился")
            return []
            
        data = response.json()  # Десериализуем JSON-ответ
        inspections = data.get('inspections', [])  # Безопасное получение данных
        print(f"Получено {len(inspections)} записей с API")
        return inspections
        
    except requests.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
        return []

def save_to_db(data):
    """Сохранение данных в PostgreSQL"""
    if not data:
        print("Нет данных для сохранения")
        return
        
    try:
        # Подключаемся к базе данных
        conn_str = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['username']} password={DB_CONFIG['password']}"
        connection = psycopg2.connect(conn_str)
        cursor = connection.cursor()
        
        saved_count = 0
        for item in data:
            try:
                insert_query = """
                    INSERT INTO inspections(company_name, ogrn, inspection_purpose, inspection_status, inspection_result)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    item.get('company_name', ''),
                    item.get('ogrn', ''),
                    item.get('inspection_purpose', ''),
                    item.get('inspection_status', ''),
                    item.get('inspection_result', '')
                ))
                saved_count += 1
            except Exception as e:
                print(f"Ошибка при сохранении записи: {e}")
                continue
        
        connection.commit()
        print(f"✅ Сохранено {saved_count} записей в базу данных")
        
        cursor.close()
        connection.close()
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка при сохранении в базу данных: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка при сохранении: {e}")

def show_table_info():
    """Показать информацию о таблице inspections"""
    try:
        conn_str = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['username']} password={DB_CONFIG['password']}"
        connection = psycopg2.connect(conn_str)
        cursor = connection.cursor()
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM inspections")
        count = cursor.fetchone()[0]
        print(f"Количество записей в таблице inspections: {count}")
        
        if count > 0:
            # Показываем последние 5 записей
            cursor.execute("SELECT * FROM inspections ORDER BY id DESC LIMIT 5")
            records = cursor.fetchall()
            print("\nПоследние 5 записей:")
            for record in records:
                print(f"ID: {record[0]}, Компания: {record[1]}, ОГРН: {record[2]}")
        
        cursor.close()
        connection.close()
        
    except psycopg2.Error as e:
        print(f"Ошибка при получении информации о таблице: {e}")

if __name__ == "__main__":
    print("=== Парсер данных проверок ===")
    print("=== Тест подключения к PostgreSQL ===")
    
    if test_connection():
        print("\n=== Получение и сохранение данных ===")
        inspections = fetch_data()
        if inspections:
            save_to_db(inspections)
        else:
            print("Нет данных для сохранения")
        
        print("\n=== Информация о таблице ===")
        show_table_info()
    else:
        print("Не удалось подключиться к базе данных")
        print("Проверьте настройки подключения и убедитесь, что PostgreSQL запущен")