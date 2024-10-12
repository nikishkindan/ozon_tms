# storage.py

import os
import json
from config import PROCESSED_IDS_FILE, ALL_REQUESTS_FILE
from logger import logger

def load_processed_ids():
    """Загружает список обработанных ID из файла."""
    if os.path.exists(PROCESSED_IDS_FILE):
        with open(PROCESSED_IDS_FILE, "r", encoding="utf-8") as f:
            try:
                processed_ids = set(json.load(f))
                logger.info(f"Загружено {len(processed_ids)} обработанных ID.")
                return processed_ids
            except json.JSONDecodeError:
                logger.error("Файл processed_ids.json поврежден. Создается новый файл.")
                return set()
    else:
        logger.info("Файл processed_ids.json не найден. Создается новый файл.")
        return set()

def save_processed_ids(processed_ids):
    """Сохраняет список обработанных ID в файл."""
    with open(PROCESSED_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=4)
    logger.info(f"Сохранено {len(processed_ids)} обработанных ID.")

def save_all_requests_to_json(all_requests):
    """Сохраняет все заявки в JSON файл."""
    with open(ALL_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_requests, f, ensure_ascii=False, indent=4)
    logger.info(f"Все заявки сохранены в файл: {ALL_REQUESTS_FILE}")

def save_request_body_to_json(request_body, lot_id):
    """Сохраняет одну заявку в отдельный JSON файл."""
    filename = f"request_body_{lot_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(request_body, f, ensure_ascii=False, indent=4)
    logger.info(f"Запрос сохранен в файл: {filename}")
