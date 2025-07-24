from scripts.headers_extractor import GosuslugiExtractor
from scripts.inspections_parser import GosuslugiInspectionsParser, load_to_sqlite
from scripts.server import run_server
import os

if __name__ == '__main__':
    if not os.path.exists('data'):
        os.makedirs('data')
    print("\n🚀 Извлечение заголовков для API...")
    extractor = GosuslugiExtractor(headless=True)
    result = extractor.run()
    headers = result["headers"]
    if not headers:
        print("\n❌ Не удалось получить заголовки. Проверьте сайт и повторите попытку.")
        exit(1)
    print("\n✅ Заголовки получены. Запуск парсера...")
    parser = GosuslugiInspectionsParser(headers=headers)
    data = parser.run()
    if data:
        load_to_sqlite(data, db_path='data/inspections.db')
    else:
        print("Нет данных для сохранения.")
    run_server()
    