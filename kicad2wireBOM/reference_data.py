# ABOUTME: Reference data for wire specifications and system configuration
# ABOUTME: Contains wire resistance, ampacity tables, and default configuration values

from typing import Dict, List

# Wire resistance in ohms per foot for common AWG sizes
# Source: Aeroelectric Connection Fig 8-3
WIRE_RESISTANCE: Dict[int, float] = {
    2: 0.000156,   # AWG 2: 0.156 milliohms/ft
    4: 0.000249,   # AWG 4: 0.249 milliohms/ft
    6: 0.000395,   # AWG 6: 0.395 milliohms/ft
    8: 0.000628,   # AWG 8: 0.628 milliohms/ft
    10: 0.000999,  # AWG 10: 0.999 milliohms/ft
    12: 0.001588,  # AWG 12: 1.588 milliohms/ft
    14: 0.002525,  # AWG 14: 2.525 milliohms/ft
    16: 0.004016,  # AWG 16: 4.016 milliohms/ft
    18: 0.006385,  # AWG 18: 6.385 milliohms/ft
    20: 0.01015,   # AWG 20: 10.15 milliohms/ft
    22: 0.01614,   # AWG 22: 16.14 milliohms/ft
    24: 0.02567,   # AWG 24: 25.67 milliohms/ft
}

# Wire ampacity (current carrying capacity) in amps for common AWG sizes
# Source: Aeroelectric Connection Fig 8-3
WIRE_AMPACITY: Dict[int, float] = {
    2: 100.0,   # AWG 2: 142A
    4: 72.0,   # AWG 4: 100A
    6: 540.0,    # AWG 6: 71A
    8: 40.0,    # AWG 8: 52A
    10: 30.0,   # AWG 10: 35A
    12: 22.0,   # AWG 12: 25.2A
    14: 15.,   # AWG 14: 19A
    16: 12.5,   # AWG 16: 12.8A
    18: 10.0,    # AWG 18: 9.2A
    20: 7.0,    # AWG 20: 6.2A
    22: 5.0,    # AWG 22: 4A
    24: 2.0,    # AWG 24: 2A
}


# Standard AWG wire sizes available (sorted smallest to largest)
STANDARD_AWG_SIZES: List[int] = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]

# Position precision for coordinate matching
# KiCad schematic coordinates are floats; we round to this many decimal places
# to reliably match positions (0.01mm precision for node/pin matching)
POSITION_PRECISION = 2

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

# 3D projection constants for diagram generation
DEFAULT_WL_SCALE = 0.2              # WL scale factor (compresses WL to 20% for compact diagrams)
DEFAULT_PROJECTION_ANGLE = 30        # Projection angle in degrees

# Diagram configuration for Phase 13 enhancements
DIAGRAM_CONFIG = {
    'wire_stroke_width': 3.0,        # Wire line thickness in pixels
    'component_radius': 6.0,         # Component marker radius in pixels
    'component_stroke_width': 2.0,   # Component marker border thickness
    'svg_width': 1100,               # Landscape width
    'svg_height': 700,               # Landscape height
    'margin': 40,                    # Page margins
    'title_height': 80,              # Title block height
    'origin_offset_y': 100,          # Distance from title to origin (FS=0, BL=0)
}

# BL scaling constants for Phase 13 non-linear scaling
BL_CENTER_EXPANSION = 20.0            # Expansion factor near centerline
BL_TIP_COMPRESSION = 10.0            # Compression factor at wing tips
BL_CENTER_THRESHOLD = 30.0           # BL value where expansion transitions to compression
