#!/usr/bin/env python3
"""
Complete preprocessing pipeline for OSM data.
Executes all steps described in the README in sequence.
"""
import sys

from otp_mobility.preparation.get_bbox_from_OD import get_bbox
from otp_mobility.preparation.extract_with_pyosmium import extract_bbox_with_pyosmium
from otp_mobility.preparation.tags_filter_with_pyosmium import our_tags_filter_with_pyosmium
from otp_mobility.preparation.add_parkrides import add_parkrides
from otp_mobility.preparation.resize_av import resize_av
from otp_mobility.preparation.extract_with_pyosmium import extract_polygon_with_pyosmium
from otp_mobility.preparation.extract_elements_outside import extract_elements_outside
from otp_mobility.preparation.add_car_restrictions import add_car_restrictions

from paths import (
    data_input_service, data_output, data_input_geo, 
    data_output_tmp, data_output,
    file_osm
)

def run_service_pipeline():
    """Execute the complete service data pipeline"""
    print("\n" + "="*60)
    print("SERVICE DATA PIPELINE START")
    print("="*60)
    
    """Step 1: Extract bounding box from OD coordinates"""
    print(f"\n► Step 1: Extract bounding box from OD coordinates")
    bbox = get_bbox(
        name_input=data_output/"od-coords-simplified.parquet",
        enlarged=False
    )
    bbox = [10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926]

    """Step 2: Extract elements in the bbox of the Bologna area from the regional OSM file"""
    print(f"\n► Step 2: Extract entities in the bbox (i.e., Bologna area)")
    extract_bbox_with_pyosmium(
        bbox=bbox, 
        input_file=file_osm, 
        output_file=str(data_output_tmp / "bologna-area.osm.pbf")
    )

    """Step 3: Filter relevant entities (roads and features) for mobility analysis"""
    print(f"\n► Step 3: Filter relevant entities in the area")
    our_tags_filter_with_pyosmium(
        input_file=str(data_output_tmp / "bologna-area.osm.pbf"), 
        output_file=str(data_output_tmp / "bologna-area-filtered.osm.pbf"),
        filter_file=str(data_input_service / "config_filter_rules.sh")
        
    )

    """
    Step 4: Correct parking data to enable park-and-ride intermodality.
    Tags all parkings as park-and-ride facilities and removes duplicates.
    """
    print(f"\n► Step 4: Correct parking features")
    add_parkrides(
        input_file=str(data_output_tmp / "bologna-area-filtered.osm.pbf"),
        output_file=str(data_output / "bologna-area-filtered-parking.osm.pbf")
    )
    
    print("\n" + "="*60)
    print("ADDITIONAL STEPS FOR INTERMODALITY ANALYSIS")
    print("="*60)
    
    '''
    Step 5: Apply negative 250m buffer to 'Area Verde' zone.
    This defines a reduced zone for accessibility restrictions.
    '''
    print(f"\n► Step 5: Reduce the size of Area Verde")
    resize_av(
        input_geojson=str(data_input_geo / "area_verde_manual_v1.geojson"),
        output_geojson=str(data_output_tmp / "small_area_verde_manual_v1.geojson")
    )
    
    """Step 6: Extract OSM elements inside the 'Area Verde' polygon"""
    print(f"\n► Step 6: Extract OSM elements inside Area Verde")
    extract_polygon_with_pyosmium(
        polygon_file=str(data_output_tmp / "small_area_verde_manual_v1.geojson"),
        input_file=str(data_output / "bologna-area-filtered-parking.osm.pbf"), 
        output_file=str(data_output_tmp / "bologna-area-filtered-parking-inside-AV.osm.pbf")
    )

    """Step 7: Extract OSM elements outside the 'Area Verde' polygon"""
    print(f"\n► Step 7: Extract OSM elements outside Area Verde")
    extract_elements_outside(
        input_file_container=str(data_output / "bologna-area-filtered-parking.osm.pbf"),
        input_file_contained=str(data_output_tmp / "bologna-area-filtered-parking-inside-AV.osm.pbf"),
        output_file=str(data_output / "bologna-area-filtered-parking-outside-AV.osm.pbf")
    )

    """Step 8: Add car restrictions to entering in the 'Area Verde'"""
    print(f"\n► Step 8: Extract OSM elements outside Area Verde")
    add_car_restrictions(
        input_file=data_output_tmp / "bologna-area-filtered-parking-inside-AV.osm.pbf",
        output_file=data_output / "bologna-area-filtered-parking-inside-AV-footway.osm.pbf"
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