# api_client.py

import requests
import json
from config import ATI_API_URL, GRAPHQL_URL, AUTHORIZATION_TOKEN
from logger import logger

def get_city_ids(addresses):
    headers = {
        "Authorization": f"Bearer {AUTHORIZATION_TOKEN}",
        "Content-Type": "application/json"
    }
    
    unique_addresses = list(set(addresses))
    logger.info(f"Запрос к API с уникальными адресами: {json.dumps(unique_addresses, ensure_ascii=False)}")

    try:
        response = requests.post(ATI_API_URL, headers=headers, json=unique_addresses, timeout=15)
        logger.debug(f"Ответ от API: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Успешный ответ от ATI API.")

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
            logger.debug(f"Сопоставление city_id и street: {json.dumps(city_info_mapping, ensure_ascii=False, indent=4)}")
            return city_info_mapping
        else:
            logger.error(f"Ошибка при запросе к ATI API: {response.status_code} - {response.text}")
            return {address: {"city_id": "Не указано", "street": None} for address in unique_addresses}
    except requests.RequestException as e:
        logger.error(f"Исключение при запросе к ATI API: {e}")
        return {address: {"city_id": "Не указано", "street": None} for address in unique_addresses}

def send_post_request(cookies, processed_ids):
    headers = {
        "Content-Type": "application/json",
    }

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

    try:
        response = requests.post(GRAPHQL_URL, cookies=cookies, headers=headers, json=payload)
        if response.status_code == 200:
            json_response = response.json()
            logger.info("Успешный запрос к GraphQL API.")
            return json_response
        else:
            logger.error(f"Ошибка запроса: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"Исключение при запросе к GraphQL API: {e}")
        return None
