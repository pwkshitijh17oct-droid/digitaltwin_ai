# DigitalTwin.ai — 35-Station Assembly Line Digital Twin Control Center

**DigitalTwin.ai** is a modern, dark-industrial digital twin control-center prototype for monitoring and optimizing a 35-station vehicle manufacturing assembly line.

---

## 🏭 35-Station Line Coverage

The assembly line spans 3 full manufacturing shops:
1. **BODY / BIW (Body Construction)**: Stations `S1` to `S10`
   - Underbody welding, framing, bodyside sub-assembly, closures hanging, laser scanning, and buffer.
2. **PAINT SHOP**: Stations `S11` to `S20`
   - Pre-treatment, E-coat ED tank, curing ovens, PVC sealing, primer/base/clear spray, quality inspection, and painted body storage.
3. **GENERAL ASSEMBLY + EOL**: Stations `S21` to `S35`
   - Wire harness, cockpit installation, marriage/powertrain integration (`S25`), wheel mounting (`S30`), alignment, brake/roll tests, monsoon leak test, and final buyoff.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Alternatively, use a virtual environment:)*
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 💡 Key Features & Navigation

- **🏭 Overview (Page 1)**:
  - Live 35-station digital twin assembly line with minimal status nodes (`🟢 S23`, `🟡 S25`, `🔴 S30`).
  - Hover tooltips with real-time cycle times, queues, and utilization.
  - Interactive **Right-Side Station Detail Drawer** showing dynamic process parameters (Torque, Temp, Vibration, Weld Current) on click without leaving the line.
  - Top KPI cards: Production (Shift), Throughput (JPH), Active Bottleneck, Defect Risk.

- **⚠ Bottleneck Intelligence (Page 2)**:
  - Real-time constraint identification for current bottleneck (`S25`) and predicted future bottleneck (`S18`).
  - Plotly interactive **Cycle Time Progression** vs Upper Control Limit.
  - Plotly **Queue Accumulation vs Buffer Capacity** area chart.
  - Plant-wide station bottleneck risk rankings.

- **🧠 Quality Intelligence (Page 3)**:
  - Active vehicle defect risk monitoring stream (`V128`, `V131`, `V125`, etc.).
  - Detailed sensor signal breakdown contributing to defect probability.
  - **Adaptive Quality Testing**: Live demonstration of automated test suite activation and `HOLD FOR INSPECTION` buyoff protocol.

- **📊 Analytics (Page 4)**:
  - Multi-shop and station telemetry filters (1h, 4h, 8h, 24h windows).
  - Cycle time box plot distributions and throughput history.
  - ML model specification cards and 6-layer end-to-end data pipeline architecture diagram.

- **🕹 Global Simulation Controls (Sidebar)**:
  - Controls: `▶️ RUN`, `⏸ PAUSE`, `↻ RESET`.
  - Speed toggles: `1x`, `2x`, `5x`.
  - Demonstrates realistic progressive degradation of `S25` and defect anomaly at `S30`.

---

## 🔌 Data Adapter & Integration

The UI is completely decoupled from the data generator via [`data/data_adapter.py`](data/data_adapter.py). 

When the physical simulator or real ML inference microservice is ready:
1. Connect inputs to the helper functions in `data/data_adapter.py` (`get_simulation_state`, `get_station_data`, `get_bottleneck_predictions`, `get_quality_predictions`, etc.).
2. The UI components will render the incoming real data automatically without modifying frontend code.

---

## 📂 Project Structure

```
digitaltwin_ai/
├── app.py                      # Main Streamlit application entrypoint
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview and setup instructions
├── config/
│   ├── stations.py             # 35-station configuration across 3 shops
│   └── styles.py               # Dark industrial CSS design system
├── data/
│   ├── mock_data.py            # Simulation engine & progression scenarios
│   └── data_adapter.py         # Decoupled interface contract
├── components/
│   ├── sidebar.py              # Persistent sidebar & simulation controls
│   ├── alerts.py               # Global alert banner with quick-jump button
│   ├── kpi_cards.py            # Compact KPI widgets
│   ├── assembly_line.py        # 3-Shop virtual assembly line with compact nodes
│   ├── station_drawer.py       # Slide-out right-side inspection drawer
│   └── charts.py               # Dark industrial Plotly visualizers
└── pages/
    ├── overview.py             # Page 1: Overview
    ├── bottleneck.py           # Page 2: Bottleneck Intelligence
    ├── quality.py              # Page 3: Quality Intelligence
    └── analytics.py            # Page 4: Analytics & Architecture
```
