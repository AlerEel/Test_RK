import requests
import json
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, timezone
import time
import uuid
import random

"""
Парсер для получения данных о проверках с API Госуслуг
Автоматически запрашивает данные за последний месяц (30 дней)
Использует реальные заголовки, полученные через parser.py (real_headers.json)
"""

def fetch_inspections_with_retry(headers, page=1, max_retries=5):
    """
    Выполняет HTTP-запрос с повторными попытками при ошибках 504 и других временных ошибках
    """
    now = datetime.now()
    one_month_ago = now - relativedelta(days=31)

    # Создаем datetime объекты в UTC с правильным временем
    # API ожидает даты в формате YYYY-MM-DDTHH:MM:SS.sssZ
    exam_start_from = datetime(
        one_month_ago.year, one_month_ago.month, one_month_ago.day, 21, 0, 0, 0,
        tzinfo=timezone.utc
    ).strftime('%Y-%m-%dT%H:%M:%S.000Z')

    exam_start_to = datetime(
        now.year, now.month, now.day, 21, 0, 0, 0,
        tzinfo=timezone.utc
    ).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
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

    # Обновляем Request-GUID для каждого запроса
    headers = headers.copy()
    headers["Request-GUID"] = str(uuid.uuid4())

    # Список кодов ошибок, для которых стоит повторить попытку
    retryable_status_codes = [408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524]
    
    for attempt in range(max_retries):
        try:
            print(f"[INFO] Попытка {attempt + 1}/{max_retries} для страницы {page}")
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
            print(f"[INFO] POST {url} — статус: {response.status_code}")
            
            # Если успешный ответ
            if response.status_code == 200:
                return response.json()
            
            # Если ошибка, которую стоит повторить
            elif response.status_code in retryable_status_codes:
                if attempt < max_retries - 1:  # Если это не последняя попытка
                    # Экспоненциальная задержка с джиттером
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[WARNING] Получен статус {response.status_code}. Повторная попытка через {delay:.1f} секунд...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"[ERROR] Превышено максимальное количество попыток для страницы {page}. Последний статус: {response.status_code}")
                    return None
            
            # Если другая ошибка, не повторяем
            else:
                print(f"[ERROR] Получен неожиданный статус {response.status_code} для страницы {page}")
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"[WARNING] Таймаут запроса. Повторная попытка через {delay:.1f} секунд...")
                time.sleep(delay)
                continue
            else:
                print(f"[ERROR] Превышено максимальное количество попыток из-за таймаутов для страницы {page}")
                return None
                
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"[WARNING] Ошибка запроса: {e}. Повторная попытка через {delay:.1f} секунд...")
                time.sleep(delay)
                continue
            else:
                print(f"[ERROR] Превышено максимальное количество попыток для страницы {page}. Последняя ошибка: {e}")
                return None
    
    return None

def fetch_inspections(headers, page=1):
    """
    Обертка для обратной совместимости
    """
    return fetch_inspections_with_retry(headers, page)

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
        'entity_name': registry_info.get('shortName', ''),
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
def main(headers):
    print("[INFO] Запуск парсера Госуслуг...")
    all_inspections = []
    page = 1
    max_pages = 50  # Ограничиваем максимальное количество страниц для безопасности
    consecutive_errors = 0  # Счетчик последовательных ошибок
    max_consecutive_errors = 3  # Максимальное количество последовательных ошибок
    
    while page <= max_pages:
        try:
            print(f"[INFO] Обрабатываем страницу {page}...")
            data = fetch_inspections(headers, page)
            
            if not data:
                consecutive_errors += 1
                print(f"[WARNING] Не удалось получить данные для страницы {page}. Ошибка {consecutive_errors}/{max_consecutive_errors}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"[ERROR] Превышено максимальное количество последовательных ошибок ({max_consecutive_errors}). Останавливаем парсинг.")
                    break
                
                # Увеличиваем задержку при ошибках
                delay = min(30, 2 ** consecutive_errors)
                print(f"[INFO] Ждем {delay} секунд перед следующей попыткой...")
                time.sleep(delay)
                page += 1
                continue
            
            if not data.get('items'):
                print(f"[INFO] Данные закончились на странице {page}.")
                break
            
            # Сбрасываем счетчик ошибок при успешном получении данных
            consecutive_errors = 0
            
            print(f"[INFO] Получено {len(data['items'])} записей на странице {page}.")
            processed_items = []
            
            for item in data['items']:
                try:
                    processed_item = process_inspection_item(item)
                    processed_items.append(processed_item)
                except Exception as e:
                    print(f"[WARNING] Ошибка при обработке элемента на странице {page}: {e}")
                    continue  # Продолжаем обработку других элементов
            
            all_inspections.extend(processed_items)
            print(f"[INFO] Обработано {len(processed_items)} записей на странице {page}.")
            
            # Проверяем, есть ли еще данные
            if len(data['items']) < 1000:
                print(f"[INFO] Получено меньше 1000 записей на странице {page}. Завершаем парсинг.")
                break
            
            page += 1
            # Небольшая задержка между страницами
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"[INFO] Парсинг прерван пользователем на странице {page}.")
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"[ERROR] Неожиданная ошибка на странице {page}: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                print(f"[ERROR] Превышено максимальное количество последовательных ошибок ({max_consecutive_errors}). Останавливаем парсинг.")
                break
            
            # Увеличиваем задержку при ошибках
            delay = min(30, 2 ** consecutive_errors)
            print(f"[INFO] Ждем {delay} секунд перед следующей попыткой...")
            time.sleep(delay)
            page += 1
            continue
    
    # Загружаем данные напрямую в БД
    if all_inspections:
        try:
            from load_to_sqlite import insert_data_from_list
            print("[INFO] Загружаю данные в базу данных...")
            insert_data_from_list(all_inspections)
            print(f"[INFO] Обработано и загружено {len(all_inspections)} записей в базу данных.")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке данных в базу: {e}")
    else:
        print("[WARNING] Не удалось получить данные для загрузки в базу.")

if __name__ == "__main__":
    import sys
    if '--show-sample' in sys.argv:
        print("[ERROR] Просмотр примера больше не поддерживается (нет JSON-файла)")
    else:
        print("[INFO] Этот скрипт теперь должен вызываться из parser.py с передачей заголовков!") 