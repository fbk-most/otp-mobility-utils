#!/usr/bin/env python3
import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


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
        """
        Processa i tag di un elemento e modifica park_ride se necessario.
        
        Args:
            tags: I tag dell'elemento OSM
            
        Returns:
            dict: I tag modificati
        """
        tag_dict = {tag.k: tag.v for tag in tags}
        
        # Verifica se è un parcheggio
        amenity = tag_dict.get('amenity')
        if amenity in self.parking_amenities:
            self.total_parking_count += 1
            
            # Controlla il tag park_ride attuale
            current_park_ride = tag_dict.get('park_ride', '')
            
            # Se non ha park_ride o è settato a 'no', lo impostiamo a 'yes'
            if not current_park_ride or current_park_ride.lower() == 'no':
                tag_dict['park_ride'] = 'yes'
                self.modified_count += 1
                #print(f"Modificato elemento con amenity={amenity}: park_ride -> yes")
        
        return tag_dict
    
    def node(self, n):
        """Processa i nodi."""
        modified_tags = self.process_tags(n.tags)
        
        # Crea un nuovo nodo con i tag modificati
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
        """Processa le way."""
        modified_tags = self.process_tags(w.tags)
        
        # Crea una nuova way con i tag modificati
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
        """Processa le relazioni."""
        modified_tags = self.process_tags(r.tags)
        
        # Crea una nuova relazione con i tag modificati
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
    print(f"N. parkings found: {handler.total_parking_count}")
    print(f"N. parkings modified: {handler.modified_count}")
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → New size: {filtered_size:.2f} MB")

def add_parkrides(input_file: str, output_file: str):
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    handler = ParkingHandler(writer)
    handler.apply_file(input_file)
    writer.close()
    if verbose:
        _show_final_stats(handler, input_file, output_file)


if __name__ == "__main__":
    
    # Configuration
    input_file = "data/input_service/bologna-area-filtered.osm.pbf"
    output_file = "data/input_service/bologna-area-filtered-parking.osm.pbf"

    add_parkrides(input_file, output_file)