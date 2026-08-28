from pathlib import Path

from otp_mobility.utils.paths import (
    data_input_od,
    data_input_geo,
    data_input_service,
)

file_centroids: Path = data_input_od / "Shape_zone_centroid.SHP"
file_shape: Path = data_input_od / "Shape_zone.SHP"
file_flows: Path = data_input_od / "PROGETTO-OD.xlsx"  

file_av: Path = data_input_geo / "area_verde_manual_v1.geojson"

file_osm = Path = data_input_service / "nord-est-latest.osm.pbf"