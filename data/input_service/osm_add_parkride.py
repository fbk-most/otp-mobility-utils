#!/usr/bin/env python3
"""
Script per modificare un file OSM.pbf aggiungendo park_ride=yes a tutti i parcheggi.

Questo script prende un file OSM.pbf e modifica tutti gli elementi con:
- amenity=parking
- amenity=parking_entrance
- amenity=parking_space
- amenity=motorcycle_parking

E imposta il tag park_ride=yes per tutti questi elementi.
"""

import osmium
import sys
import os


class ParkingHandler(osmium.SimpleHandler):
    """
    Handler per processare gli elementi OSM e modificare i tag dei parcheggi.
    """
    
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
                print(f"Modificato elemento con amenity={amenity}: park_ride -> yes")
        
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


def main():
    """Funzione principale."""
    input_file = "bologna-area-filtered-outside-AV.osm.pbf"
    output_file = "bologna-area-filtered-outside-AV-parking.osm.pbf"
    
    # Verifica che il file di input esista
    if not os.path.exists(input_file):
        print(f"ERRORE: File di input '{input_file}' non trovato!")
        print("Assicurati che il file sia nella stessa cartella dello script.")
        sys.exit(1)
    
    print(f"Inizio elaborazione di: {input_file}")
    print(f"File di output: {output_file}")
    print("-" * 50)
    
    try:
        # Crea il writer per il file di output
        writer = osmium.SimpleWriter(output_file)
        
        # Crea l'handler
        handler = ParkingHandler(writer)
        
        # Processa il file
        handler.apply_file(input_file)
        
        # Chiude il writer
        writer.close()
        
        # Statistiche finali
        print("-" * 50)
        print(f"Elaborazione completata!")
        print(f"Parcheggi totali trovati: {handler.total_parking_count}")
        print(f"Parcheggi modificati: {handler.modified_count}")
        print(f"File salvato come: {output_file}")
        
        # Verifica dimensione dei file
        input_size = os.path.getsize(input_file) / (1024*1024)  # MB
        output_size = os.path.getsize(output_file) / (1024*1024)  # MB
        print(f"Dimensione file input: {input_size:.2f} MB")
        print(f"Dimensione file output: {output_size:.2f} MB")
        
    except Exception as e:
        print(f"ERRORE durante l'elaborazione: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()