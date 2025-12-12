local_raw: bool = True
local_input: bool = False
local_processing: bool = True

verbose: bool = True

file_centroids: str = "data/input_od/Shape_zone_centroid.SHP"
file_shape: str = "data/input_od/Shape_zone.SHP"
file_av: str = "data/input_od/area_verde_manual_v1.geojson"
file_flows: str = "data/input_od/PROGETTO-OD.xlsx"  

params_list = [
    {"method": "simplified", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "simplified", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "extended", "zoi": "restrictedAv", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "av", "zoi": "allBologna", "modes": ["CAR_PARK", "TRANSIT"]},
    {"method": "av", "zoi": "allBologna", "modes": ["TRANSIT"]}
]

OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"