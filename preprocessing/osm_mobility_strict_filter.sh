
#!/bin/bash

# Script per filtrare solo le strade principali da un file OSM.PBF

echo "Filtraggio strade principali in corso..."

osmium tags-filter bologna-area.osm.pbf \
    \
    `# === STRADE PRINCIPALI ===` \
    w/highway=motorway \
    w/highway=motorway_link \
    w/highway=trunk \
    w/highway=trunk_link \
    w/highway=primary \
    w/highway=primary_link \
    w/highway=secondary \
    w/highway=secondary_link \
    w/highway=tertiary \
    w/highway=tertiary_link \
    w/highway=unclassified \
    \
    -o bologna-highway-filtered.osm.pbf --overwrite -f pbf,add_metadata=false

echo "Filtro completato! File salvato come bologna-highway-filtered.osm.pbf"

# Statistiche dimensioni file
if [ -f bologna-area.osm.pbf ]; then
    original_size=$(du -h bologna-area.osm.pbf | cut -f1)
    echo "Dimensione originale: $original_size"
fi

if [ -f bologna-highway-filtered.osm.pbf ]; then
    filtered_size=$(du -h bologna-highway-filtered.osm.pbf | cut -f1)
    echo "Dimensione filtrata: $filtered_size"
fi