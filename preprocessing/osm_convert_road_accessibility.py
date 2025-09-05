"""
Script per aggiungere restrizioni anti-auto a tutte le highway in un file OSM
Blocca solo auto private e moto, permette bus, bici, pedoni, servizi di emergenza

Richiede: pip install osmium
Uso: python osm_road_accessibility_convert.py input.osm.pbf output.osm.pbf
"""

import osmium
import sys

class CarRestrictionHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer
        self.highways_modified = 0

    def way(self, w):
        if 'highway' in w.tags:
            # Crea dizionario con i tag originali
            tags = dict(w.tags)
            
            # MANTIENE il tipo highway originale (primary, secondary, etc.)
            # Aggiunge solo restrizioni per auto e moto
            tags['motorcar'] = 'no'      # Blocca auto private
            tags['motorcycle'] = 'no'    # Blocca moto/scooter
            
            # Permessi espliciti per altri utenti (opzionale ma più chiaro)
            if 'foot' not in tags:
                tags['foot'] = 'yes'     # Pedoni sempre permessi
            if 'bicycle' not in tags:
                tags['bicycle'] = 'yes'  # Bici sempre permesse
            # bus, psv, emergency sono permessi di default
            
            # Rimuovi solo tag specifici per auto che non hanno più senso
            tags_to_remove = [
                # Velocità auto
                'maxspeed', 'maxspeed:forward', 'maxspeed:backward', 'minspeed',
                # Corsie auto
                'lanes', 'lanes:forward', 'lanes:backward', 
                'turn:lanes', 'turn:lanes:forward', 'turn:lanes:backward',
                # Parcheggio auto
                'parking:lane', 'parking:lane:left', 'parking:lane:right',
                'parking:both', 'parking:left', 'parking:right',
                # Servizio auto (ma mantieni highway type!)
                'service'  # Solo se è service road, non highway type
            ]
            
            # Rimuovi tag inappropriati solo se esistono
            for tag in tags_to_remove:
                if tag in tags:
                    del tags[tag]
            
            # MANTIENI tag utili:
            # - ref (numero strada)
            # - name (nome strada) 
            # - surface, width (utili per pedoni/bici)
            # - oneway (può essere utile anche per bici)
            # - cycleway, sidewalk (ancora rilevanti)
            
            # Crea la nuova way con restrizioni
            new_way = w.replace(tags=tags)
            self.writer.add_way(new_way)
            self.highways_modified += 1
            
            if self.highways_modified % 1000 == 0:
                print(f"Modificate {self.highways_modified} highway...")
        else:
            # Mantieni way senza highway
            self.writer.add_way(w)

    def node(self, n):
        self.writer.add_node(n)

    def relation(self, r):
        self.writer.add_relation(r)

def add_car_restrictions(input_file, output_file):
    print(f"Aggiunta restrizioni anti-auto da {input_file} a {output_file}...")
    
    try:
        with osmium.SimpleWriter(output_file, overwrite=True) as writer:
            handler = CarRestrictionHandler(writer)
            handler.apply_file(input_file)
            
        print(f"✓ Conversione completata! {handler.highways_modified} highway modificate con restrizioni anti-auto.")
        print("✓ Permessi: pedoni, biciclette, bus, taxi, servizi emergenza")
        print("✗ Bloccati: auto private, moto/scooter")
        
    except Exception as e:
        print(f"✗ Errore durante la conversione: {e}")
        return False
    
    return True

def test_conversion(input_file):
    """Test veloce per verificare che il file sia leggibile"""
    print("Test di lettura del file di input...")
    try:
        count = 0
        highway_count = 0
        
        class TestHandler(osmium.SimpleHandler):
            def __init__(self):
                osmium.SimpleHandler.__init__(self)
                self.max_ways = 100
                
            def way(self, w):
                nonlocal count, highway_count
                count += 1
                if 'highway' in w.tags:
                    highway_count += 1
                    # Mostra esempio di highway trovato
                    if highway_count <= 3:
                        print(f"  Esempio highway: {w.tags.get('highway')} - {w.tags.get('name', 'senza nome')}")
                # Ferma dopo 100 way per il test
                if count >= self.max_ways:
                    return
        
        handler = TestHandler()
        handler.apply_file(input_file)
        
        print(f"✓ File leggibile. Nelle prime {count} way: {highway_count} hanno tag highway")
        return True
        
    except Exception as e:
        print(f"✗ Errore nella lettura: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python osm_road_accessibility_convert.py input.osm.pbf output.osm.pbf")
        print("Esempio: python osm_road_accessibility_convert.py city.osm.pbf city_no_cars.osm.pbf")
        print("\nQuesto script:")
        print("- MANTIENE i tipi highway originali (primary, residential, etc.)")
        print("- BLOCCA solo auto private e moto")  
        print("- PERMETTE pedoni, bici, bus, taxi, emergenze")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Test preliminare
    if not test_conversion(input_file):
        sys.exit(1)
    
    # Conversione vera e propria
    if add_car_restrictions(input_file, output_file):
        print(f"\n✓ File con restrizioni anti-auto salvato come: {output_file}")
    else:
        sys.exit(1)