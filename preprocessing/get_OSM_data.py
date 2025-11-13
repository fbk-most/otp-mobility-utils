#!/usr/bin/env python3
"""
Complete preprocessing pipeline for OSM data.
Executes all steps described in the README in sequence.
"""
import subprocess
import sys
from pathlib import Path
import osmium
from shutil import which

from extract_bbox_from_OD import extract_bbox
from extract_with_pyosmium import extract_bbox_with_pyosmium
from filter_mobility_entities2 import filter_mobility_entities
from add_parkrides import add_parkrides
from sort_entities import sort_entities
from resize_av import resize_av
from extract_with_pyosmium import extract_polygon_with_pyosmium
from extract_elements_inside_outside import extract_elements_inside, extract_elements_outside
from add_car_restrictions import add_car_restrictions

base_dir = Path(".")
data_input_service = base_dir / "data" / "input_service"
data_input_od = base_dir / "data" / "input_od"
preprocessing_dir = base_dir / "preprocessing"
which_osmium = which("osmium") is not None


def run_service_pipeline():
    """Execute the complete service data pipeline"""
    print("\n" + "="*60)
    print("SERVICE DATA PIPELINE START")
    print("="*60 + "\n")
    
    """Step 1: Extract bounding box from OD coordinates"""
    print(f"\n► Step 1: Extract bounding box from OD coordinates")
    bbox = extract_bbox(
        name_input=str("od-coords-simplified"),
        enlarged=False
    )
    bbox = [10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926]

    """Step 2: Extract Bologna area from regional OSM file using bounding box"""
    print(f"\n► Step 2: Extract Bologna area with osmium")
    extract_with_pyosmium(
        bbox=bbox, 
        input_file=str(data_input_service / "nord-est-latest.osm.pbf"), 
        output_file=str(data_input_service / "bologna-area.osm.pbf")
    )
    # SLOW!! But OK :D

    """Step 3: Filter relevant entities (roads and features) for mobility analysis"""
    print(f"\n► Step 3: Filter relevant entities")
    # filter_mobility_entities(
    #    input_file=str(data_input_service / "bologna-area.osm.pbf"), 
    #    output_file=str(data_input_service / "bologna-area-filtered.osm.pbf")
    #)
    #cmd = ["bash", str(preprocessing_dir / "filter_mobility_entities.sh")]
    #subprocess.run(cmd, check=True)
    # Different results 

    """
    Step 4: Correct parking data to enable park-and-ride intermodality.
    Tags all parkings as park-and-ride facilities and removes duplicates.
    """
    print(f"\n► Step 4: Correct parking features")
    add_parkrides(
        input_file=str(data_input_service / "bologna-area-filtered.osm.pbf"),
        output_file=str(data_input_service / "bologna-area-filtered-parking.osm.pbf")
    )
    # Works well
    
    """
    Step 5: Reorder the data entities
    """
    print(f"\n► Step 5: Reorder entities based on their id")
    sort_entities(
        input_file=str(data_input_service / "bologna-area-filtered-parking.osm.pbf"),
        output_file=str(data_input_service / "bologna-area-filtered-parking-sorted.osm.pbf")
    )
    # Seems to work well

    print("\n" + "="*60)
    print("ADDITIONAL STEPS FOR INTERMODALITY ANALYSIS")
    print("="*60)
    
    '''
    Step 6: Apply negative 250m buffer to 'Area Verde' zone.
    This defines a reduced zone for accessibility restrictions.
    '''
    print(f"\n► Step 6: Reduce the size of Area Verde")
    resize_av(
        input_geojson=str(data_input_service / "area_verde_manual_v1.geojson"),
        output_geojson=str(data_input_service / "small_area_verde_manual_v1.geojson")
    )
    # OK :)
    
    """Step 7: Extract OSM elements inside the 'Area Verde' polygon"""
    print(f"\n► Step 7: Extract OSM elements inside Area Verde")
    extract_polygon_with_pyosmium(
        polygon_geojson=str(data_input_service / "small_area_verde_manual_v1.geojson"),
        input_pbf=str(data_input_service / "bologna-area-filtered-parking-sorted.osm.pbf"), 
        output_pbf=str(data_input_service / "bologna-area-filtered-parking-inside-AV.osm.pbf")
    )
    # OK :)

    """Step 8: Extract OSM elements outside the 'Area Verde' polygon"""
    print(f"\n► Step 8: Extract OSM elements outside Area Verde")
    extract_elements_outside(
        polygon_geojson=str(data_input_service / "small_area_verde_manual_v1.geojson"),
        input_pbf=str(data_input_service / "bologna-area-filtered-parking-sorted.osm.pbf"),
        output_pbf=str(data_input_service / "bologna-area-filtered-parking-outside-AV.osm.pbf")
    )
    # Keeps too many thinks

    """Step 9: Add car restrictions to entering in the Area Verde"""
    print(f"\n► Step 9: Extract OSM elements outside Area Verde")
    add_car_restrictions(
        input_file=data_input_service / "bologna-area-filtered-parking-inside-AV.osm.pbf",
        output_file=data_input_service / "bologna-area-filtered-parking-inside-AV-footway.osm.pbf"
    )
    

if __name__ == "__main__":
    try:
        run_service_pipeline()
    except KeyboardInterrupt:
        print("\n\n Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n Unexpected error: {e}")
        sys.exit(1)