# SquadSentinel: Football Network Operations Center (NOC) Model

## Overview
**SquadSentinel** is a Data Engineering pipeline that applies enterprise telecommunications and IT infrastructure concepts to sports analytics. It treats a football team as a critical network cluster and evaluates player metrics the same way a Network Operations Center (NOC) would evaluate a server array or a cloud architecture.

Built entirely with Python and Pandas, the system extracts real-time logs, calculates Quality of Service (QoS) indices, and uses statistical anomalies to detect degraded hardware (player fatigue/underperformance).

## The Infrastructure Analogy
In standard IT infrastructure environments, engineers monitor thousands of nodes. When a node's latency increases or its packet loss ratio balloons, the system alerts the engineer to swap the hardware or reroute traffic before the network cluster fails. SquadSentinel applies this exact logic to a football match:

| IT / Telecom Concept | Football Equivalent | Explanation |
| :--- | :--- | :--- |
| **Network Cluster** | The Football Team | The synchronized unit operating together to achieve a goal (e.g., Barcelona). |
| **Operating Node** | A single Player | The individual hardware unit processing data and handling load. |
| **Data Packet / Payload** | Pass Attempted | The core unit of communication traversing the network. |
| **Packet Loss** | Incomplete Pass | A payload that failed to reach its destination. |
| **Hardware Stress** | Duels Attempted & Won | The physical/processing load a node must withstand under pressure. |
| **Node Degradation** | Physical Fatigue | A drop in the Quality of Service (QoS) Index, calculated using a 15-minute rolling average. |
| **SLA Breach (Fault)** | Severe Underperformance | A node whose QoS falls below an absolute threshold (e.g., 80% accuracy) AND deviates significantly from the cluster's moving average. |

## Pipeline Architecture & Data Flow

| Phase | Component | Action | Output |
| :--- | :--- | :--- | :--- |
| **1. Extraction** | `data_ingestion.py` | Fetches massive raw JSON event logs from the REST API (StatsBomb). | Raw JSON Payload |
| **2. Sanity Check** | `data_ingestion.py` | Validates routing headers (`player_id`, `type`). Corrupted packets (NaNs) are strictly dropped. | Cleaned Data |
| **3. Normalization**| `data_ingestion.py` | Flattens nested JSON structures into an analytics-ready DataFrame. | Flat Relational Table |
| **4. QoS Engine** | `qos_engine.py` | Calculates the node's stability metric based on routing success and stress capacity. | Base QoS Metrics |
| **5. Anomaly Det.** | `qos_engine.py` | Uses Python's Rolling Averages and Z-Scores to continuously detect node failures and SLA breaches. | Fault Logs |
| **6. Reporting** | `reporter.py` | Generates a conditionally formatted Excel incident log and renders an automated traffic degradation plot. | Visual Artifacts |

### Technical Highlights
*   **Vectorized Processing:** Uses vectorized operations in Pandas to ensure $O(1)$ or $O(n)$ processing speed per column, avoiding costly loops and optimizing memory for large datasets.
*   **Weighted QoS Algorithm:** The QoS calculation uses adjustable weights to simulate traffic prioritization (Passes vs. Duels), similar to how 5G Network Slicing prioritizes different data types.
*   **Time-Series Smoothing:** Implements rolling windows to eliminate raw data "noise", providing a clear, continuous view of performance degradation in real-time.

## Enterprise Features Incorporated
To meet enterprise standards, this pipeline relies on robust data engineering principles:
1.  **Data Sanity Check**: Ensures 100% data integrity before processing by dropping malformed packets.
2.  **SLA Thresholds**: We've codified Service Level Agreements directly into the anomaly detection engine. It's not just a relative drop in form; it's a breach of a predefined performance contract.
3.  **Dockerization**: The entire pipeline is containerized, enabling immediate deployment across any cloud cluster.

## Running the Pipeline

Ensure you have your virtual environment activated and dependencies installed (`pandas`, `matplotlib`, `seaborn`, `openpyxl`, `statsbombpy`).

Run the orchestrator script:
```bash
python main.py
```

By default, the script will analyze **Barcelona's** performance cluster during the 2019 El Clasico. 
You can switch the target cluster by passing arguments:
```bash
python main.py --match-id 22912 --team "Tottenham Hotspur"
```

## Deployment & CI/CD
This pipeline is fully containerized and includes Continuous Integration logic:
*   **Docker Compatibility**: Can be deployed immediately on any cloud cluster.
```bash
docker build -t squad_sentinel .
docker run -v ${PWD}:/app squad_sentinel
```
*   **GitHub Actions CI/CD**: Every push to the `main` branch automatically triggers a test build and runs a validation match (Match ID 303430) to ensure Data Sanity Checks and the QoS Engine are operational before merging.

## System Outputs
All generated artifacts are automatically stored in the dynamically created `reports/` directory with standardized naming conventions:
1.  **reports/SLA_Breach_Log_Match_[ID]_[Cluster].xlsx**: A spreadsheet structured for management, automatically conditional-formatting critical `SLA BREACH` rows in red for immediate attention.
2.  **reports/Degradation_Plot_Match_[ID]_[Cluster].png**: A timeline visualization that plots exactly when nodes degraded or failed to process their required loads accurately.

## Future Scalability
*   **Real-time Streaming**: Migrating from batch processing of REST API data to Apache Kafka for real-time match/network monitoring.
*   **Predictive AI**: Implementing an LSTM model to predict node failure (fatigue) 15-20 minutes before an SLA breach occurs, triggering automated alerts for preemptive "hot-swaps".

## Potential Interview Notes / Q&A

**"Why did you choose to treat a football match like a network?"**  
*Because both domains rely on complex, interdependent systems operating under stress. A football team passing the ball is essentially a mesh network routing packets. Treating it this way allowed me to apply proven IT infrastructure logic (QoS, Fault Management, Anomaly Detection) to a completely different dataset, demonstrating abstract problem-solving and system architectural thinking.*

**"How would you scale this system for all matches in a year?"**  
*I would transition from the current local script orchestrator to a cloud-based Airflow DAG. The extraction phase would run asynchronously (e.g., pulling multiple APIs concurrently). The JSON flattening and QoS processing would be migrated from local Pandas to PySpark or Snowflake for distributed computing. Final reports would be piped directly into a BI tool like Tableau or PowerBI instead of generating local Excel files.*
