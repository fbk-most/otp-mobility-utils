from pathlib import Path
import pandas as pd

from otp_mobility.utils.config import OTP_ENDPOINT
from otp_mobility.utils.utils import get_dataframe, log_dataframe, put_dataframe
from otp_mobility.utils.paths import data_output, folder_zip_gtfs
from otp_mobility.otp.processor import OTPBatchProcessor
from otp_mobility.otp.generate_config import build_config, routing_config

from config import params_list, version


def main(
    df,
    main_modes: list,
    otp_endpoint,
):
    """
    Processes travel routes using the OpenTripPlanner batch processor based on the specified main modes.
    Args:
        main_modes (list): List of main travel modes to process. Valid values are "CAR", "CAR_PARK", "TRANSIT", and "WALK".
    Workflow:
        - Validates the provided main modes.
        - Ensures "WALK" is included in the main modes.
        - Configures OTP endpoint and input/output file paths.
            - Here, properly set the dataset of ODs and the name of the output file.
        - Initializes the OTPBatchProcessor.
        - Processes the dataset for the specified travel modes and parameters.
            - Inside this step the output of the simulator is found and saved.
        - Prints statistics about the processed routes, including total, successful, and unsuccessful routes,
          as well as duration statistics for successful routes.
    """

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
        departure_date="2025-06-10",  # YYYY-MM-DD format
        departure_time="07:00:00",  # HH:MM:SS format
        delay_seconds=1.0,  # Pausa tra le richieste,
        dest_change=True,
        origin_change=True
    )
 
    # Show statistics
    print(f"\n--- STATISTICS ---")
    print(f"Total routes processed: {len(results)}")
    print(f"Routes found: {len(results[results['status'] == 'success'])}")
    print(f"Routes not found: {len(results[results['status'] == 'no_route'])}")
    
    if len(results[results['status'] == 'success']) > 0:
        successful_routes = results[results['status'] == 'success']
        print(f"Avg. duration: {(successful_routes['duration_seconds'].mean())/60:.2f} minuti")
        print(f"Min duration: {(successful_routes['duration_seconds'].min())/60:.2f} minuti")
        print(f"Max duration: {(successful_routes['duration_seconds'].max())/60:.2f} minuti")
        print(results.head(5))

    return results


if __name__ == "__main__":

    # Create the config-routing file for OTP
    output_file = data_output / f"routing-config.json"
    config_dict = routing_config(output_file=output_file)

    # Start the simulations!
    for param in params_list:

        print(f"\n► Simulation: ")
        print([f"{i}: '{val}'" for i, val in param.items()])

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
            otp_endpoint=OTP_ENDPOINT
        )

        res.to_parquet(output_times_file)
        print("Simulation completed and results saved!")