#!/bin/bash

# Comando osmium completo per filtrare elementi utili allo studio della mobilità

osmium tags-filter data/input_service/bologna-area.osm.pbf \
    \
    `# === INFRASTRUTTURA STRADALE ===` \
    w/highway \
    w/bridge=yes \
    w/tunnel=yes \
    \
    `# === TRASPORTO PUBBLICO ===` \
    wa/public_transport \
    wa/railway=platform \
    wa/railway=station \
    wa/railway=halt \
    wa/railway=subway_entrance \
    wa/railway=tram_stop \
    wa/bus=yes \
    wa/trolleybus=yes \
    wa/amenity=bus_station \
    wa/amenity=ferry_terminal \
    \
    `# === FERROVIE E ROTAIE ===` \
    w/railway=rail \
    w/railway=light_rail \
    w/railway=subway \
    w/railway=tram \
    w/railway=monorail \
    w/railway=funicular \
    w/railway=narrow_gauge \
    \
    `# === PARCHEGGI E SOSTA ===` \
    wa/amenity=parking \
    r/amenity=parking \
    wa/amenity=parking_space \
    wa/amenity=motorcycle_parking \
    wa/amenity=bicycle_parking \
    wa/park_ride=yes \
    wa/parking=* \
    wa/parking:fee=* \
    \
    `# === MOBILITÀ SOSTENIBILE ===` \
    w/cycleway \
    w/bicycle=yes \
    w/bicycle=designated \
    wa/amenity=bicycle_rental \
    wa/amenity=bicycle_repair_station \
    wa/amenity=charging_station \
    wa/amenity=fuel \
    w/footway \
    w/pedestrian \
    \
    `# === AEROPORTI E AVIAZIONE ===` \
    wa/aeroway \
    wa/amenity=airport \
    wa/amenity=helipad \
    \
    `# === TRASPORTO ACQUA ===` \
    wa/amenity=ferry_terminal \
    w/route=ferry \
    wa/waterway=ferry \
    wa/harbour=yes \
    wa/amenity=marina \
    \
    `# === INTERSCAMBI E NODI ===` \
    n/highway=traffic_signals \
    n/highway=stop \
    n/highway=give_way \
    n/railway=level_crossing \
    wa/highway=services \
    wa/highway=rest_area \
    \
    `# === RESTRIZIONI E REGOLE ===` \
    r/type=restriction \
    r/type=route \
    r/type=route_master \
    r/restriction=* \
    \
    `# === BARRIERE E PEDAGGI ===` \
    nw/barrier=toll_booth \
    nw/barrier=gate \
    nw/barrier=lift_gate \
    nw/barrier=cycle_barrier \
    nw/amenity=toll_booth \
    \
    `# === LOGISTICA E TRASPORTO MERCI ===` \
    wa/amenity=truck_stop \
    wa/landuse=depot \
    wa/railway=depot \
    wa/amenity=warehouse \
    \
    `# === ACCESSIBILITÀ ===` \
    nwr/wheelchair=* \
    nwr/tactile_paving=* \
    \
    `# === INFORMAZIONI TRAFFICO ===` \
    n/highway=speed_camera \
    nw/maxspeed=* \
    nw/lanes=* \
    nw/oneway=* \
    \
    -o data/input_service/bologna-area-filtered.osm.pbf  --overwrite -f pbf,add_metadata=false

echo "Filtering completed!"

original_size=$(du -h data/input_service/bologna-area.osm.pbf | cut -f1)
filtered_size=$(du -h data/input_service/bologna-area-filtered.osm.pbf | cut -f1)
echo "Original size: $original_size → Filtered size: $filtered_size"