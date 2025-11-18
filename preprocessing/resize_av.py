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
    if len(sys.argv) != 3:
        print(f"Error: wrong number of inputs. Given {len(sys.argv)-1}, while needed 2.")
        print("Correct usage: python resize_av.py input output")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    print(f"Executing resize_av.py with: \n- input = {input_file}\n- output = {output_file}\n")

    resize_av(input_geojson=input_file, output_geojson=output_file)
    print("\n")