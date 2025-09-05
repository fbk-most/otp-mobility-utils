#!/usr/bin/env python3
"""
Script per creare la differenza tra due file OSM PBF
Mantiene tutti gli elementi che sono nel primo file ma non nel secondo
"""

import osmium
import sys

# Primo passo: raccogli gli ID di tutti gli elementi nel file "inside"
inside_node_ids = set()
inside_way_ids = set()
inside_relation_ids = set()

class IDCollector(osmium.SimpleHandler):
    def node(self, n):
        inside_node_ids.add(n.id)
        
    def way(self, w):
        inside_way_ids.add(w.id)
        
    def relation(self, r):
        inside_relation_ids.add(r.id)

print("Raccogliendo ID degli elementi dentro l'area...")
osmium.apply(osmium.io.Reader('data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf'), IDCollector())
print(f"Trovati {len(inside_node_ids)} nodi, {len(inside_way_ids)} way, {len(inside_relation_ids)} relation dentro l'area")

# Secondo passo: scrivi solo gli elementi che NON sono nel set
class DiffWriter(osmium.SimpleHandler):
    def __init__(self, inside_nodes, inside_ways, inside_relations, writer):
        super().__init__()
        self.inside_nodes = inside_nodes
        self.inside_ways = inside_ways
        self.inside_relations = inside_relations
        self.writer = writer
        self.nodes_outside = 0
        self.ways_outside = 0
        self.relations_outside = 0
        
    def node(self, n):
        # Scrivi solo i nodi che NON sono nell'area
        if n.id not in self.inside_nodes:
            self.writer.add_node(n)
            self.nodes_outside += 1
            
    def way(self, w):
        # Scrivi solo le way che NON sono nell'area
        if w.id not in self.inside_ways:
            self.writer.add_way(w)
            self.ways_outside += 1
            
    def relation(self, r):
        # Scrivi solo le relation che NON sono nell'area
        if r.id not in self.inside_relations:
            self.writer.add_relation(r)
            self.relations_outside += 1

print("Creando file con elementi fuori dall'area...")
writer = osmium.SimpleWriter('data/input_service/bologna-area-filtered-parking-outside-AV.osm.pbf')
diff_handler = DiffWriter(inside_node_ids, inside_way_ids, inside_relation_ids, writer)
osmium.apply(osmium.io.Reader('data/input_service/bologna-area-filtered-parking-sorted.osm.pbf'), diff_handler)
writer.close()

print(f"Completato! Scritti {diff_handler.nodes_outside} nodi, {diff_handler.ways_outside} way, {diff_handler.relations_outside} relation")