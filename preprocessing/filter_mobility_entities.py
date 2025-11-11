import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


class MobilityFilter(osmium.SimpleHandler):
    def __init__(self, writer):
        super().__init__()
        self.writer = writer
    
    def node(self, n):
        tags = {tag.k: tag.v for tag in n.tags}
        
        # Traffic signals and stops
        if tags.get('highway') in ['traffic_signals', 'stop', 'give_way', 'speed_camera']:
            self.writer.add_node(n)
            return
        
        # Railway crossings
        if tags.get('railway') == 'level_crossing':
            self.writer.add_node(n)
            return
        
        # Barriers
        if tags.get('barrier') in ['toll_booth', 'gate', 'lift_gate', 'cycle_barrier']:
            self.writer.add_node(n)
            return
        
        if tags.get('amenity') == 'toll_booth':
            self.writer.add_node(n)
            return
        
        # Accessibility
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            self.writer.add_node(n)
            return
        
        # Traffic info
        if 'maxspeed' in tags or 'lanes' in tags or 'oneway' in tags:
            self.writer.add_node(n)
            return
    
    def way(self, w):
        tags = {tag.k: tag.v for tag in w.tags}
        
        # Road infrastructure
        if 'highway' in tags:
            self.writer.add_way(w)
            return
        
        if tags.get('bridge') == 'yes' or tags.get('tunnel') == 'yes':
            self.writer.add_way(w)
            return
        
        # Railways
        railway = tags.get('railway')
        if railway in ['rail', 'light_rail', 'subway', 'tram', 'monorail', 
                       'funicular', 'narrow_gauge', 'platform']:
            self.writer.add_way(w)
            return
        
        # Sustainable mobility
        if 'cycleway' in tags or tags.get('bicycle') in ['yes', 'designated']:
            self.writer.add_way(w)
            return
        
        if tags.get('footway') or tags.get('pedestrian'):
            self.writer.add_way(w)
            return
        
        # Ferry routes
        if tags.get('route') == 'ferry':
            self.writer.add_way(w)
            return
        
        # Barriers
        if tags.get('barrier') in ['toll_booth', 'gate', 'lift_gate', 'cycle_barrier']:
            self.writer.add_way(w)
            return
        
        # Traffic info
        if 'maxspeed' in tags or 'lanes' in tags or 'oneway' in tags:
            self.writer.add_way(w)
            return
        
        # Accessibility
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            self.writer.add_way(w)
            return
    
    def area(self, a):
        tags = {tag.k: tag.v for tag in a.tags}
        
        # Public transport
        if 'public_transport' in tags:
            self.writer.add_area(a)
            return
        
        railway = tags.get('railway')
        if railway in ['platform', 'station', 'halt', 'subway_entrance', 'tram_stop']:
            self.writer.add_area(a)
            return
        
        if tags.get('bus') == 'yes' or tags.get('trolleybus') == 'yes':
            self.writer.add_area(a)
            return
        
        # Amenities
        amenity = tags.get('amenity')
        if amenity in ['bus_station', 'ferry_terminal', 'parking', 'parking_space',
                       'motorcycle_parking', 'bicycle_parking', 'bicycle_rental',
                       'bicycle_repair_station', 'charging_station', 'fuel',
                       'airport', 'helipad', 'marina', 'truck_stop', 'warehouse',
                       'toll_booth']:
            self.writer.add_area(a)
            return
        
        # Parking
        if tags.get('park_ride') == 'yes' or 'parking' in tags or 'parking:fee' in tags:
            self.writer.add_area(a)
            return
        
        # Aviation
        if 'aeroway' in tags:
            self.writer.add_area(a)
            return
        
        # Water transport
        if tags.get('waterway') == 'ferry' or tags.get('harbour') == 'yes':
            self.writer.add_area(a)
            return
        
        # Services
        highway = tags.get('highway')
        if highway in ['services', 'rest_area']:
            self.writer.add_area(a)
            return
        
        # Logistics
        landuse = tags.get('landuse')
        if landuse == 'depot' or tags.get('railway') == 'depot':
            self.writer.add_area(a)
            return
        
        # Accessibility
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            self.writer.add_area(a)
            return
    
    def relation(self, r):
        tags = {tag.k: tag.v for tag in r.tags}
        
        # Routes and restrictions
        rel_type = tags.get('type')
        if rel_type in ['restriction', 'route', 'route_master']:
            self.writer.add_relation(r)
            return
        
        if 'restriction' in tags:
            self.writer.add_relation(r)
            return
        
        # Accessibility
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            self.writer.add_relation(r)
            return

def _show_file_sizes(input_file: str, output_file: str):
    # Show file sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")

def filter_mobility_entities(input_file: str, output_file: str):
    # Initialize the writer
    writer = osmium.SimpleWriter(output_file, overwrite=True)

    # Perform the filtering
    handler = MobilityFilter(writer)
    handler.apply_file(input_file, locations=True)
    writer.close()

    # Print stats
    if verbose:
        _show_file_sizes(input_file, output_file)


if __name__ == "__main__":
    # Configuration
    input_file = Path("data/input_service/bologna-area.osm.pbf")
    output_file = Path("data/input_service/bologna-area-filtered.osm.pbf")

    filter_mobility_entities(str(input_file), str(output_file))