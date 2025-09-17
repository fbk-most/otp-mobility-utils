import pandas as pd
import random
import requests
import json
from datetime import datetime, timezone, date, time
import time as time_module
from typing import Dict, List, Optional
import sys

QUERY_SIMPLE = """
            query PlanTrip(
            $from: InputCoordinates!, 
            $to: InputCoordinates!, 
            $date: String!, 
            $time: String!, 
            $mode: [TransportMode!]!
            ) {
            plan(
                from: $from,
                to: $to,
                date: $date,
                time: $time,
                transportModes: $mode
            ) {
                itineraries {
                    duration
                    walkTime
                    start
                    end
                }
            }
            }
        """

QUERY_COMPLEX = """
            query PlanTrip(
                $from: InputCoordinates!, 
                $to: InputCoordinates!, 
                $date: String!, 
                $time: String!, 
                $mode: [TransportMode!]!) {
            plan(
                from: $from, 
                to: $to, 
                date: $date, 
                time: $time, 
                transportModes: $mode) {
            itineraries {
                duration
                walkTime
                numberOfTransfers
                start
                end
                legs {
                    mode
                    duration
                    startTime
                    endTime
                }
            }
        }
    }
"""

class OTPBatchProcessor:
    def __init__(self, otp_graphql_endpoint: str):
        """
        Inizializza il processore per OpenTripPlanner
        
        Args:
            otp_graphql_endpoint: URL dell'endpoint GraphQL di OTP (es: "http://localhost:8080/otp/gtfs/v1")
        """
        self.endpoint = otp_graphql_endpoint
        
        self.query = QUERY_COMPLEX
    
    def execute_query(self, origin_lat: float, origin_lon: float, 
                     dest_lat: float, dest_lon: float, main_mode: list,
                     departure_date: str|None = None, 
                     departure_time: str|None = None) -> Optional[Dict]:
        """
        Esegue una singola query GraphQL.
        Il parametro di main_mode deve essere fornito come una lista di stringhe: es: ["CAR", "WALK"]
        """
        # CORREZIONE 1: Formato corretto per data e ora
        if departure_date is None:
            departure_date = date.today().isoformat()  # "YYYY-MM-DD"
        if departure_time is None:
            departure_time = time(9, 0).isoformat()   # "HH:MM:SS"

        # correzione 2  
        modes = [{"mode": "WALK"}]
        if "CAR_PARK" in main_mode:
            modes.append({"mode": "CAR", "qualifier": "PARK"})
        if "CAR" in main_mode:
            modes.append({"mode": "CAR"})
        if "TRANSIT" in main_mode:
            modes.append({"mode": "TRANSIT"})

        variables = {
            "from": {
                "lat": float(origin_lat),
                "lon": float(origin_lon)
            },
            "to": {
                "lat": float(dest_lat),
                "lon": float(dest_lon)
            },
            "date": str(departure_date),
            "time": str(departure_time),
            "mode": modes
        }

        payload = {
            "query": self.query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                print(f"GraphQL errors: {result['errors']}")
                return None
                
            return result

        except requests.RequestException as e:
            raise RuntimeError(f"Errore nella richiesta HTTP: {e}")

        except json.JSONDecodeError as e:
            print(f"Errore JSON decode: {e}")
            print(f"Response text: {response.text[:500]}...") # type: ignore
            return None
    
    def extract_route_info(self, result: Dict) -> Dict:
        """
        Estrae le informazioni principali dal risultato della query
        TODO: add other information on the query related to %time car, %time bus, sequences of car-bus
        """
        # Handle the cases with no output
        error_return = {
                'status': 'error',
                'duration_seconds': None,
                'walk_time_seconds': None,
                'number_of_legs': None,
                'transport_modes': [],
                'transport_mode_sequences': [],
                'transport_sequence': '',
                'transport_durations': [],
                'transport_percentages': [],
                'number_of_transit_transfers': None,
                'start_time': None,
                'end_time': None
            }

        if not result or 'data' not in result:
            return error_return
        
        plan = result['data'].get('plan')
        if not plan:
            error_return['status'] = 'no_plan'
            return error_return
        
        itineraries = plan.get('itineraries', [])
        if not itineraries:
            error_return['status'] = 'no_itineraries'
            return error_return
         
        # Handle the cases with one or more solutions
        best_itinerary = min(itineraries, key=lambda x: x.get('duration', float('inf')))
        
        legs = best_itinerary.get('legs', [])
        total_duration = sum(leg.get('duration', 0) for leg in legs)
        transport_modes = []
        transport_durations = []
        transport_percentages = []
        for leg in legs:
            mode = leg.get('mode', 'UNKNOWN')
            transport_modes.append(mode)

            duration = leg.get('duration', 0)
            transport_durations.append(duration)

            percentage = (duration / total_duration * 100) if total_duration > 0 else 0
            transport_percentages.append(round(percentage, 2))

        return {
            'status': 'success',
            'duration_seconds': best_itinerary.get('duration'),
            'walk_time_seconds': best_itinerary.get('walkTime'),
            'number_of_legs': len(legs),
            'transport_modes': transport_modes,
            'transport_mode_sequences': [],
            'transport_durations': transport_durations,
            'transport_percentages': transport_percentages,
            'number_of_transit_transfers': best_itinerary.get('numberOfTransfers'),
            'start_time': best_itinerary.get('start'),
            'end_time': best_itinerary.get('end')
        }

    
    def process_dataset(
        self, input_file: str, output_file: str, 
        main_mode: list,
        origin_lat_col: str = 'origin_lat', 
        origin_lon_col: str = 'origin_lon',
        origin_id_col: str = 'from',
        dest_lat_col: str = 'dest_lat', 
        dest_lon_col: str = 'dest_lon',
        dest_id_col: str = 'to',
        departure_date: str = "2025-06-10",
        departure_time: str = "07:00:00",
        delay_seconds: float = 2.0,
        origin_change: bool = False,
        dest_change: bool = False
    ) -> pd.DataFrame:
        """
        Processa un intero dataset
        """
        # Leggi il dataset
        try:
            df = pd.read_parquet(input_file)
            print(f"Dataset caricato: {len(df)} righe")
        except Exception as e:
            raise RuntimeError(f"Errore nel caricare il PARQUET: {e}")
        
        df.reset_index(drop=True, inplace=True)
        
        # Verifica le colonne richieste
        required_cols = [origin_lat_col, origin_lon_col, dest_lat_col, dest_lon_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise RuntimeError(f"Colonne mancanti nel PARQUET: {missing_cols}")
        
        # Lista per i risultati
        results = []
        percent = 0
        
        # Processa ogni riga
        for idx, row in df.iterrows():
            result_found = False

            try:
                origin_lat = float(row[origin_lat_col])
                origin_lon = float(row[origin_lon_col])
                dest_lat = float(row[dest_lat_col])
                dest_lon = float(row[dest_lon_col])
                from_id = int(row[origin_id_col])
                to_id = int(row[dest_id_col])
            except (ValueError, TypeError) as e:
                raise RuntimeError(f"Errore lettura coordinate riga {idx}: {e}")
            
            origin_lat_tmp = origin_lat
            origin_lon_tmp = origin_lon
            dest_lat_tmp = dest_lat
            dest_lon_tmp = dest_lon 
            n_iter=0
                
            while not result_found and n_iter < 20:
                # Esegui la query
                result = self.execute_query(
                    origin_lat=origin_lat_tmp, origin_lon=origin_lon_tmp, 
                    dest_lat=dest_lat_tmp, dest_lon=dest_lon_tmp, 
                    departure_date=departure_date, departure_time=departure_time, 
                    main_mode=main_mode
                )
                route_info = self.extract_route_info(result) # type: ignore
                
                # Aggiungi le informazioni al risultato
                if route_info['status'] == 'success':
                    result_found = True

                if not result_found and dest_change:
                    # Se non è stato trovato un percorso, riprova spostando le coordinate di 5*10 m a dx/sx e 5*10m sopra/sotto
                    lon_plus, lat_plus = random.choice([True, False]), random.choice([True, False])
                    dest_lon_tmp = dest_lon_tmp + 5*0.000127 if lon_plus else dest_lon_tmp - 5*0.000127  # Sposta di 10 metri in longitudine
                    dest_lat_tmp = dest_lat_tmp + 5*0.0000899 if lat_plus else dest_lat_tmp - 5*0.0000899  # Sposta di 10 metri in longitudine
                
                if not result_found and origin_change:
                    # Se non è stato trovato un percorso, riprova spostando le coordinate di 5*10 m a dx/sx e 5*10m sopra/sotto
                    lon_plus, lat_plus = random.choice([True, False]), random.choice([True, False])
                    origin_lon_tmp = origin_lon_tmp + 5*0.000127 if lon_plus else origin_lon_tmp - 5*0.000127  # Sposta di 10 metri in longitudine
                    origin_lat_tmp = origin_lat_tmp + 5*0.0000899 if lat_plus else origin_lat_tmp - 5*0.0000899  # Sposta di 10 metri in longitudine
                n_iter += 1
                
            # Pausa per non sovraccaricare il server
            #print(route_info)
            if delay_seconds > 0:
                time_module.sleep(delay_seconds)

            result_row = {
                'row_index': idx,
                'origin_lat': origin_lat,
                'origin_lon': origin_lon,
                'from': from_id,
                'dest_lat': dest_lat,
                'dest_lon': dest_lon,
                'to': to_id,
                'origin_lat_tmp': origin_lat_tmp,
                'origin_lon_tmp': origin_lon_tmp,
                'dest_lat_tmp': dest_lat_tmp,
                'dest_lon_tmp': dest_lon_tmp,
                'n_iter': n_iter,
                **route_info # type: ignore
            }

            # Debugging
            if result_row['status'] != 'success':
                print(f"Error in line {idx} from ({origin_lat}, {origin_lon}) to ({dest_lat}, {dest_lon}): {result_row['status']}")
            else:
                print(f"OK in line {idx} from ({origin_lat}, {origin_lon}) to ({dest_lat}, {dest_lon}): {result_row['status']} - {result_row['duration_seconds']}")
            
            results.append(result_row)
        
        # Crea il DataFrame dei risultati
        results_df = pd.DataFrame(results)
        
        # Salva i risultati
        try:
            results_df.to_parquet(output_file)
            print(f"Risultati salvati in: {output_file}")
        except Exception as e:
            print(f"Errore nel salvare il file: {e}")
            
        return results_df


def test_single_query(MAIN_MODEs: list):
    """
    Executes a test query to the OpenTripPlanner (OTP) GraphQL endpoint using the specified main travel modes.    
    """

    if "WALK" not in MAIN_MODEs:
        MAIN_MODEs = MAIN_MODEs + ["WALK"]

    OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"
    
    processor = OTPBatchProcessor(OTP_ENDPOINT)
    
    # Test con coordinate di esempio
    dest_lat_tmp, dest_lon_tmp = 44.498149, 11.340096
    origin_lat_tmp, origin_lon_tmp = 44.545637, 11.201394

    result_found = False
    n_iter = 0
    max_iter = 5

    while not result_found and n_iter < max_iter:
        result = processor.execute_query(
            origin_lat=origin_lat_tmp,
            origin_lon=origin_lon_tmp,
            dest_lat=dest_lat_tmp,
            dest_lon=dest_lon_tmp,
            departure_date="2025-06-10",
            departure_time="07:00:00",
            main_mode=MAIN_MODEs
        )
        print(result)
        route_info = processor.extract_route_info(result) # type: ignore

        if route_info['status'] == 'success':
            result_found = True

        if not result_found:
            # Se non è stato trovato un percorso, riprova spostando le coordinate di 10 m a dx/sx e 10m sopra/sotto
            lon_plus, lat_plus = random.choice([True, False]), random.choice([True, False])
            dest_lon_tmp = dest_lon_tmp + 5*0.000127 if lon_plus else dest_lon_tmp - 5*0.000127  # Sposta di 10 metri in longitudine
            dest_lat_tmp = dest_lat_tmp + 5*0.0000899 if lat_plus else dest_lat_tmp - 5*0.0000899  # Sposta di 10 metri in longitudine
        n_iter += 1
        
    print("Risultato raw:")
    print(json.dumps(result, indent=2)) # type: ignore
    
    print("\nInformazioni estratte:")
    print(route_info) # type: ignore

    print(f"Iterazioni prima della convergenza: {n_iter}")
    

def main(MAIN_MODEs: list):
    """
    Processes travel routes using the OpenTripPlanner batch processor based on the specified main modes.
    Args:
        MAIN_MODEs (list): List of main travel modes to process. Valid values are "CAR", "CAR_PARK", "TRANSIT", and "WALK".
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
    if "WALK" not in MAIN_MODEs:
        MAIN_MODEs = MAIN_MODEs + ["WALK"]

    # Configuration
    OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql" ## Questo funziona
    INPUT_FILE = "data/input_od/OD_coordinates_extended_v2.parquet"
    OUTPUT_FILE = f"data/output/travelTimesAndRoutes_extended_allBologna_{"_".join(MAIN_MODEs)}_20250917.parquet"
    
    # Initialize the processor
    processor = OTPBatchProcessor(OTP_ENDPOINT)
    
    # Process the dataset
    results = processor.process_dataset(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        main_mode=MAIN_MODEs,
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
    print(f"\n--- STATISTICHE ---")
    print(f"Totale route processate: {len(results)}")
    print(f"Route trovate: {len(results[results['status'] == 'success'])}")
    print(f"Route non trovate: {len(results[results['status'] == 'no_route'])}")
    
    if len(results[results['status'] == 'success']) > 0:
        successful_routes = results[results['status'] == 'success']
        print(f"Durata media: {(successful_routes['duration_seconds'].mean())/60:.2f} minuti")
        print(f"Durata minima: {(successful_routes['duration_seconds'].min())/60:.2f} minuti")
        print(f"Durata massima: {(successful_routes['duration_seconds'].max())/60:.2f} minuti")
        print(results.head(5))


if __name__ == "__main__":
    # Check IO
    if len(sys.argv) < 2:
        raise ValueError("Error: at least 1 argument needed")
    for main_mode in sys.argv[1:]:
        if main_mode not in ["CAR", "CAR_PARK", "TRANSIT", "WALK"]:
            raise ValueError("Error: One of the MAIN_MODEs is not in ['CAR', 'CAR_PARK', 'TRANSIT', 'WALK]")
    if ("CAR" in sys.argv[1:]) and ("CAR_PARK" in sys.argv[1:]):
        raise ValueError("Error: Specify either 'CAR' or 'CAR_PARK', not both.")

    # Test a single query
    test_single_query(MAIN_MODEs=sys.argv[1:])
    
    # Process the whole dataset of OD pairs
    main(MAIN_MODEs=sys.argv[1:])

