from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json

# Настройки подключения к браузеру
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Максимизировать окно браузера
browser = webdriver.Chrome(service=service, options=options)

try:
    # Открываем страницу
    browser.get("https://dom.gosuslugi.ru/#!/rp")
    sleep(5)  # Ждем загрузки страницы

    # Явное ожидание загрузки полей
    wait = WebDriverWait(browser, 10)

    # Получаем текущую дату и дату месяц назад
    today = datetime.now()
    last_month = today - timedelta(days=30)

    # Форматируем даты в нужный формат (например, "ДД.ММ.ГГГГ")
    start_date = last_month.strftime("%d.%m.%Y")
    end_date = today.strftime("%d.%m.%Y")

    # Первое поле (первый input с placeholder="ДД.ММ.ГГГГ")
    first_input = wait.until(EC.element_to_be_clickable((By.XPATH, '(//input[@placeholder="ДД.ММ.ГГГГ"])[1]')))
    first_input.clear()
    first_input.send_keys(start_date)

    # Второе поле (второй input с placeholder="ДД.ММ.ГГГГ")
    second_input = wait.until(EC.element_to_be_clickable((By.XPATH, '(//input[@placeholder="ДД.ММ.ГГГГ"])[2]')))
    second_input.clear()
    second_input.send_keys(end_date)

    # Пауза для проверки результата
    sleep(3)

    # Нажимаем кнопку поиска (если есть)
    find_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Найти")]')))
    find_button.click()

    # Ждем загрузки результатов
    sleep(25)

    # Получаем cookies
    cookies = browser.get_cookies()

    # Получаем Session-GUID / State-GUID из заголовков или localStorage/sessionStorage
    session_guid = browser.execute_script("return localStorage.getItem('Session-GUID');")
    state_guid = browser.execute_script("return sessionStorage.getItem('State-GUID');")
    print(cookies)
    print(session_guid)
    print(state_guid)

     # Получить HTML-код страницы
    page_source = browser.page_source

    # Использовать Beautiful Soup для парсинга HTML
    soup = BeautifulSoup(page_source, "html.parser")

    # Найти таблицу по классу
    table = soup.find("table", class_="table register-card__table register-card__table_stripped")

    if table:
        # Спарсить данные из таблицы
        rows = table.find_all("tr")
        data = []

        for row in rows:
            cols = row.find_all("td")
            cols = [col.text.strip() for col in cols]
            data.append(cols)

        # Вывести данные
        print("Парсинг данных из таблицы:")
        for row in data:
            print(row)

    else:
        print("Таблица не найдена.")

    # Найти таблицу по классу
    table = soup.find("table", class_="table register-card__table register-card__table_pad_dark register-card__table_stripped")
        
    if table:
        # Спарсить данные из таблицы
        rows = table.find_all("tr")
        data = []

        for row in rows:
            cols = row.find_all("td")
            cols = [col.text.strip() for col in cols]
            data.append(cols)

        # Вывести данные
        print("Парсинг данных из таблицы:")
        for row in data:
            print(row)

    else:
        print("Таблица не найдена.")

    # Ищем нужный <script> с JSON.parse
    script_tag = soup.find('script', string=lambda t: t and 'JSON.parse' in t)

    if script_tag:
        # Получаем содержимое скрипта
        script_text = script_tag.string

        # Находим JSON строку внутри JSON.parse(...)
        try:
            json_str = script_text.split('JSON.parse("')[1].split('")')[0]

            # Декодируем из экранированной строки
            decoded_json = json.loads(json_str.replace('\\"', '"'))

            print(decoded_json)
        except IndexError:
            print("Не удалось найти JSON.parse в скрипте")
        except json.JSONDecodeError as e:
            print("Ошибка декодирования JSON:", e)

    else:
        print("Script-тег с JSON.parse не найден")


finally:
    #browser.quit()
    pass