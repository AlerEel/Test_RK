from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import aiosqlite
import os

DB_NAME = 'inspections.db'
PAGE_SIZE = 10

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создаем папку templates если её нет
if not os.path.exists('templates'):
    os.makedirs('templates')

async def get_db_connection():
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = Query(1)):
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

if __name__ == '__main__':
    import uvicorn
    print("\nСайт доступен по адресу: http://localhost:5001/\n")
    uvicorn.run(app, host="0.0.0.0", port=5001)