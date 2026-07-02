import pandas as pd
from statsbombpy import sb
import numpy as np
import warnings

# Ignore the open data access warning from statsbomb
warnings.filterwarnings("ignore", category=UserWarning, module="statsbombpy")

def fetch_match_data(match_id):
    """
    Simulates a 'Network Log Harvester'.
    Connects to StatsBomb API and extracts all events for a session.
    """
    print(f"[INFO] Initiating data connection to Match ID: {match_id}...")
    try:
        events = sb.events(match_id=match_id)
        print(f"[INFO] Successfully ingested {len(events)} match events.")
        return events
    except Exception as e:
        print(f"[ERROR] Connection failure to Data Source: {e}")
        return pd.DataFrame()

def simulate_weather_conditions():
    """
    Simulates the 'Environment Monitoring Service' (OpenWeatherMap API equivalent).
    Returns a Weather Severity Index (0-1).
    High Severity (Rain/Wind) increases the 'Packet Loss' impact.
    """
    # Simulate a rainy day for the enterprise scenario
    weather_types = ['Clear', 'Cloudy', 'Rain', 'Storm']
    current_weather = 'Rain'
    
    # Severity impact: Clear=0, Cloudy=0.1, Rain=0.3, Storm=0.5
    severity_map = {'Clear': 0.0, 'Cloudy': 0.1, 'Rain': 0.3, 'Storm': 0.5}
    severity = severity_map[current_weather]
    
    print(f"\n[ENVIRONMENT MONITOR] Weather Service Status: {current_weather}")
    print(f"[ENVIRONMENT MONITOR] Weather Severity Impact: {severity * 100}% additional stress on data transmission.")
    
    return severity

def process_and_flatten_data(df):
    """
    Schema Normalizer.
    Cleans the raw log data and extracts critical football features.
    """
    print(f"[INFO] Normalizing schema and processing data...")
    
    # --- 0. Data Sanity Check (Data Integrity) ---
    print(f"[INFO] Performing Data Sanity Check...")
    initial_len = len(df)
    # Ensure critical routing fields exist and remove corrupted packets
    if 'type' not in df.columns or 'player_id' not in df.columns:
        raise ValueError("[CRITICAL ERROR] Payload missing critical headers ('type' or 'player_id').")
    
    df = df.dropna(subset=['type', 'player_id', 'team'])
    dropped = initial_len - len(df)
    if dropped > 0:
        print(f"[WARNING] Dropped {dropped} corrupted data points (NaN in critical fields).")
    else:
        print(f"[INFO] Data Sanity Check Passed. 100% Data Integrity.")
    
    # --- 1. Filter Relevant Match Actions ---
    relevant_events = df[df['type'].isin(['Pass', 'Duel'])].copy()
    
    # --- 2. Extract Event Minute (Timestamping) ---
    relevant_events['Time_Minute'] = relevant_events['minute']
    
    # --- 3. Extract Player IDs & Names ---
    relevant_events['Player_ID'] = relevant_events['player_id']
    relevant_events['Player_Name'] = relevant_events['player']
    relevant_events['Team_Name'] = relevant_events['team']
    
    # --- 4. Flatten JSON/Dictionary nested fields ---
    
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

    # Extract Pass Recipient for Topology Mapping
    if 'pass_recipient' in relevant_events.columns:
        relevant_events['Pass_Recipient_Name'] = relevant_events.apply(
            lambda row: row['pass_recipient'] if row['type'] == 'Pass' else None, axis=1
        )
    else:
        relevant_events['Pass_Recipient_Name'] = None

    # Keep only the columns needed for Analysis
    columns_to_keep = [
        'Time_Minute', 'Team_Name', 'Player_ID', 'Player_Name', 'type',
        'Pass_Attempt', 'Pass_Successful', 'Duel_Attempt', 'Duel_Won', 'Pass_Recipient_Name'
    ]
    
    processed_logs = relevant_events[columns_to_keep]
    print(f"[INFO] Flattening complete. Output shape: {processed_logs.shape}")
    
    return processed_logs

if __name__ == "__main__":
    # Test the ingestion script on a Barcelona match (El Clasico 2019)
    MATCH_ID = 303596 
    raw_logs = fetch_match_data(MATCH_ID)
    processed_logs = process_and_flatten_data(raw_logs)
    print(processed_logs.head())
