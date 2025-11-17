import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


FILTERS = {
    "w": [
        ("highway", None),
        ("bridge", "yes"),
        ("tunnel", "yes"),
        ("railway", "rail"),
        ("railway", "light_rail"),
        ("railway", "subway"),
        ("railway", "tram"),
        ("railway", "monorail"),
        ("railway", "funicular"),
        ("railway", "narrow_gauge"),
        ("cycleway", None),
        ("bicycle", "yes"),
        ("bicycle", "designated"),
        ("footway", None),
        ("pedestrian", None),
        ("route", "ferry"),
    ],
    "n": [
        ("highway", "traffic_signals"),
        ("highway", "stop"),
        ("highway", "give_way"),
        ("railway", "level_crossing"),
    ],
    "wa": [
        ("public_transport", None),
        ("railway", "platform"),
        ("railway", "station"),
        ("railway", "halt"),
        ("railway", "subway_entrance"),
        ("railway", "tram_stop"),
        ("bus", "yes"),
        ("trolleybus", "yes"),
        ("amenity", "bus_station"),
        ("amenity", "ferry_terminal"),
        ("amenity", "parking"),
        ("amenity", "parking_space"),
        ("amenity", "motorcycle_parking"),
        ("amenity", "bicycle_parking"),
        ("park_ride", "yes"),
        ("parking", "*"),
        ("parking:fee", "*"),
        ("amenity", "bicycle_rental"),
        ("amenity", "bicycle_repair_station"),
        ("amenity", "charging_station"),
        ("amenity", "fuel"),
        ("aeroway", None),
        ("amenity", "airport"),
        ("amenity", "helipad"),
        ("waterway", "ferry"),
        ("harbour", "yes"),
        ("amenity", "marina"),
        ("amenity", "truck_stop"),
        ("landuse", "depot"),
        ("railway", "depot"),
        ("amenity", "warehouse"),
        ("highway", "services"),
        ("highway", "rest_area"),
    ],
    "nw": [
        ("barrier", "toll_booth"),
        ("barrier", "gate"),
        ("barrier", "lift_gate"),
        ("barrier", "cycle_barrier"),
        ("amenity", "toll_booth"),
    ],
    "nwr": [
        ("wheelchair", "*"),
        ("tactile_paving", "*"),
        ("maxspeed", "*"),
        ("lanes", "*"),
        ("oneway", "*"),
    ],
    "r": [
        ("type", "restriction"),
        ("type", "route"),
        ("type", "route_master"),
        ("restriction", "*"),
    ]
}

# Funzione per verificare se un tag corrisponde a un filtro
def matches_filter(tags, filter_list):
    for key, value in filter_list:
        if key in tags:
            if value is None:      # valore esatto
                return True
            if value == '*':       # wildcard: qualsiasi valore presente
                return True
            if tags[key] == value:
                return True
    return False

class MobilityFilter(osmium.SimpleHandler):
    def __init__(self, writer):
        super().__init__()
        self.writer = writer
        self.included_ids = set() 

    def add_unique(self, obj):
        if obj.id not in self.included_ids:
            self.included_ids.add(obj.id)
            if isinstance(obj, osmium.osm.Node):
                self.writer.add_node(obj)
            elif isinstance(obj, osmium.osm.Way):
                self.writer.add_way(obj)
            elif isinstance(obj, osmium.osm.Relation):
                self.writer.add_relation(obj)

    def node(self, n):
        if matches_filter(n.tags, FILTERS["n"]) \
           or matches_filter(n.tags, FILTERS["nw"]) \
           or matches_filter(n.tags, FILTERS["nwr"]):
            self.add_unique(n)

    def way(self, w):
        if matches_filter(w.tags, FILTERS["w"]) \
           or matches_filter(w.tags, FILTERS["wa"]) \
           or matches_filter(w.tags, FILTERS["nw"]) \
           or matches_filter(w.tags, FILTERS["nwr"]):
            self.add_unique(w)

    def relation(self, r):
        if matches_filter(r.tags, FILTERS["r"]) \
           or matches_filter(r.tags, FILTERS["nwr"]):
            self.add_unique(r)

def _show_file_sizes(input_file: str, output_file: str):
    # Show file sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")

def filter_mobility_entities(input_file: str, output_file: str):
    # Initialize the writer
    writer = osmium.BackSimpleWriter(output_file, overwrite=True)

    # Perform the filtering
    handler = MobilityFilter(writer)
    handler.apply_file(input_file, locations=True)
    writer.close()

    # Print stats
    if verbose:
        _show_file_sizes(input_file, output_file)

if __name__ == "__main__":
    # Configuration
    input_file = "data/input_service/bologna-area.osm.pbf"
    output_file = "data/input_service/bologna-area-filtered.osm.pbf"

    filter_mobility_entities(str(input_file), str(output_file))