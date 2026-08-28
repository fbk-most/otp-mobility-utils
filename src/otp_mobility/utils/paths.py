from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_DIR / "data" 

data_input_geo = DATA_DIR / "input_geo"
data_input_service = DATA_DIR / "input_service"
data_input_od = DATA_DIR / "input_od"
data_output = DATA_DIR / "output"

data_output_tmp = data_output / "tmp"
data_output_otp_ab = data_output / "otp_allBologna"
data_output_otp_ra = data_output / "otp_restrictedAv"
data_output_otp_av = data_output / "otp_av"

file_centroids = data_input_od / "Shape_zone_centroid.SHP"
file_shape = data_input_od / "Shape_zone.SHP"
file_flows = data_input_od / "PROGETTO-OD.xlsx"  

file_av = data_input_geo / "area_verde_manual_v1.geojson"

file_osm = data_input_service / "nord-est-260826.osm.pbf"

folder_zip_gtfs = data_input_service / "gommagtfsbo_20250513.zip"