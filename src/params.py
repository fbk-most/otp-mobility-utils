local_raw: bool = True
local_input: bool = False
local_processing: bool = True

file_centroids: str = "data/input_od/Shape_zone_centroid.SHP"
file_shape: str = "data/input_od/Shape_zone.SHP"
file_av: str = "data/input_od/area_verde_manual_v1.geojson"
file_flows: str = "data/input_od/PROGETTO-OD.xlsx"  

modes: list[str] = ["CAR", "TRANSIT"]  ## Choose one or more among: "car_park", "car", "walk", "transit
zoi: str = "allBologna"  ## Choose between "allBologna" and "restrictedAv"
method: str = "av" ## Choose between "simplified" and "extended" and "av"
version: str = "20251011"

modes_str =  "_".join(modes)

input_coord_file: str = f"od-coords-{zoi}"
if local_input:
    input_coord_file = "input_od/" + input_coord_file

output_times_file: str = f"otp_results_{method}_{zoi}_{modes_str}_v{version}"
if local_input:
    output_times_file = "output/" + output_times_file

OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"