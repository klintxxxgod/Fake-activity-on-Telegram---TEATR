import os
import sys
import webbrowser
import threading
from server import app
import time
from pathlib import Path

def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_browser():
    """Открывает браузер с главной страницей приложения"""
    # Даем серверу время на запуск
    time.sleep(2)
    webbrowser.open('http://localhost:8000')

def start_app():
    """Основная функция запуска приложения"""
    try:
        # Устанавливаем рабочую директорию
        if getattr(sys, 'frozen', False):
            os.chdir(sys._MEIPASS)
        
        # Создаем необходимые директории, если их нет
        base_dir = os.path.expanduser("~/Desktop/Коды/Teatr")
        accounts_dir = os.path.join(base_dir, "accounts")
        scripts_dir = os.path.join(base_dir, "scripts")
        
        Path(accounts_dir).mkdir(parents=True, exist_ok=True)
        Path(scripts_dir).mkdir(parents=True, exist_ok=True)

        # Запускаем браузер в отдельном потоке
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Запускаем Flask-сервер
        app.run(port=8000, threaded=True)

    except Exception as e:
        import traceback
        with open("error_log.txt", "w") as f:
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    start_app() 