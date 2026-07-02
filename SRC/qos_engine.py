import pandas as pd
import numpy as np

def calculate_qos_index(df, weather_severity=0.0):
    """
    Performance Score Algorithm.
    Calculates a Quality of Service (Performance) metric based on successful passes
    and physical load absorption (duels won).
    If weather_severity > 0, we apply a 'Transmission Penalty' to unsuccessful passes.
    """
    print(f"[INFO] Calculating Performance Score (Env Adjusted: {weather_severity})...")
    
    # We group by the minimum 5-minute interval to smooth out the data initially
    # but still allow for time-series flow
    df['Time_Window'] = (df['Time_Minute'] // 5) * 5
    
    # Aggregate data into 5-minute chunks for each player
    agg_df = df.groupby(['Player_ID', 'Player_Name', 'Team_Name', 'Time_Window']).agg(
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
    
    # Environment Impact: Weather reduces accuracy by a factor
    # (e.g., if severity is 0.3, it penalizes the Pass Accuracy specifically)
    agg_df['Pass_Acc'] = agg_df['Pass_Acc'] * (1 - (weather_severity * 0.5))
    
    # Let's adjust weight: 0.6 for Pass accuracy, 0.4 for Duels
    agg_df['QoS_Index'] = (agg_df['Pass_Acc'] * 0.6) + (agg_df['Duel_Acc'] * 0.4)
    
    # Scale QoS from 0-1 to 0-100%
    agg_df['QoS_Index'] = agg_df['QoS_Index'] * 100
    
    return agg_df

def calculate_player_roi(agg_df, team_name):
    """
    Simulates the 'Transfermarkt Financial API' integration.
    Calculates ROI: (Market Value in M€ / Avg Performance Score).
    Lower value = Higher Financial Efficiency.
    """
    # Approx Transfermarkt Market Values (2019) for Barcelona players analyzed
    market_values = {
        'Lionel Andrés Messi Cuccittini': 150.0,
        'Luis Alberto Suárez Díaz': 50.0,
        'Antoine Griezmann': 120.0,
        'Frenkie de Jong': 90.0,
        'Sergio Busquets i Burgos': 35.0,
        'Ivan Rakitić': 25.0,
        'Gerard Piqué Bernabéu': 35.0,
        'Clément Nicolas Laurent Lenglet': 60.0,
        'Jordi Alba Ramos': 40.0,
        'Sergi Roberto Carnicer': 40.0,
        'Marc-André ter Stegen': 90.0
    }
    
    print(f"[FINANCIAL ENGINE] Calculating ROI based on Market Capitalization for {team_name}...")
    
    # Map the values to a new column
    agg_df['Market_Value_M€'] = agg_df['Player_Name'].map(market_values).fillna(20.0) # Default to 20M for others
    
    # Calculate ROI (M€ per 1% of Performance)
    # We use the raw QoS_Index for this or the average
    player_avg_qos = agg_df.groupby('Player_Name')['QoS_Index'].transform('mean')
    agg_df['ROI_Efficiency'] = agg_df['Market_Value_M€'] / (player_avg_qos + 0.001)
    
    return agg_df

def apply_hardware_fatigue_simulation(agg_df):
    """
    Simulates 'Player Fatigue' using Dual Rolling Averages (5-min vs 20-min moving windows).
    Helps detect if a Player's performance is degrading over time and predict fatigue limit.
    """
    print("[INFO] Applying Rolling Windows for Time-Series Fatigue Analysis...")
    
    # Sort to ensure time is perfectly sequential for the rolling function
    agg_df = agg_df.sort_values(by=['Player_ID', 'Time_Window'])
    
    # We keep Performance_Rolling_15m for backward compatibility with existing SLA detection
    agg_df['Performance_Rolling_15m'] = agg_df.groupby('Player_ID')['QoS_Index'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    
    # Short-term Memory (5 minutes - 1 period since we aggregated by 5 mins)
    agg_df['Performance_Rolling_5m'] = agg_df.groupby('Player_ID')['QoS_Index'].transform(
        lambda x: x.rolling(window=1, min_periods=1).mean()
    )
    
    # Long-term Memory (20 minutes - 4 periods)
    agg_df['Performance_Rolling_20m'] = agg_df.groupby('Player_ID')['QoS_Index'].transform(
        lambda x: x.rolling(window=4, min_periods=1).mean()
    )
    
    # Predictive Warning: Short term < Long term by a margin (e.g., 20% drop) AND Long term is valid
    agg_df['Predictive_Warning'] = np.where(
        (agg_df['Time_Window'] >= 20) & # Only start predicting after 20 mins of data
        (agg_df['Performance_Rolling_5m'] < (agg_df['Performance_Rolling_20m'] - 20.0)),
        True, False    )
    
    warnings = agg_df[agg_df['Predictive_Warning']]
    if not warnings.empty:
        # Print a few samples of the predictive alerts
        for idx, row in warnings.drop_duplicates(subset=['Player_Name']).head(3).iterrows():
            print(f"[PREDICTIVE ALERT] Player '{row['Player_Name']}' shows rapid structural fatigue at minute {row['Time_Window']}. Approaching Underperformance Limit.")
            
    return agg_df

import networkx as nx

def calculate_network_centrality(processed_df, team_name):
    """
    Uses Network Theory to find the 'Playmaker' or 'Tactical Hub' of the Team.
    Builds a directed graph of successful interactions (passes) between players.
    """
    print(f"[INFO] Calculating Passing Centrality Matrix for team: {team_name}...")
    
    # Filter successful passes for the specific team
    passes = processed_df[(processed_df['Team_Name'] == team_name) & 
                          (processed_df['type'] == 'Pass') & 
                          (processed_df['Pass_Successful'] == 1) &
                          (processed_df['Pass_Recipient_Name'].notna())]
                          
    if passes.empty:
        print("[WARNING] Insufficient data packets for passing network topology mapping.")
        return None
        
    # Build Graph
    G = nx.from_pandas_edgelist(passes, source='Player_Name', target='Pass_Recipient_Name', create_using=nx.DiGraph())
    
    # Calculate Degree Centrality
    centrality = nx.degree_centrality(G)
    
    # Sort nodes by centrality
    sorted_players = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    
    if sorted_players:
        print(f"[INFO] Tactical Hub (Playmaker) identified: {sorted_players[0][0]} with Centrality Score {sorted_players[0][1]:.3f}")
    
    return G

def detect_critical_nodes(agg_df, perf_threshold_pct=80.0):
    """
    The 'Performance Degradation System'.
    Uses Z-Scores and explicit Thresholds to identify statistically significant underperformance.
    If a player drops below the acceptable Reliability threshold (e.g., 80% Performance) AND drops significantly
    compared to the team average, it's flagged as a CRITICAL UNDERPERFORMANCE.
    """
    print("[INFO] Running Performance Deviation & Reliability Check...")
    
    # Need to compare players against their team's average form in that match
    # Calculate Team average and std dev across the entire match
    team_stats = agg_df.groupby('Team_Name')['Performance_Rolling_15m'].agg(['mean', 'std']).reset_index()
    team_stats.rename(columns={'mean': 'Team_Rolling_Mean', 'std': 'Team_Rolling_Std'}, inplace=True)
    
    # Merge back to the main DataFrame
    agg_df = agg_df.merge(team_stats, on='Team_Name', how='left')
    
    # Calculate Z-score
    # Formula: (Z = (X - Mean) / Std Dev)
    agg_df['Performance_Z_Score'] = (agg_df['Performance_Rolling_15m'] - agg_df['Team_Rolling_Mean']) / agg_df['Team_Rolling_Std']
    
    # Flag Players as FATIGUE ALERT if their performance falls below the absolute threshold (e.g. 80%) 
    # OR their Z-score falls below -1.0 (approximating bottom 16% of normal distribution)
    # AND they had significant involvement
    agg_df['Total_Actions'] = agg_df['Total_Passes'] + agg_df['Total_Duels']
    
    conditions = [
        ((agg_df['Performance_Rolling_15m'] < perf_threshold_pct) | (agg_df['Performance_Z_Score'] < -1.0)) & (agg_df['Total_Actions'] >= 2), 
        (agg_df['Performance_Z_Score'] >= -1.0) & (agg_df['Performance_Z_Score'] < 0),
        (agg_df['Performance_Z_Score'] >= 0)
    ]
    
    choices = ['FATIGUE ALERT (CRITICAL)', 'WARNING (SUBOPTIMAL)', 'STABLE']
    
    agg_df['Player_Status'] = np.select(conditions, choices, default='UNKNOWN')
    
    # We'll filter down to severe faults to isolate incidents for the incident log
    incidents = agg_df[agg_df['Player_Status'] == 'FATIGUE ALERT (CRITICAL)'].copy()
    print(f"[INFO] Detected {len(incidents)} severe performance alerts across the match timeline.")
    
    return agg_df, incidents

def generate_actionable_improvement_report(agg_df, team_name):
    """
    Identifies the Top 3 players requiring immediate improvement based on their 
    average Z-score (deviation) and Performance Index throughout the match.
    """
    print(f"\n[INFO] Generating Actionable Improvement Report for {team_name}...")
    
    team_df = agg_df[agg_df['Team_Name'] == team_name].copy()
    
    # Calculate overall match stats for each player
    player_summary = team_df.groupby('Player_Name').agg(
        Avg_Performance=('Performance_Rolling_15m', 'mean'),
        Avg_Z_Score=('Performance_Z_Score', 'mean'),
        Total_Involvement=('Total_Actions', 'sum')
    ).reset_index()
    
    # Filter out players with very little involvement (e.g., late subs with < 15 actions)
    player_summary = player_summary[player_summary['Total_Involvement'] >= 15]
    
    if player_summary.empty:
        print("[WARNING] Not enough data to generate improvement report.")
        return []
        
    # Sort by lowest Z-Score (worst consistent deviation from team average)
    worst_performers = player_summary.sort_values(by='Avg_Z_Score', ascending=True).head(3)
    
    print("\n======================================================")
    print("!! ACTIONABLE INSIGHT: PLAYERS REQUIRING IMPROVEMENT !!")
    print("======================================================")
    
    top_3_names = []
    for idx, row in worst_performers.iterrows():
        top_3_names.append(row['Player_Name'])
        print(f"-> {row['Player_Name']}")
        print(f"   Avg Performance: {row['Avg_Performance']:.1f}% | Dev: {row['Avg_Z_Score']:.2f} StdDev | Actions: {row['Total_Involvement']}")
        
    print("======================================================\n")
    return top_3_names

if __name__ == "__main__":
    from data_ingestion import fetch_match_data, process_and_flatten_data
    
    MATCH_ID = 303596 
    raw = fetch_match_data(MATCH_ID)
    processed = process_and_flatten_data(raw)
    
    qos_data = calculate_qos_index(processed)
    fatigue_data = apply_hardware_fatigue_simulation(qos_data)
    final_data, faults = detect_critical_nodes(fatigue_data)
    
    print("\n[SAMPLE FATIGUE ALERTS]")
    print(faults[['Time_Window', 'Player_Name', 'Team_Name', 'Performance_Rolling_15m', 'Performance_Z_Score', 'Player_Status']].head(10))
