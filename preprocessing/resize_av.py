import geopandas as gpd
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from constants import CRS_LATLONG, CRS_PROJECTED

def resize_av(input_geojson: str, output_geojson: str):
    av = gpd.read_file(input_geojson).to_crs(CRS_PROJECTED)
    av['geometry'] = av.buffer(-250)
    av = av.to_crs(CRS_LATLONG)
    av.to_file(output_geojson, driver="GeoJSON")


if __name__ == "__main__":
    input_file = "data/input_service/area_verde_manual_v1.geojson"
    output_file = "data/input_service/small_area_verde_manual_v1.geojson"
    resize_av(input_geojson=input_file, output_geojson=output_file)