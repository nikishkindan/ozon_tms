# selenium_utils.py

import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROMEDRIVER_PATH, AUTH_URL, COOKIES_FILE
from logger import logger

def get_cookies_from_selenium():
    # Настройки для Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Инициализация веб-драйвера
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Открываем страницу авторизации
    driver.get(AUTH_URL)

    # Ожидаем, пока пользователь введет логин и пароль и нажмет кнопку входа
    try:
        # Ожидание элемента после успешной авторизации
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//selector_after_login"))  # Замените на правильный селектор
        )

        # Получаем куки
        cookies = driver.get_cookies()

        # Преобразуем куки в формат, подходящий для requests
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

        # Сохраняем куки в файл
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookie_dict, f, ensure_ascii=False, indent=4)

        logger.info("Куки успешно получены и сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при получении куки: {e}")
    finally:
        driver.quit()  # Закрываем веб-драйвер

    return cookie_dict
