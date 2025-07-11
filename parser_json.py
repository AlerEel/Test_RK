import requests

# URL API
url = "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search?page=1&itemsPerPage=100"


# Тело запроса (фильтр по датам)
payload = {
    "examStartFrom": "2025-06-09T21:00:00.000Z",
    "examStartTo": "2025-07-09T21:00:00.000Z",
    "formList": [],
    "hasOffences": [],
    "isAssigned": None,
    "numberOrUriNumber": None,
    "orderNumber": None,
    "oversightActivitiesRefList": [],
    "preceptsMade": [],
    "statusList": [],
    "typeList": [],
}

# Отправляем POST-запрос
response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    print("Всего записей:", data.get("total", 0))

    # Вывод первых 5 записей
    for item in data.get("data", [])[:5]:
        exam_date = item.get("examStart")
        address = item.get("address")
        result = item.get("resultText")
        print(f"{exam_date} — {address} — {result}")

else:
    print("Ошибка:", response.status_code)
    print(response.text)