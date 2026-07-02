# SquadSentinel

**A Python data pipeline that applies NOC-style reliability metrics to football match event data.**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![StatsBomb](https://img.shields.io/badge/Data-StatsBomb_Open_Data-green)](https://github.com/statsbomb/open-data)
[![CI](https://github.com/darknick131/Football-Analysis/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/darknick131/Football-Analysis/actions/workflows/ci-pipeline.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Visual Proof

> Replace the placeholders below with actual screenshots from `SRC/reports/`.

|               Performance Timeline                |            Financial ROI Matrix            |
| :-----------------------------------------------: | :----------------------------------------: |
| `Performance_Timeline_Match_303596_Barcelona.png` | `Financial_ROI_Match_303596_Barcelona.png` |

|               Consistency Violin                |               Improvement Radar                |
| :---------------------------------------------: | :--------------------------------------------: |
| `Consistency_Violin_Match_303596_Barcelona.png` | `Improvement_Radar_Match_303596_Barcelona.png` |

---

## Overview

SquadSentinel ingests football match event data from the StatsBomb open API, computes a per-player Quality of Service (QoS) score using pass accuracy and duel win rate, applies rolling-window fatigue simulation, and flags underperforming players via Z-score anomaly detection. The pipeline exports six charts (matplotlib/seaborn) and one color-coded Excel report to a `reports/` folder — all from a single CLI command.

The project uses NOC/telecom terminology as a framing device: players are "nodes," passes are "data packets," missed passes are "packet loss," and falling below the 80% performance threshold is an "SLA breach." This is a deliberate narrative choice, not an architectural one — the underlying mechanics are standard data engineering: ETL, time-series aggregation, graph centrality, and anomaly detection.

**Domain:** Data Engineering / Sports Analytics — Python backend CLI tool. No web frontend, no mobile component.

---

## Key Features

- **Real match data ingestion** via `statsbombpy` — fetches thousands of structured event records per match from StatsBomb's free open-data API, no API key required.
- **QoS scoring in 5-minute windows** — aggregates Pass Accuracy (60% weight) and Duel Win Rate (40% weight) into a 0–100 performance index per player per time window.
- **Weather penalty simulation** — applies a configurable severity factor (hardcoded to `0.3` = Rain for the demo) that reduces effective pass accuracy by up to 15%.
- **Dual rolling-window fatigue detection** — computes 5-minute and 20-minute rolling averages per player; raises a predictive warning when the short-term average drops more than 20 points below the long-term average after minute 20.
- **Z-score anomaly detection** — compares each player's 15-minute rolling performance against the team mean and standard deviation; labels each window as `FATIGUE ALERT (CRITICAL)`, `WARNING (SUBOPTIMAL)`, or `STABLE`.
- **Passing network centrality** — builds a directed `networkx` graph from successful passes and computes degree centrality to identify the tactical playmaker ("hub node").
- **Financial ROI calculation** — maps 2019 Transfermarkt market values to Barcelona squad members and calculates M€ spent per 1% of performance delivered.
- **Six automated visual reports** — Performance Timeline, Consistency Violin, Improvement Radar, Weather Impact, Financial ROI bubble chart, and a Kafka throughput chart.
- **Color-coded Excel export** — `openpyxl` writes critical-alert rows with a red `PatternFill` for at-a-glance review.
- **Stream simulation mode** — `--mode stream` replays events through a Python generator at ~200 events/second to demonstrate an event-driven architecture pattern (no real Kafka broker required).
- **Docker and GitHub Actions CI** — `Dockerfile` and a CI pipeline that validate the full batch run on every push to `main`.

---

## System Architecture & Data Flow

```
CLI: python main.py --match-id N --team T --mode [batch|stream]
            │
            ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 1 — data_ingestion.py                         │
│  sb.events(match_id) → raw DataFrame (~3000+ rows)  │
│  Filter to 'Pass' and 'Duel' event types            │
│  Flatten: pass_outcome, duel_outcome, pass_recipient│
│  Drop rows with NaN in type / player_id / team      │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 2 — qos_engine.calculate_qos_index()          │
│  Group by (Player, Team, 5-min Time_Window)         │
│  Pass_Acc = Successful_Passes / Total_Passes        │
│  Pass_Acc *= (1 - weather_severity * 0.5)           │
│  Duel_Acc = Duels_Won / Total_Duels                 │
│  QoS_Index = (Pass_Acc*0.6 + Duel_Acc*0.4) * 100   │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 3 — qos_engine.calculate_player_roi()         │
│  Map hardcoded 2019 market values to player names   │
│  ROI_Efficiency = Market_Value_M€ / avg_QoS_Index   │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 4 — qos_engine.apply_hardware_fatigue_sim()   │
│  Rolling 5m  (window=1 period)                      │
│  Rolling 15m (window=3 periods) ← used for alerts  │
│  Rolling 20m (window=4 periods)                     │
│  Predictive_Warning: 5m < (20m − 20) after min 20  │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 4.5 — qos_engine.calculate_network_centrality │
│  Build DiGraph from successful passes               │
│  nx.degree_centrality() → identify playmaker        │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 5 — qos_engine.detect_critical_nodes()        │
│  Z_score = (15m_rolling − team_mean) / team_std     │
│  CRITICAL if: (15m_rolling < 80 OR Z < −1.0)       │
│               AND total_actions >= 2                │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PHASE 6 — reporter.py                               │
│  Performance_Timeline.png  (line chart, 15m avg)    │
│  Consistency_Violin.png    (QoS distribution)       │
│  Weather_Impact.png        (observed vs potential)  │
│  Financial_ROI.png         (bubble: perf vs M€)     │
│  Improvement_Radar.png     (spider, top 3 worst)    │
│  Performance_Alerts_Log.xlsx (red-highlighted rows) │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
              SRC/reports/  (6 PNG + 1 XLSX)
```

**Alternate path (`--mode stream`):** `kafka_streamer.py` replays the processed DataFrame event-by-event through a Python generator with `time.sleep(0.005)`, filtering for the target team and printing a live counter every 50 events. Stops after 300 events and writes a throughput chart.

---

## Project Structure

```
Football-Analysis/
├── .github/
│   └── workflows/
│       └── ci-pipeline.yml       # GitHub Actions: install deps, run batch pipeline on push to main
├── SRC/
│   ├── main.py                   # CLI entry point; orchestrates all 6 pipeline phases
│   ├── data_ingestion.py         # StatsBomb API fetch, Pass/Duel filtering, schema flattening
│   ├── qos_engine.py             # QoS formula, rolling fatigue windows, Z-score detection, ROI, NetworkX
│   ├── reporter.py               # All chart generation (matplotlib/seaborn) + Excel export (openpyxl)
│   ├── kafka_streamer.py         # Stream mode simulation (Python generator, no real Kafka dependency)
│   ├── Dockerfile                # python:3.11-slim; ENTRYPOINT = python main.py
│   └── reports/                  # Auto-generated on each run (not committed in CI)
│       ├── Performance_Timeline_Match_*.png
│       ├── Consistency_Violin_Match_*.png
│       ├── Weather_Impact_Match_*.png
│       ├── Financial_ROI_Match_*.png
│       ├── Improvement_Radar_Match_*.png
│       ├── Kafka_Stream_Throughput.png
│       └── Performance_Alerts_Log_Match_*.xlsx
└── README.md
```

---

## Tech Stack

| Layer            | Library        | Version | Role in this project                                                         |
| :--------------- | :------------- | :------ | :--------------------------------------------------------------------------- |
| Data source      | `statsbombpy`  | 1.17.0  | Fetches real football event data from StatsBomb's free open API              |
| Data processing  | `pandas`       | 3.0.1   | DataFrame aggregation, groupby, rolling windows, Excel export                |
| Numerical        | `numpy`        | 2.4.3   | Vectorized QoS formula, Z-score calculation, `np.select` for status labeling |
| Charting         | `matplotlib`   | —       | Base rendering engine for all PNG output                                     |
| Charting         | `seaborn`      | 0.13.2  | Violin plots, line plots, bar plots with consistent styling                  |
| Excel export     | `openpyxl`     | 3.1.5   | Writes `.xlsx` and applies red `PatternFill` to critical-alert rows          |
| Graph analysis   | `networkx`     | —       | Directed passing graph, degree centrality to find the playmaker              |
| Runtime          | Python         | 3.11    | Target version pinned in CI and Docker                                       |
| Containerization | Docker         | —       | `python:3.11-slim` base; single-command execution                            |
| CI/CD            | GitHub Actions | —       | Runs full batch pipeline on every push to `main`                             |

> No database, web framework, or message broker is required at runtime.

---

## Getting Started

### Prerequisites

- Python 3.11+
- No API keys needed — StatsBomb open data is freely accessible

### Local setup

```bash
# 1. Clone the repository
git clone https://github.com/darknick131/Football-Analysis.git
cd Football-Analysis

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install pandas matplotlib seaborn openpyxl statsbombpy networkx

# 4. Run the pipeline
cd SRC
python main.py
```

Reports are written to `SRC/reports/`.

### Docker

```bash
cd SRC

# Build
docker build -t squadsentinel .

# Run (mount reports folder to retrieve output files)
docker run --rm -v "${PWD}/reports:/app/reports" squadsentinel
```

---

## Usage

### Batch mode (default)

Runs the full 6-phase analytics pipeline and writes all reports.

```bash
# Default: Match 303596, Barcelona
python main.py

# Custom match and team
python main.py --match-id 303430 --team "Barcelona"
```

| Argument     | Default     | Description                                                  |
| :----------- | :---------- | :----------------------------------------------------------- |
| `--match-id` | `303596`    | StatsBomb Match ID                                           |
| `--team`     | `Barcelona` | Team name — must match the exact string StatsBomb uses       |
| `--mode`     | `batch`     | `batch` for full analysis, `stream` for streaming simulation |

### Stream mode

Replays events through a Python generator and produces a throughput chart. Exits after 300 team events.

```bash
python main.py --mode stream --team "Barcelona"
```

### Finding valid match IDs

```python
from statsbombpy import sb

# Browse available competitions
competitions = sb.competitions()
print(competitions[['competition_id', 'competition_name', 'season_name']])

# List matches for a competition (e.g. La Liga 2019/20)
matches = sb.matches(competition_id=11, season_id=42)
print(matches[['match_id', 'home_team', 'away_team', 'match_date']])
```

---

## Example Output

```
======================================================
SQUAD SENTINEL - FOOTBALL ANALYTICS PIPELINE...
Target Session: Match ID 303596 | Focus Team: Barcelona
======================================================

>>> PHASE 1: DATA PIPELINE EXTRACTION (Log Harvester)
[INFO] Successfully ingested 4158 match events.
[WARNING] Dropped 11 corrupted data points (NaN in critical fields).
[INFO] Flattening complete. Output shape: (1227, 10)
[ENVIRONMENT MONITOR] Weather Service Status: Rain
[ENVIRONMENT MONITOR] Weather Severity Impact: 30.0% additional stress on data transmission.

>>> PHASE 3: PERFORMANCE METRICS & TIME-SERIES FATIGUE CALCULATION
[INFO] Calculating Performance Score (Env Adjusted: 0.3)...
[FINANCIAL ENGINE] Calculating ROI based on Market Capitalization for Barcelona...
[PREDICTIVE ALERT] Player 'Thibaut Courtois' shows rapid structural fatigue at minute 60.
[PREDICTIVE ALERT] Player 'Sergio Ramos Garcia' shows rapid structural fatigue at minute 25.
[PREDICTIVE ALERT] Player 'Jordi Alba Ramos' shows rapid structural fatigue at minute 40.

>>> PHASE 4: RELIABILITY (FAULT) DETECTION
[INFO] Detected 301 severe performance alerts across the match timeline.

>>> PHASE 4.5: ADVANCED FOOTBALL ANALYTICS
[INFO] Tactical Hub (Playmaker) identified: Sergi Roberto Carnicer with Centrality Score 1.833

>>> PHASE 5.5: ACTIONABLE INSIGHTS
!! ACTIONABLE INSIGHT: PLAYERS REQUIRING IMPROVEMENT !!
-> Luis Alberto Suarez Diaz    Avg Performance: 35.5% | Dev: -0.94 StdDev | Actions: 31
-> Jordi Alba Ramos            Avg Performance: 39.0% | Dev: -0.57 StdDev | Actions: 62
-> Sergi Roberto Carnicer      Avg Performance: 41.7% | Dev: -0.29 StdDev | Actions: 62

======================================================
SQUAD SENTINEL PIPELINE EXECUTION COMPLETE.
Output 1: .../reports/Performance_Alerts_Log_Match_303596_Barcelona.xlsx
Output 2: .../reports/Performance_Timeline_Match_303596_Barcelona.png
Output 3: .../reports/Consistency_Violin_Match_303596_Barcelona.png
Output 4: .../reports/Weather_Impact_Match_303596_Barcelona.png
Output 5: .../reports/Financial_ROI_Match_303596_Barcelona.png
Output 6: .../reports/Improvement_Radar_Match_303596_Barcelona.png
======================================================
```

---

## Known Issues

| Severity    | Location            | Description                                                                                                                                                                             | Status   |
| :---------- | :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- |
| **Fixed**   | `qos_engine.py:217` | `print()` with a `🚨` emoji crashed on Windows terminals using `cp1250` encoding (`UnicodeEncodeError`). Replaced with plain ASCII `!!`.                                                | Resolved |
| **Warning** | `reporter.py:121`   | seaborn `violinplot` passes `palette` without a `hue` argument. Works on seaborn 0.13.x but will raise an error when seaborn 0.14 releases. Needs `hue='Player_Name'` + `legend=False`. | Open     |

---

## Roadmap

The following are incomplete or stubbed features visible in the current code:

| Gap                          | Current state                                                                                                                  | What's needed                                                                   |
| :--------------------------- | :----------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **Real weather integration** | `simulate_weather_conditions()` in `data_ingestion.py:30` hardcodes `'Rain'` (severity `0.3`) — no HTTP call is made           | Replace with an OpenWeatherMap API call using the match date and venue location |
| **Real Kafka integration**   | `KafkaSimulator` in `kafka_streamer.py:32` uses a Python generator + `time.sleep(0.005)` — no broker required                  | Replace with `confluent-kafka` or `kafka-python` connected to a real broker     |
| **Test suite**               | `pytest` is installed in CI and Docker but zero `test_*.py` files exist in the repository                                      | Unit tests for `calculate_qos_index()` and `detect_critical_nodes()` at minimum |
| **Multi-squad ROI**          | `calculate_player_roi()` in `qos_engine.py:50` has a hardcoded dict of 11 Barcelona 2019 players; all others default to `20M€` | Dynamic lookup from a market-value data source for any team/season              |

---

## Assumptions to Verify

The following are inferences from reading the code, not explicitly stated in any config or doc:

1. **Match 303596 = El Clásico 2019** — inferred from a code comment: `"Test the ingestion script on a Barcelona match (El Clasico 2019)"`. Confirm with `sb.matches()`.
2. **Weather data is always `Rain`** — `simulate_weather_conditions()` hardcodes the weather type; there is no live API call.
3. **Transfermarkt values are static** — the ROI dict reflects 2019 approximate valuations and is not fetched from any external source.
4. **No real Kafka dependency** — `kafka_streamer.py` requires only `time`, `os`, `pandas`, and the two project modules. No `confluent-kafka`, `kafka-python`, or broker connection is present.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss scope.

---

## Contact

**Author:** darknick131  
**GitHub:** [github.com/darknick131](https://github.com/darknick131)  
**Email:** dariasianisia@gmail.com
