from pathlib import Path

local_raw: bool = True
local_input: bool = True
local_processing: bool = True
local_output: bool = False

verbose: bool = True

params_list = [
    {"method": "simplified", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "simplified", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "av", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "av", "zoi": "allBologna", "modes": ["TRANSIT"]}
]

OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"

PROJECT = "test-otp-v2"

