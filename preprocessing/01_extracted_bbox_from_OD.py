import pandas as pd
from shapely.geometry import box
from shapely.ops import transform
from pyproj import Transformer, CRS
from pathlib import Path

import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import local_input
from utils import get_dataframe

name_input = "od-coords-simplified"
if local_input:
    name_input = "input_od/" + name_input
coord = get_dataframe(name=name_input, local=local_input)

min_lat = min(
    coord['origin_lat'].min(),
    coord['dest_lat'].min()
)

max_lat = max(
    coord['origin_lat'].max(),
    coord['dest_lat'].max()
)

min_lon = min(
    coord['origin_lon'].min(),
    coord['dest_lon'].min()
)

max_lon = max(
    coord['origin_lon'].max(),
    coord['dest_lon'].max()
)

bounding_box = (float(min_lon), float(min_lat), float(max_lon), float(max_lat))

print("\n Original bounding box in lon/lat (WGS84):")
print(bounding_box)
#  (10.860721599862547, 44.05630624769124, 12.012741989785605, 44.820050726223485)


# Enlarge the BBox of 10km
bbox_wgs84 = box(float(min_lon), float(min_lat), float(max_lon), float(max_lat))

wgs84 = CRS.from_epsg(4326)
projected_crs = CRS.from_epsg(32632)  # Change to your projected EPSG code

to_projected = Transformer.from_crs(wgs84, projected_crs, always_xy=True).transform
bbox_projected = transform(to_projected, bbox_wgs84)

bbox_enlarged_projected = bbox_projected.buffer(50000)

to_wgs84 = Transformer.from_crs(projected_crs, wgs84, always_xy=True).transform
bbox_enlarged_wgs84 = transform(to_wgs84, bbox_enlarged_projected)

print("\n Enlarged bounding box in lon/lat (WGS84) with a 50km buffer:")
print(bbox_enlarged_wgs84.bounds)
#(10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926)
