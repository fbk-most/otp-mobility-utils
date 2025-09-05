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
                        transitTime
                        start
                        end
                        numberOfTransfers
                        legs {
                            mode
                            duration
                            startTime
                            endTime
                            distance
                            from {
                                name
                                lat
                                lon
                            }
                            to {
                                name
                                lat
                                lon
                            }
                            route {
                                shortName
                                longName
                                mode
                            }
                            trip {
                                routeShortName
                            }
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
        
        self.query = QUERY_SIMPLE
    
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
        if not result or 'data' not in result:
            return {
                'status': 'error',
                'duration_seconds': None,
                'duration_minutes': None,
                'walk_time_seconds': None,
                'start_time': None,
                'end_time': None
            }
        
        plan = result['data'].get('plan')
        if not plan:
            return {
                'status': 'no_plan',
                'duration_seconds': None,
                'duration_minutes': None,
                'walk_time_seconds': None,
                'start_time': None,
                'end_time': None
            }
        
        itineraries = plan.get('itineraries', [])
        if not itineraries:
            return {
                'status': 'no_route',
                'duration_seconds': None,
                'duration_minutes': None,
                'walk_time_seconds': None,
                'start_time': None,
                'end_time': None
            }
        
        # Prendi l'itinerario più breve
        best_itinerary = min(itineraries, key=lambda x: x.get('duration', float('inf')))
        
        return {
            'status': 'success',
            'duration_seconds': best_itinerary.get('duration'),
            'duration_minutes': round(best_itinerary.get('duration', 0) / 60, 2) if best_itinerary.get('duration') else None,
            'walk_time_seconds': best_itinerary.get('walkTime'),
            'start_time': best_itinerary.get('start'),
            'end_time': best_itinerary.get('end')
        }

    
    def process_dataset(
        self, input_file: str, output_file: str, 
        main_mode: list,
        origin_lat_col: str = 'origin_lat', 
        origin_lon_col: str = 'origin_lon',
        dest_lat_col: str = 'dest_lat', 
        dest_lon_col: str = 'dest_lon',
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
                'dest_lat': dest_lat,
                'dest_lon': dest_lon,
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
                print(f"OK in line {idx} from ({origin_lat}, {origin_lon}) to ({dest_lat}, {dest_lon}): {result_row['status']} - {result_row['duration_minutes']}")
            
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


def test_single_query(args: list):
    """Funzione per testare una singola query"""
    MAIN_MODEs = args
    if "WALK" not in MAIN_MODEs:
        MAIN_MODEs = MAIN_MODEs + ["WALK"]
    for main_mode in args:
        if main_mode not in ["CAR", "CAR_PARK", "TRANSIT", "WALK"]:
            raise ValueError("Error: One of the MAIN_MODEs is not in ['CAR', 'CAR_PARK', 'TRANSIT', 'WALK]")
    if ("CAR" in args) and ("CAR_PARK" in args):
        raise ValueError("Error: Specify either 'CAR' or 'CAR_PARK', not both.")
     

    OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql"
    
    processor = OTPBatchProcessor(OTP_ENDPOINT)
    
    # Test con coordinate di esempio
    # lat = 44.53083
    # lon = 11.18020
    # dest_lat_tmp = 44.46925193255113
    # dest_lon_tmp = 11.366358609573888
    # origin_lat_tmp = 44.29138432534488
    # origin_lon_tmp = 11.085878478293031
    lat, lon = 44.498149, 11.340096
    dest_lat_tmp, dest_lon_tmp = 44.498149, 11.340096
    origin_lat_tmp, origin_lon_tmp = 44.545637, 11.201394

    result_found = False
    n_iter = 0
    max_iter = 5

    while not result_found and n_iter < max_iter:
        result = processor.execute_query(
            origin_lat=origin_lat_tmp,
            origin_lon=origin_lon_tmp,
            dest_lat=lat,
            dest_lon=lon,
            departure_date="2025-06-10",
            departure_time="07:30:00",
            main_mode=MAIN_MODEs
        )
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
    
def main(argv: list):
    # IO da terminale
    if len(sys.argv) < 1:
        raise ValueError("Error: at least 1 argument needed")
    for main_mode in argv:
        if main_mode not in ["CAR", "CAR_PARK", "TRANSIT", "WALK"]:
            raise ValueError("Error: One of the MAIN_MODEs is not in ['CAR', 'CAR_PARK', 'TRANSIT', 'WALK]")
    if ("CAR" in argv) and ("CAR_PARK" in argv):
        raise ValueError("Error: Specify either 'CAR' or 'CAR_PARK', not both.")
        
    MAIN_MODEs = argv
    if "WALK" not in MAIN_MODEs:
        MAIN_MODEs = MAIN_MODEs + ["WALK"]

    # Configurazione
    OTP_ENDPOINT = "http://localhost:8080/otp/routers/default/index/graphql" ## Questo funziona
    INPUT_FILE = "data/input_od/OD_coordinates_v2.parquet"
    OUTPUT_FILE = f"data/output/OD_travel_times_{"_".join(MAIN_MODEs)}_7AM_5h_spatialDynamic.parquet"
    OUTPUT_FILE = f"data/output/OUTPUT_DI_PROVA_20250905.parquet"
    
    # Inizializza il processore
    processor = OTPBatchProcessor(OTP_ENDPOINT)
    
    # Processa il dataset
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
    
    # Mostra statistiche
    print(f"\n--- STATISTICHE ---")
    print(f"Totale route processate: {len(results)}")
    print(f"Route trovate: {len(results[results['status'] == 'success'])}")
    print(f"Route non trovate: {len(results[results['status'] == 'no_route'])}")
    
    if len(results[results['status'] == 'success']) > 0:
        successful_routes = results[results['status'] == 'success']
        print(f"Durata media: {successful_routes['duration_minutes'].mean():.2f} minuti")
        print(f"Durata minima: {successful_routes['duration_minutes'].min():.2f} minuti")
        print(f"Durata massima: {successful_routes['duration_minutes'].max():.2f} minuti")
        print(results.head(5))

if __name__ == "__main__":
    main(argv=sys.argv[1:])
    #test_single_query(args=sys.argv[1:])