import os
import argparse
from data_ingestion import fetch_match_data, process_and_flatten_data
from qos_engine import calculate_qos_index, apply_hardware_fatigue_simulation, detect_critical_nodes
from reporter import generate_incident_log, plot_degradation_timeline

def run_pipeline(match_id, team_name):
    print("======================================================")
    print(f"SQUAD SENTINEL - NOC PIPELINE INITIALIZING...")
    print(f"Target Session: Match ID {match_id} | Focus Cluster: {team_name}")
    print("======================================================\n")
    
    # 1. Extraction (Ingestion)
    print(">>> PHASE 1: DATA PIPELINE EXTRACTION")
    raw_logs = fetch_match_data(match_id)
    
    # 2. Transformation (Flattening)
    print("\n>>> PHASE 2: SCHEMA NORMALIZATION")
    processed_logs = process_and_flatten_data(raw_logs)
    
    # 3. Analytics Engine (QoS & Fatigue)
    print("\n>>> PHASE 3: QOS METRICS & TIME-SERIES CALCULATION")
    qos_data = calculate_qos_index(processed_logs)
    fatigue_data = apply_hardware_fatigue_simulation(qos_data)
    
    # 4. Anomaly Detection
    print("\n>>> PHASE 4: ANOMALY (FAULT) DETECTION")
    final_data, faults = detect_critical_nodes(fatigue_data)
    
    # 5. Reporting
    print("\n>>> PHASE 5: AUTOMATED BUSINESS INTELLIGENCE")
    
    # Create a dedicated reports directory
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Format team name to be file-system safe
    safe_team_name = team_name.replace(' ', '_').replace('/', '_')
    
    excel_path = os.path.join(reports_dir, f"SLA_Breach_Log_Match_{match_id}_{safe_team_name}.xlsx")
    plot_path = os.path.join(reports_dir, f"Degradation_Plot_Match_{match_id}_{safe_team_name}.png")
    
    generate_incident_log(faults, filename=excel_path)
    plot_degradation_timeline(final_data, team_name=team_name, filename=plot_path)
    
    print("\n======================================================")
    print("SQUAD SENTINEL PIPELINE EXECUTION COMPLETE.")
    print(f"Output 1: {os.path.abspath(excel_path)}")
    print(f"Output 2: {os.path.abspath(plot_path)}")
    print("======================================================")

if __name__ == "__main__":
    # We can use argparse to make it a true CLI tool
    parser = argparse.ArgumentParser(description="SquadSentinel - Football Network Operations Center")
    parser.add_argument("--match-id", type=int, default=303596, help="StatsBomb Match ID (Default: 2019 El Clasico Barcelona vs Real Madrid)")
    parser.add_argument("--team", type=str, default="Barcelona", help="Target Team to Analyze")
    
    args = parser.parse_args()
    
    run_pipeline(args.match_id, args.team)
