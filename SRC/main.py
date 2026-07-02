import os
import argparse
from data_ingestion import fetch_match_data, process_and_flatten_data, simulate_weather_conditions
from qos_engine import calculate_qos_index, apply_hardware_fatigue_simulation, detect_critical_nodes, calculate_network_centrality, generate_actionable_improvement_report, calculate_player_roi
from reporter import generate_incident_log, plot_degradation_timeline, plot_node_stability, plot_improvement_radar, plot_weather_impact, plot_roi_efficiency
from kafka_streamer import consume_stream_simulation

def run_pipeline(match_id, team_name):
    print("======================================================")
    print(f"SQUAD SENTINEL - FOOTBALL ANALYTICS PIPELINE...")
    print(f"Target Session: Match ID {match_id} | Focus Team: {team_name}")
    print("======================================================\n")
    
    # 1. Extraction (Ingestion)
    print(">>> PHASE 1: DATA PIPELINE EXTRACTION (Log Harvester)")
    raw_logs = fetch_match_data(match_id)
    
    # [ENTERPRISE] Weather Service Integration
    env_severity = simulate_weather_conditions()
    
    # 2. Transformation (Flattening)
    print("\n>>> PHASE 2: NORMALIZATION (JSON Flattening)")
    processed_logs = process_and_flatten_data(raw_logs)
    
    # 3. Analytics Engine
    print("\n>>> PHASE 3: PERFORMANCE METRICS & TIME-SERIES FATIGUE CALCULATION")
    qos_data = calculate_qos_index(processed_logs, weather_severity=env_severity)
    
    # [ENTERPRISE] Financial ROI Engine
    qos_data = calculate_player_roi(qos_data, team_name)
    
    fatigue_data = apply_hardware_fatigue_simulation(qos_data)
    
    # 4. Anomaly Detection
    print("\n>>> PHASE 4: RELIABILITY (FAULT) DETECTION")
    final_data, faults = detect_critical_nodes(fatigue_data)
    
    # 4.5 Advanced Analytics (Gold Tier)
    print("\n>>> PHASE 4.5: ADVANCED FOOTBALL ANALYTICS")
    # Network Centrality Matrix
    calculate_network_centrality(processed_logs, team_name)
    
    # 5.5 Actionable Insights (Improvement Matrix)
    print("\n>>> PHASE 5.5: ACTIONABLE INSIGHTS")
    players_to_improve = generate_actionable_improvement_report(final_data, team_name)
    
    # 6. Reporting
    print("\n>>> PHASE 6: AUTOMATED BUSINESS INTELLIGENCE")
    
    # Create a dedicated reports directory
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Format team name to be file-system safe
    safe_team_name = team_name.replace(' ', '_').replace('/', '_')
    
    excel_path = os.path.join(reports_dir, f"Performance_Alerts_Log_Match_{match_id}_{safe_team_name}.xlsx")
    plot_path = os.path.join(reports_dir, f"Performance_Timeline_Match_{match_id}_{safe_team_name}.png")
    violin_path = os.path.join(reports_dir, f"Consistency_Violin_Match_{match_id}_{safe_team_name}.png")
    radar_path = os.path.join(reports_dir, f"Improvement_Radar_Match_{match_id}_{safe_team_name}.png")
    weather_path = os.path.join(reports_dir, f"Weather_Impact_Match_{match_id}_{safe_team_name}.png")
    roi_path = os.path.join(reports_dir, f"Financial_ROI_Match_{match_id}_{safe_team_name}.png")
    
    generate_incident_log(faults, filename=excel_path)
    plot_degradation_timeline(final_data, team_name=team_name, filename=plot_path)
    plot_node_stability(final_data, team_name=team_name, filename=violin_path)
    plot_weather_impact(final_data, env_severity, team_name, filename=weather_path)
    plot_roi_efficiency(final_data, team_name, filename=roi_path)
    
    if players_to_improve:
        plot_improvement_radar(final_data, team_name, players_to_improve, filename=radar_path)
    
    print("\n======================================================")
    print("SQUAD SENTINEL PIPELINE EXECUTION COMPLETE.")
    print(f"Output 1: {os.path.abspath(excel_path)}")
    print(f"Output 2: {os.path.abspath(plot_path)}")
    print(f"Output 3: {os.path.abspath(violin_path)}")
    print(f"Output 4: {os.path.abspath(weather_path)}")
    print(f"Output 5: {os.path.abspath(roi_path)}")
    if players_to_improve:
        print(f"Output 6: {os.path.abspath(radar_path)}")
    print("======================================================")

if __name__ == "__main__":
    # We can use argparse to make it a true CLI tool
    parser = argparse.ArgumentParser(description="SquadSentinel - Football Performance Reliability Tracker [ENTERPRISE]")
    parser.add_argument("--match-id", type=int, default=303596, help="StatsBomb Match ID")
    parser.add_argument("--team", type=str, default="Barcelona", help="Target Team to Analyze")
    parser.add_argument("--mode", type=str, choices=['batch', 'stream'], default='batch', help="Execution Mode: Batch (Full Analysis) or Stream (Real-time Demo)")
    
    args = parser.parse_args()
    
    if args.mode == 'stream':
        consume_stream_simulation(args.match_id, args.team)
    else:
        run_pipeline(args.match_id, args.team)
