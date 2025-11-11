import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


class MobilityFilter(osmium.SimpleHandler):
    """
    First pass: collect IDs of elements to keep and their dependencies
    """
    def __init__(self):
        super().__init__()
        self.nodes_to_keep = set()
        self.ways_to_keep = set()
        self.relations_to_keep = set()
        self.way_nodes = {}  # way_id -> list of node_ids
        self.relation_members = {}  # relation_id -> list of member_ids
    
    def node(self, n):
        tags = {tag.k: tag.v for tag in n.tags}
        should_keep = False
        
        # Traffic signals and stops
        if tags.get('highway') in ['traffic_signals', 'stop', 'give_way', 'speed_camera']:
            should_keep = True
        
        # Railway crossings
        if tags.get('railway') == 'level_crossing':
            should_keep = True
        
        # Barriers
        if tags.get('barrier') in ['toll_booth', 'gate', 'lift_gate', 'cycle_barrier']:
            should_keep = True
        
        if tags.get('amenity') == 'toll_booth':
            should_keep = True
        
        # Accessibility
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            should_keep = True
        
        # Traffic info
        if 'maxspeed' in tags or 'lanes' in tags or 'oneway' in tags:
            should_keep = True
        
        if should_keep:
            self.nodes_to_keep.add(n.id)
    
    def way(self, w):
        tags = {tag.k: tag.v for tag in w.tags}
        should_keep = False
        
        # Store way nodes for later
        self.way_nodes[w.id] = [n.ref for n in w.nodes]
        
        # === INFRASTRUTTURA STRADALE ===
        if 'highway' in tags:
            should_keep = True
        
        if tags.get('bridge') == 'yes':
            should_keep = True
            
        if tags.get('tunnel') == 'yes':
            should_keep = True
        
        # === FERROVIE E ROTAIE ===
        railway = tags.get('railway')
        if railway in ['rail', 'light_rail', 'subway', 'tram', 'monorail', 
                       'funicular', 'narrow_gauge', 'platform']:
            should_keep = True
        
        # === MOBILITÀ SOSTENIBILE ===
        if 'cycleway' in tags:
            should_keep = True
            
        if tags.get('bicycle') in ['yes', 'designated']:
            should_keep = True
        
        if 'footway' in tags:
            should_keep = True
            
        if 'pedestrian' in tags:
            should_keep = True
        
        # === TRASPORTO ACQUA ===
        if tags.get('route') == 'ferry':
            should_keep = True
        
        # === BARRIERE E PEDAGGI ===
        if tags.get('barrier') in ['toll_booth', 'gate', 'lift_gate', 'cycle_barrier']:
            should_keep = True
        
        # === ACCESSIBILITÀ ===
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            should_keep = True
        
        # === INFORMAZIONI TRAFFICO ===
        if 'maxspeed' in tags or 'lanes' in tags or 'oneway' in tags:
            should_keep = True
        
        if should_keep:
            self.ways_to_keep.add(w.id)
            # Add all nodes that compose this way
            for node_ref in self.way_nodes[w.id]:
                self.nodes_to_keep.add(node_ref)
    
    def area(self, a):
        tags = {tag.k: tag.v for tag in a.tags}
        should_keep = False
        
        # === TRASPORTO PUBBLICO ===
        if 'public_transport' in tags:
            should_keep = True
        
        railway = tags.get('railway')
        if railway in ['platform', 'station', 'halt', 'subway_entrance', 'tram_stop']:
            should_keep = True
        
        if tags.get('bus') == 'yes':
            should_keep = True
            
        if tags.get('trolleybus') == 'yes':
            should_keep = True
        
        # === AMENITIES ===
        amenity = tags.get('amenity')
        if amenity in ['bus_station', 'ferry_terminal', 'parking', 'parking_space',
                       'motorcycle_parking', 'bicycle_parking', 'bicycle_rental',
                       'bicycle_repair_station', 'charging_station', 'fuel',
                       'airport', 'helipad', 'marina', 'truck_stop', 'warehouse',
                       'toll_booth']:
            should_keep = True
        
        # === PARCHEGGI E SOSTA ===
        if tags.get('park_ride') == 'yes':
            should_keep = True
        
        if any(k.startswith('parking') for k in tags.keys()):
            should_keep = True
        
        # === AEROPORTI E AVIAZIONE ===
        if 'aeroway' in tags:
            should_keep = True
        
        # === TRASPORTO ACQUA ===
        if tags.get('waterway') == 'ferry':
            should_keep = True
            
        if tags.get('harbour') == 'yes':
            should_keep = True
        
        # === INTERSCAMBI E NODI ===
        highway = tags.get('highway')
        if highway in ['services', 'rest_area']:
            should_keep = True
        
        # === LOGISTICA E TRASPORTO MERCI ===
        if tags.get('landuse') == 'depot':
            should_keep = True
            
        if tags.get('railway') == 'depot':
            should_keep = True
        
        # === ACCESSIBILITÀ ===
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            should_keep = True
        
        if should_keep:
            # Areas are stored as ways in OSM
            # We need to add the way and its nodes
            # The from_way() gives us the underlying way
            if hasattr(a, 'orig_id'):
                way_id = a.orig_id()
                self.ways_to_keep.add(way_id)
                if way_id in self.way_nodes:
                    for node_ref in self.way_nodes[way_id]:
                        self.nodes_to_keep.add(node_ref)
    
    def relation(self, r):
        tags = {tag.k: tag.v for tag in r.tags}
        should_keep = False
        
        # Store relation members for later
        members = []
        for member in r.members:
            members.append((member.type, member.ref))
        self.relation_members[r.id] = members
        
        # === RESTRIZIONI E REGOLE ===
        rel_type = tags.get('type')
        if rel_type in ['restriction', 'route', 'route_master']:
            should_keep = True
        
        if 'restriction' in tags:
            should_keep = True
        
        # === ACCESSIBILITÀ ===
        if 'wheelchair' in tags or 'tactile_paving' in tags:
            should_keep = True
        
        if should_keep:
            self.relations_to_keep.add(r.id)
            # Add all members of this relation
            for member_type, member_ref in members:
                if member_type == 'n':
                    self.nodes_to_keep.add(member_ref)
                elif member_type == 'w':
                    self.ways_to_keep.add(member_ref)
                    # Also add nodes of this way
                    if member_ref in self.way_nodes:
                        for node_ref in self.way_nodes[member_ref]:
                            self.nodes_to_keep.add(node_ref)
                elif member_type == 'r':
                    self.relations_to_keep.add(member_ref)


class MobilityWriter(osmium.SimpleHandler):
    """
    Second pass: write only the elements we decided to keep
    """
    def __init__(self, writer, filter_handler):
        super().__init__()
        self.writer = writer
        self.filter = filter_handler
    
    def node(self, n):
        if n.id in self.filter.nodes_to_keep:
            self.writer.add_node(n)
    
    def way(self, w):
        if w.id in self.filter.ways_to_keep:
            self.writer.add_way(w)
    
    def relation(self, r):
        if r.id in self.filter.relations_to_keep:
            self.writer.add_relation(r)


def _show_file_sizes(input_file: str, output_file: str):
    """Show file sizes before and after filtering"""
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    reduction = ((original_size - filtered_size) / original_size) * 100
    print(f"\nFiltering completed:")
    print(f"  Original size:  {original_size:.2f} MB")
    print(f"  Filtered size:  {filtered_size:.2f} MB")
    print(f"  Size reduction: {reduction:.1f}%")


def filter_mobility_entities(input_file: str, output_file: str):
    """
    Filter OSM file to keep only mobility-related entities.
    
    Uses a two-pass approach:
    1. First pass: identify elements to keep and collect their dependencies
    2. Second pass: write only the selected elements
    
    This includes:
    - Road infrastructure (highways, bridges, tunnels)
    - Public transport (stations, stops, platforms)
    - Railways and rail infrastructure
    - Parking facilities
    - Sustainable mobility (bike lanes, pedestrian paths, charging stations)
    - Airports and aviation
    - Water transport (ferries, harbours)
    - Traffic control (signals, restrictions)
    - Barriers and tolls
    - Logistics and freight transport
    - Accessibility features
    
    All referenced nodes and ways are automatically included to maintain
    geometric integrity.
    """
    if verbose:
        print("Pass 1: Collecting elements and dependencies...")
    
    # First pass: collect what to keep
    filter_handler = MobilityFilter()
    filter_handler.apply_file(input_file, locations=True)
    
    if verbose:
        print(f"  Nodes to keep: {len(filter_handler.nodes_to_keep)}")
        print(f"  Ways to keep: {len(filter_handler.ways_to_keep)}")
        print(f"  Relations to keep: {len(filter_handler.relations_to_keep)}")
        print("\nPass 2: Writing filtered file...")
    
    # Second pass: write the filtered file
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    writer_handler = MobilityWriter(writer, filter_handler)
    writer_handler.apply_file(input_file, locations=True)
    writer.close()
    
    # Print stats
    if verbose:
        _show_file_sizes(input_file, output_file)


if __name__ == "__main__":
    # Configuration
    input_file = Path("data/input_service/bologna-area.osm.pbf")
    output_file = Path("data/input_service/bologna-area-filtered.osm.pbf")

    filter_mobility_entities(str(input_file), str(output_file))