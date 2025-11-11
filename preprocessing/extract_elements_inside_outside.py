import osmium
import shapely.geometry as geom
import json
import sys
import os
from pathlib import Path
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


class PolygonInFilterHandler(osmium.SimpleHandler):
    def __init__(self, polygon, writer):
        super().__init__()
        self.polygon = polygon
        self.writer = writer

    def node(self, n):
        point = geom.Point(n.location.lon, n.location.lat)
        if self.polygon.contains(point):
            self.writer.add_node(n)

    def way(self, w):
        coords = [(n.lon, n.lat) for n in w.nodes if n.location.valid()]
        line = geom.LineString(coords)
        if self.polygon.intersects(line):
            self.writer.add_way(w)

    def relation(self, r):
        # (opzionale: gestisci relazioni se necessario)
        self.writer.add_relation(r)

class PolygonOutFilterHandler(osmium.SimpleHandler):
    def __init__(self, polygon, writer):
        super().__init__()
        self.polygon = polygon
        self.writer = writer

    def node(self, n):
        point = geom.Point(n.location.lon, n.location.lat)
        if not self.polygon.contains(point):
            self.writer.add_node(n)

    def way(self, w):
        coords = [(n.lon, n.lat) for n in w.nodes if n.location.valid()]
        line = geom.LineString(coords)
        if not self.polygon.intersects(line):
            self.writer.add_way(w)

    def relation(self, r):
        self.writer.add_relation(r)

def _show_file_sizes(input_file: str, output_file: str):
    # Show file sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")

def extract_elements_inside(polygon_geojson: str, input_pbf: str, output_pbf: str):
    # Load polygon GeoJSON
    with open(polygon_geojson, 'r') as f:
        geo = json.load(f)
    polygon = geom.shape(geo['features'][0]['geometry'])
    
    # Writer OSM
    writer = osmium.SimpleWriter(output_pbf, overwrite=True)
    
    # Handler
    handler = PolygonInFilterHandler(polygon, writer)
    handler.apply_file(input_pbf)
    writer.close()

    if verbose:
        _show_file_sizes(input_pbf, output_pbf)

def extract_elements_outside(polygon_geojson: str, input_pbf: str, output_pbf: str):
    # Load polygon GeoJSON
    with open(polygon_geojson, 'r') as f:
        geo = json.load(f)
    polygon = geom.shape(geo['features'][0]['geometry'])
    
    # Writer OSM
    writer = osmium.SimpleWriter(output_pbf, overwrite=True)
    
    # Handler
    handler = PolygonOutFilterHandler(polygon, writer)
    handler.apply_file(input_pbf)
    writer.close()

    if verbose:
        _show_file_sizes(input_pbf, output_pbf)


if __name__ == "__main__":
    # Configure input and output files
    polygon_geojson = "data/input_service/small_area_verde_manual_v1.geojson"
    input_pbf = "data/input_service/bologna-area-filtered-parking-sorted.osm.pbf"
    output_in_pbf = "data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf"
    output_out_pbf = "data/input_service/bologna-area-filtered-parking-outside-AV.osm.pbf"

    extract_elements_inside(polygon_geojson, input_pbf, output_in_pbf)
    extract_elements_outside(polygon_geojson, input_pbf, output_out_pbf)