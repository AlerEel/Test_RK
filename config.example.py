# Пример конфигурационного файла
# Скопируйте этот файл как config.py и заполните своими данными

# Настройки подключения к PostgreSQL
DB_CONFIG = {
    'host': 'localhost',           # Адрес сервера БД
    'port': 5432,                  # Порт PostgreSQL
    'database': 'your_database',   # Имя базы данных
    'username': 'your_username',   # Имя пользователя
    'password': 'your_password'    # Пароль
}

# Настройки API
API_CONFIG = {
    'url': 'https://api.example.com/data.json',  # URL API
    'timeout': 10                                 # Таймаут запроса в секундах
} 