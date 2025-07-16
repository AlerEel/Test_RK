import requests
import json
from datetime import datetime, timedelta
import time
import uuid

"""
Парсер для получения данных о проверках с API Госуслуг
Автоматически запрашивает данные за последний месяц (30 дней)
Использует реальные заголовки, полученные через parser.py (real_headers.json)
"""

def fetch_inspections(page=1):
    # Рассчитываем даты за последний месяц
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    
    # Форматируем даты в ISO 8601 формат с UTC
    exam_start_from = one_month_ago.strftime('%Y-%m-%dT21:00:00.000Z')
    exam_start_to = now.strftime('%Y-%m-%dT21:00:00.000Z')
    
    print(f"[INFO] Страница {page}: запрашиваем данные с {exam_start_from} по {exam_start_to}")
    
    url = "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search"

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

    try:
        with open("real_headers.json", encoding="utf-8") as f:
            real_headers = json.load(f)
        # Обновляем Request-GUID для каждого запроса
        real_headers["Request-GUID"] = str(uuid.uuid4())
        print(f"[INFO] Заголовки успешно загружены из real_headers.json")
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить real_headers.json: {e}")
        return None

    try:
        response = requests.post(url, headers=real_headers, params=params, json=payload)
        print(f"[INFO] POST {url} — статус: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Ошибка при выполнении запроса: {e}")
        return None

def format_status(item):
    status = item.get('status', '')
    is_assigned = item.get('isAssigned', False)
    if status == "FINISHED":
        if is_assigned:
            return "Назначено"
        else:
            return "Завершено"
    status_map = {
        "CANCELLED": "Отменена",
        "PLANNED": "Запланирована"
    }
    result_status = status_map.get(status, status)
    change_info = item.get('examinationChangeInfo')
    last_edit = item.get('lastEditingDate')
    if change_info:
        reason = change_info.get('changingBase', {}).get('name', '')
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
    if item.get('examinationResult') and 'hasOffence' in item['examinationResult']:
        has_offence = item['examinationResult']['hasOffence']
    elif 'hasOffence' in item:
        has_offence = item['hasOffence']
    if has_offence is True:
        return "Нарушения выявлены (в том числе факты невыполнения предписаний)"
    elif has_offence is False:
        return "Нарушений не выявлено"
    return result or ""

def process_inspection_item(item):
    """Обработка одного элемента проверки"""
    # Извлекаем данные из вложенной структуры с проверками на None
    subject = item.get('subject', {})
    organization_info = subject.get('organizationInfoEnriched', {}) if subject else {}
    registry_info = organization_info.get('registryOrganizationCommonDetailWithNsi', {}) if organization_info else {}
    
    return {
        'entity_name': registry_info.get('fullName', ''),
        'ogrn': registry_info.get('ogrn', ''),
        'purpose': item.get('examObjective', ''),
        'status': format_status(item),
        'result': format_result(item),
        'examStartDate': item.get('from', '')
    }

# Сохранение данных в JSON-файл
def save_to_json(data, filename='inspections.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Данные сохранены в {filename}")

# Основной процесс с поддержкой пагинации
def main():
    print("[INFO] Запуск парсера Госуслуг...")
    all_inspections = []
    page = 1
    while True:
        data = fetch_inspections(page)
        if not data or not data.get('items'):
            print(f"[INFO] Данные закончились или не получены на странице {page}.")
            break
        print(f"[INFO] Получено {len(data['items'])} записей на странице {page}.")
        
        # Обрабатываем каждый элемент
        processed_items = []
        for item in data['items']:
            processed_item = process_inspection_item(item)
            processed_items.append(processed_item)
        
        all_inspections.extend(processed_items)
        print(f"[INFO] Обработано {len(processed_items)} записей на странице {page}.")
        page += 1
        time.sleep(1)
    save_to_json(all_inspections)
    print(f"[INFO] Обработано и сохранено {len(all_inspections)} записей в inspections.json")

if __name__ == "__main__":
    main() 