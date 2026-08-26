"""
Mock Simulation Engine & State Generator for DigitalTwin.ai.
Generates realistic manufacturing telemetry for all 35 stations.
"""

import math
import random
import time
from typing import Dict, List, Any, Optional
from config.stations import STATIONS_CONFIG, StationInfo

class SimulationEngine:
    def __init__(self):
        self.running: bool = True
        self.speed: int = 1  # 1x, 2x, 5x
        self.tick: int = 8
        self.start_time: float = time.time()
        self.target_production: int = 150
        self.base_jph: float = 42.5
        
        # Historical metrics cache for charts
        self.history_cycle_times: Dict[str, List[float]] = {s["id"]: [] for s in STATIONS_CONFIG}
        self.history_queues: Dict[str, List[int]] = {s["id"]: [] for s in STATIONS_CONFIG}
        self.history_timestamps: List[str] = []
        self.history_throughput: List[float] = []
        
        self._init_history()

    def _init_history(self):
        """Pre-populate 20 historical points for realistic initial charts."""
        for t in range(20):
            t_str = f"T-{20-t}m"
            self.history_timestamps.append(t_str)
            # simulate progressive degradation of S25 over time
            s25_ct = 13.0 + (t * 0.26) + random.uniform(-0.1, 0.1)
            s25_q = min(8, int(2 + (t * 0.3)))
            
            self.history_throughput.append(round(43.5 - (t * 0.08) + random.uniform(-0.3, 0.3), 1))
            
            for s in STATIONS_CONFIG:
                sid = s["id"]
                if sid == "S25":
                    self.history_cycle_times[sid].append(round(s25_ct, 2))
                    self.history_queues[sid].append(s25_q)
                elif sid == "S18":
                    self.history_cycle_times[sid].append(round(16.0 + math.sin(t*0.5)*0.8, 2))
                    self.history_queues[sid].append(int(3 + math.sin(t*0.3)*1.5))
                elif sid == "S5":
                    self.history_cycle_times[sid].append(round(11.0 + math.cos(t*0.4)*0.6, 2))
                    self.history_queues[sid].append(int(2 + math.cos(t*0.4)))
                else:
                    nom = s["nominal_cycle_time"]
                    self.history_cycle_times[sid].append(round(nom + random.uniform(-0.4, 0.4), 2))
                    self.history_queues[sid].append(max(0, min(s["buffer_capacity"], int(random.uniform(1, 3)))))

    def reset(self):
        """Reset simulation state to baseline."""
        self.tick = 0
        self.running = False
        self.history_timestamps.clear()
        self.history_throughput.clear()
        for sid in self.history_cycle_times:
            self.history_cycle_times[sid].clear()
            self.history_queues[sid].clear()
        self._init_history()

    def step(self):
        """Advance simulation tick by 1 step."""
        if not self.running:
            return
        
        self.tick += 1
        curr_t_str = f"T+{self.tick}m"
        self.history_timestamps.append(curr_t_str)
        if len(self.history_timestamps) > 30:
            self.history_timestamps.pop(0)

        # Generate current tick data
        s25_phase = min(25, self.tick)
        s25_ct = 13.0 + (s25_phase * 0.22) + random.uniform(-0.15, 0.15)
        s25_q = min(8, int(2 + (s25_phase * 0.28)))
        
        tp = round(max(38.0, 43.5 - (s25_phase * 0.15) + random.uniform(-0.2, 0.2)), 1)
        self.history_throughput.append(tp)
        if len(self.history_throughput) > 30:
            self.history_throughput.pop(0)

        for s in STATIONS_CONFIG:
            sid = s["id"]
            if sid == "S25":
                self.history_cycle_times[sid].append(round(s25_ct, 2))
                self.history_queues[sid].append(s25_q)
            elif sid == "S18":
                self.history_cycle_times[sid].append(round(16.0 + math.sin(self.tick*0.4)*0.9, 2))
                self.history_queues[sid].append(int(3 + math.sin(self.tick*0.3)*1.5))
            else:
                nom = s["nominal_cycle_time"]
                ct = round(nom + random.uniform(-0.3, 0.3), 2)
                q = max(0, min(s["buffer_capacity"], int(random.uniform(1, 3))))
                self.history_cycle_times[sid].append(ct)
                self.history_queues[sid].append(q)
            
            if len(self.history_cycle_times[sid]) > 30:
                self.history_cycle_times[sid].pop(0)
            if len(self.history_queues[sid]) > 30:
                self.history_queues[sid].pop(0)

    def get_station_parameters(self, s: StationInfo) -> List[Dict[str, Any]]:
        """Generate dynamic sensor/process parameters according to station category."""
        sid = s["id"]
        cat = s["category"]
        params = []
        
        # Scenario 1: S25 Degradation
        if sid == "S25":
            phase = min(20, self.tick)
            torque_val = round(98.0 + (phase * 0.45) + random.uniform(-0.5, 0.5), 1)
            angle_val = round(91.0 + (phase * 0.4) + random.uniform(-0.3, 0.3), 1)
            vib_val = round(4.2 + (phase * 0.08) + random.uniform(-0.1, 0.1), 2)
            temp_val = round(82.0 + (phase * 0.5) + random.uniform(-0.4, 0.4), 1)
            
            t_status = "CRITICAL" if torque_val > 104 or angle_val > 96 else ("WARNING" if torque_val > 100 else "NORMAL")
            v_status = "CRITICAL" if vib_val > 5.2 else ("WARNING" if vib_val > 4.5 else "NORMAL")
            temp_status = "CRITICAL" if temp_val > 90 else ("WARNING" if temp_val > 85 else "NORMAL")
            
            return [
                {"name": "Fastener Torque", "value": f"{torque_val}", "unit": "Nm", "status": t_status, "nominal": "95-102 Nm"},
                {"name": "Torque Angle", "value": f"{angle_val}", "unit": "°", "status": t_status, "nominal": "88-93°"},
                {"name": "Spindle Vibration", "value": f"{vib_val}", "unit": "mm/s", "status": v_status, "nominal": "< 4.0 mm/s"},
                {"name": "Drive Temp", "value": f"{temp_val}", "unit": "°C", "status": temp_status, "nominal": "70-80 °C"},
            ]
        
        # Scenario 2: S30 Wheel & Tire Quality Anomaly
        if sid == "S30":
            torque = round(94.0 + random.uniform(-0.8, 1.2), 1)
            angle = round(82.0 + random.uniform(-0.5, 0.8), 1)
            vib = round(4.7 + random.uniform(-0.1, 0.2), 2)
            cur = round(10.8 + random.uniform(-0.3, 0.3), 1)
            return [
                {"name": "Nutrunner Torque", "value": f"{torque}", "unit": "Nm", "status": "WARNING", "nominal": "110-125 Nm"},
                {"name": "Torque Angle", "value": f"{angle}", "unit": "°", "status": "WARNING", "nominal": "90-105°"},
                {"name": "Spindle Vibration", "value": f"{vib}", "unit": "mm/s", "status": "WARNING", "nominal": "< 3.8 mm/s"},
                {"name": "Motor Current", "value": f"{cur}", "unit": "A", "status": "NORMAL", "nominal": "9.5-12.0 A"},
            ]
            
        if cat == "Welding":
            weld_i = round(12.4 + random.uniform(-0.3, 0.3), 1)
            weld_t = int(240 + random.uniform(-10, 10))
            temp = round(68.5 + random.uniform(-1.5, 1.5), 1)
            pres = round(5.2 + random.uniform(-0.1, 0.1), 2)
            params = [
                {"name": "Weld Current", "value": f"{weld_i}", "unit": "kA", "status": "NORMAL", "nominal": "11.8-13.0 kA"},
                {"name": "Weld Time", "value": f"{weld_t}", "unit": "ms", "status": "NORMAL", "nominal": "220-260 ms"},
                {"name": "Electrode Temp", "value": f"{temp}", "unit": "°C", "status": "NORMAL", "nominal": "60-75 °C"},
                {"name": "Clamp Pressure", "value": f"{pres}", "unit": "bar", "status": "NORMAL", "nominal": "4.8-5.5 bar"},
            ]
        elif cat in ["Chemical", "Oven", "Coating", "Spray"]:
            temp = round(145.0 + random.uniform(-2.5, 2.5), 1) if cat == "Oven" else round(23.5 + random.uniform(-0.8, 0.8), 1)
            pres = round(3.8 + random.uniform(-0.15, 0.15), 2)
            hum = round(55.2 + random.uniform(-2.0, 2.0), 1)
            flow = round(280 + random.uniform(-8, 8), 0)
            params = [
                {"name": "Zone Temperature", "value": f"{temp}", "unit": "°C", "status": "NORMAL", "nominal": f"{temp-5}-{temp+5} °C"},
                {"name": "Fluid / Air Pressure", "value": f"{pres}", "unit": "bar", "status": "NORMAL", "nominal": "3.5-4.2 bar"},
                {"name": "Chamber Humidity", "value": f"{hum}", "unit": "%RH", "status": "NORMAL", "nominal": "50-60 %RH"},
                {"name": "Paint Flow Rate", "value": f"{int(flow)}", "unit": "cc/min", "status": "NORMAL", "nominal": "260-300 cc/min"},
            ]
        elif cat == "Assembly":
            torque = round(45.0 + random.uniform(-1.2, 1.2), 1)
            angle = round(65.0 + random.uniform(-1.0, 1.0), 1)
            vib = round(1.8 + random.uniform(-0.15, 0.15), 2)
            cur = round(4.5 + random.uniform(-0.2, 0.2), 1)
            params = [
                {"name": "Joint Torque", "value": f"{torque}", "unit": "Nm", "status": "NORMAL", "nominal": "42-48 Nm"},
                {"name": "Torque Angle", "value": f"{angle}", "unit": "°", "status": "NORMAL", "nominal": "60-70°"},
                {"name": "Vibration Level", "value": f"{vib}", "unit": "mm/s", "status": "NORMAL", "nominal": "< 2.5 mm/s"},
                {"name": "Servo Current", "value": f"{cur}", "unit": "A", "status": "NORMAL", "nominal": "4.0-5.0 A"},
            ]
        elif cat in ["Test", "Inspection"]:
            tol = round(0.12 + random.uniform(-0.02, 0.02), 3)
            score = round(98.5 + random.uniform(-0.8, 0.8), 1)
            err = round(0.04 + random.uniform(-0.01, 0.01), 3)
            params = [
                {"name": "Laser Accuracy", "value": f"{tol}", "unit": "mm", "status": "NORMAL", "nominal": "< 0.25 mm"},
                {"name": "Inspection Score", "value": f"{score}", "unit": "pts", "status": "NORMAL", "nominal": "> 95.0 pts"},
                {"name": "Measurement Error", "value": f"{err}", "unit": "mm", "status": "NORMAL", "nominal": "< 0.08 mm"},
                {"name": "Optical Confidence", "value": "99.4", "unit": "%", "status": "NORMAL", "nominal": "> 98.0 %"},
            ]
        else: # Buffer
            inflow = round(42.0 + random.uniform(-1.0, 1.0), 1)
            occupancy = round(65.0 + random.uniform(-3.0, 3.0), 1)
            speed = round(0.45 + random.uniform(-0.02, 0.02), 2)
            params = [
                {"name": "Inflow Rate", "value": f"{inflow}", "unit": "JPH", "status": "NORMAL", "nominal": "40-45 JPH"},
                {"name": "Buffer Occupancy", "value": f"{occupancy}", "unit": "%", "status": "NORMAL", "nominal": "30-80 %"},
                {"name": "Conveyor Speed", "value": f"{speed}", "unit": "m/s", "status": "NORMAL", "nominal": "0.4-0.5 m/s"},
                {"name": "Transfer Status", "value": "OPTIMAL", "unit": "", "status": "NORMAL", "nominal": "OPTIMAL"},
            ]
        return params

    def get_all_stations_state(self) -> List[Dict[str, Any]]:
        """Return real-time state for all 35 stations."""
        result = []
        for s in STATIONS_CONFIG:
            sid = s["id"]
            nom = s["nominal_cycle_time"]
            
            # S25 Progressive Bottleneck
            if sid == "S25":
                phase = min(20, self.tick)
                ct = round(13.0 + (phase * 0.26) + random.uniform(-0.1, 0.1), 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = min(8, int(2 + (phase * 0.3)))
                util = min(99, int(88 + (phase * 0.6)))
                
                if phase < 5:
                    status = "NORMAL"
                    b_risk = 35.0
                    b_level = "LOW"
                    b_pred = "~25 mins"
                elif phase < 12:
                    status = "WARNING"
                    b_risk = 68.0
                    b_level = "WARNING"
                    b_pred = "~14 mins"
                else:
                    status = "CRITICAL"
                    b_risk = 91.0
                    b_level = "CRITICAL"
                    b_pred = "~8 mins"
                    
                q_risk = 34.0
                q_level = "LOW"
                q_defect = "None"
            
            # S30 Quality Anomaly
            elif sid == "S30":
                ct = round(nom + random.uniform(-0.2, 0.3), 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = 3
                util = 89
                status = "WARNING"
                b_risk = 42.0
                b_level = "LOW"
                b_pred = "Stable"
                q_risk = 82.0
                q_level = "HIGH"
                q_defect = "Wheel Fastening Torque Deviation"
            
            # S18 Baking Oven (Mild warning for secondary bottleneck demo)
            elif sid == "S18":
                ct = round(17.2 + math.sin(self.tick * 0.2) * 0.5, 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = 4
                util = 93
                status = "WARNING"
                b_risk = 68.0
                b_level = "WARNING"
                b_pred = "~18 mins"
                q_risk = 22.0
                q_level = "LOW"
                q_defect = "None"
                
            # S5 Main Body Framing (Tertiary)
            elif sid == "S5":
                ct = round(11.8 + math.cos(self.tick * 0.3) * 0.3, 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = 3
                util = 91
                status = "WARNING"
                b_risk = 54.0
                b_level = "WARNING"
                b_pred = "~32 mins"
                q_risk = 18.0
                q_level = "LOW"
                q_defect = "None"
                
            # S16 Base Coat Spray
            elif sid == "S16":
                ct = round(nom + random.uniform(-0.1, 0.2), 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = 2
                util = 84
                status = "NORMAL"
                b_risk = 28.0
                b_level = "LOW"
                b_pred = "Stable"
                q_risk = 71.0
                q_level = "HIGH"
                q_defect = "Paint Film Thickness Anomaly"

            else:
                ct = round(nom + random.uniform(-0.3, 0.3), 1)
                dev = round(((ct - nom) / nom) * 100, 1)
                q = max(0, min(s["buffer_capacity"], int(random.uniform(1, 3))))
                util = int(75 + random.uniform(0, 12))
                status = "NORMAL"
                b_risk = round(15.0 + random.uniform(0, 15), 1)
                b_level = "LOW"
                b_pred = "Stable"
                q_risk = round(5.0 + random.uniform(0, 10), 1)
                q_level = "LOW"
                q_defect = "None"

            params = self.get_station_parameters(s)
            
            result.append({
                "id": sid,
                "num": s["num"],
                "name": s["name"],
                "shop": s["shop"],
                "category": s["category"],
                "nominal_cycle_time": nom,
                "buffer_capacity": s["buffer_capacity"],
                "status": status,
                "cycle_time": ct,
                "cycle_time_dev": dev,
                "queue_length": q,
                "utilization": util,
                "bottleneck_risk": b_risk,
                "bottleneck_level": b_level,
                "bottleneck_predicted_time": b_pred,
                "quality_risk": q_risk,
                "quality_level": q_level,
                "predicted_defect": q_defect,
                "parameters": params
            })
        return result

    def get_tracked_vehicles(self) -> List[Dict[str, Any]]:
        """Return vehicles currently tracked along the digital twin line."""
        return [
            {
                "vehicle_id": "V128",
                "station_id": "S30",
                "station_name": "Wheel & Tire Mounting",
                "defect_prob": 82.0,
                "risk_level": "HIGH",
                "predicted_issue": "Wheel fastening torque anomaly",
                "recommended_action": "ADAPTIVE TEST TRIGGERED",
                "signals": [
                    {"name": "Torque", "value": "94 Nm", "nominal": "110-125 Nm", "status": "CRITICAL"},
                    {"name": "Torque Angle", "value": "82°", "nominal": "90-105°", "status": "CRITICAL"},
                    {"name": "Spindle Vibration", "value": "4.7 mm/s", "nominal": "< 3.8 mm/s", "status": "WARNING"},
                    {"name": "Cycle Time", "value": "10.8 min", "nominal": "10.1 min", "status": "NORMAL"}
                ],
                "adaptive_test": {
                    "active": True,
                    "trigger_reason": "Defect Risk: 82% > Threshold: 70%",
                    "checklist": [
                        {"name": "Torque verification", "status": "PASSED"},
                        {"name": "Torque-angle verification", "status": "FAILED"},
                        {"name": "Vibration harmonic check", "status": "PASSED"},
                        {"name": "Wheel rotation dynamic test", "status": "FLAGGED"}
                    ],
                    "result": "HOLD FOR INSPECTION"
                }
            },
            {
                "vehicle_id": "V131",
                "station_id": "S16",
                "station_name": "Base Coat Spray",
                "defect_prob": 71.0,
                "risk_level": "HIGH",
                "predicted_issue": "Paint coating thickness non-uniformity",
                "recommended_action": "OPTICAL RE-SCAN",
                "signals": [
                    {"name": "Atomizer Flow", "value": "245 cc/min", "nominal": "260-300 cc/min", "status": "WARNING"},
                    {"name": "Chamber Humidity", "value": "64 %RH", "nominal": "50-60 %RH", "status": "WARNING"},
                    {"name": "Robot Traverse Speed", "value": "1.2 m/s", "nominal": "1.0 m/s", "status": "NORMAL"}
                ],
                "adaptive_test": {
                    "active": True,
                    "trigger_reason": "Defect Risk: 71% > Threshold: 70%",
                    "checklist": [
                        {"name": "Laser film thickness measurement", "status": "FLAGGED"},
                        {"name": "Multi-angle spectro-photometry", "status": "PASSED"},
                        {"name": "Surface waviness wave-scan", "status": "PASSED"}
                    ],
                    "result": "HOLD FOR INSPECTION"
                }
            },
            {
                "vehicle_id": "V125",
                "station_id": "S8",
                "station_name": "Geometry Laser Scanning",
                "defect_prob": 38.0,
                "risk_level": "MODERATE",
                "predicted_issue": "Sub-assembly seam gap variance",
                "recommended_action": "MONITOR S9 BUFFING",
                "signals": [
                    {"name": "Seam Gap Delta", "value": "+0.32 mm", "nominal": "< 0.25 mm", "status": "WARNING"},
                    {"name": "Flushness", "value": "0.18 mm", "nominal": "< 0.20 mm", "status": "NORMAL"}
                ],
                "adaptive_test": {
                    "active": False,
                    "trigger_reason": "Defect Risk: 38% <= Threshold: 70%",
                    "checklist": [],
                    "result": "PASS (STANDARD FLOW)"
                }
            },
            {
                "vehicle_id": "V134",
                "station_id": "S25",
                "station_name": "Marriage / Powertrain Integration",
                "defect_prob": 29.0,
                "risk_level": "LOW",
                "predicted_issue": "Minor mating alignment drift",
                "recommended_action": "ROUTINE LOGGING",
                "signals": [
                    {"name": "Pallet Docking", "value": "0.11 mm", "nominal": "< 0.20 mm", "status": "NORMAL"},
                    {"name": "Drive Temp", "value": "84 °C", "nominal": "70-80 °C", "status": "WARNING"}
                ],
                "adaptive_test": {
                    "active": False,
                    "trigger_reason": "Defect Risk: 29% <= Threshold: 70%",
                    "checklist": [],
                    "result": "PASS"
                }
            },
            {
                "vehicle_id": "V135",
                "station_id": "S33",
                "station_name": "Dynamic Brake & Roll Test",
                "defect_prob": 12.0,
                "risk_level": "LOW",
                "predicted_issue": "None",
                "recommended_action": "STANDARD PROCEED",
                "signals": [
                    {"name": "Brake Force Left", "value": "4.2 kN", "nominal": "4.0-4.5 kN", "status": "NORMAL"},
                    {"name": "Brake Force Right", "value": "4.1 kN", "nominal": "4.0-4.5 kN", "status": "NORMAL"}
                ],
                "adaptive_test": {
                    "active": False,
                    "trigger_reason": "Normal operational metrics",
                    "checklist": [],
                    "result": "PASS"
                }
            }
        ]

# Global singleton instance
SIM_ENGINE = SimulationEngine()
