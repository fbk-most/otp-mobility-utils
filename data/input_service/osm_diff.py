#!/usr/bin/env python3
"""
Script per creare la differenza tra due file OSM PBF
Mantiene le strade che sono nel primo file ma non nel secondo
"""

import osmium
import sys

# Primo passo: raccogli gli ID delle way nel file "inside"
inside_way_ids = set()

class IDCollector(osmium.SimpleHandler):
    def way(self, w):
        inside_way_ids.add(w.id)

print("Raccogliendo ID delle way dentro l'area...")
osmium.apply(osmium.io.Reader('bologna-highway-inside-AV.osm.pbf'), IDCollector())
print(f"Trovate {len(inside_way_ids)} way dentro l'area")

# Secondo passo: scrivi solo le way che NON sono nel set
class DiffWriter(osmium.SimpleHandler):
    def __init__(self, inside_ids, writer):
        super().__init__()
        self.inside_ids = inside_ids
        self.writer = writer
        self.nodes_written = set()
        self.ways_outside = 0
        
    def node(self, n):
        # Scrivi tutti i nodi (verranno referenziati dalle way)
        if n.id not in self.nodes_written:
            self.writer.add_node(n)
            self.nodes_written.add(n.id)
            
    def way(self, w):
        # Scrivi solo le way che NON sono nell'area
        if w.id not in self.inside_ids:
            self.writer.add_way(w)
            self.ways_outside += 1

print("Creando file con strade fuori dall'area...")
writer = osmium.SimpleWriter('bologna-highway-outside-AV.osm.pbf')
diff_handler = DiffWriter(inside_way_ids, writer)
osmium.apply(osmium.io.Reader('bologna-highways.osm.pbf'), diff_handler)
writer.close()

print(f"Completato! {diff_handler.ways_outside} way scritte nel file di output")
print("File creato: bologna-highway-outside-AV.osm.pbf")