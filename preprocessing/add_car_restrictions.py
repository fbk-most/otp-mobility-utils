"""
Script to add anti-car restrictions to all highways in an OSM file.
Blocks only private cars and motorcycles; allows buses, bicycles, pedestrians, and emergency services.

Requires: pip install osmium
Usage: python osm_road_accessibility_convert.py input.osm.pbf output.osm.pbf
"""

import osmium
from pathlib import Path
from datetime import datetime
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
            
            # Create the new way with restrictions
            new_way = w.replace(tags=tags)
            self.writer.add_way(new_way)
            self.highways_modified += 1

        else:
            # Keep non-highway ways unchanged
            self.writer.add_way(w)

    def node(self, n):
        self.writer.add_node(n)

    def relation(self, r):
        self.writer.add_relation(r)

def _show_print(handler, input_file: str, output_file: str):         
    print(f"-> Conversion completed! {handler.highways_modified} highways modified with anti-car restrictions.")
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")
    print(f"-> Original elems: {_count_elements(input_file)} → Filtered elems: {_count_elements(output_file)}")

def _count_elements(input_file: str):
    i_in, i_iw, i_ir = 0, 0, 0
    for obj in osmium.FileProcessor(input_file):
        if obj.is_node():
            i_in = i_in+1  
        elif obj.is_way():
            i_iw = i_iw + 1
        elif obj.is_relation():
            i_ir = i_ir +1 
    return i_in, i_iw, i_ir
    
def add_car_restrictions(input_file: str, output_file: str):
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    handler = CarRestrictionHandler(writer)
    print(f"-> Getting elems \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
    handler.apply_file(input_file)
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we finished") if verbose else None
    if verbose:
        _show_print(handler, input_file, output_file)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Error: wrong number of inputs. Given {len(sys.argv)-1}, while needed 2.")
        print("Correct usage: python add_car_restrictions.py input output")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    print(f"Executing add_car_restrictions.py with: \n- input = {input_file}\n- output = {output_file}\n")

    add_car_restrictions(input_file, output_file)
    print("\n")