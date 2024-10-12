# main.py

import requests
import json  # Импортируем модуль json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import logging
import time  # Импортируем модуль time для реализации задержки

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROCESSED_IDS_FILE = "processed_ids.json"  # Файл для хранения обработанных ID

def load_processed_ids():
    """Загружает список обработанных ID из файла."""
    if os.path.exists(PROCESSED_IDS_FILE):
        with open(PROCESSED_IDS_FILE, "r", encoding="utf-8") as f:
            try:
                processed_ids = set(json.load(f))
                logging.info(f"Загружено {len(processed_ids)} обработанных ID.")
                return processed_ids
            except json.JSONDecodeError:
                logging.error("Файл processed_ids.json поврежден. Создается новый файл.")
                return set()
    else:
        logging.info("Файл processed_ids.json не найден. Создается новый файл.")
        return set()

def save_processed_ids(processed_ids):
    """Сохраняет список обработанных ID в файл."""
    with open(PROCESSED_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=4)
    logging.info(f"Сохранено {len(processed_ids)} обработанных ID.")

def get_cookies_from_selenium():
    # Настройки для Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Укажите путь к вашему драйверу
    service = Service(executable_path='path/to/chromedriver')  # Укажите путь к ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Открываем страницу авторизации
    driver.get("https://tms.ozon.ru/ozi-orders")  # URL страницы авторизации

    # Ожидаем, пока пользователь введет логин и пароль и нажмет кнопку входа
    try:
        # Ожидаем, пока загрузится элемент, который появляется после успешной авторизации
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//selector_after_login")))  # Замените на правильный селектор

        # Получаем куки
        cookies = driver.get_cookies()
        
        # Преобразуем куки в формат, подходящий для requests
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        
        # Сохраняем куки в файл
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookie_dict, f, ensure_ascii=False, indent=4)

    finally:
        driver.quit()  # Закрываем веб-драйвер

    return cookie_dict

def get_city_ids(addresses, authorization_token):
    url = "https://api.ati.su/v1.0/dictionaries/locations/parse"
    headers = {
        "Authorization": f"Bearer {authorization_token}",
        "Content-Type": "application/json"
    }
    
    # Удаляем дубликаты, используя множество
    unique_addresses = list(set(addresses))  # Преобразуем множество обратно в список
    logging.info(f"Запрос к API с уникальными адресами: {json.dumps(unique_addresses, ensure_ascii=False)}")

    try:
        response = requests.post(url, headers=headers, json=unique_addresses, timeout=15)
        logging.debug(f"Ответ от API: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Ответ от API: {json.dumps(data, ensure_ascii=False, indent=4)}")

            city_info_mapping = {}
            for address in unique_addresses:
                address_info = data.get(address, {})
                if address_info.get('is_success'):
                    city_id = address_info.get('city_id', "Не указано")
                    street = address_info.get('street') if address_info.get('street') else None
                    city_info_mapping[address] = {
                        "city_id": city_id,
                        "street": street
                    }
                else:
                    city_info_mapping[address] = {
                        "city_id": "Не указано",
                        "street": None
                    }
            logging.debug(f"Сопоставление city_id и street: {json.dumps(city_info_mapping, ensure_ascii=False, indent=4)}")
            return city_info_mapping
        else:
            logging.error(f"Ошибка при запросе к ATI API: {response.status_code} - {response.text}")
            return {address: {"city_id": "Не указано", "street": None} for address in unique_addresses}
    except requests.RequestException as e:
        logging.error(f"Исключение при запросе к ATI API: {e}")
        return {address: {"city_id": "Не указано", "street": None} for address in unique_addresses}

def send_post_request(cookies, authorization_token, processed_ids):
    url = "https://tms.ozon.ru/graphql-decorator.lpp/gql"
    headers = {
        "Content-Type": "application/json",  # Убедитесь, что это правильный заголовок для вашего API
    }

    # Тело запроса
    payload = {
        "operationName": "BiddingsList",
        "variables": {
            "filter": {
                "Limit": 40,
                "OnlyCurrentContractBids": False,
                "Status": ["InBidding"],
                "TransportTypesIDs": [],
                "ProceduresIDs": [],
                "Directions": [],
                "RoutesFilter": {
                    "StartClusters": [],
                    "StartPointIDs": [],
                    "EndClusters": [],
                    "EndPointIDs": [],
                    "ReturnClusters": [],
                    "ReturnPointIDs": []
                },
                "WayType": "Direct"
            }
        },
        "query": """query BiddingsList($filter: LotsInput!) {
            Lots(filter: $filter) {
                Auction {
                    Countdown
                    __typename
                }
                Status
                Currency
                ID
                BiddingDurationSeconds
                Procedure {
                    Name
                    __typename
                }
                ProcedureInfo {
                    ...ProcedureInfo
                    __typename
                }
                TransportType {
                    Capacity
                    ID
                    Name
                    __typename
                }
                Temperature {
                    ID
                    Name
                    __typename
                }
                Version
                Route {
                    ReturnPointID
                    WayPoints {
                        ArrivalAt
                        Point {
                            ID
                            Name
                            Address
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                __typename
            }
        }

        fragment ProcedureInfo on ProcedureInfo {
            ... on BiddingWithLimit {
                __typename
                Rank
                BiddingStarted
                StartPrice
                ContractorLastBid {
                    Price
                    __typename
                }
            }
            ... on DownBiddingWithStartPrice {
                __typename
                StartPrice
                Step
                LastBid {
                    Price
                    FromCurrentContractor
                    __typename
                }
            }
            __typename
        }"""
    }

    response = requests.post(url, cookies=cookies, headers=headers, json=payload)
    
    # Обработка ответа
    if response.status_code == 200:
        json_response = response.json()  # Сохранение ответа в формате JSON
        logging.info("Успешный запрос.")
        # Обработка каждой заявки
        new_requests = []  # Список для хранения новых request_body

        for lot in json_response.get("data", {}).get("Lots", []):
            lot_id = lot.get("ID")
            if lot_id in processed_ids:
                logging.info(f"Заявка с ID {lot_id} уже обработана. Пропуск.")
                continue  # Пропускаем уже обработанные заявки

            # Извлечение необходимых данных
            bet_start = lot.get("ProcedureInfo", {}).get("StartPrice")
            bet_step = lot.get("ProcedureInfo", {}).get("Step")
            cargo_weight = lot.get("TransportType", {}).get("Name", "").split('т')[0]  # до первой буквы 'т'
            cargo_value = lot.get("TransportType", {}).get("Capacity", "").split('.')[0]  # до знака точки
            
            # Обработка WayPoints
            way_points = lot.get("Route", {}).get("WayPoints", [])
            way_points_data = []  # Массив для хранения данных WayPoints
            addresses = []  # Список для хранения адресов

            for wp in way_points:
                arrival_at = wp.get("ArrivalAt", "")
                date = arrival_at.split("T")[0] if arrival_at else ""
                time_str = arrival_at.split("T")[1].split("Z")[0] if arrival_at else ""
                address = wp.get("Point", {}).get("Address", "")
                
                addresses.append(address)  # Добавляем адрес в список

            # Получаем city_id для всех уникальных адресов
            city_info_mapping = get_city_ids(addresses, authorization_token)

            for wp in way_points:
                address = wp.get("Point", {}).get("Address", "")
                city_id = city_info_mapping.get(address, {}).get("city_id", "Не указано")

                way_points_data.append({
                    "Date": date,
                    "Time": time_str,
                    "Address": address,
                    "CityId": city_id  # Добавляем CityId
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
            logging.info(f"Заявка с ID {lot_id} обработана и добавлена в processed_ids.")

        # Сохраняем все новые заявки в один файл (можно изменить логику сохранения по необходимости)
        if new_requests:
            save_all_requests_to_json(new_requests)
            save_processed_ids(processed_ids)
        else:
            logging.info("Нет новых заявок для обработки.")

        # Выводим структуру новых заявок для проверки
        if new_requests:
            print(json.dumps(new_requests, ensure_ascii=False, indent=4))
    else:
        logging.error(f"Ошибка запроса: {response.status_code} - {response.text}")  # Вывод текста ошибки

def create_route(way_points_data, cargo_weight, cargo_value):
    if not way_points_data:
        return {}

    # Загрузка - первый элемент
    loading_wp = way_points_data[0]
    unloading_wp = way_points_data[-1]

    route = {
        "loading": {
            "type": "loading",
            "city_id": loading_wp["CityId"],
            "location": {
                "type": "manual",
                "city_id": loading_wp["CityId"],
                "address": loading_wp["Address"]
            },
            "dates": {
                "type": "ready",
                "time": {
                    "type": "bounded",
                    "start": loading_wp["Time"]
                },
                "first_date": loading_wp["Date"]
            },
            "cargos": [
                {
                    "id": 1,
                    "name": "Любой закрытый",
                    "weight": {
                        "type": "tons",
                        "quantity": cargo_weight  # Здесь теперь передается значение CargoWeight
                    },
                    "volume": {
                        "quantity": cargo_value  # Здесь теперь передается значение CargoValue
                    }
                }
            ]
        },
        "unloading": {
            "type": "unloading",
            "city_id": unloading_wp["CityId"],
            "location": {
                "type": "manual",
                "city_id": unloading_wp["CityId"],
                "address": unloading_wp["Address"]
            },
            "dates": {
                "type": "ready",
                "time": {
                    "type": "bounded",
                    "start": unloading_wp["Time"]
                },
                "first_date": unloading_wp["Date"]
            }
        },
        "is_round_trip": False
    }

    return route

def create_request_body(lot_id, bet_start, bet_step, route, way_points):
    # Промежуточные точки
    intermediate_way_points = []
    
    for wp in way_points:
        intermediate_wp = {
            "type": "intermediate",  # Пока непонятно, что тут писать
            "city_id": wp["CityId"],  # Используем CityId
            "location": {
                "type": "manual",
                "city_id": wp["CityId"],
                "address": wp["Address"]  # Адрес точки
            },
            "dates": {
                "type": "ready",
                "time": {
                    "type": "bounded",
                    "start": wp["Time"]  # Время прибытия
                },
                "first_date": wp["Date"]  # Дата прибытия
            }
        }
        intermediate_way_points.append(intermediate_wp)

    request_body = {
        "cargo_application": {
            "external_id": lot_id,  # ID по каждой заявке
            "route": route,
            "way_points": intermediate_way_points,  # Добавляем промежуточные way_points
            "payment": {
                "cash": bet_start,  # Указываем bet_start
                "type": "without-bargaining",
                "currency_type": 1,
                "hide_counter_offers": True,
                "direct_offer": False,
                "prepayment": {
                    "percent": 50,
                    "using_fuel": True
                },
                "payment_mode": {
                    "type": "delayed-payment",
                    "payment_delay_days": 7
                },
                "accept_bids_with_vat": True,
                "accept_bids_without_vat": False,
                "vat_percents": 20,
                "start_rate": bet_start,  # Указываем bet_start
                "auction_currency_type": 1,
                "bid_step": bet_step,  # Указываем bet_step
                "auction_duration": {
                    "fixed_duration": "1h",
                },
                "accept_counter_offers": True,
                "auto_renew": {
                    "enabled": True,
                    "renew_interval": 24
                },
                "is_antisniper": False,
                "rate_rise": {
                    "interval": 1,
                    "rise_amount": 5
                },
                "winner_criteria": "best-rate",
                "time_to_provide_documents": {
                    "hours": 48
                },
                "winner_reselection_count": 2,
                "auction_restart": {
                    "enabled": True,
                    "restart_interval": 24
                },
                "no_winner_end_options": {
                    "type": "archive"
                },
                "rates": {
                    "cash": bet_start,  # Указываем bet_start
                    "rate_with_nds": bet_start,  # Указываем bet_start
                    "rate_without_nds": bet_start  # Указываем bet_start
                }
            },
            "boards": [
                {
                    "id": os.getenv('BOARD_ID', 'Не указано'),  # Получаем BOARD_ID из переменных окружения
                    "publication_mode": "now",
                    "cancel_publish_on_auction_bet": False,
                    "reservation_enabled": True
                }
            ],
            "note": lot_id  # Указываем ID заявки
        }
    }

    return request_body


def save_request_body_to_json(request_body, lot_id):
    # Указываем имя файла, например, с использованием ID заявки
    filename = f"request_body_{lot_id}.json"
    
    # Сохраняем request_body в JSON файл
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(request_body, f, ensure_ascii=False, indent=4)
    
    print(f"Запрос сохранен в файл: {filename}")

def save_all_requests_to_json(all_requests):
    # Указываем имя файла для сохранения всех заявок
    filename = "all_requests.json"
    
    # Сохраняем все заявки в JSON файл
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_requests, f, ensure_ascii=False, indent=4)
    
    print(f"Все заявки сохранены в файл: {filename}")

def process_requests():
    # Проверяем наличие куки
    if os.path.exists("cookies.json"):
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
    else:
        cookies = get_cookies_from_selenium()

    # Укажите ваш токен авторизации
    authorization_token = "5462e7f8f17441ee8f8beac2626493d0"  # Замените на ваш токен

    # Загружаем обработанные ID
    processed_ids = load_processed_ids()

    # Отправляем запрос и обрабатываем заявки
    send_post_request(cookies, authorization_token, processed_ids)

def main():
    try:
        while True:
            logging.info("Запуск обработки заявок.")
            process_requests()
            logging.info("Завершена обработка заявок. Ожидание 60 секунд.")
            time.sleep(60)  # Ждем 60 секунд перед следующим запуском
    except KeyboardInterrupt:
        logging.info("Программа остановлена пользователем.")

# Основная логика
if __name__ == "__main__":
    main()
