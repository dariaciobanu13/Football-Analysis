import pandas as pd
import numpy as np

def calculate_qos_index(df):
    """
    Acts as the 'QoS Policy Engine'.
    Calculates a Quality of Service (QoS) metric based on successful data transmission (passes)
    and hardware stress absorption (duels won).
    """
    print("[NOC INFO] Calculating baseline QoS Index per node...")
    
    # We group by the minimum 5-minute interval to smooth out the data initially
    # but still allow for time-series flow
    df['Time_Window'] = (df['Time_Minute'] // 5) * 5
    
    # Aggregate data into 5-minute chunks for each player
    agg_df = df.groupby(['Node_ID', 'Node_Name', 'Network_Segment', 'Time_Window']).agg(
        Total_Passes=pd.NamedAgg(column='Pass_Attempt', aggfunc='sum'),
        Successful_Passes=pd.NamedAgg(column='Pass_Successful', aggfunc='sum'),
        Total_Duels=pd.NamedAgg(column='Duel_Attempt', aggfunc='sum'),
        Duels_Won=pd.NamedAgg(column='Duel_Won', aggfunc='sum')
    ).reset_index()
    
    # QoS Formula: 
    # Weighted calculation treating passes as 60% of the grade and duels as 40%.
    # If 0 attempts, assume 0 for that part of the metric to avoid division by zero
    agg_df['Pass_Acc'] = np.where(agg_df['Total_Passes'] > 0, agg_df['Successful_Passes'] / agg_df['Total_Passes'], 0)
    agg_df['Duel_Acc'] = np.where(agg_df['Total_Duels'] > 0, agg_df['Duels_Won'] / agg_df['Total_Duels'], 0)
    
    # Let's adjust weight: 0.6 for Pass accuracy, 0.4 for Duels
    agg_df['QoS_Index'] = (agg_df['Pass_Acc'] * 0.6) + (agg_df['Duel_Acc'] * 0.4)
    
    # Scale QoS from 0-1 to 0-100%
    agg_df['QoS_Index'] = agg_df['QoS_Index'] * 100
    
    return agg_df

def apply_hardware_fatigue_simulation(agg_df):
    """
    Simulates 'Hardware Fatigue' using Rolling Averages (15-min moving windows).
    Helps detect if a Node's performance is degrading over time.
    """
    print("[NOC INFO] Applying Rolling Windows for Time-Series Analysis...")
    
    # Sort to ensure time is perfectly sequential for the rolling function
    agg_df = agg_df.sort_values(by=['Node_ID', 'Time_Window'])
    
    # Apply a rolling window of 3 periods (which equates to 15 minutes since periods are 5 mins)
    # We use min_periods=1 so we get data even in the first 10 minutes
    agg_df['QoS_Rolling_15m'] = agg_df.groupby('Node_ID')['QoS_Index'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    
    return agg_df

def detect_critical_nodes(agg_df, sla_threshold_pct=80.0):
    """
    The 'Fault Detection System'.
    Uses Z-Scores and explicit SLA Contracts to identify statistically significant underperformance.
    If a node drops below the agreed SLA Threshold (e.g., 80% QoS) AND drops significantly
    compared to the cluster average, it's flagged as an SLA Breach.
    """
    print("[NOC INFO] Running Anomaly Detection & SLA Compliance Check...")
    
    # Need to compare players against their team's average form in that match
    # Calculate Team average and std dev across the entire match
    team_stats = agg_df.groupby('Network_Segment')['QoS_Rolling_15m'].agg(['mean', 'std']).reset_index()
    team_stats.rename(columns={'mean': 'Team_Rolling_Mean', 'std': 'Team_Rolling_Std'}, inplace=True)
    
    # Merge back to the main DataFrame
    agg_df = agg_df.merge(team_stats, on='Network_Segment', how='left')
    
    # Calculate Z-score
    # Formula: (Z = (X - Mean) / Std Dev)
    agg_df['QoS_Z_Score'] = (agg_df['QoS_Rolling_15m'] - agg_df['Team_Rolling_Mean']) / agg_df['Team_Rolling_Std']
    
    # Flag Nodes as SLA BREACH if their performance falls below the absolute SLA threshold (e.g. 80%) 
    # OR their Z-score falls below -1.0 (approximating bottom 16% of normal distribution)
    # AND they had significant involvement
    agg_df['Total_Actions'] = agg_df['Total_Passes'] + agg_df['Total_Duels']
    
    conditions = [
        ((agg_df['QoS_Rolling_15m'] < sla_threshold_pct) | (agg_df['QoS_Z_Score'] < -1.0)) & (agg_df['Total_Actions'] >= 2), 
        (agg_df['QoS_Z_Score'] >= -1.0) & (agg_df['QoS_Z_Score'] < 0),
        (agg_df['QoS_Z_Score'] >= 0)
    ]
    
    choices = ['SLA BREACH (CRITICAL)', 'WARNING (SUBOPTIMAL)', 'STABLE']
    
    agg_df['Node_Status'] = np.select(conditions, choices, default='UNKNOWN')
    
    # We'll filter down to severe faults to isolate incidents for the incident log
    incidents = agg_df[agg_df['Node_Status'] == 'SLA BREACH (CRITICAL)'].copy()
    print(f"[NOC INFO] Detected {len(incidents)} SLA Breach incidents across the match timeline.")
    
    return agg_df, incidents

if __name__ == "__main__":
    from data_ingestion import fetch_match_data, process_and_flatten_data
    
    MATCH_ID = 303596 
    raw = fetch_match_data(MATCH_ID)
    processed = process_and_flatten_data(raw)
    
    qos_data = calculate_qos_index(processed)
    fatigue_data = apply_hardware_fatigue_simulation(qos_data)
    final_data, faults = detect_critical_nodes(fatigue_data)
    
    print("\n[SAMPLE FAULT LOGS]")
    print(faults[['Time_Window', 'Node_Name', 'Network_Segment', 'QoS_Rolling_15m', 'QoS_Z_Score', 'Node_Status']].head(10))
