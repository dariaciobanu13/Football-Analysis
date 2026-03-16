import pandas as pd
from statsbombpy import sb
import warnings

# Ignore the open data access warning from statsbomb
warnings.filterwarnings("ignore", category=UserWarning, module="statsbombpy")

def fetch_match_data(match_id):
    """
    Acts as the 'Log Harvester'. Fetches raw event data from the API.
    Treats the football match as a specific time-bound network session.
    """
    print(f"[NOC INFO] Initiating data connection to Match Session ID: {match_id}...")
    
    # Fetch all events (passes, duels, shots, etc.) for the match
    events_df = sb.events(match_id=match_id)
    
    # We only care about events with a specific player attached (ignoring generic tactical shifts)
    events_df = events_df.dropna(subset=['player'])
    
    print(f"[NOC INFO] Successfully ingested {len(events_df)} network events.")
    return events_df

def process_and_flatten_data(df):
    """
    Acts as the 'JSON Flattener' & Schema Normalizer.
    Cleans the raw log data and extracts critical telecom-style features.
    """
    print(f"[NOC INFO] Normalizing schema and processing data...")
    
    # --- 0. Data Sanity Check (Data Integrity) ---
    print(f"[NOC INFO] Performing Data Sanity Check...")
    initial_len = len(df)
    # Ensure critical routing fields exist and remove corrupted packets
    if 'type' not in df.columns or 'player_id' not in df.columns:
        raise ValueError("[CRITICAL ERROR] Payload missing routing headers ('type' or 'player_id').")
    
    df = df.dropna(subset=['type', 'player_id', 'team'])
    dropped = initial_len - len(df)
    if dropped > 0:
        print(f"[NOC WARNING] Dropped {dropped} corrupted data packets (NaN in critical routing fields).")
    else:
        print(f"[NOC INFO] Data Sanity Check Passed. 100% Payload Integrity.")
    
    # --- 1. Filter Relevant Network Actions ---
    # We want to track Passes (Data Packets Sent) and Duels (Hardware Stress)
    relevant_events = df[df['type'].isin(['Pass', 'Duel'])].copy()
    
    # --- 2. Extract Event Minute (Timestamping) ---
    # Creating a linear timeline for time-series analysis
    relevant_events['Time_Minute'] = relevant_events['minute']
    
    # --- 3. Extract Node IDs & Node Names ---
    relevant_events['Node_ID'] = relevant_events['player_id']
    relevant_events['Node_Name'] = relevant_events['player']
    relevant_events['Network_Segment'] = relevant_events['team']
    
    # --- 4. Flatten JSON/Dictionary nested fields (The Pandas Magic) ---
    
    # PASSES: Check if pass was successful or incomplete (Packet Loss)
    # StatsBomb records a pass as 'incomplete' if 'pass_outcome' IS NOT null. 
    # If 'pass_outcome' IS null, the pass was successful.
    if 'pass_outcome' in relevant_events.columns:
        relevant_events['Pass_Successful'] = relevant_events.apply(
            lambda row: 1 if row['type'] == 'Pass' and pd.isna(row['pass_outcome']) else (0 if row['type'] == 'Pass' else 0), axis=1
        )
        relevant_events['Pass_Attempt'] = relevant_events.apply(
            lambda row: 1 if row['type'] == 'Pass' else 0, axis=1
        )
    else:
        # Fallback if column completely missing (rare, but good practice)
        relevant_events['Pass_Successful'] = 1
        relevant_events['Pass_Attempt'] = 1

    # DUELS: Check if duel was won (Stress handled) or lost (Hardware failure)
    if 'duel_outcome' in relevant_events.columns:
        relevant_events['Duel_Won'] = relevant_events.apply(
            lambda row: 1 if row['type'] == 'Duel' and row['duel_outcome'] in ['Won', 'Success In Play', 'Success'] else 0, axis=1
        )
        relevant_events['Duel_Attempt'] = relevant_events.apply(
            lambda row: 1 if row['type'] == 'Duel' else 0, axis=1
        )
    else:
        relevant_events['Duel_Won'] = 0
        relevant_events['Duel_Attempt'] = 0

    # Keep only the columns needed for QoS calculation
    columns_to_keep = [
        'Time_Minute', 'Network_Segment', 'Node_ID', 'Node_Name', 'type',
        'Pass_Attempt', 'Pass_Successful', 'Duel_Attempt', 'Duel_Won'
    ]
    
    processed_logs = relevant_events[columns_to_keep]
    print(f"[NOC INFO] Flattening complete. Output shape: {processed_logs.shape}")
    
    return processed_logs

if __name__ == "__main__":
    # Test the ingestion script on a Barcelona match (El Clasico 2019)
    MATCH_ID = 303596 
    raw_logs = fetch_match_data(MATCH_ID)
    processed_logs = process_and_flatten_data(raw_logs)
    print(processed_logs.head())
