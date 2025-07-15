import requests
import json
from datetime import datetime, timedelta
import time
import uuid
from cookie_manager import CookieManager

"""
Парсер для получения данных о проверках с API Госуслуг
Автоматически запрашивает данные за последний месяц (30 дней)
С автоматическим получением cookies
"""

def fetch_inspections(page=1, cookie_manager=None):
    # Рассчитываем даты за последний месяц
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    
    # Форматируем даты в ISO 8601 формат с UTC
    exam_start_from = one_month_ago.strftime('%Y-%m-%dT21:00:00.000Z')
    exam_start_to = now.strftime('%Y-%m-%dT21:00:00.000Z')
    
    print(f"Запрашиваем данные с {exam_start_from} по {exam_start_to}")
    
    url = "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search "

    params = {
        'page': page,
        'itemsPerPage': 1000
    }
    payload = {
        "numberOrUriNumber": None,
        "typeList": [],
        "examStartFrom": exam_start_from,
        "examStartTo": exam_start_to,
        "formList": [],
        "hasOffences": [],
        "isAssigned": None,
        "orderNumber": None,
        "oversightActivitiesRefList": [],
        "preceptsMade": [],
        "statusList": [],
        "typeList": []
    }

    if cookie_manager is None:
        print("Не передан cookie_manager — невозможно выполнить запрос")
        return None

    # Принудительно обновляем cookies
    cookie_string, cookies_dict = cookie_manager.get_fresh_cookies(force_refresh=True)

    if not cookie_string:
        print("Не удалось получить свежие cookies — запрос не будет выполнен")
        return None

    headers = cookie_manager.generate_headers(cookie_string)

    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

def format_status(item):
    status = item.get('status', '')
    is_assigned = item.get('isAssigned', False)
    # Если статус "FINISHED", проверяем значение isAssigned
    if status == "FINISHED":
        if is_assigned:
            return "Назначено"
        else:
            return "Завершено"
    # Статусы по маппингу
    status_map = {
        "CANCELLED": "Отменена",
        "PLANNED": "Запланирована"
    }
    result_status = status_map.get(status, status)
    # Проверяем изменение статуса и дату последнего редактирования
    change_info = item.get('examinationChangeInfo')
    last_edit = item.get('lastEditingDate')

    if change_info:
        reason = change_info.get('changingBase', {}).get('name', '')  # основание изменения
    else:
        reason = ''

    if last_edit:
        dt = datetime.fromtimestamp(last_edit / 1000)
        last_edit_str = dt.strftime('%d.%m.%Y %H:%M')
    else:
        last_edit_str = ''

    if reason or last_edit_str:
        additional_info = f". Изменено. Основание: {reason} Последнее изменение: {last_edit_str}"
        result_status += additional_info

    return result_status

def format_result(item):
    result = (item.get('examinationResult') or {}).get('desc')
    has_offence = False
    # Вложенность: examinationResult.hasOffence или просто hasOffence на верхнем уровне
    if item.get('examinationResult') and 'hasOffence' in item['examinationResult']:
        has_offence = item['examinationResult']['hasOffence']
    elif 'hasOffence' in item:
        has_offence = item['hasOffence']
    if has_offence is True:
        return "Нарушения выявлены (в том числе факты невыполнения предписаний)"
    elif has_offence is False:
        return "Нарушений не выявлено"
    return result or ""



# Сохранение данных в JSON-файл
def save_to_json(data, filename='inspections.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Данные сохранены в {filename}")

# Основной процесс с поддержкой пагинации
def main():
    print("Инициализация менеджера cookies...")
    cookie_manager = CookieManager()
    
    all_inspections = []
    page = 1
    while True:
        data = fetch_inspections(page, cookie_manager)
        if not data or not data.get('items'):  # Если данных нет, завершаем
            break
        #filtered_data = filter_all(data)
        all_inspections.extend(data)
        page += 1
        time.sleep(1)  # Пауза для избежания блокировки
    save_to_json(all_inspections)
    print(f"Обработано и сохранено {len(all_inspections)} записей")

if __name__ == "__main__":
    main() 