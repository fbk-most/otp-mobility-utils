import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose

class Collector(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.ways = []
        self.relations = []
    
    def node(self, n):
        # Memorizza i dati essenziali invece dell'oggetto
        self.nodes.append({
            'id': n.id,
            'location': (n.location.lon, n.location.lat) if n.location.valid() else None,
            'tags': dict(n.tags),
            'version': n.version,
            'timestamp': n.timestamp,
            'changeset': n.changeset,
            'uid': n.uid,
            'user': n.user
        })
    
    def way(self, w):
        self.ways.append({
            'id': w.id,
            'nodes': [n.ref for n in w.nodes],
            'tags': dict(w.tags),
            'version': w.version,
            'timestamp': w.timestamp,
            'changeset': w.changeset,
            'uid': w.uid,
            'user': w.user
        })
    
    def relation(self, r):
        self.relations.append({
            'id': r.id,
            'members': [(m.type, m.ref, m.role) for m in r.members],
            'tags': dict(r.tags),
            'version': r.version,
            'timestamp': r.timestamp,
            'changeset': r.changeset,
            'uid': r.uid,
            'user': r.user
        })

def _deduplicate(entities):
    seen = set()
    unique = []
    for e in entities:
        if e['id'] not in seen:
            seen.add(e['id'])
            unique.append(e)
    return unique

def sort_entities(input_file: str, output_file: str):
    # Collect all the elements
    collector = Collector()
    collector.apply_file(input_file, locations=True)
    
    # Reorder
    collector.nodes.sort(key=lambda n: n['id'])
    collector.ways.sort(key=lambda w: w['id'])
    collector.relations.sort(key=lambda r: r['id'])
    
    # Remove duplicates
    unique_nodes = _deduplicate(collector.nodes)
    unique_ways = _deduplicate(collector.ways)
    unique_relations = _deduplicate(collector.relations)
    
    # Write output ordered
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    
    for n in unique_nodes:
        if n['location']:
            writer.add_node(osmium.osm.mutable.Node(
                id=n['id'],
                location=n['location'],
                tags=n['tags'],
                version=n['version'],
                timestamp=n['timestamp'],
                changeset=n['changeset'],
                uid=n['uid'],
                user=n['user']
            ))
    
    for w in unique_ways:
        writer.add_way(osmium.osm.mutable.Way(
            id=w['id'],
            nodes=w['nodes'],
            tags=w['tags'],
            version=w['version'],
            timestamp=w['timestamp'],
            changeset=w['changeset'],
            uid=w['uid'],
            user=w['user']
        ))
    
    for r in unique_relations:
        writer.add_relation(osmium.osm.mutable.Relation(
            id=r['id'],
            members=r['members'],
            tags=r['tags'],
            version=r['version'],
            timestamp=r['timestamp'],
            changeset=r['changeset'],
            uid=r['uid'],
            user=r['user']
        ))
    
    writer.close()
    
    if verbose:
        print(f"Original entities: {len(collector.nodes)} nodes, {len(collector.ways)} ways, {len(collector.relations)} relations")
        print(f"After removing duplicates: {len(unique_nodes)} nodes, {len(unique_ways)} ways, {len(unique_relations)} relations")
        original_size = Path(input_file).stat().st_size / (1024 * 1024)
        filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
        print(f"Original size: {original_size:.2f} MB → New size: {filtered_size:.2f} MB")



if __name__ == "__main__":
    input_path = Path("data/input_service/bologna-area-filtered-parking.osm.pbf")
    output_path = Path("data/input_service/bologna-area-filtered-parking-sorted.osm.pbf")
    sort_entities(str(input_path), str(output_path))