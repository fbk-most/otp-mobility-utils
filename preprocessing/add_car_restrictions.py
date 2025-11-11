"""
Script to add anti-car restrictions to all highways in an OSM file.
Blocks only private cars and motorcycles; allows buses, bicycles, pedestrians, and emergency services.

Requires: pip install osmium
Usage: python osm_road_accessibility_convert.py input.osm.pbf output.osm.pbf
"""

import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


class CarRestrictionHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer
        self.highways_modified = 0

    def way(self, w):
        if 'highway' in w.tags:
            # Create a dictionary with the original tags
            tags = dict(w.tags)
            
            # KEEP the original highway type (primary, secondary, etc.)
            # Only add restrictions for cars and motorcycles
            tags['motorcar'] = 'no'          # Block private cars
            tags['motor_vehicle'] = 'no'     # Block private cars
            tags['bus'] = 'yes'              # Allow buses
            tags['motorcycle'] = 'no'        # Block motorcycles/scooters
            
            # Explicit permissions for other users (optional but clearer)
            if 'foot' not in tags:
                tags['foot'] = 'yes'         # Pedestrians always allowed
            if 'bicycle' not in tags:
                tags['bicycle'] = 'yes'      # Bicycles always allowed
            # bus, psv, emergency are allowed by default
            
            # Remove only car-specific tags that no longer make sense
            tags_to_remove = [
                # Car speed
                'maxspeed', 'maxspeed:forward', 'maxspeed:backward', 'minspeed',
                # Car lanes
                'lanes', 'lanes:forward', 'lanes:backward', 
                'turn:lanes', 'turn:lanes:forward', 'turn:lanes:backward',
                # Car parking
                'parking:lane', 'parking:lane:left', 'parking:lane:right',
                'parking:both', 'parking:left', 'parking:right',
                # Car-specific service (but keep the highway type!)
                'service'  # Only if it’s a service road, not the highway type
            ]
            
            # Remove inappropriate tags only if they exist
            for tag in tags_to_remove:
                if tag in tags:
                    del tags[tag]
            
            # KEEP useful tags:
            # - ref (road number)
            # - name (road name)
            # - surface, width (useful for pedestrians/bikes)
            # - oneway (can also apply to bikes)
            # - cycleway, sidewalk (still relevant)
            
            # Create the new way with restrictions
            new_way = w.replace(tags=tags)
            self.writer.add_way(new_way)
            self.highways_modified += 1
            
            if self.highways_modified % 1000 == 0:
                print(f"Modified {self.highways_modified} highways...")
        else:
            # Keep non-highway ways unchanged
            self.writer.add_way(w)

    def node(self, n):
        self.writer.add_node(n)

    def relation(self, r):
        self.writer.add_relation(r)

def _show_print(handler, input_file, output_file):         
    print(f"Conversion completed! {handler.highways_modified} highways modified with anti-car restrictions.")
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")

def add_car_restrictions(input_file, output_file):
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    handler = CarRestrictionHandler(writer)
    handler.apply_file(input_file)
    if verbose:
        _show_print(handler, input_file, output_file)


if __name__ == "__main__":
    input_file = "data/input_service/"
    output_file = "data/input_service/"

    add_car_restrictions(input_file, output_file)