"""
Tentative implementation of the extract function from osmium-tool. 

Taken from the osmium-tool documentation: 'Strategy complete_ways: Runs in two passes. The extract will contain all nodes inside the region and all ways referencing those nodes as well as all nodes referenced by those ways. The extract will also contain all relations referenced by nodes inside the region or ways already included and, recursively, their parent relations. The ways are reference-complete, but the relations are not.'
https://docs.osmcode.org/osmium/latest/osmium-extract.html

Here, we define a class of the type `ForwardReferenceWriter`, which not only writes the objects which are explicitely asked to be written, but also those objects referencing to them.

Then, we define a handler class of type `SimpleHandler`, initialized with the writer and a bbox. It reads the input file and adds nodes inside of the bbox, ways containing nodes inside the bbox and their additional nodes. 

We finally define the main function of the code, extract_with_pyosmium, that generates the writer, call the handler, and then close the writer. In this way, the file with the required data is saved.
"""

import osmium
import geopandas
from shapely import wkt
from pathlib import Path
from datetime import datetime
from shapely.geometry import Point

import sys
import os
from back_way_forward_reference_writer import BackWayForwardReferenceWriter
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


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
    
def _show_stats(n_objects, input_file: str, output_file: str):
    # N. elements
    i_in, i_iw, i_ir = _count_elements(input_file)
    i_on, i_ow, i_or = _count_elements(output_file)
    print(f"-> How many in the original file: {i_in} nodes, {i_iw} ways, {i_ir} relations")
    print(f"   How many explicitly added: {n_objects[0]} nodes, {n_objects[1]} ways, {n_objects[2]} relations") 
    print(f"   How many in the output file: {i_on} nodes, {i_ow} ways, {i_or} relations")  

    # Sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original size: {original_size:.2f} MB")
    print(f"   New size: {filtered_size:.2f} MB")


class ExtractInBbox(osmium.SimpleHandler):
    def __init__(self, bbox, writer):
        super().__init__()
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox
        self.writer = writer
        self.id_tracker = osmium.IdTracker()
        self.n_nodes = 0
        self.n_ways = 0
        self.n_relations = 0

    def node(self, n):
        if not n.location.valid():
            return
        lon, lat = n.location.lon, n.location.lat
        if self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat:
            self.writer.add_node(n)
            self.n_nodes += 1
            self.id_tracker.add_node(n.id)

    def way(self, w):
        if self.id_tracker.contains_any_references(w):
            self.writer.add_way(w)
            self.n_ways += 1
            self.id_tracker.add_way(w.id)
    
    def relation(self, r):
        if self.id_tracker.contains_any_references(r):
            self.writer.add_relation(r)
            self.n_relations += 1


def extract_bbox_with_pyosmium(bbox, input_file: str, output_file: str):
    # Create the writer
    writer = BackWayForwardReferenceWriter(
        outfile=output_file, ref_src=input_file, 
        overwrite=True,
        forward_relation_depth=5, backward_relation_depth=1
    )

    # Nodes and Ways
    print(f"-> Getting elems \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
    handler = ExtractInBbox(bbox, writer)
    handler.apply_file(input_file)
    n_objects = [handler.n_nodes, handler.n_ways, handler.n_relations]
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

    # Print info
    if verbose:
        _show_stats(n_objects, input_file, output_file)


class ExtractInPolygon(osmium.SimpleHandler):
    def __init__(self, polygon, writer):
        super().__init__()
        self.polygon = polygon
        self.fab = osmium.geom.WKTFactory()
        self.writer = writer
        self.id_tracker = osmium.IdTracker()
        self.n_nodes = 0
        self.n_ways = 0
        self.n_relations = 0

    def node(self, n):
        if not n.location.valid():
            return
        wkt_point = self.fab.create_point(n.location)
        point = wkt.loads(wkt_point)
        if self.polygon.contains(point):
            self.writer.add_node(n)
            self.n_nodes += 1
            self.id_tracker.add_node(n.id)

    def way(self, w):
        if self.id_tracker.contains_any_references(w):
            self.writer.add_way(w)
            self.n_ways += 1
            self.id_tracker.add_way(w.id)
    
    def relation(self, r):
        if self.id_tracker.contains_any_references(r):
            self.writer.add_relation(r)
            self.n_relations += 1
        
def extract_polygon_with_pyosmium(polygon_file, input_file: str, output_file: str):
    # Create the writer
    writer = BackWayForwardReferenceWriter(
        outfile=output_file, ref_src=input_file, 
        overwrite=True,
        forward_relation_depth=5, backward_relation_depth=1
    )

    # Read the polygon 
    polygon = geopandas.read_file(polygon_file).geometry.iloc[0]

    # Nodes and Ways
    print(f"-> Getting elements \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
    handler = ExtractInPolygon(polygon, writer)
    handler.apply_file(input_file)
    n_objects = [handler.n_nodes, handler.n_ways, handler.n_relations]
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

    # Print info
    if verbose:
        _show_stats(n_objects, input_file, output_file)

 
def extract_polygon_with_pyosmium_no(polygon_file, input_file: str, output_file: str):
    # Create the writer
    writer = BackWayForwardReferenceWriter(
        outfile=output_file, ref_src=input_file, 
        overwrite=True,
        forward_relation_depth=5, backward_relation_depth=1
    )

    # Read the polygon 
    polygon = geopandas.read_file(polygon_file).geometry.iloc[0]

    # Read the input file -> with geointerfacefilter
    fp = (
        osmium.FileProcessor(input_file)
        .with_locations()
        .with_filter(osmium.filter.GeoInterfaceFilter())
    )

    # Iterate: read and write
    fab = osmium.geom.WKTFactory()
    n_nodes, n_ways, n_relations = 0,0,0
    id_tracker = osmium.IdTracker()
    for o in fp:
        if o.is_node():
            wkt_point = fab.create_point(o.location)
            point = wkt.loads(wkt_point)
            if polygon.contains(point):
                writer.add_node(o)
                n_nodes += 1
                id_tracker.add_node(o.id)
        if o.is_way():
            if id_tracker.contains_any_references(o):
                writer.add_way(o)
                n_ways += 1
                id_tracker.add_way(o.id)
        if o.is_relation():
            if id_tracker.contains_any_references(o):
                writer.add_relation(o)
                n_relations += 1
    writer.close()

    if verbose:
        _show_stats([n_nodes, n_ways, n_relations], input_file, output_file)



if __name__ == "__main__":
    input_file = "./data/input_service/nord-est-latest.osm.pbf"
    output_file = "./data/input_service/bologna-area.osm.pbf"
    bbox = [10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926]
    #extract_bbox_with_pyosmium(bbox, input_file, output_file)
    
    input_file = "./data/input_service/bologna-area-filtered-parking.osm.pbf"
    output_file = "./data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf"
    polygon_file = f"./data/input_service/small_area_verde_manual_v1.geojson"

    extract_polygon_with_pyosmium(polygon_file, input_file, output_file)