import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl.styles import PatternFill
import os

def generate_incident_log(incidents_df, filename="Incident_Log.xlsx"):
    """
    Acts as the 'Automated IT Reporting Tool'.
    Exports the critical faults to an Excel spreadsheet and applies visual SLA alerts (Red formatting).
    """
    print(f"[NOC INFO] Generating Automated Incident Report: {filename}...")
    
    # Select columns for the final executive report
    report_columns = [
        'Time_Window', 'Network_Segment', 'Node_ID', 'Node_Name', 
        'Total_Actions', 'QoS_Rolling_15m', 'QoS_Z_Score', 'Node_Status'
    ]
    
    report_data = incidents_df[report_columns].copy()
    
    # Sort by time so the NOC engineer can see a timeline of issues
    report_data = report_data.sort_values(by=['Time_Window', 'QoS_Z_Score'])
    
    # Write to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        report_data.to_excel(writer, index=False, sheet_name='SLA_Breaches')
        
        # Access the openpyxl workbook and sheet to add colors (Data Engineering touch)
        workbook  = writer.book
        worksheet = writer.sheets['SLA_Breaches']
        
        # Define a red fill for SLA Breaches
        red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        
        # Iterate through the rows and color those labeled 'SLA BREACH (CRITICAL)'
        # In report_columns, 'Node_Status' is index 7 (0-indexed), which is column 8 (1-indexed) in Excel
        for row in range(2, len(report_data) + 2):  # Skip header (row 1)
            status_val = worksheet.cell(row=row, column=8).value
            if status_val == 'SLA BREACH (CRITICAL)':
                # Color the whole row red
                for col in range(1, 9):
                    worksheet.cell(row=row, column=col).fill = red_fill

    print(f"[NOC INFO] Incident Log successfully saved to {os.path.abspath(filename)}")

def plot_degradation_timeline(team_df, team_name, filename="degradation_plot.png"):
    """
    Visualizes the 'Network Traffic Overload' and QoS drop off over time.
    Plots the QoS index of players on a specific team to show when specific nodes degraded.
    """
    print(f"[NOC INFO] Rendering Degradation Plot for cluster: {team_name}...")
    
    # Filter data for the requested team
    df = team_df[team_df['Network_Segment'] == team_name].copy()
    
    plt.figure(figsize=(14, 8))
    sns.set_style("darkgrid") # Looks more like a monitoring dashboard
    
    # Plot a line for each primary node (player with >= 20 actions in the match)
    # This avoids cluttering the graph with subs who played 5 mins
    action_counts = df.groupby('Node_Name')['Total_Actions'].sum()
    primary_nodes = action_counts[action_counts >= 20].index
    
    plot_data = df[df['Node_Name'].isin(primary_nodes)]
    
    # Create the lineplot
    ax = sns.lineplot(
        data=plot_data,
        x='Time_Window', 
        y='QoS_Rolling_15m',
        hue='Node_Name', 
        marker='o',
        linewidth=2,
        alpha=0.8
    )
    
    # Add a horizontal line representing the "SLA Threshold" (e.g., 50% QoS)
    plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='Critical SLA Threshold (50%)')
    
    # Styling the plot to look like a NOC Dashboard
    plt.title(f"Network QoS Degradation Monitor - Cluster: {team_name}", fontsize=16, fontweight='bold')
    plt.xlabel("Session Timeline (Minutes)", fontsize=12)
    plt.ylabel("QoS Index (Rolling 15m Avg %)", fontsize=12)
    plt.ylim(0, 105) # QoS is 0-100%
    
    # Move legend outside the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., title='Network Nodes')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"[NOC INFO] Degradation Plot plotted and saved to {os.path.abspath(filename)}")

if __name__ == "__main__":
    # Test script standalone (requires preceding steps)
    from data_ingestion import fetch_match_data, process_and_flatten_data
    from qos_engine import calculate_qos_index, apply_hardware_fatigue_simulation, detect_critical_nodes
    
    # Run the Pipeline
    MATCH_ID = 303596 
    raw = fetch_match_data(MATCH_ID)
    processed = process_and_flatten_data(raw)
    qos_data = calculate_qos_index(processed)
    fatigue_data = apply_hardware_fatigue_simulation(qos_data)
    final_data, faults = detect_critical_nodes(fatigue_data)
    
    # reporting
    generate_incident_log(faults)
    plot_degradation_timeline(final_data, team_name="Barcelona")
