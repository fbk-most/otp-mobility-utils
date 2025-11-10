#!/usr/bin/env python3
"""
Complete preprocessing pipeline for OSM data.
Executes all steps described in the README in sequence.
"""
import subprocess
import sys
from pathlib import Path
import osmium

class PreprocessingPipeline:
    """
    Main pipeline class that orchestrates all preprocessing steps.
    Handles both service data (GTFS, OSM network) and OD (Origin-Destination) data.
    """
    
    def __init__(self):
        self.base_dir = Path(".")
        self.data_input_service = self.base_dir / "data" / "input_service"
        self.data_input_od = self.base_dir / "data" / "input_od"
        self.preprocessing_dir = self.base_dir / "preprocessing"
        
    def run_command(self, cmd, description):
        """Execute a command"""
        print(f"\n► {description}")
        try:
            subprocess.run(cmd, check=True)
            print("✓ Done")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
    
    def step_1_extract_bbox(self):
        """Step 1: Extract bounding box from OD coordinates"""
        self.run_command(
            ["python", str(self.preprocessing_dir / "01_extracted_bbox_from_OD.py")],
            "Step 1: Extract bounding box from OD coordinates"
        )
    
    def step_2_extract_bologna_area(self):
        """Step 2: Extract Bologna area from regional OSM file using bounding box"""
        bbox = "10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926"
        self.run_command(
            [
                "osmium extract--bbox", 
                bbox,
                str(self.data_input_service / "nord-est-latest.osm.pbf"),
                "--overwrite", "-o", 
                str(self.data_input_service / "bologna-area.osm.pbf")
            ],
            "Step 2: Extract Bologna area with osmium"
        )
    
    def step_3_filter_roads(self):
        """Step 3: Filter main roads for mobility analysis"""
        self.run_command(
            ["bash", str(self.preprocessing_dir / "03_osm_mobility_filter.sh")],
            "Step 3: Filter main roads"
        )
    
    def step_4_correct_parkings(self):
        """
        Step 4: Correct parking data to enable park-and-ride intermodality.
        Tags all parkings as park-and-ride facilities and removes duplicates.
        """
        # Part 1: Add park and ride tags
        self.run_command(
            ["python", str(self.preprocessing_dir / "04_osm_add_parkride.py")],
            "Step 4a: Add 'park and ride' tags to parking facilities"
        )
        
        # Part 2: Sort and remove duplicates
        self.run_command(
            [
                "osmium", "sort", "-o", 
                str(self.data_input_service / "bologna-area-filtered-parking-sorted.osm.pbf"),
                str(self.data_input_service / "bologna-area-filtered-parking.osm.pbf"),
                "--overwrite"
            ],
            "Step 4b: Sort and remove duplicate relations"
        )
    
    def step_5_buffer_area_verde(self):
        """
        Step 5: Apply negative 250m buffer to 'Area Verde' zone.
        This defines a reduced zone for accessibility restrictions.
        """
        # Part 1: Reproject to UTM for accurate metric buffer
        self.run_command(
            [
                "ogr2ogr", "-f", "GeoJSON",
                str(self.data_input_service / "area_verde_manual_v1_utm.geojson"),
                str(self.data_input_service / "area_verde_manual_v1.geojson"),
                "-t_srs", "EPSG:6875"
            ],
            "Step 5a: Reproject Area Verde to UTM (EPSG:6875)"
        )
        
        # Part 2: Apply negative 250m buffer
        self.run_command(
            [
                "ogr2ogr", "-f", "GeoJSON",
                str(self.data_input_service / "small_area_verde_manual_v1_utm.geojson"),
                str(self.data_input_service / "area_verde_manual_v1_utm.geojson"),
                "-dialect", "SQLite",
                "-sql", "SELECT ST_Buffer(geometry, -250) AS geometry FROM area_verde_manual_v1"
            ],
            "Step 5b: Apply negative 250m buffer"
        )
        
        # Part 3: Reproject back to WGS84
        self.run_command(
            [
                "ogr2ogr", "-f", "GeoJSON",
                str(self.data_input_service / "small_area_verde_manual_v1.geojson"),
                str(self.data_input_service / "small_area_verde_manual_v1_utm.geojson"),
                "-t_srs", "EPSG:4326"
            ],
            "Step 5c: Reproject back to WGS84 (EPSG:4326)"
        )
    
    def step_6_extract_inside_area_verde(self):
        """Step 6: Extract OSM elements inside the 'Area Verde' polygon"""
        self.run_command(
            [
                "osmium", "extract", "--polygon", 
                str(self.data_input_service / "small_area_verde_manual_v1.geojson"),
                str(self.data_input_service / "bologna-area-filtered-parking-sorted.osm.pbf"),
                "-o", 
                str(self.data_input_service / "bologna-area-filtered-parking-inside-AV.osm.pbf"),
                "--overwrite"
            ],
            "Step 6: Extract elements inside Area Verde"
        )
    
    def step_7_extract_outside_area_verde(self):
        """Step 7: Extract OSM elements outside the 'Area Verde' using spatial difference"""
        self.run_command(
            ["python", str(self.preprocessing_dir / "07_osm_spatial_diff.py")],
            "Step 7: Extract elements outside Area Verde (spatial difference)"
        )
    
    def step_8_convert_road_accessibility(self):
        """
        Step 8: Convert road accessibility inside 'Area Verde'.
        Makes all roads inaccessible to private vehicles (footway only).
        """
        self.run_command(
            [
                "python", str(self.preprocessing_dir / "08_osm_convert_road_accessibility.py"),
                str(self.data_input_service / "bologna-area-filtered-parking-inside-AV.osm.pbf"),
                str(self.data_input_service / "bologna-area-filtered-parking-inside-AV-footway.osm.pbf")
            ],
            "Step 8: Convert road accessibility inside Area Verde"
        )
    
    def run_service_pipeline(self):
        """Execute the complete service data pipeline"""
        print("\n" + "="*60)
        print("SERVICE DATA PIPELINE START")
        print("="*60 + "\n")
        
        self.step_1_extract_bbox()
        self.step_2_extract_bologna_area()
        self.step_3_filter_roads()
        self.step_4_correct_parkings()
        
        print("\n" + "="*60)
        print("ADDITIONAL STEPS FOR INTERMODALITY ANALYSIS")
        print("="*60 + "\n")
        
        self.step_5_buffer_area_verde()
        self.step_6_extract_inside_area_verde()
        self.step_7_extract_outside_area_verde()
        self.step_8_convert_road_accessibility()


if __name__ == "__main__":
    
    pipeline = PreprocessingPipeline()
    try:
        pipeline.run_service_pipeline()
    except KeyboardInterrupt:
        print("\n\n Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n Unexpected error: {e}")
        sys.exit(1)