"""
Configuration of all 35 stations in the DigitalTwin.ai assembly line.
Decoupled from sensor schemas to ensure future simulator flexibility.
"""

from typing import Dict, List, TypedDict, Optional

class StationInfo(TypedDict):
    id: str
    num: int
    name: str
    shop: str
    category: str
    nominal_cycle_time: float
    buffer_capacity: int

STATIONS_CONFIG: List[StationInfo] = [
    # BIW / Body Construction (S1 - S10)
    {"id": "S1", "num": 1, "name": "Underbody Front Welding", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 9.5, "buffer_capacity": 4},
    {"id": "S2", "num": 2, "name": "Underbody Rear Welding", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 9.8, "buffer_capacity": 4},
    {"id": "S3", "num": 3, "name": "Underbody Framing", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 10.2, "buffer_capacity": 4},
    {"id": "S4", "num": 4, "name": "Left & Right Bodyside Sub-Assembly", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 10.0, "buffer_capacity": 4},
    {"id": "S5", "num": 5, "name": "Main Body Framing", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 11.0, "buffer_capacity": 5},
    {"id": "S6", "num": 6, "name": "Roof Framing & Welding", "shop": "BODY / BIW", "category": "Welding", "nominal_cycle_time": 9.6, "buffer_capacity": 4},
    {"id": "S7", "num": 7, "name": "Closures Hanging", "shop": "BODY / BIW", "category": "Assembly", "nominal_cycle_time": 10.4, "buffer_capacity": 4},
    {"id": "S8", "num": 8, "name": "Geometry Laser Scanning", "shop": "BODY / BIW", "category": "Inspection", "nominal_cycle_time": 8.5, "buffer_capacity": 3},
    {"id": "S9", "num": 9, "name": "Body Buffing & Inspection", "shop": "BODY / BIW", "category": "Inspection", "nominal_cycle_time": 9.0, "buffer_capacity": 4},
    {"id": "S10", "num": 10, "name": "Storage Buffer / BIW Exit", "shop": "BODY / BIW", "category": "Buffer", "nominal_cycle_time": 6.0, "buffer_capacity": 12},

    # Paint Shop (S11 - S20)
    {"id": "S11", "num": 11, "name": "Pre-Treatment & Degreasing", "shop": "PAINT", "category": "Chemical", "nominal_cycle_time": 12.0, "buffer_capacity": 4},
    {"id": "S12", "num": 12, "name": "E-Coat / ED Tank", "shop": "PAINT", "category": "Chemical", "nominal_cycle_time": 13.5, "buffer_capacity": 4},
    {"id": "S13", "num": 13, "name": "ED Baking & Curing Oven", "shop": "PAINT", "category": "Oven", "nominal_cycle_time": 15.0, "buffer_capacity": 6},
    {"id": "S14", "num": 14, "name": "Underbody Sealing & PVC Application", "shop": "PAINT", "category": "Coating", "nominal_cycle_time": 11.2, "buffer_capacity": 4},
    {"id": "S15", "num": 15, "name": "Primer Surfacer Spray", "shop": "PAINT", "category": "Spray", "nominal_cycle_time": 10.8, "buffer_capacity": 4},
    {"id": "S16", "num": 16, "name": "Base Coat Spray", "shop": "PAINT", "category": "Spray", "nominal_cycle_time": 11.5, "buffer_capacity": 4},
    {"id": "S17", "num": 17, "name": "Clear Coat Spray", "shop": "PAINT", "category": "Spray", "nominal_cycle_time": 11.0, "buffer_capacity": 4},
    {"id": "S18", "num": 18, "name": "Final Paint Baking Oven", "shop": "PAINT", "category": "Oven", "nominal_cycle_time": 16.0, "buffer_capacity": 6},
    {"id": "S19", "num": 19, "name": "Paint Quality Inspection", "shop": "PAINT", "category": "Inspection", "nominal_cycle_time": 9.5, "buffer_capacity": 4},
    {"id": "S20", "num": 20, "name": "Painted Body Storage", "shop": "PAINT", "category": "Buffer", "nominal_cycle_time": 6.5, "buffer_capacity": 15},

    # General Assembly + EOL (S21 - S35)
    {"id": "S21", "num": 21, "name": "Wire Harness Layout", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.0, "buffer_capacity": 4},
    {"id": "S22", "num": 22, "name": "Sound Proofing & Brake Lines", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.2, "buffer_capacity": 4},
    {"id": "S23", "num": 23, "name": "Cockpit Module Installation", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 11.8, "buffer_capacity": 4},
    {"id": "S24", "num": 24, "name": "Fuel Tank / Under-Car Components", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.5, "buffer_capacity": 4},
    {"id": "S25", "num": 25, "name": "Marriage / Powertrain Integration", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 13.0, "buffer_capacity": 5},
    {"id": "S26", "num": 26, "name": "Fluid Filling", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 9.2, "buffer_capacity": 4},
    {"id": "S27", "num": 27, "name": "Windshield & Glass Glazing", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 9.8, "buffer_capacity": 4},
    {"id": "S28", "num": 28, "name": "Interior Trim & Carpet", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.6, "buffer_capacity": 4},
    {"id": "S29", "num": 29, "name": "Seat Installation", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 9.4, "buffer_capacity": 4},
    {"id": "S30", "num": 30, "name": "Wheel & Tire Mounting", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.1, "buffer_capacity": 4},
    {"id": "S31", "num": 31, "name": "Doors-On & Bumper Marriage", "shop": "GENERAL ASSEMBLY + EOL", "category": "Assembly", "nominal_cycle_time": 10.7, "buffer_capacity": 4},
    {"id": "S32", "num": 32, "name": "Wheel Alignment & Headlight Calibration", "shop": "GENERAL ASSEMBLY + EOL", "category": "Test", "nominal_cycle_time": 8.8, "buffer_capacity": 3},
    {"id": "S33", "num": 33, "name": "Dynamic Brake & Roll Test", "shop": "GENERAL ASSEMBLY + EOL", "category": "Test", "nominal_cycle_time": 9.0, "buffer_capacity": 3},
    {"id": "S34", "num": 34, "name": "Monsoon Water Leak Test", "shop": "GENERAL ASSEMBLY + EOL", "category": "Test", "nominal_cycle_time": 11.5, "buffer_capacity": 3},
    {"id": "S35", "num": 35, "name": "Final Validation / Buyoff", "shop": "GENERAL ASSEMBLY + EOL", "category": "Inspection", "nominal_cycle_time": 12.0, "buffer_capacity": 4},
]

SHOPS = [
    "BODY / BIW",
    "PAINT",
    "GENERAL ASSEMBLY + EOL"
]

STATIONS_BY_ID: Dict[str, StationInfo] = {s["id"]: s for s in STATIONS_CONFIG}

def get_station_info(station_id: str) -> Optional[StationInfo]:
    return STATIONS_BY_ID.get(station_id)
