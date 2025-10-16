# ABOUTME: Wire calculation functions for length, gauge, and specifications
# ABOUTME: Implements Manhattan distance, voltage drop, and ampacity calculations

from typing import List
from kicad2wireBOM.component import Component
from kicad2wireBOM.reference_data import WIRE_RESISTANCE, WIRE_AMPACITY, STANDARD_AWG_SIZES, DEFAULT_CONFIG


def calculate_length(component1: Component, component2: Component, slack: float) -> float:
    """
    Calculate wire length between two components using Manhattan distance.

    Manhattan distance is the sum of absolute differences in each coordinate axis.
    This approximates wire routing through aircraft structure.

    Args:
        component1: First component
        component2: Second component
        slack: Additional slack length to add (inches)

    Returns:
        Total wire length in inches (Manhattan distance + slack)
    """
    fs1, wl1, bl1 = component1.coordinates
    fs2, wl2, bl2 = component2.coordinates

    manhattan_distance = abs(fs2 - fs1) + abs(wl2 - wl1) + abs(bl2 - bl1)

    return manhattan_distance + slack


def calculate_voltage_drop(current: float, awg_size: int, length_inches: float) -> float:
    """
    Calculate voltage drop for a given current, wire gauge, and length.

    Formula: Vdrop = I * R * L
    where:
        I = current (amps)
        R = resistance per foot (ohms/ft)
        L = length (feet)

    Args:
        current: Current in amps
        awg_size: AWG wire size
        length_inches: Wire length in inches

    Returns:
        Voltage drop in volts
    """
    resistance_per_foot = WIRE_RESISTANCE[awg_size]
    length_feet = length_inches / 12.0

    return current * resistance_per_foot * length_feet


def determine_min_gauge(current: float, length_inches: float, system_voltage: float) -> int:
    """
    Determine minimum wire gauge that meets both voltage drop and ampacity constraints.

    Constraints:
    1. Voltage drop must be <= voltage_drop_percent (from DEFAULT_CONFIG)
    2. Wire ampacity must be >= current

    Args:
        current: Load current in amps
        length_inches: Wire length in inches
        system_voltage: System voltage (e.g., 14V for 12V aircraft system)

    Returns:
        Minimum AWG wire size (largest number = smallest wire that meets constraints)
    """
    max_voltage_drop = system_voltage * (DEFAULT_CONFIG['voltage_drop_percent'] / 100.0)

    # Try AWG sizes from largest wire (smallest number) to smallest wire (largest number)
    # Return the smallest wire (largest AWG number) that meets both constraints
    suitable_gauges = []

    for awg in STANDARD_AWG_SIZES:
        # Check ampacity constraint
        if WIRE_AMPACITY[awg] < current:
            continue  # Wire too small for current

        # Check voltage drop constraint
        vdrop = calculate_voltage_drop(current, awg, length_inches)
        if vdrop > max_voltage_drop:
            continue  # Voltage drop too high

        suitable_gauges.append(awg)

    # Return smallest wire (highest AWG number) that meets constraints
    # If no wire meets constraints, return largest wire (lowest AWG number) available
    if suitable_gauges:
        return max(suitable_gauges)
    else:
        return min(STANDARD_AWG_SIZES)  # Return largest wire as fallback


def detect_system_code(components: List[Component], net_name: str) -> str:
    """
    Detect system code based on component references and net name.

    Patterns:
    - Component ref prefix "L" (lamp/light) → "L" (Lighting)
    - LIGHT, LAMP, LED keywords → "L" (Lighting)
    - BAT, BATT, BATTERY → "P" (Power)
    - Check net name for hints
    - Check switch/fuse refs for keywords
    - Default → "U" (Unknown)

    Args:
        components: List of components in the circuit
        net_name: Name of the net

    Returns:
        Single-letter system code
    """
    # Check component ref prefixes for loads
    for comp in components:
        if comp.is_load:
            # Check if lamp/light (L prefix)
            if comp.ref.upper().startswith('L'):
                return 'L'
            # Check if radio/nav/comm (R, NAV, COM, etc.)
            if any(comp.ref.upper().startswith(prefix) for prefix in ['R', 'NAV', 'COM', 'XPNDR']):
                return 'R'

    # Combine all text to search for keywords
    search_text = net_name.upper()
    for comp in components:
        search_text += " " + comp.ref.upper()

    # Check for lighting keywords
    if any(keyword in search_text for keyword in ['LIGHT', 'LAMP', 'LED']):
        return 'L'

    # Check for power/battery patterns
    if any(keyword in search_text for keyword in ['BAT', 'BATT', 'BATTERY', 'PWR', 'POWER']):
        return 'P'

    # Default to Unknown
    return 'U'


def generate_wire_label(system_code: str, circuit_id: str, segment_letter: str) -> str:
    """
    Generate wire label in EAWMS format.

    Format: {system_code}-{circuit_id}-{segment_letter}
    Example: "L-105-A"

    Args:
        system_code: Single-letter system code (L, P, R, etc.)
        circuit_id: Circuit identifier (numeric string)
        segment_letter: Segment letter (A, B, C, etc.)

    Returns:
        Formatted wire label string
    """
    return f"{system_code}-{circuit_id}-{segment_letter}"
