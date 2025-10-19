# ABOUTME: Reference data for wire specifications and system configuration
# ABOUTME: Contains wire resistance, ampacity tables, and default configuration values

from typing import Dict, List

# Wire resistance in ohms per foot for common AWG sizes
# Source: Standard copper wire resistance tables
WIRE_RESISTANCE: Dict[int, float] = {
    12: 0.001588,  # AWG 12: 1.588 milliohms/ft
    16: 0.004016,  # AWG 16: 4.016 milliohms/ft
    18: 0.006385,  # AWG 18: 6.385 milliohms/ft
    20: 0.01015,   # AWG 20: 10.15 milliohms/ft
}

# Wire ampacity (current carrying capacity) in amps for common AWG sizes
# Source: Conservative ratings for bundled aircraft wiring
WIRE_AMPACITY: Dict[int, float] = {
    12: 25.0,   # AWG 12: 25A
    16: 13.0,   # AWG 16: 13A
    18: 10.0,   # AWG 18: 10A
    20: 7.5,    # AWG 20: 7.5A
}

# Standard AWG wire sizes available (sorted smallest to largest)
STANDARD_AWG_SIZES: List[int] = [12, 16, 18, 20]

# System code to wire color mapping
# Based on experimental aircraft wire marking standards
SYSTEM_COLOR_MAP: Dict[str, str] = {
    'L': 'White',    # Lighting
    'P': 'Red',      # Power
    'G': 'Black',    # Ground
    'R': 'Gray',     # Radio/Nav
    'E': 'Brown',    # Engine Instruments
    'K': 'Orange',   # Engine Control
    'M': 'Yellow',   # Miscellaneous
    'W': 'Green',    # Warning Systems
    'A': 'Blue',     # Avionics
    'F': 'Violet',   # Fuel Systems
    'U': 'Pink'      # Utility/Unknown
}

# Default system configuration
DEFAULT_CONFIG: Dict[str, any] = {
    'system_voltage': 14.0,          # 14V nominal for 12V aircraft system
    'slack_length': 24.0,            # 24 inches of slack per wire
    'voltage_drop_percent': 5.0,     # 5% maximum voltage drop
    'label_threshold': 10.0,         # 10mm max distance for label association
    'default_wire_type': 'M22759/16' # MIL-SPEC wire type
}
