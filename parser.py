from seleniumwire import webdriver  # Важно! Не обычный selenium.webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
from time import sleep
from selenium.webdriver.common.by import By
import uuid
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# Настройки браузера
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Запускаем браузер с selenium-wire
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
# Переходим на страницу
driver.get("https://dom.gosuslugi.ru/#!/rp")

# Ждём загрузки
sleep(10)

# Ждём, пока кнопка станет кликабельной
find_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Найти")]'))
)
driver.save_screenshot("before_click.png")
find_button.click()

# Ждём загрузки
sleep(15)

# Путь к файлу
output_file = "requests_and_responses.json"

# Список для хранения данных
data = []

# Перебираем все запросы
for request in driver.requests:
    if request.response:
        try:
            req_body = request.body.decode('utf-8', errors='replace')
        except:
            req_body = None

        try:
            resp_body = request.response.body.decode('utf-8', errors='replace')
        except:
            resp_body = None

        data.append({
            "url": request.url,
            "method": request.method,
            "request_headers": dict(request.headers),
            "request_body": req_body,
            "response_headers": dict(request.response.headers),
            "response_body": resp_body,
            "status_code": request.response.status_code
        })

for entry in data:
    url = entry.get("url", "")
    request_headers = entry.get("request_headers", {})
    
    # Фильтруем по нужному URL или просто берём первый подходящий
    if "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search" in url:
        headers = {
            "User-Agent": request_headers.get("User-Agent"),
            "Content-Type": request_headers.get("Content-Type", "application/json"),
            "Referer": request_headers.get("Referer", "https://dom.gosuslugi.ru/ "),
            "Origin": request_headers.get("Origin", "https://dom.gosuslugi.ru/ "),
            "Session-GUID": request_headers.get("Session-GUID"),
            "State-GUID": request_headers.get("State-GUID", "/rp"),
            "Request-GUID": str(uuid.uuid4()),  # генерируем новый
            "Cookie": request_headers.get("Cookie")  # может быть None
        }

        # Проверяем, что все нужные поля присутствуют
        if all(headers.values()):
            print("Найдены нужные заголовки:")
            print(json.dumps(headers, indent=2, ensure_ascii=False))
            with open("real_headers.json", "w", encoding="utf-8") as f:
                json.dump(headers, f, ensure_ascii=False, indent=2)
            print("Заголовки сохранены в real_headers.json")
            break

# Закрываем браузер
driver.quit()