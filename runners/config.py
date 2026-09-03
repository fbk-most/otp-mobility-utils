from otp_mobility.utils.config import logging_level

version: str = "20251205"

params_list = [
    {"method": "simplified", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"], "date": "2025-06-10", "time": "07:00:00"},
    {"method": "simplified", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"], "date": "2025-06-10", "time": "07:00:00"},
    {"method": "extended", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"], "date": "2025-06-10", "time": "07:00:00"},
    {"method": "extended", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"], "date": "2025-06-10", "time": "07:00:00"},
    # {"method": "av", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"], "date": "2025-06-10", "time": "07:00:00"},
    # {"method": "av", "zoi": "allBologna", "modes": ["TRANSIT"], "date": "2025-06-10", "time": "07:00:00"}
]

