from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination, get_page_args
import os

app = Flask(__name__)

# Конфигурация базы данных с поддержкой переменных окружения
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/Test_RK')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Inspections(db.Model):
    __tablename__ = 'inspections'  # Указываем нужное имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    entity_name = db.Column(db.String(255))
    ogrn = db.Column(db.String(13))
    purpose = db.Column(db.Text)
    status = db.Column(db.String(100))
    result = db.Column(db.Text)

@app.route('/')
def index():
    # Получаем текущую страницу
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10  # Количество элементов на странице

    # Получаем данные из БД
    total = Inspections.query.count()
    inspections = Inspections.query.offset(offset).limit(per_page).all()

    # Создаем объект пагинации
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template('index.html', checks=inspections, pagination=pagination)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)