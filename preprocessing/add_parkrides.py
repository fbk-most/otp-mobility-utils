#!/usr/bin/env python3
import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose
from datetime import datetime


class ParkingHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer
        self.parking_amenities = {
            'parking',
            'parking_entrance', 
            'parking_space',
            'motorcycle_parking'
        }
        self.modified_count = 0
        self.total_parking_count = 0
    
    def process_tags(self, tags):
        tag_dict = {tag.k: tag.v for tag in tags}
        
        # Check if it is a parking
        amenity = tag_dict.get('amenity')
        if amenity in self.parking_amenities:
            self.total_parking_count += 1
            
            # If it is not a park-and-ride one (i.e., empty "park_ride" feature or "park_ride=no"), 
            # change the setting to "yes"
            current_park_ride = tag_dict.get('park_ride', '')
            if not current_park_ride or current_park_ride.lower() == 'no':
                tag_dict['park_ride'] = 'yes'
                self.modified_count += 1
        
        return tag_dict
    
    def node(self, n):
        modified_tags = self.process_tags(n.tags)
        
        new_tags = [(k, v) for k, v in modified_tags.items()]
        self.writer.add_node(osmium.osm.mutable.Node(
            id=n.id,
            version=n.version,
            visible=n.visible,
            changeset=n.changeset,
            timestamp=n.timestamp,
            uid=n.uid,
            user=n.user,
            tags=new_tags,
            location=n.location
        ))
    
    def way(self, w):
        modified_tags = self.process_tags(w.tags)
        
        new_tags = [(k, v) for k, v in modified_tags.items()]
        self.writer.add_way(osmium.osm.mutable.Way(
            id=w.id,
            version=w.version,
            visible=w.visible,
            changeset=w.changeset,
            timestamp=w.timestamp,
            uid=w.uid,
            user=w.user,
            tags=new_tags,
            nodes=w.nodes
        ))
    
    def relation(self, r):
        modified_tags = self.process_tags(r.tags)
        
        new_tags = [(k, v) for k, v in modified_tags.items()]
        self.writer.add_relation(osmium.osm.mutable.Relation(
            id=r.id,
            version=r.version,
            visible=r.visible,
            changeset=r.changeset,
            timestamp=r.timestamp,
            uid=r.uid,
            user=r.user,
            tags=new_tags,
            members=r.members
        ))

def _show_final_stats(handler, input_file: str, output_file: str):
    print(f"-> N. parkings found: {handler.total_parking_count}; N. parkings modified: {handler.modified_count}")
    
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original size: {original_size:.2f} MB; New size: {filtered_size:.2f} MB")

    print(f"-> Elements in the original file: {_count_elements(input_file)}")
    print(f"   Elements in the new file: {_count_elements(output_file)}")
    

def add_parkrides(input_file: str, output_file: str):
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    handler = ParkingHandler(writer)
    print(f"-> Getting elems \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
    handler.apply_file(input_file)
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None
    if verbose:
        _show_final_stats(handler, input_file, output_file)

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
    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Error: wrong number of inputs. Given {len(sys.argv)-1}, while needed 2.")
        print("Correct usage: python add_parkrides.py input output")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    print(f"Executing add_parkrides.py with: \n- input = {input_file}\n- output = {output_file}\n")

    add_parkrides(input_file, output_file)
    print("\n")