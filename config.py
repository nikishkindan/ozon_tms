# config.py

import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Загрузить переменные из .env файла

CHROMEDRIVER_PATH = 'path/to/chromedriver'
AUTH_URL = "https://tms.ozon.ru/ozi-orders"
ATI_API_URL = "https://api.ati.su/v1.0/dictionaries/locations/parse"
GRAPHQL_URL = "https://tms.ozon.ru/graphql-decorator.lpp/gql"

COOKIES_FILE = "cookies.json"
PROCESSED_IDS_FILE = "processed_ids.json"
ALL_REQUESTS_FILE = "all_requests.json"

AUTHORIZATION_TOKEN = os.getenv("AUTHORIZATION_TOKEN")
BOARD_ID = os.getenv('BOARD_ID', 'Не указано')

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
