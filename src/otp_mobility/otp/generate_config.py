import json
from pathlib import Path

from otp_mobility.utils.paths import folder_zip_gtfs, data_output

def _to_uri(path: str | Path) -> str:
    return Path(path).absolute().as_uri()  # return file:///path/assoluto

def build_config(
    output_file: str|Path,
    osm_list: list,
    gtfs_list: list,
):
    config = {
        "staticParkAndRide": True,
        "osm": [
            {
                "source": _to_uri(osm_elem),
                "timeZone": "Europe/Rome"
            } 
            for osm_elem in osm_list
        ],
        "transitFeeds": [
            {
                "source": _to_uri(gtfs_elem),
                "type": "gtfs",
            } 
            for gtfs_elem in gtfs_list
        ]
    }

    with open(str(output_file), "w") as f:
        json.dump(config, f, indent=2)

    return config

def routing_config(
    output_file: str|Path,
):
    config = {
        "routingDefaults": {
            "searchWindow": "5h",
            "numItineraries": 5,
            "walkReluctance" : 3.0
        },
    }

    with open(str(output_file), "w") as f:
        json.dump(config, f, indent=2)

    return config

