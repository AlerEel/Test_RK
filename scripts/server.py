# server.py — FastAPI сервер, совместимый с асинхронным окружением

from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiosqlite
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.headers_extractor import GosuslugiExtractor
from scripts.inspections_parser import GosuslugiInspectionsParser, load_to_sqlite
import threading

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Константы
DB_NAME = 'data/inspections.db'
PAGE_SIZE = 10

# Создание приложения
app = FastAPI()

# Раздача статики
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

# Создаем папку templates, если её нет
if not os.path.exists('templates'):
    os.makedirs('templates')

async def get_db_connection():
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = Query(1, ge=1)):
    offset = (page - 1) * PAGE_SIZE
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    await cursor.execute('SELECT COUNT(*) FROM inspections')
    total_row = await cursor.fetchone()
    total = total_row[0]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    
    await cursor.execute('SELECT * FROM inspections ORDER BY id LIMIT ? OFFSET ?', (PAGE_SIZE, offset))
    rows = await cursor.fetchall()
    
    await conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "rows": rows,
        "page": page,
        "total_pages": total_pages
    })

LAST_UPDATE_FILE = 'data/last_update.txt'

def update_data_job():
    try:
        logger.info('[SCHEDULER] Запуск автоматического обновления данных...')
        extractor = GosuslugiExtractor(headless=True)
        result = extractor.run()
        headers = result["headers"]
        if not headers:
            logger.warning('[SCHEDULER] Не удалось получить заголовки для обновления данных.')
            return
        parser = GosuslugiInspectionsParser(headers=headers)
        data = parser.run()
        if data:
            load_to_sqlite(data, db_path=DB_NAME)
            logger.info(f'[SCHEDULER] Данные успешно обновлены.')
            # Сохраняем время последнего обновления
            from datetime import datetime
            with open(LAST_UPDATE_FILE, 'w', encoding='utf-8') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            logger.warning('[SCHEDULER] Нет новых данных для обновления.')
    except Exception as e:
        logger.error(f'[SCHEDULER] Ошибка при обновлении данных: {e}')

@app.get('/last-update', response_class=JSONResponse)
async def last_update():
    import os
    if os.path.exists(LAST_UPDATE_FILE):
        with open(LAST_UPDATE_FILE, 'r', encoding='utf-8') as f:
            ts = f.read().strip()
        return {"last_update": ts}
    else:
        return {"last_update": None, "message": "Данные ещё не обновлялись."}

# Запуск планировщика при старте сервера
scheduler = BackgroundScheduler()
scheduler.add_job(update_data_job, 'interval', minutes=10, next_run_time=None)
scheduler.start()

def run_server():
    """
    Запускает сервер даже внутри уже запущенного event loop.
    Использует nest-asyncio для совместимости.
    """
    import uvicorn
    import nest_asyncio
    import asyncio

    print("\nСервер запущен на http://localhost:5001\n")
    # Применяем патч, чтобы разрешить вложенные event loops
    nest_asyncio.apply()

    # Создаём конфиг и сервер
    config = uvicorn.Config(app, host="0.0.0.0", port=5001, lifespan="off")
    server = uvicorn.Server(config)

    # Запускаем сервер
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(server.serve())
    finally:
        scheduler.shutdown()
    

# Для запуска из терминала
if __name__ == "__main__":
    logger.info("Запуск сервера на http://0.0.0.0:5001")
    run_server()