import pandas as pd
from zipfile import ZipFile
import geopandas as gpd
import sys
from shapely.geometry import box
from shapely.ops import transform
from pyproj import Transformer, CRS

from otp_mobility.utils.config import logging, logging_level
from otp_mobility.utils.constants import N_CRS_PROJECTED, N_CRS_LATLONG


def get_bbox_from_gtfs(folder_zip_gtfs):
    with ZipFile(folder_zip_gtfs) as gtfs_zip:
        stops_path = next(
            path for path in gtfs_zip.namelist()
            if path.rstrip('/').split('/')[-1] == 'stops.txt'
        )
        with gtfs_zip.open(stops_path) as stops_file:
            stops = pd.read_csv(stops_file)

    # Ensure required columns exist
    if 'stop_lat' not in stops or 'stop_lon' not in stops:
        raise ValueError("stops.txt must contain 'stop_lat' and 'stop_lon' columns")

    # Calculate bounding box
    min_lat = stops['stop_lat'].min()
    max_lat = stops['stop_lat'].max()
    min_lon = stops['stop_lon'].min()
    max_lon = stops['stop_lon'].max()

    # Bounding box format: (min_lon, min_lat, max_lon, max_lat)
    bounding_box = (float(min_lon), 
                    float(min_lat), 
                    float(max_lon), 
                    float(max_lat))
    logging.info("Bounding Box: %s", bounding_box)
    return bounding_box


def get_bbox_from_od(name_input: str, enlarged: bool = False):
    # Read the file of coordinates
    coord = gpd.read_parquet(name=name_input)

    # Get bbox
    min_lat = min(coord['origin_lat'].min(), coord['dest_lat'].min())
    max_lat = max(coord['origin_lat'].max(), coord['dest_lat'].max())
    min_lon = min(coord['origin_lon'].min(), coord['dest_lon'].min())
    max_lon = max(coord['origin_lon'].max(), coord['dest_lon'].max())
    
    bounding_box = (float(min_lon), float(min_lat), float(max_lon), float(max_lat))
    
    logging.debug("Original bounding box in lon/lat (WGS84): %s", bounding_box)

    if not enlarged:
        return bounding_box

    # Enlarge the BBox of 50km
    bbox_wgs84 = box(float(min_lon), float(min_lat), float(max_lon), float(max_lat))
    
    wgs84 = CRS.from_epsg(N_CRS_LATLONG)
    projected_crs = CRS.from_epsg(N_CRS_PROJECTED)
    
    to_projected = Transformer.from_crs(wgs84, projected_crs, always_xy=True).transform
    bbox_projected = transform(to_projected, bbox_wgs84)
    
    bbox_enlarged_projected = bbox_projected.buffer(50000)
    
    to_wgs84 = Transformer.from_crs(projected_crs, wgs84, always_xy=True).transform
    bbox_enlarged_wgs84 = transform(to_wgs84, bbox_enlarged_projected)
    
    logging.debug("Enlarged bounding box in lon/lat (WGS84) with a 50km buffer: %s", bbox_enlarged_wgs84.bounds)
    
    return bbox_enlarged_wgs84.bounds

if __name__ == "__main__":
    logging.basicConfig(level=logging_level)
    if len(sys.argv) != 2:
        logging.error("Wrong number of inputs. Given %s, while needed 2.", len(sys.argv) - 1)
        logging.error("Correct usage: python extract_bbox.py od input_zip_folder")
        logging.error("or: python extract_bbox.py gtfs input_file")
        sys.exit(1)
    
    # Configuration
    which_function = sys.argv[1]
    input_file = sys.argv[2]

    if ~which_function.isin("od", "gtfs"):
        logging.error("Wrong method selected: either 'od' or 'gtfs'")
        sys.exit(1)

    logging.info("Executing extract_bbox.py with method=get_bbox_from_%s using input=%s", which_function, input_file)
    if which_function == "od":
        bbox = get_bbox_from_od(input_file)
    else:
        bbox = get_bbox_from_gtfs(input_file)