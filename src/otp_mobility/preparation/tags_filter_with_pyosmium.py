"""
Tentative implementation of the tag-filter function from osmium-tool. 

Taken from the osmium-tool documentation: 'All objects matching the expressions will be read from OSM-FILE and written to the output. All objects referenced from those objects will also be added to the output [...]. This applies to nodes referenced in ways and members referenced in relations.'
https://docs.osmcode.org/osmium/latest/osmium-tags-filter.html

We add to a new file all nodes, ways, and relations that have at least one of the key-tag combinations explicited in the filter file, and we add all of their references through a back-reference writer. The implementation is based on this suggestion from the package author: https://github.com/osmcode/pyosmium/discussions/274

Note: assumptions: nodes are filtered based on the "n*/" lines of the filter file; ways based on the "w*/" lines; relations on the "r*/" lines, and if they are of type "multypolygon" they consider also the "a*/" lines (since they represent areas).

Note: this filter implementation is tested to work with our filters written in filter_expressiosn.sh. However, it is not straightforward that it will work with every filter (e.g., for sure it does not handle "!=" filters, or empty key tags).
"""

import osmium
from pathlib import Path
import sys
from datetime import datetime

from otp_mobility.preparation.back_way_forward_reference_writer import BackWayForwardReferenceWriter
from otp_mobility.preparation.parse_filter_expression import parse_filter_expression
from otp_mobility.utils.config import logging, logging_level


def our_tags_filter_with_pyosmium(input_file, output_file, filter_file):
    # Read the filters
    full_filter_n, full_filter_w, full_filter_r, full_filter_a = parse_filter_expression(filter_file) 

    # Use a back-reference writer to guarantee completeness
    writer = osmium.BackReferenceWriter(output_file, ref_src=input_file, overwrite=True)

    # Read file, filter and write file
    logging.debug("Getting elements at %s", datetime.now().strftime('%H:%M:%S'))
    fp = osmium.FileProcessor(input_file)
    osmium_filters = [
        osmium.filter.KeyFilter(*full_filter_n.keys()).enable_for(osmium.osm.NODE),
        osmium.filter.KeyFilter(*full_filter_w.keys()).enable_for(osmium.osm.WAY),
        osmium.filter.KeyFilter(*full_filter_r.keys(), *full_filter_a.keys()).enable_for(osmium.osm.RELATION)
    ]
    for f in osmium_filters:
        fp = fp.with_filter(f)
    for obj in fp:
        if obj.is_node() and _check_condition(obj.tags, full_filter_n):
            writer.add_node(obj)
        elif obj.is_way() and _check_condition(obj.tags, full_filter_w):
            writer.add_way(obj)
        elif obj.is_relation() and _check_condition_relations(obj.tags, full_filter_r, full_filter_a):
            writer.add_relation(obj)
    logging.debug("Almost finished at %s", datetime.now().strftime('%H:%M:%S'))
    writer.close()
    logging.debug("Finished at %s", datetime.now().strftime('%H:%M:%S'))

    # Print stats
    _show_stats([0,0,0], input_file, output_file)

def _check_condition(tags, filter):
    for t in tags:
        if t.k in filter.keys():
            if (not filter.get(t.k)) or (filter.get(t.k) and t.v in filter.get(t.k)):
                    return True
    return False

def _check_condition_relations(tags, filter1, filter2):
    additional_check = False
    for t in tags:
        if t.k == "type" and t.v == "multipolygon":
            additional_check = True
        if t.k in filter1.keys():
            if (not filter1.get(t.k)) or (filter1.get(t.k) and t.v in filter1.get(t.k)):
                    return True
    if additional_check:
        for t in tags:
            if t.k in filter2.keys():
                if (not filter2.get(t.k)) or (filter2.get(t.k) and t.v in filter2.get(t.k)):
                        return True
    return False

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
    
def _show_stats(n_objects, input_file: str, output_file: str):
    # N. elements
    i_in, i_iw, i_ir = _count_elements(input_file)
    i_on, i_ow, i_or = _count_elements(output_file)
    logging.info("Original file: %s nodes, %s ways, %s relations", i_in, i_iw, i_ir)
    logging.info("Explicitly added: %s nodes, %s ways, %s relations", *n_objects)
    logging.info("Output file: %s nodes, %s ways, %s relations", i_on, i_ow, i_or)

    # Sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    logging.info("Original size: %.2f MB", original_size)
    logging.info("New size: %.2f MB", filtered_size)


if __name__ == "__main__":
    logging.basicConfig(level=logging_level)
    if len(sys.argv) != 4:
        logging.error("Wrong number of inputs. Given %s, while needed 3.", len(sys.argv) - 1)
        logging.error("Correct usage: python tag_filter_with_pyosmium.py input output filter_file")
        sys.exit(1)
    
    # Configuration
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    filter_file = sys.argv[3]
    logging.info("Executing tags_filter_with_pyosmium.py with input=%s, output=%s, filter=%s", input_file, output_file, filter_file)

    our_tags_filter_with_pyosmium(str(input_file), str(output_file), str(filter_file))