from __future__ import annotations
from typing import Any, Dict, List

SPECIAL_QUEUE_CAPACITY = {"S10": 50, "S20": 50}

# Define the stations that have no IoT sensor coverage
SENSORLESS_STATIONS = {"S04", "S11", "S17", "S24", "S31"}

DEFECT_FIELDS = (
    "defect_present","defect_introduced_here","defect_detected",
    "defect_cause","defect_type","defect_severity","defect_risk_score",
    "defect_probability","defect_source_station","process_drift_score",
    "input_variation_score","fixture_alignment_score","environmental_deviation_score",
)

def _float(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default

def _int(v, default=0):
    try: return int(v)
    except (TypeError, ValueError): return default

def _round_record(record):
    out={}
    for k,v in record.items():
        if isinstance(v,bool): out[k]=v
        elif isinstance(v,(int,float)): 
            # Force exactly 8 decimal places for simulation time
            if k == "simulation_time_hours":
                out[k] = round(float(v), 8)
            else:
                out[k] = round(float(v), 3)
        else: out[k]=v
    return out

def build_telemetry(events: List[Dict[str,Any]], sensor_rows: List[Dict[str,Any]],
                    station_meta: Dict[str,Dict[str,Any]]) -> List[Dict[str,Any]]:
    if len(events) != len(sensor_rows):
        raise ValueError("events and sensor_rows must have identical lengths.")
    output=[]
    for event,sensor in zip(events,sensor_rows):
        sid=event["station_id"]
        if sid not in station_meta: raise KeyError(f"Station metadata missing for {sid}")
        meta=station_meta[sid]
        
        is_buffer=sid in SPECIAL_QUEUE_CAPACITY
        cap=50 if is_buffer else 10
        q=max(0,min(cap,_int(event.get("queue_length",0))))
        
        row={
            "vehicle_id":_int(event.get("vehicle_id")),
            "station_id":sid,
            "station_name":meta.get("station_name",sid),
            "station_family":meta.get("station_family",""),
            "equipment_driven":bool(meta.get("equipment_driven",False)),
            "simulation_time_hours":_float(event.get("simulation_time_hours"),
                _float(event.get("completion_time_min"))/(365*24*60)),
            "arrival_time_min":_float(event.get("arrival_time_min")),
            "start_time_min":_float(event.get("start_time_min")),
            "completion_time_min":_float(event.get("completion_time_min")),
            "waiting_time_min":_float(event.get("waiting_time_min")),
            "base_cycle_time_min":_float(event.get("base_cycle_time_min")),
            "installation_time_min":_float(event.get("installation_time_min")),
            "health_slowdown_min":_float(event.get("health_slowdown_min")),
            "cycle_time_min":_float(event.get("cycle_time_min")),
            "ctd_min":_float(event.get("ctd_min")),
            "equipment_health":1.0 if is_buffer else _float(event.get("equipment_health"),1.0),
            "queue_length":q,
            "queue_capacity":cap,
            "takt_slack_min":_float(event.get("takt_slack_min")),
            "recovery_mode":False if is_buffer else bool(event.get("recovery_mode",False)),
            "recovery_trigger":"NONE" if is_buffer else event.get("recovery_trigger","NONE"),
            "utilization_pct":_float(event.get("utilization_pct")),
            "station_status":event.get("station_status","RUNNING"),
            "maintenance_active":False if is_buffer else bool(event.get("maintenance_active",False)),
            "tool_replacement_event":False if is_buffer else bool(event.get("tool_replacement_event",False)),
            "tool_replacement_number":0 if is_buffer else _int(event.get("tool_replacement_number",0)),
        }

        if is_buffer:
            row.update({
                "defect_present":False,"defect_introduced_here":False,"defect_detected":False,
                "defect_cause":"NONE","defect_type":"NONE","defect_severity":0.0,
                "defect_risk_score":0.0,"defect_probability":0.0,"defect_source_station":"",
                "process_drift_score":0.0,"input_variation_score":0.0,
                "fixture_alignment_score":0.0,"environmental_deviation_score":0.0,
            })
        else:
            for key in DEFECT_FIELDS:
                if key in event: row[key]=event[key]
                elif key in {"defect_present","defect_introduced_here","defect_detected"}: row[key]=False
                elif key in {"defect_cause","defect_type"}: row[key]="NONE"
                elif key=="defect_source_station": row[key]=""
                else: row[key]=0.0

        # Merge sensor data into the row
        for key,value in sensor.items():
            if key not in row:
                # If this station is sensorless, redact the physical readings by outputting None
                if sid in SENSORLESS_STATIONS:
                    row[key] = None
                else:
                    row[key] = value
                    
        output.append(_round_record(row))
    return output

def build_station_summary(telemetry):
    grouped={}
    for row in telemetry: grouped.setdefault(row["station_id"],[]).append(row)
    out=[]
    for sid,rows in grouped.items():
        nums=lambda k:[_float(r.get(k,0)) for r in rows]
        cts=nums("cycle_time_min"); q=nums("queue_length"); w=nums("waiting_time_min")
        h=nums("equipment_health"); u=nums("utilization_pct")
        out.append({
            "station_id":sid,"station_name":rows[0]["station_name"],
            "station_family":rows[0]["station_family"],
            "records":len(rows),
            "queue_capacity": 50 if sid in SPECIAL_QUEUE_CAPACITY else 10,
            "average_cycle_time_min":round(sum(cts)/len(cts),3),
            "max_cycle_time_min":round(max(cts),3),
            "average_queue_length":round(sum(q)/len(q),3),
            "max_queue_length":int(max(q)),
            "average_waiting_time_min":round(sum(w)/len(w),3),
            "average_utilization_pct":round(sum(u)/len(u),3),
            "average_equipment_health":round(sum(h)/len(h),3),
            "minimum_equipment_health":round(min(h),3),
            "tool_replacement_events":sum(bool(r.get("tool_replacement_event",False)) for r in rows),
            "recovery_records":sum(bool(r.get("recovery_mode",False)) for r in rows),
            "defect_records":sum(bool(r.get("defect_present",False)) for r in rows),
            "defects_introduced_here":sum(bool(r.get("defect_introduced_here",False)) for r in rows),
            "detected_defects":sum(bool(r.get("defect_detected",False)) for r in rows),
        })
    return sorted(out,key=lambda x:x["station_id"])