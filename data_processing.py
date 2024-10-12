# data_processing.py

import json
from logger import logger

def create_route(way_points_data, cargo_weight, cargo_value):
    if not way_points_data:
        return {}

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
                        "quantity": cargo_weight
                    },
                    "volume": {
                        "quantity": cargo_value
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
    intermediate_way_points = []
    
    for wp in way_points:
        intermediate_wp = {
            "type": "intermediate",  # Можно уточнить тип, если требуется
            "city_id": wp["CityId"],
            "location": {
                "type": "manual",
                "city_id": wp["CityId"],
                "address": wp["Address"]
            },
            "dates": {
                "type": "ready",
                "time": {
                    "type": "bounded",
                    "start": wp["Time"]
                },
                "first_date": wp["Date"]
            }
        }
        intermediate_way_points.append(intermediate_wp)

    request_body = {
        "cargo_application": {
            "external_id": lot_id,
            "route": route,
            "way_points": intermediate_way_points,
            "payment": {
                "cash": bet_start,
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
                "start_rate": bet_start,
                "auction_currency_type": 1,
                "bid_step": bet_step,
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
                    "cash": bet_start,
                    "rate_with_nds": bet_start,
                    "rate_without_nds": bet_start
                }
            },
            "boards": [
                {
                    "id": 12213,
                    "publication_mode": "now",
                    "cancel_publish_on_auction_bet": False,
                    "reservation_enabled": True
                }
            ],
            "note": lot_id
        }
    }

    return request_body
