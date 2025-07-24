# parser_v2.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ

import requests
import json
import time
import uuid
import random
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

# Настройка логгирования
import logging
logger = logging.getLogger(__name__)


class BaseAPIParser(ABC):
    """
    Абстрактный базовый класс для парсинга API с пагинацией.
    Реализует общую логику: запросы, retry, обработку, сохранение.
    """

    def __init__(self, headers: Dict[str, str], max_retries: int = 5, max_pages: int = 50):
        self.headers = {k: v for k, v in headers.items() if v}  # Убираем пустые
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3

    @abstractmethod
    def get_url(self) -> str:
        """Возвращает базовый URL API (без параметров)"""
        pass

    @abstractmethod
    def get_params(self, page: int) -> dict:
        """Возвращает параметры запроса (page, itemsPerPage и т.п.)"""
        pass

    @abstractmethod
    def get_payload(self) -> dict:
        """Возвращает тело POST-запроса (JSON)"""
        pass

    @abstractmethod
    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает один элемент из ответа API"""
        pass

    def get_retryable_status_codes(self) -> List[int]:
        return [408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524]

    def fetch_page(self, page: int) -> Optional[Dict]:
        """Выполняет запрос к API с повторными попытками"""
        # Чистим URL: убираем пробелы, лишние параметры
        url = self.get_url().strip()  # 🔥 Ключевое исправление
        params = self.get_params(page)
        payload = self.get_payload()

        request_headers = self.headers.copy()
        request_headers["Request-GUID"] = str(uuid.uuid4())
        request_headers["Content-Type"] = "application/json"

        retryable = self.get_retryable_status_codes()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Попытка {attempt + 1}/{self.max_retries} для страницы {page}")
                response = requests.post(
                    url,
                    headers=request_headers,
                    params=params,
                    json=payload,
                    timeout=30
                )
                logger.info(f"POST {url} — статус: {response.status_code}")

                if response.status_code == 200:
                    return response.json()

                elif response.status_code in retryable:
                    if attempt < self.max_retries - 1:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Статус {response.status_code}. Повтор через {delay:.1f} сек...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Превышено кол-во попыток. Последний статус: {response.status_code}")
                        return None
                else:
                    logger.error(f"Неожиданный статус {response.status_code}")
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Таймаут. Повтор через {delay:.1f} сек...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Превышено кол-во попыток из-за таймаутов")
                    return None

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Ошибка: {e}. Повтор через {delay:.1f} сек...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Превышено кол-во попыток. Последняя ошибка: {e}")
                    return None

        return None

    def run(self) -> List[Dict[str, Any]]:
        logger.info("Запуск парсера...")
        all_data = []
        page = 1

        while page <= self.max_pages:
            try:
                logger.info(f"Обрабатываем страницу {page}...")
                data = self.fetch_page(page)

                if not data:
                    self.consecutive_errors += 1
                    logger.warning(f"Не удалось получить данные. Ошибки подряд: {self.consecutive_errors}")
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logger.error("Превышено макс. кол-во последовательных ошибок. Остановка.")
                        break
                    delay = min(30, 2 ** self.consecutive_errors)
                    time.sleep(delay)
                    page += 1
                    continue

                if not data.get("items"):
                    logger.info("Данные закончились.")
                    break

                self.consecutive_errors = 0
                items = data["items"]
                logger.info(f"Получено {len(items)} записей на странице {page}.")

                processed_items = []
                for item in items:
                    if not isinstance(item, dict):
                        logger.warning(f"Пропущен несловарный элемент: {item!r}")
                        continue
                    try:
                        processed = self.process_item(item)
                        processed_items.append(processed)
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке элемента: {e}")
                        continue

                all_data.extend(processed_items)
                logger.info(f"Обработано {len(processed_items)} записей.")

                if len(items) < 1000:
                    logger.info("Меньше 1000 записей — завершаем пагинацию.")
                    break

                page += 1
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Парсинг прерван пользователем.")
                break
            except Exception as e:
                self.consecutive_errors += 1
                logger.error(f"Неожиданная ошибка: {e}")
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.error("Превышено макс. кол-во ошибок. Остановка.")
                    break
                delay = min(30, 2 ** self.consecutive_errors)
                time.sleep(delay)
                page += 1
                continue

        return all_data


class GosuslugiInspectionsParser(BaseAPIParser):
    """
    Конкретная реализация для API проверок Госуслуг
    """

    def get_url(self) -> str:
        return "https://dom.gosuslugi.ru/inspection/api/rest/services/examinations/public/search "

    def get_params(self, page: int) -> dict:
        return {"page": page, "itemsPerPage": 1000}

    def get_payload(self) -> dict:
        now = datetime.now(timezone.utc)
        one_month_ago = now - relativedelta(days=31)

        exam_start_from = one_month_ago.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        exam_start_to = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        return {
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

    def format_status(self, item: Dict[str, Any]) -> str:
        status = item.get('status', '')
        is_assigned = item.get('isAssigned', False)

        if status == "FINISHED":
            return "Назначено" if is_assigned else "Завершено"

        status_map = {"CANCELLED": "Отменена", "PLANNED": "Запланирована"}
        result_status = status_map.get(status, status)

        change_info = item.get('examinationChangeInfo') or {}
        last_edit = item.get('lastEditingDate')

        reason = change_info.get('changingBase', {}).get('name', '') if change_info else ''

        if last_edit:
            try:
                dt = datetime.fromtimestamp(last_edit / 1000, tz=timezone.utc)
                last_edit_str = dt.strftime('%d.%m.%Y %H:%M')
            except:
                last_edit_str = ''
        else:
            last_edit_str = ''

        if reason or last_edit_str:
            additional_info = f". Изменено. Основание: {reason} Последнее изменение: {last_edit_str}"
            result_status += additional_info

        return result_status.strip()

    def format_result(self, item: Dict[str, Any]) -> str:
        result = (item.get('examinationResult') or {}).get('desc', '')
        has_offence = item.get('examinationResult', {}).get('hasOffence')
        if has_offence is None:
            has_offence = item.get('hasOffence')

        if has_offence is True:
            return "Нарушения выявлены (в том числе факты невыполнения предписаний)"
        elif has_offence is False:
            return "Нарушений не выявлено"
        return result

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:  # ← Вот он! Правильное имя
        subject = item.get('subject') or {}
        org_info = subject.get('organizationInfoEnriched') or {}
        registry = org_info.get('registryOrganizationCommonDetailWithNsi') or {}

        return {
            'entity_name': (registry.get('shortName') or '').strip(),
            'ogrn': (registry.get('ogrn') or '').strip(),
            'purpose': (item.get('examObjective') or '').strip(),
            'status': self.format_status(item),
            'result': self.format_result(item),
            'examStartDate': item.get('from', '')
        }


def save_to_json(data: List[Dict], filename: str = 'inspections.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные сохранены в {filename}")


def load_to_sqlite(data: List[Dict]):
    try:
        from load_to_sqlite import insert_data_from_list
        logger.info("Загружаю данные в базу данных...")
        insert_data_from_list(data)
        logger.info(f"Загружено {len(data)} записей в БД.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке в БД: {e}")


def main(headers: Dict[str, str]):
    parser = GosuslugiInspectionsParser(headers=headers)
    data = parser.run()

    if data:
        save_to_json(data)
        load_to_sqlite(data)
    else:
        logger.warning("Нет данных для сохранения.")