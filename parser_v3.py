import requests
import json
from datetime import datetime, timedelta
import time
import uuid

# Функция для получения данных с реестра
def fetch_inspections(page=1):
    url = "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Referer': 'https://dom.gosuslugi.ru/',
        'Origin': 'https://dom.gosuslugi.ru',
        'Session-GUID': '48904512-7e68-446b-b37e-d5f894a3c23c',  # <-- вставьте актуальный из браузера
        'State-GUID': '/rp',      # <-- вставьте актуальный из браузера
        'Request-GUID': str(uuid.uuid4()),   # генерируется автоматически
        'Cookie': 'JSESSIONID="pqzqZ6AtZ6QNFdf3fYa_nZeLe2m1DuB8SLqX9Htv.ppak-app-wf-ui-srv04:rest"; userSelectedLanguage=ru; nau=e443c74d-8315-d6d1-4679-3d01696a1f0f; _ym_uid=1747825891223188734; _ym_d=1747825891; _idp_authn_id=email%3Adom.gosuslugi.ru@roskvartal.ru; _ym_isad=2; suimSessionGuid=48904512-7e68-446b-b37e-d5f894a3c23c; route_rest=c534c9649dd9079a562a354c7548548d; route_pafo-reports=6b1d75b53760d2e77f53d6f8401f3118; route_suim=fd7af85ab1486fdca90b4bd5fc38e102'             # <-- скопируйте все cookies одной строкой из браузера
    }
    params = {
        'page': page,
        'itemsPerPage': 1000
    }
    payload = {
        "numberOrUriNumber": None,
        "typeList": [],
        "examStartFrom": "2025-06-11T21:00:00.000Z",
        "examStartTo": "2025-07-11T21:00:00.000Z",
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
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None

'''def format_status(item):
    status_map = {
        "FINISHED": "Завершена",
        "CANCELLED": "Отменена",
        "PLANNED": "Запланирована"
    }
    status = status_map.get(item.get('status', ''), item.get('status', ''))
    change_info = item.get('examinationChangeInfo')
    last_edit = item.get('lastEditingDate')
    if change_info:
        reason = change_info.get('desc', '')
        if last_edit:
            from datetime import datetime
            dt = datetime.fromtimestamp(last_edit / 1000)
            last_edit_str = dt.strftime('%d.%m.%Y %H:%M')
        else:
            last_edit_str = ''
        return f"{status}. Изменено. Основание: {reason} Последнее изменение {last_edit_str}"
    return status'''

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

# Фильтрация данных за последний месяц
def filter_last_month(data):
    one_month_ago = datetime.now() - timedelta(days=30)
    filtered = []
    for item in data.get('items', []):
        try:
            inspection_date = datetime.strptime(item.get('date', ''), '%d.%m.%Y %H:%M')
            if one_month_ago <= inspection_date <= datetime.now():
                subject = item.get('subject', {})
                org_info_enriched = subject.get('organizationInfoEnriched')
                if org_info_enriched and org_info_enriched.get('registryOrganizationCommonDetailWithNsi'):
                    org_info = org_info_enriched['registryOrganizationCommonDetailWithNsi']
                else:
                    org_info = {}
                filtered.append({
                    'entity_name': org_info.get('fullName', ''),
                    'ogrn': org_info.get('ogrn', ''),
                    'purpose': item.get('examObjective', ''),
                    'status': format_status(item),
                    'result': format_result(item),
                    'inspection_date': item.get('date', '')
                })
        except (ValueError, KeyError) as e:
            print(f"Ошибка обработки записи: {e}, запись пропущена")
            continue
    return filtered

# Сохранение данных в JSON-файл
def save_to_json(data, filename='inspections.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Данные сохранены в {filename}")

# Основной процесс с поддержкой пагинации
def main():
    all_inspections = []
    page = 1
    while True:
        data = fetch_inspections(page)
        if not data or not data.get('items'):  # Если данных нет, завершаем
            break
        filtered_data = filter_last_month(data)
        all_inspections.extend(filtered_data)
        page += 1
        #time.sleep(1)  # Пауза для избежания блокировки
    save_to_json(all_inspections)
    print(f"Обработано и сохранено {len(all_inspections)} записей")

if __name__ == "__main__":
    main()