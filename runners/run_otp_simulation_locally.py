import pandas as pd
import sys
import logging

from otp_mobility.utils.config import OTP_ENDPOINT
from otp_mobility.otp.processor import OTPBatchProcessor, simulate_otp
from otp_mobility.otp.manager import start_otp, wait_for_otp, stop_otp
from otp_mobility.otp.generate_config import build_config, routing_config

from paths import data_output, folder_zip_gtfs, otp_jar_file
from config import params_list, version

logger = logging.getLogger(__name__)


def log_statistics(results):
    logger.info("--- STATISTICS ---")
    logger.info("Total routes processed: %s", len(results))
    logger.info("Routes found: %s", len(results[results['status'] == 'success']))
    logger.info("Routes not found: %s", len(results[results['status'] == 'no_route']))

    if len(results[results['status'] == 'success']) > 0:
        successful_routes = results[results['status'] == 'success']
        logger.info("Avg. duration: %.2f minutes", (successful_routes['duration_seconds'].mean()) / 60)
        logger.info("Min duration: %.2f minutes", (successful_routes['duration_seconds'].min()) / 60)
        logger.info("Max duration: %.2f minutes", (successful_routes['duration_seconds'].max()) / 60)
        logger.info("Sample results: %s", results.head(5).to_dict(orient='records'))

    return 1

def main(
    df,
    main_modes: list,
    otp_endpoint,
    folder_data_path,
    folder_jar_path,
    delay_seconds: float,
    selected_date: str,
    selected_times: str,
    shuffle_coords: bool,
):
    otp_process = None

    try:
        # Launch the OTP server, and wait for it to be ready
        otp_process = start_otp(
            folder_jar_path=folder_jar_path,
            folder_data_path=folder_data_path,
            )

        wait_for_otp(otp_process)

        # Fix: eventually add WALK
        if "WALK" not in main_modes:
            main_modes = main_modes + ["WALK"]

        # Initialize the processor
        processor = OTPBatchProcessor(otp_endpoint)
        
        # Process the dataset
        results = processor.process_dataset(
            df=df,
            main_mode=main_modes,
            origin_lat_col='origin_lat',
            origin_lon_col='origin_lon',
            dest_lat_col='dest_lat',
            dest_lon_col='dest_lon',
            departure_date=selected_date,  # YYYY-MM-DD format
            departure_time=selected_times,  # HH:MM:SS format
            delay_seconds=delay_seconds,  # Pausa tra le richieste,
            dest_change=shuffle_coords,
            origin_change=shuffle_coords,
        )

        log_statistics(results)

        return res

    except Exception as e:
        logging.exception("Errore durante la simulazione: %s", e)
        sys.exit(1)

    finally:
        if otp_process is not None:
            stop_otp(otp_process)


if __name__ == "__main__":
    # Create the config-routing file for OTP
    output_file = data_output / f"routing-config.json"
    logging.info("Routing configuration: %s", output_file)
    config_dict = routing_config(output_file=output_file)

    # Start the simulations!
    for param in params_list:

        logging.info("Simulation: %s", [f"{i}: '{val}'" for i, val in param.items()])

         # Create the config-build file for OTP
        if param["zoi"] == "allBologna":
            osm_list = [
                str(data_output / "bologna-area-filtered-parking.osm.pbf")
            ]
        elif param["zoi"] == "restrictedAv":
            osm_list = [
                str(data_output / "bologna-area-filtered-parking-inside-AV-footway.osm.pbf"),
                str(data_output / "bologna-area-filtered-parking-outside.osm.pbf")
            ]
        gtfs_list = [
            str(folder_zip_gtfs)
        ]
        output_file = data_output / "build-config.json"
        config_dict = build_config(output_file=output_file, osm_list=osm_list, gtfs_list=gtfs_list)

        # Prepare input params
        modes_str =  "_".join(param["modes"])
        input_coord_file = data_output / f"od-coords-{param["method"]}.parquet"
        output_times_file = data_output / f"otp_results_{param["method"]}_{param["zoi"]}_{modes_str}_v{version}.parquet"

        # Process the whole dataset of OD pairs
        df = pd.read_parquet(input_coord_file)

        # Simulate!
        res = main(
            df=df, 
            main_modes=param["modes"], 
            otp_endpoint=OTP_ENDPOINT,
            folder_data_path=data_output,
            folder_jar_path=otp_jar_file,
            delay_seconds=1.0,
            selected_date=param["date"],
            selected_times=param["time"],
            shuffle_coords=True,
        )

        res.to_parquet(output_times_file)
        logging.info("Simulation completed and results saved!")