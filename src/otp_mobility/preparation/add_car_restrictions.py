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
from otp_mobility.utils.config import logging, logging_level

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

def _show_stats(handler, input_file: str, output_file: str):
    logging.info("Conversion completed: %s highways modified with anti-car restrictions.", handler.highways_modified)
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    logging.info("Original size: %.2f MB; filtered size: %.2f MB", original_size, filtered_size)
    logging.info("Original elements: %s; filtered elements: %s", _count_elements(input_file), _count_elements(output_file))

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
    logging.debug("Getting elements at %s", datetime.now().strftime('%H:%M:%S'))
    handler.apply_file(input_file)
    writer.close()
    logging.debug("Finished at %s", datetime.now().strftime('%H:%M:%S'))
    _show_stats(handler, input_file, output_file)


if __name__ == "__main__":
    logging.basicConfig(level=logging_level)
    if len(sys.argv) != 3:
        logging.error("Wrong number of inputs. Given %s, while needed 2.", len(sys.argv) - 1)
        logging.error("Correct usage: python add_car_restrictions.py input output")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    logging.info("Executing add_car_restrictions.py with input=%s, output=%s", input_file, output_file)

    add_car_restrictions(input_file, output_file)