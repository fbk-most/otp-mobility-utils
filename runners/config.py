import os
import logging

version: str = "20251205"

params_list = [
    {"method": "simplified", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "simplified", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    # {"method": "av", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    # {"method": "av", "zoi": "allBologna", "modes": ["TRANSIT"]}
]

_level_name = os.environ.get("BDT_LOG_LEVEL", "INFO").upper()
logging_level = getattr(logging, _level_name, logging.INFO)
