# headers_extractor.py — Финальная ООП-версия

from playwright.sync_api import sync_playwright
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import sys
import os

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Добавляем путь для импорта parser_v2
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser_v2 import main as run_parser_v2


class BaseExtractor(ABC):
    """
    Абстрактный базовый класс для извлечения данных с веб-сайтов.
    Реализует общую структуру: запуск браузера, навигация, перехват запросов.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.captured_data = {
            "url": None,
            "headers": None,
            "body": None
        }

    @abstractmethod
    def get_target_keywords(self) -> list:
        """Возвращает ключевые слова URL для перехвата (например, 'search', 'api')"""
        pass

    @abstractmethod
    def get_start_url(self) -> str:
        """Возвращает стартовый URL"""
        pass

    @abstractmethod
    def navigate_and_trigger(self):
        """Определяет, как навигировать и запустить нужный запрос"""
        pass

    def setup_browser(self):
        """Запускает браузер и создаёт контекст"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        self.page = self.context.new_page()
        logger.info("🌐 Браузер запущен")

    def setup_route_handler(self):
        """Настраивает перехват сетевых запросов"""
        def handle_route(route, request):
            url = request.url.lower()
            keywords = [k.lower() for k in self.get_target_keywords()]

            if any(keyword in url for keyword in keywords) and request.method == "POST":
                logger.info(f"🎯 Перехвачен целевой запрос: {request.url}")
                self.captured_data["url"] = request.url
                self.captured_data["headers"] = dict(request.headers)
                self.captured_data["body"] = request.post_data
            route.continue_()

        self.page.route("**/*", handle_route)
        logger.info("🔧 Настроен перехват запросов")

    def wait_for_api_response(self, timeout: int = 15000):
        """Ожидает ответа от API"""
        try:
            self.page.wait_for_response(
                lambda resp: (
                    any(k.lower() in resp.url.lower() for k in self.get_target_keywords())
                    and resp.status == 200
                ),
                timeout=timeout
            )
            logger.info("✅ Ответ от API получен (200 OK)")
        except Exception:
            logger.warning("⚠️ Не удалось дождаться ответа от API")

    def close(self):
        """Закрывает браузер"""
        if self.browser:
            self.browser.close()
            logger.info("🛑 Браузер закрыт")

    def run(self) -> Dict[str, Any]:
        """
        Основной метод — шаблонный алгоритм (Template Method)
        """
        try:
            self.setup_browser()
            self.setup_route_handler()

            logger.info(f"🌐 Переход на {self.get_start_url()}")
            self.page.goto(self.get_start_url(), wait_until="domcontentloaded", timeout=30000)

            self.navigate_and_trigger()

            self.wait_for_api_response()

            return self.captured_data

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return self.captured_data
        finally:
            self.close()


class GosuslugiExtractor(BaseExtractor):
    """
    Конкретная реализация для https://dom.gosuslugi.ru 
    """

    def get_target_keywords(self) -> list:
        return ["examinations/public/search"]

    def get_start_url(self) -> str:
        return "https://dom.gosuslugi.ru/#!/rp"

    def navigate_and_trigger(self):
        logger.info("⏳ Ожидание кнопки 'Найти'...")
        self.page.wait_for_selector("button:has-text('Найти')", timeout=15000)
        logger.info("🖱️ Кликаем по кнопке 'Найти'...")
        self.page.click("button:has-text('Найти')")


def main():
    print("🚀 Запуск извлечения данных с dom.gosuslugi.ru (OOП версия)\n")

    extractor = GosuslugiExtractor(headless=False)
    result = extractor.run()

    if result["headers"]:
        print("\n" + "=" * 60)
        print("✅ УСПЕШНО: ЗАГОЛОВКИ И ТЕЛО ПОЛУЧЕНЫ")
        print("=" * 60)
        print(f"🔗 URL: {result['url']}")
        print(f"📄 Тело запроса: {result['body']}")
        print("\n🔐 ЗАГОЛОВКИ:")
        important = ["user-agent", "referer", "origin", "session-guid", "state-guid", "request-guid", "cookie"]
        for key, value in result["headers"].items():
            if key.lower() in important:
                print(f"  • {key}: {value[:100]}{'...' if len(value) > 100 else ''}")
        print("=" * 60)
        print("💡 Передача данных в parser_v2.py...")
        
        # Передаём только заголовки в parser_v2
        run_parser_v2(result["headers"])
        
    else:
        print("\n" + "❌" * 40)
        print("      ОШИБКА: Не удалось перехватить запрос")
        print("      Проверь: сеть, капчу, кнопку 'Найти'")
        print("❌" * 40)


if __name__ == "__main__":
    main()