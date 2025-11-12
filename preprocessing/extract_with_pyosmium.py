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
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


def _show_stats(n_objects: int, input_file: str, output_file: str):
    # N. elements
    i_i = 0
    for obj in osmium.FileProcessor(input_file):
        i_i = i_i+1  
    i_o = 0
    for obj in osmium.FileProcessor(output_file):
        i_o = i_o+1
    print(f"-> How many in the original file: {i_i}")
    print(f"   How many explicitly added: {n_objects}") 
    print(f"   How many in the output file: {i_o}")  

    # Sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original size: {original_size:.2f} MB")
    print(f"   New size: {filtered_size:.2f} MB")
    
class NodeWayInBbox(osmium.SimpleHandler):
    def __init__(self, bbox, writer):
        super().__init__()
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox
        self.writer = writer
        self.i = 0

    def node(self, n):
        if not n.location.valid():
            return
        lon, lat = n.location.lon, n.location.lat
        if self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat:
            self.writer.add_node(n)
            self.i += 1

    def way(self, w):
        nodes = [n for n in w.nodes if n.location.valid()]
        if any(self.min_lon <= n.location.lon <= self.max_lon and self.min_lat <= n.location.lat <= self.max_lat for n in nodes):
            self.writer.add_way(w)
            self.i += 1
            for n in nodes:
                if not (self.min_lon <= n.location.lon <= self.max_lon and self.min_lat <= n.location.lat <= self.max_lat for n in nodes):
                    self.writer.add_node(n)
                    self.i += 1
    
    def relation(self, r):
        return

def extract_bbox_with_pyosmium(bbox, input_file: str, output_file: str):
    # Create the writer
    writer = osmium.ForwardReferenceWriter(outfile=output_file, ref_src=input_file, overwrite=True, forward_relation_depth=0, back_references=False)

    # Nodes and Ways
    print(f"-> Getting nodes and ways \n and it's {datetime.now().strftime('%H:%M:%S')}")
    nw_handler = NodeWayInBbox(bbox, writer)
    nw_handler.apply_file(input_file)
    n_objects = nw_handler.i
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and finished")

    # Print info
    if verbose:
        _show_stats(n_objects, input_file, output_file)

class NodeWayInPolygon(osmium.SimpleHandler):
    def __init__(self, bbox, writer):
        super().__init__()
        self.polygon = polygon
        self.fab = osmium.geom.WKTFactory()
        self.writer = writer
        self.i = 0

    def node(self, n):
        if not n.location.valid():
            return
        wkt_point = fab.create_point(n.location)
        point = wkt.loads(wkt_point)
        if self.polygon.contains(point):
            self.writer.add_node(n)
            self.i += 1

    def way(self, w):
        wkt_line = fab.create_linestring(o.nodes)
        line = wkt.loads(wkt_line)
        if self.polygon.intersects(line):
            self.writer.add_way(w)
            self.i += 1
            for n in [n for n in w.nodes if n.location.valid()]:
                wkt_point = fab.create_point(n.location)
                point = wkt.loads(wkt_point)
                if not self.polygon.contains(point):
                    self.writer.add_node(n)
                    self.i += 1
    
    def relation(self, r):
        return
        
def extract_polygon_with_pyosmium(polygon, input_file: str, output_file: str):
    # Create the writer
    writer = osmium.ForwardReferenceWriter(outfile=output_file, ref_src=input_file, overwrite=True, forward_relation_depth=0, back_references=False)

    # Nodes and Ways
    print(f"-> Getting nodes ans ways \n and it's {datetime.now().strftime('%H:%M:%S')}")
    nw_handler = NodeWayInPolygon(polygon, writer)
    nw_handler.apply_file(input_file)
    n_objects = nw_handler.i
    writer.close()

    # Print info
    if verbose:
        _show_stats(n_objects, input_file, output_file)

# class RelationFilterHandler2(osmium.SimpleHandler):
#     def __init__(self, written_nodes, written_ways, writer=None):
#         super().__init__()
#         self.written_nodes = written_nodes
#         self.written_ways = written_ways
#         self.writer = writer
#         self.relation_map = {}        # relation_id -> osmium relation
#         self.children_map = {}        # relation_id -> set of parent IDs

#     def relation(self, r):
#         self.relation_map[r.id] = {
#             "id": r.id,
#             "members": [(m.type, m.ref, m.role) for m in r.members],
#             "tags": {t.k: t.v for t in r.tags}
#         }
#         for m in r.members:
#             if m.type == 'r':
#                 self.children_map.setdefault(m.ref, set()).add(r.id)

#     def write_relations(self):
#         # Set relazioni già scritte
#         written_relations = set()
#         queue = []

#         # aggiungi relazioni che hanno membri già inclusi
#         for rid, rdata in self.relation_map.items():
#             if any((t == 'n' and ref in self.written_nodes) or
#                    (t == 'w' and ref in self.written_ways)
#                    for t, ref, role in rdata["members"]):
#                 queue.append(rid)
#                 written_relations.add(rid)

#         # BFS sui parent relations
#         while queue:
#             rid = queue.pop(0)
#             rdata = self.relation_map[rid]
#             # Costruisci oggetto mutabile per scrittura
#             rel = osmium.osm.mutable.Relation(id=rdata["id"])
#             for t, ref, role in rdata["members"]:
#                 rel.members.append(osmium.osm.RelationMember(ref, t, role))
#             for k, v in rdata["tags"].items():
#                 rel.tags[k] = v
#             self.writer.add_relation(rel)

#             # aggiungi i genitori
#             for parent_id in self.children_map.get(rid, []):
#                 if parent_id not in written_relations:
#                     queue.append(parent_id)
#                     written_relations.add(parent_id)

# def extract_with_pyosmium2(bbox, input_file: str, output_file: str):
#     writer = osmium.SimpleWriter(output_file, overwrite=True)

#     # Nodes and Ways
#     print(f"-> Getting nodes ans ways \n and it's {datetime.now().strftime('%H:%M:%S')}")
#     nw_handler = NodeWayFilterHandler2(bbox, writer)
#     nw_handler.apply_file(input_file)

#     # Relations 
#     print(f"-> Getting relations\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     rel_handler = RelationFilterHandler2(written_nodes=nw_handler.written_nodes, written_ways=nw_handler.written_ways, writer=writer)
#     rel_handler.apply_file(input_file)
#     rel_handler.write_relations()

#     writer.close()

# class NodeFilterHandler(osmium.SimpleHandler):
#     def __init__(self, bbox, writer):
#         super().__init__()
#         self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox
#         self.nodes_inside = set() #set

#     def node(self, n):
#         if not n.location.valid():
#             return
#         lon, lat = n.location.lon, n.location.lat
#         if self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat:
#             self.nodes_inside.add(n.id)

# class WayFilterHandler(osmium.SimpleHandler):
#     def __init__(self, nodes_inside):
#         super().__init__()
#         self.nodes_inside = nodes_inside #set
#         self.ways_included = {} #dict
#         self.extra_nodes = set() #set

#     def way(self, w):
#         node_ids = [n.ref for n in w.nodes]
#         if any(nid in self.nodes_inside for nid in node_ids):
#             self.ways_included[w.id] = w
#             self.extra_nodes.update(node_ids)

# class ExtraNodeFilterHandler(osmium.SimpleHandler):
#     def __init__(self, nodes_inside, extra_nodes):
#         super().__init__()
#         self.nodes_included = nodes_inside.union(extra_nodes)
#         self.nodes_included_data = {}

#     def node(self, n):
#         if n.id in self.nodes_included:
#             self.nodes_included_data[n.id] = n

# class RelationFilterHandler(osmium.SimpleHandler):
#     def __init__(self, nodes_inside, ways_inside):
#         super().__init__()
#         self.nodes_included = nodes_inside #set
#         self.ways_included = ways_inside #dict
#         self.relations_included = {} #dict

#     def relation(self, r):
#         member_ids = [m.ref for m in r.members if m.type in ('n','w')]
#         if any(mid in self.nodes_included or mid in self.ways_included for mid in member_ids):
#             self.relations_included[r.id] = r

# class RelationCollector(osmium.SimpleHandler):
#     def __init__(self):
#         super().__init__()
#         self.relation_map = {}

#     def relation(self, r):
#         self.relation_map[r.id] = r

# def _include_parent_relations_nodes_ways(included_nodes, included_ways, included_relations, relation_map):
#     extra_relations = {}
#     new_relations = True
#     while new_relations:
#         new_relations = False
#         for r in relation_map.values():
#             if r.id in included_relations:
#                 continue
#             for m in r.members:
#                 if (m.type == "n" and m.ref in included_nodes) or (m.type == "w" and m.ref in included_ways) or (m.type == "r" and m.ref in included_relations):
#                     extra_relations[r.id] = r
#                     new_relations = True
#     return extra_relations

# def _include_parent_relations(included_relations, relation_map):
#     extra_relations = {}
#     new_relations = True
#     while new_relations:
#         new_relations = False
#         for r in relation_map.values():
#             if r.id in included_relations:
#                 continue
#             for m in r.members:
#                 if (m.type == "r" and m.ref in included_relations):
#                     extra_relations[r.id] = r
#                     new_relations = True
#     return extra_relations


# def extract_with_pyosmium(bbox, input_file: str, output_file: str):
#     # Process the dataset to get which entities to keep
#     # Get nodes
#     print(f"-> Getting nodes\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     node_handler = NodeFilterHandler(bbox)
#     node_handler.apply_file(input_file)
#     print(f"Nodi dentro poligono: {len(node_handler.nodes_inside)}")
    
#     # Get ways
#     print(f"-> Getting ways\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     way_handler = WayFilterHandler(nodes_inside=node_handler.nodes_inside)
#     way_handler.apply_file(input_file)
#     print(f"Ways dentro regione: {len(way_handler.ways_included)}")
#     print(f"Nodi aggiuntivi necessari: {len(way_handler.extra_nodes)}")

#     # Get all nodes
#     print(f"-> Getting ALL nodes\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     extra_node_handler = ExtraNodeFilterHandler(node_handler.nodes_inside, way_handler.extra_nodes)
#     extra_node_handler.apply_file(input_file)
#     print(f"Nodi da tenere: {len(extra_node_handler.nodes_included)}")
    
#     # Get relations
#     print(f"-> Getting relations\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     relation_handler = RelationFilterHandler(extra_node_handler.nodes_included, set(way_handler.ways_included))
#     relation_handler.apply_file(input_file)
#     print(f"Relazioni selezionate: {len(relation_handler.relations_included)}")
    
#     # Update relations with their parents
#     print(f"-> Getting ALL relations\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     relation_map_handler = RelationCollector()
#     relation_map_handler.apply_file(input_file)
#     extra_relations = _include_parent_relations(extra_node_handler.nodes_included, set(way_handler.ways_included), set(relation_handler.relations_included), relation_map_handler.relation_map)
    
#     # Write the dataset to be returned
#     print(f"-> Writing file, finally\n and it's {datetime.now().strftime('%H:%M:%S')}")
#     writer = osmium.SimpleWriter(output_file)
#     # Add nodes
#     for nid in extra_node_handler.nodes_included:
#         writer.add_node(extra_node_handler.nodes_included_data[nid])
#     # Add ways
#     for w in way_handler.ways_included.values():
#         writer.add_way(w)
#     # Add relations
#     for r in relation_handler.relations_included.values():
#         writer.add_relation(r)
#     for r in extra_relations:
#         writer.add_relation(r)
#     writer.close()

#     print(f"Finished, finally\n and it's {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    data_folder = "./data/input_service"
    input_file = f"{data_folder}/nord-est-latest.osm.pbf"
    output_file = f"{data_folder}/bologna-area.osm.pbf"
    
    polygon_file = f"{data_folder}/area_verde_manual_v1.geojson"
    polygon = geopandas.read_file(polygon_file).geometry.iloc[0]
    print(polygon)
    bbox = [10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926]
    extract_bbox_with_pyosmium(bbox, input_file, output_file)

    #extract_polygon_with_pyosmium(polygon, input_file, output_file)