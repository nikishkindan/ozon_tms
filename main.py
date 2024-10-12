# main.py

import json
import os
import time
from logger import logger
from selenium_utils import get_cookies_from_selenium
from api_client import send_post_request, get_city_ids
from data_processing import create_route, create_request_body
from storage import load_processed_ids, save_processed_ids, save_all_requests_to_json
from config import AUTHORIZATION_TOKEN

def process_requests(cookies, authorization_token, processed_ids):
    json_response = send_post_request(cookies, authorization_token)
    if not json_response:
        logger.error("Не удалось получить ответ от API. Пропуск итерации.")
        return

    new_requests = []

    for lot in json_response.get("data", {}).get("Lots", []):
        lot_id = lot.get("ID")
        if lot_id in processed_ids:
            logger.info(f"Заявка с ID {lot_id} уже обработана. Пропуск.")
            continue

        # Извлечение необходимых данных
        bet_start = lot.get("ProcedureInfo", {}).get("StartPrice")
        bet_step = lot.get("ProcedureInfo", {}).get("Step")
        transport_type = lot.get("TransportType", {})
        cargo_weight = transport_type.get("Name", "").split('т')[0]  # до первой буквы 'т'
        cargo_value = transport_type.get("Capacity", "").split('.')[0]  # до знака точки

        # Обработка WayPoints
        way_points = lot.get("Route", {}).get("WayPoints", [])
        way_points_data = []
        addresses = []

        for wp in way_points:
            arrival_at = wp.get("ArrivalAt", "")
            date = arrival_at.split("T")[0] if arrival_at else ""
            time_str = arrival_at.split("T")[1].split("Z")[0] if arrival_at else ""
            address = wp.get("Point", {}).get("Address", "")
            addresses.append(address)

        # Получаем city_id для всех уникальных адресов
        city_info_mapping = get_city_ids(addresses)

        for wp in way_points:
            address = wp.get("Point", {}).get("Address", "")
            city_id = city_info_mapping.get(address, {}).get("city_id", "Не указано")

            way_points_data.append({
                "Date": date,
                "Time": time_str,
                "Address": address,
                "CityId": city_id
            })

        # Создаем маршрут
        route = create_route(way_points_data, cargo_weight, cargo_value)

        # Извлекаем way_points, исключая первый и последний элементы
        way_points_list = way_points_data[1:-1]  # Все точки, кроме первой и последней

        # Создаем тело запроса
        request_body = create_request_body(lot_id, bet_start, bet_step, route, way_points_list)

        # Добавляем request_body в список новых заявок
        new_requests.append(request_body)

        # Добавляем lot_id в processed_ids
        processed_ids.add(lot_id)
        logger.info(f"Заявка с ID {lot_id} обработана и добавлена в processed_ids.")

    # Сохраняем все новые заявки
    if new_requests:
        save_all_requests_to_json(new_requests)
        save_processed_ids(processed_ids)
    else:
        logger.info("Нет новых заявок для обработки.")

    # Выводим структуру новых заявок для проверки
    if new_requests:
        print(json.dumps(new_requests, ensure_ascii=False, indent=4))

def main():
    try:
        while True:
            logger.info("Запуск обработки заявок.")
            # Проверяем наличие куки
            if os.path.exists("cookies.json"):
                with open("cookies.json", "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                logger.info("Куки загружены из файла.")
            else:
                cookies = get_cookies_from_selenium()

            # Укажите ваш токен авторизации
            authorization_token = AUTHORIZATION_TOKEN  # Замените на ваш токен или получите из config

            # Загружаем обработанные ID
            processed_ids = load_processed_ids()

            # Отправляем запрос и обрабатываем заявки
            process_requests(cookies, authorization_token, processed_ids)

            logger.info("Завершена обработка заявок. Ожидание 60 секунд.")
            time.sleep(60)  # Ждем 60 секунд перед следующим запуском
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
