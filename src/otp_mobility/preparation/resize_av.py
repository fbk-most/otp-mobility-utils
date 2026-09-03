import logging
from otp_mobility.utils.config import logging_level

import geopandas as gpd
import sys
from otp_mobility.utils.constants import CRS_LATLONG, CRS_PROJECTED

def resize_av(input_geojson: str, output_geojson: str):
    av = gpd.read_file(input_geojson).to_crs(CRS_PROJECTED)
    av['geometry'] = av.buffer(-250)
    av = av.to_crs(CRS_LATLONG)
    av.to_file(output_geojson, driver="GeoJSON")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Wrong number of inputs. Given %s, while needed 2.", len(sys.argv) - 1)
        logging.error("Correct usage: python resize_av.py input output")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    logging.info("Executing resize_av.py with input=%s, output=%s", input_file, output_file)

    resize_av(input_geojson=input_file, output_geojson=output_file)