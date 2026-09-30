import osmium
import logging
from otp_mobility.utils.config import logging_level
from datetime import datetime
import sys
from pathlib import Path

def extract_elements_outside(input_file_container: str, input_file_contained: str, output_file:str):
    # Inizialize the ids file
    ids_nodes, ids_ways, ids_relations = set(), set(), set()
    
    # Read the contained file, and save the ids:
    fp = osmium.FileProcessor(input_file_contained)
    for obj in fp:
        if obj.is_node():
            ids_nodes.add(obj.id)
        elif obj.is_way():
            ids_ways.add(obj.id)
        elif obj.is_relation():
            ids_relations.add(obj.id)

    # Writer OSM
    writer = osmium.SimpleWriter(output_file, overwrite=True)

    # Load the container file
    fp = osmium.FileProcessor(input_file_container)
    for obj in fp:
        if obj.is_node() and obj.id not in ids_nodes:
            writer.add_node(obj)
        elif obj.is_way() and obj.id not in ids_ways:
            writer.add_way(obj)
        elif obj.is_relation() and obj.id not in ids_relations:
            writer.add_relation(obj)
    logging.debug("Almost finished at %s", datetime.now().strftime('%H:%M:%S'))
    writer.close()
    logging.debug("Finished at %s", datetime.now().strftime('%H:%M:%S'))

    _show_file_sizes(input_file_container, input_file_contained, output_file)


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
    
def _show_file_sizes(input_file_container: str, input_file_contained: str, output_file:str):
    # N. elements
    i_in, i_iw, i_ir = _count_elements(input_file_container)
    i_i2n, i_i2w, i_i2r = _count_elements(input_file_contained)
    i_on, i_ow, i_or = _count_elements(output_file)
    logging.info("Original container: %s nodes, %s ways, %s relations", i_in, i_iw, i_ir)
    logging.info("Original contained: %s nodes, %s ways, %s relations", i_i2n, i_i2w, i_i2r)
    logging.info("Output: %s nodes, %s ways, %s relations", i_on, i_ow, i_or)

    # Sizes
    original_container_size = Path(input_file_container).stat().st_size / (1024 * 1024)
    original_contained_size = Path(input_file_contained).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    logging.info("Original container size: %.2f MB", original_container_size)
    logging.info("Original contained size: %.2f MB", original_contained_size)
    logging.info("New size: %.2f MB", filtered_size)


if __name__ == "__main__":
    logging.basicConfig(level=logging_level)
    if len(sys.argv) != 4:
        logging.error("Wrong number of inputs. Given %s, while needed 3.", len(sys.argv) - 1)
        logging.error("Correct usage: python extract_elements_outside.py input_container input_contained output")
        sys.exit(1)
    
    # Configuration
    input_file_container = sys.argv[1]
    input_file_contained = sys.argv[2]
    output_file = sys.argv[3]
    logging.info("Executing extract_elements_outside.py with input_container=%s, input_contained=%s, output=%s", input_file_container, input_file_contained, output_file)

    extract_elements_outside(input_file_container, input_file_contained, output_file)