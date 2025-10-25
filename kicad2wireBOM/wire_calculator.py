# ABOUTME: Wire calculation functions for length, gauge, and specifications
# ABOUTME: Implements Manhattan distance, voltage drop, and ampacity calculations

from typing import List, Optional, Dict, TYPE_CHECKING
import re
from kicad2wireBOM.component import Component
from kicad2wireBOM.reference_data import WIRE_RESISTANCE, WIRE_AMPACITY, STANDARD_AWG_SIZES, DEFAULT_CONFIG

if TYPE_CHECKING:
    from kicad2wireBOM.wire_bom import WireConnection


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


def parse_net_name(net_name: str) -> Optional[Dict[str, str]]:
    r"""
    Parse net name to extract system code, circuit ID, and segment letter.

    Pattern: /([A-Z])-?(\d+)-?([A-Z])/
    Handles: /L1A, /L-1-A, /L001A, /L-001-A, /P1A, /G1A

    Args:
        net_name: Net name from KiCad netlist (e.g., "/P1A", "/L-105-B")

    Returns:
        Dict with 'system', 'circuit', 'segment' keys, or None if no match
        Example: {'system': 'L', 'circuit': '1', 'segment': 'A'}
    """
    # Pattern: /([A-Z])-?(\d+)-?([A-Z])
    # - Starts with /
    # - System code: single uppercase letter
    # - Optional dash
    # - Circuit ID: one or more digits
    # - Optional dash
    # - Segment letter: single uppercase letter
    pattern = r'/([A-Z])-?(\d+)-?([A-Z])'

    match = re.search(pattern, net_name)
    if not match:
        return None

    return {
        'system': match.group(1),
        'circuit': match.group(2),
        'segment': match.group(3)
    }


def infer_system_code_from_components(components: List[Component], net_name: str) -> Optional[str]:
    """
    Infer system code from component analysis for validation purposes.

    This is used to validate the SD's system code choices from net names.
    Search priority:
    1. Component description fields
    2. Component value fields
    3. Component reference designators
    4. Net name keywords

    Patterns:
    - LIGHT, LAMP, LED → "L" (Lighting)
    - BAT, BATT, BATTERY, PWR, POWER → "P" (Power)
    - RADIO, NAV, COM, XPNDR → "R" (Radio/Nav/Comm)
    - GND, GROUND → "G" (Ground)

    Args:
        components: List of components in the circuit
        net_name: Name of the net

    Returns:
        Single-letter system code or None if unknown
    """
    # Define keyword patterns for each system
    lighting_keywords = ['LIGHT', 'LAMP', 'LED']
    power_keywords = ['BAT', 'BATT', 'BATTERY', 'PWR', 'POWER']
    radio_keywords = ['RADIO', 'NAV', 'COM', 'XPNDR']
    ground_keywords = ['GND', 'GROUND']

    # 1. Check description fields first (highest priority)
    for comp in components:
        desc_upper = comp.desc.upper()
        if any(keyword in desc_upper for keyword in lighting_keywords):
            return 'L'
        if any(keyword in desc_upper for keyword in power_keywords):
            return 'P'
        if any(keyword in desc_upper for keyword in radio_keywords):
            return 'R'
        if any(keyword in desc_upper for keyword in ground_keywords):
            return 'G'

    # 2. Check value fields
    for comp in components:
        value_upper = comp.value.upper()
        if any(keyword in value_upper for keyword in lighting_keywords):
            return 'L'
        if any(keyword in value_upper for keyword in power_keywords):
            return 'P'
        if any(keyword in value_upper for keyword in radio_keywords):
            return 'R'
        if any(keyword in value_upper for keyword in ground_keywords):
            return 'G'

    # 3. Check reference designators
    for comp in components:
        ref_upper = comp.ref.upper()
        # Check for load component ref prefixes
        if comp.is_load:
            if ref_upper.startswith('L'):
                return 'L'
            if any(ref_upper.startswith(prefix) for prefix in ['R', 'NAV', 'COM', 'XPNDR']):
                return 'R'
        # Check for keywords in ref
        if any(keyword in ref_upper for keyword in lighting_keywords):
            return 'L'
        if any(keyword in ref_upper for keyword in power_keywords):
            return 'P'
        if any(keyword in ref_upper for keyword in radio_keywords):
            return 'R'
        if any(keyword in ref_upper for keyword in ground_keywords):
            return 'G'

    # 4. Check net name (lowest priority)
    net_name_upper = net_name.upper()
    if any(keyword in net_name_upper for keyword in lighting_keywords):
        return 'L'
    if any(keyword in net_name_upper for keyword in power_keywords):
        return 'P'
    if any(keyword in net_name_upper for keyword in radio_keywords):
        return 'R'
    if any(keyword in net_name_upper for keyword in ground_keywords):
        return 'G'

    # Unknown
    return None


def detect_system_code(components: List[Component], net_name: str) -> str:
    """
    Detect system code from net name (primary) or component analysis (fallback).

    Per Design Revision 2025-10-17:
    - PRIMARY: Parse system code from net name (e.g., /P1A → 'P')
    - FALLBACK: Infer from component analysis if net name parsing fails

    Args:
        components: List of components in the circuit
        net_name: Name of the net (e.g., "/P1A", "/L-105-B")

    Returns:
        Single-letter system code (default 'U' for Unknown)
    """
    # PRIMARY: Try to parse system code from net name
    parsed = parse_net_name(net_name)
    if parsed:
        return parsed['system']

    # FALLBACK: Infer from component analysis
    inferred = infer_system_code_from_components(components, net_name)
    if inferred:
        return inferred

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


def group_wires_by_circuit(wire_connections: List['WireConnection']) -> Dict[str, List['WireConnection']]:
    """
    Group wire connections by circuit_id (system_code + circuit_num).

    Args:
        wire_connections: List of all wire connections from BOM

    Returns:
        Dict mapping circuit_id to list of WireConnections
        Example: {'L1': [L1A_conn, L1B_conn], 'L2': [L2A_conn, L2B_conn, L2C_conn]}
    """
    circuit_groups: Dict[str, List['WireConnection']] = {}

    for wire in wire_connections:
        # Parse wire label to extract system code and circuit number
        # Wire labels are in EAWMS format: "L-105-A"
        # Add leading slash to match parse_net_name format: "/L-105-A"
        parsed = parse_net_name(f"/{wire.wire_label}")

        if parsed:
            # Circuit ID = system_code + circuit_num (e.g., "L1", "G2", "P1")
            circuit_id = f"{parsed['system']}{parsed['circuit']}"

            if circuit_id not in circuit_groups:
                circuit_groups[circuit_id] = []

            circuit_groups[circuit_id].append(wire)

    return circuit_groups


def determine_circuit_current(
    circuit_wires: List['WireConnection'],
    all_components: List[Component],
    connectivity_graph
) -> float:
    """
    Determine total current for a circuit by finding all components connected
    to any wire in the circuit group.

    Args:
        circuit_wires: All wires in this circuit group
        all_components: All components in schematic
        connectivity_graph: Connectivity graph for component lookup (unused - components from wire refs)

    Returns:
        Total circuit current in amps
        Special value: -99 if no loads or sources found (missing data)
    """
    # Build component reference lookup map
    component_map = {comp.ref: comp for comp in all_components}

    # Collect all unique component references from circuit wires
    component_refs = set()
    for wire in circuit_wires:
        if wire.from_component:
            component_refs.add(wire.from_component)
        if wire.to_component:
            component_refs.add(wire.to_component)

    # Get Component objects for those references
    components = []
    for ref in component_refs:
        if ref in component_map:
            components.append(component_map[ref])

    # Extract loads and sources
    loads = [comp.load for comp in components if comp.is_load]
    sources = [comp.source for comp in components if comp.source]

    # Determine current based on priority
    if loads:
        return sum(loads)
    elif sources:
        return max(sources)
    else:
        return -99  # Sentinel for missing data
