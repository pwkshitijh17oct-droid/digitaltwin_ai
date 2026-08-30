# DIGITALTWIN.AI — 35-Station Assembly Line Digital Twin Control Center

**DIGITALTWIN.AI** is a modern, dark industrial control center prototype for monitoring, analyzing, and controlling a 35-station vehicle manufacturing assembly line.

The application connects directly to an integrated 35-station discrete-event python simulation engine (`IntegratedSimulationController`), serving as the single source of truth for station operational states, cycle times, queues, equipment health, sensor parameters, defects, and telemetry.

---

## 🏭 35-Station Virtual Assembly Line Coverage

The 35 stations span 3 manufacturing shops loaded dynamically from `simulator/phase1_station_config.json`:

1. **BODY / BIW SHOP (`S01` to `S10`)**:
   - `S01`–`S06`: Body Framing Weld 1–4 & Roof Weld
   - `S07`: Closures Hanging
   - `S08`–`S09`: Geometry Laser Scanning & Body Buffing Inspection
   - `S10`: Buffer Station 1 (Sensorless storage buffer)

2. **PAINT SHOP (`S11` to `S20`)**:
   - `S11`–`S12`: Pre-treatment Degreasing & E-Coat ED Tank
   - `S13`: ED Baking Oven
   - `S14`: Underbody PVC Sealing
   - `S15`–`S17`: Primer, Base, and Clear Coat Painting
   - `S18`: Final Paint Baking Oven
   - `S19`: Paint Quality Inspection
   - `S20`: Buffer Station 2 (Sensorless storage buffer)

3. **GENERAL ASSEMBLY & EOL (`S21` to `S35`)**:
   - `S21`–`S24`: Wire Harness, Sound Proofing, Cockpit, Fuel Tank
   - `S25`: Powertrain Marriage (Mechanical Assembly)
   - `S26`–`S31`: Fluid Filling, Glazing, Interior, Seats, Wheels, Doors Marriage
   - `S32`–`S35`: Alignment Calibration, Dynamic Brake/Roll Test, Monsoon Water Leak Test, Final Buyoff

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+
- pip or uv

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Alternatively, using uv:)*
```bash
uv venv
uv pip install -r requirements.txt
```

### 2. Launch the Control Center
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 🕹 Simulation Controls & Navigation

### Permanent Sidebar Controls:
- **`▶ RUN`**: Starts/resumes continuous background simulation thread.
- **`⏸ PAUSE`**: Suspends simulation execution without resetting state.
- **`↻ RESET`**: Resets engine state, vehicles, and telemetry generation.
- **`1x / 2x / 5x`**: Speed multiplier toggles.
- **Simulation Time Readout**: Displays active production day and time.

### Main Navigation Pages:
1. **🏭 Overview**:
   - Live KPI cards (Vehicles Released, Completed, Active Vehicles, Throughput JPH, Line Takt, Current Bottleneck).
   - Global active alert banner with quick-jump station inspection.
   - Interactive 35-station virtual assembly line with compact status nodes (`🟢`, `🟡`, `🔴`, `🔵`, `⚪`).
   - Slide-out **Right-Side Station Detail Drawer** displaying real operational metrics, equipment health bar, tool replacement counts, manual operator reset action, and dynamic IoT sensor parameters (or sensorless notice).
2. **⚠ Bottleneck Intelligence**:
   - Primary current bottleneck details & secondary trend-based projection.
   - Plotly interactive Cycle Time vs Line Takt chart.
   - Queue Accumulation vs Buffer Capacity chart.
   - Station Bottleneck Pressure Ranking table & chart.
3. **🧠 Quality Intelligence**:
   - Simulated DefectEngine monitoring stream.
   - Vehicle defect probability, risk levels, and primary defect causes.
   - Automated Adaptive Quality Testing protocol simulation.
   - Blueprint for future station-specific ML model integration (S01 to S35 models).
4. **📊 Analytics**:
   - Multi-shop and station telemetry filters.
   - Equipment health degradation curves across equipment-driven stations.
   - Historical telemetry plots and raw log tables.
   - End-to-end digital twin system data-flow diagram.

---

## 🔌 Architecture & Data Adapter Layer

The frontend is completely decoupled from internal simulator mechanics via [`data/adapter.py`](data/adapter.py).

```
                      DIGITALTWIN.AI
                            │
                            v
                    STREAMLIT WEBSITE
                            │
                       DATA ADAPTER
                            │
                            v
             INTEGRATED SIMULATION CONTROLLER
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           v                v                v
      LINE ENGINE      SENSOR ENGINE    HEALTH/MAINTENANCE
           │                │                │
           └────────────────┼────────────────┘
                            │
                            v
                        TELEMETRY
```

### Future Machine Learning Integration:
Future station-specific ML models (e.g. `S01 Model`, `S25 Model`, `S35 Model`) will plug directly into `adapter.get_quality_predictions()`. The frontend UI consumes normalized prediction records, isolating visual rendering from ML model internals.

---

## 📂 Project Structure

```
digitaltwin_ai/
├── app.py                      # Main Streamlit entrypoint with state preservation
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── test_app_logic.py           # Integration & logic test suite
├── simulator/                  # Integrated simulation engine
│   ├── simulation_controller.py
│   ├── phase1_station_config.json
│   ├── phase2_sensor_engine.py
│   ├── phase3_health_maintenance_engine.py
│   ├── phase4_incremental_line_engine.py
│   ├── phase5_telemetry_generator.py
│   ├── phase7_data_layer.py
│   ├── defect_model.py
│   └── validate_simulator.py
├── data/
│   └── adapter.py              # Data adapter bridge to simulator controller
├── config/
│   └── styles.py               # Dark industrial CSS design system
├── components/
│   ├── sidebar.py              # Permanent sidebar & simulation controls
│   ├── kpi_cards.py            # Real simulator KPI widgets
│   ├── assembly_line.py        # 35-station compact node assembly line
│   ├── station_drawer.py       # Slide-out right-side station detail panel
│   ├── alerts.py               # Global alert banner
│   └── charts.py               # Plotly dark industrial visualizers
└── views/
    ├── overview.py             # Page 1: Overview
    ├── bottleneck.py           # Page 2: Bottleneck Intelligence
    ├── quality.py              # Page 3: Quality Intelligence
    └── analytics.py            # Page 4: Analytics
```

---

## 🧪 Verification & Testing

Run the automated integration test suite:
```bash
python test_app_logic.py
```
This tests controller singleton instantiation, 35-station configuration matching, dynamic sensor coverage vs sensorless buffer handling, run/pause/reset lifecycle, operator health resets, bottleneck pressure calculations, and defect evaluation streams.
