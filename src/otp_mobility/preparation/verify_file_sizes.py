import logging
from otp_mobility.utils.config import logging_level

import osmium
import os

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

if __name__ == "__main__":
    files = [
        "../data/input_service/bologna-area.osm.pbf", # OK ricalcolato
        "../data/input_service/bologna-area-filtered.osm.pbf",
        "../data/input_service/bologna-area-filtered-parking.osm.pbf",
        "../data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf",
        "../data/input_service/bologna-area-filtered-parking-outside-AV.osm.pbf",
        "../data/input_service/bologna-area-filtered-parking-inside-AV-footway.osm.pbf"
    ]

    for f in files:
        logging.info("File: %s", f)
        output_file3 = f
        i_in, i_iw, i_ir = _count_elements(output_file3)
        output_size3 = os.path.getsize(output_file3) / (1024*1024)  # MB
        logging.info("Elements in the file: %s nodes, %s ways, %s relations", i_in, i_iw, i_ir)
        logging.info("File size: %.2f MB", output_size3)