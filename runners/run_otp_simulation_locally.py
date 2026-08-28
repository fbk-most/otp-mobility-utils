import pandas as pd
import sys

from otp_mobility.utils.config import OTP_ENDPOINT
from otp_mobility.otp.processor import OTPBatchProcessor, simulate_otp
from otp_mobility.otp.manager import start_otp, wait_for_otp, stop_otp
from otp_mobility.otp.generate_config import build_config, routing_config

from paths import data_output, folder_zip_gtfs, otp_jar_file
from config import params_list, version

def main(
    df,
    main_modes: list,
    otp_endpoint,
    folder_data_path,
    folder_jar_path,
):
    otp_process = None

    try:
        otp_process = start_otp(
            folder_jar_path=folder_jar_path,
            folder_data_path=folder_data_path,
            )

        wait_for_otp(otp_process)

        res = simulate_otp(
            df=df, 
            main_modes=main_modes,
            otp_endpoint=otp_endpoint
        )
        return res

    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(1)

    finally:
        if otp_process is not None:
            stop_otp(otp_process)


if __name__ == "__main__":

    # Create the config-routing file for OTP
    output_file = data_output / f"routing-config.json"
    print(output_file)
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
            otp_endpoint=OTP_ENDPOINT,
            folder_data_path=data_output,
            folder_jar_path=otp_jar_file,
        )

        res.to_parquet(output_times_file)
        print("Simulation completed and results saved!")