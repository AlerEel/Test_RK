#!/usr/bin/env python3
"""
Модуль для автоматического получения cookies с сайта Госуслуг
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os

class CookieManager:
    def __init__(self):
        self.base_url = "https://dom.gosuslugi.ru"
        self.session = requests.Session()
        self.cookies_file = "cookies.json"
        self.cookies_expiry_file = "cookies_expiry.json"
        
    def setup_chrome_options(self):
        """Настройка Chrome для работы в Docker"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        return chrome_options
    
    def get_cookies_with_selenium(self):
        """Получение cookies через Selenium"""
        print("Запуск браузера для получения cookies...")
        
        try:
            driver = webdriver.Chrome(options=self.setup_chrome_options())
            
            # Переходим на главную страницу
            driver.get(self.base_url)
            time.sleep(3)
            
            # Ждем загрузки страницы
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Переходим на страницу проверок
            inspections_url = f"{self.base_url}/#!/rp"
            driver.get(inspections_url)
            time.sleep(5)
            
            # Ждем загрузки контента
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
            except TimeoutException:
                print("Таймаут ожидания загрузки страницы, продолжаем...")
            
            # Получаем cookies
            cookies_list = driver.get_cookies()
            
            # Преобразуем список cookies в словарь
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies_list}
            
            # Формируем строку cookies
            cookie_string = "; ".join([f"{name}={value}" for name, value in cookies_dict.items()])
            
            driver.quit()
            
            return cookie_string, cookies_dict
            
        except Exception as e:
            print(f"Ошибка при получении cookies через Selenium: {e}")
            return None, None
    
    
    def save_cookies(self, cookies_dict, expiry_hours=24):
        """Сохранение cookies в файл"""
        try:
            # Проверяем, что cookies_dict это словарь
            if not isinstance(cookies_dict, dict):
                print(f"Ошибка: cookies_dict должен быть словарем, получен {type(cookies_dict)}")
                return False
            
            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            
            cookies_data = {
                'cookies': cookies_dict,
                'expiry': expiry_time.isoformat(),
                'created': datetime.now().isoformat()
            }
            
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, ensure_ascii=False, indent=2)
            
            print(f"Cookies сохранены до {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении cookies: {e}")
            return False
    
    def load_cookies(self):
        """Загрузка cookies из файла"""
        try:
            if not os.path.exists(self.cookies_file):
                return None, None
            
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # Проверяем срок действия
            expiry_time = datetime.fromisoformat(cookies_data['expiry'])
            if datetime.now() > expiry_time:
                print("Cookies устарели")
                return None, None
            
            cookies_dict = cookies_data['cookies']
            
            # Проверяем, что cookies_dict это словарь
            if not isinstance(cookies_dict, dict):
                print(f"Неверный формат cookies: {type(cookies_dict)}")
                return None, None
            
            cookie_string = "; ".join([f"{name}={value}" for name, value in cookies_dict.items()])
            
            print("Cookies загружены из файла")
            return cookie_string, cookies_dict
            
        except Exception as e:
            print(f"Ошибка при загрузке cookies: {e}")
            return None, None
    
    def get_fresh_cookies(self, force_refresh=False):
        """Получение свежих cookies"""
        if not force_refresh:
            # Пытаемся загрузить существующие cookies
            cookie_string, cookies_dict = self.load_cookies()
            if cookie_string and cookies_dict:
                return cookie_string, cookies_dict
        
        print("Получение новых cookies...")
        
        # Пытаемся получить cookies через requests (быстрее)
        cookie_string, cookies_dict = self.get_cookies_with_selenium()
        
        
        if cookie_string and cookies_dict:
            # Сохраняем новые cookies
            self.save_cookies(cookies_dict)
            return cookie_string, cookies_dict
        
        return None, None
    
    def generate_headers(self, cookie_string):
        """Генерация заголовков для запросов"""
        if not cookie_string:
            return None
        
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Referer': 'https://dom.gosuslugi.ru/',
            'Origin': 'https://dom.gosuslugi.ru',
            'Session-GUID': '48904512-7e68-446b-b37e-d5f894a3c23c',
            'State-GUID': '/rp',
            'Request-GUID': str(uuid.uuid4()),
            'Cookie': cookie_string
        }

def main():
    """Тестирование модуля"""
    manager = CookieManager()
    cookie_string, cookies_dict = manager.get_fresh_cookies()
    
    if cookie_string:
        print("Cookies получены успешно!")
        print(f"Количество cookies: {len(cookies_dict)}")
        
        # Тестируем заголовки
        headers = manager.generate_headers(cookie_string)
        if headers:
            print("Заголовки сгенерированы успешно")
    else:
        print("Не удалось получить cookies")

if __name__ == "__main__":
    main() 