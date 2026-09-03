import re
import logging
from otp_mobility.utils.config import logging_level
from collections import defaultdict

def parse_filter_expression(filepath: str):
    filter_n = defaultdict(set)
    filter_w = defaultdict(set)
    filter_r = defaultdict(set)
    filter_a = defaultdict(set)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find filters: n/key=value, nw/key=value, nwr/key=value, etc.
    # Also supports keys without explicit values
    pattern = r'([nwra]+)/([a-zA-Z_:]+)(?:=([a-zA-Z_]+))?'
    
    matches = re.findall(pattern, content)
    
    for match in matches:
        types, key, value = match
        
        # types can be 'n', 'w', 'r', 'a', 'nw', 'wr', 'wa', 'nr', 'nwr', 
        for typ in types:
            if typ == 'n':
                if value:
                    filter_n[key].add(value)
                else:
                    # If no value, create an empty set (accepts all values)
                    if key not in filter_n:
                        filter_n[key] = set()
            elif typ == 'w':
                if value:
                    filter_w[key].add(value)
                else:
                    if key not in filter_w:
                        filter_w[key] = set()
            elif typ == 'r':
                if value:
                    filter_r[key].add(value)
                else:
                    if key not in filter_r:
                        filter_r[key] = set()
            elif typ == 'a':
                if value:
                    filter_a[key].add(value)
                else:
                    if key not in filter_a:
                        filter_a[key] = set()
    
    # Convert from defaultdict to regular dict
    filter_n = dict(filter_n)
    filter_w = dict(filter_w)
    filter_r = dict(filter_r)
    filter_a = dict(filter_a)
    
    return filter_n, filter_w, filter_r, filter_a


# Usage example
if __name__ == "__main__":
    filepath = "data/input_service/filter_expression.sh"
    
    filter_n, filter_w, filter_r, filter_a = parse_filter_expression(filepath)
    
    logging.info("=== NODE FILTERS (n/) ===")
    for key, values in sorted(filter_n.items()):
        if values:
            logging.info("'%s': %s,", key, values)
        else:
            logging.info("'%s': set(),", key)
    
    logging.info("=== WAY FILTERS (w/) ===")
    for key, values in sorted(filter_w.items()):
        if values:
            logging.info("'%s': %s,", key, values)
        else:
            logging.info("'%s': set(),", key)
    
    logging.info("=== RELATION FILTERS (r/) ===")
    for key, values in sorted(filter_r.items()):
        if values:
            logging.info("'%s': %s,", key, values)
        else:
            logging.info("'%s': set(),", key)
    
    logging.info("=== AREA FILTERS (a/) ===")
    for key, values in sorted(filter_a.items()):
        if values:
            logging.info("'%s': %s,", key, values)
        else:
            logging.info("'%s': set(),", key)
    
    logging.info("=== STATISTICS ===")
    logging.info("Nodes: %s keys", len(filter_n))
    logging.info("Ways: %s keys", len(filter_w))
    logging.info("Relations: %s keys", len(filter_r))
    logging.info("Areas: %s keys", len(filter_a))