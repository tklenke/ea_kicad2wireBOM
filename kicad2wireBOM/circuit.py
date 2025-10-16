# ABOUTME: Circuit analysis module for grouping components and analyzing signal flow
# ABOUTME: Builds circuits from netlist data and manages wire segmentation

from dataclasses import dataclass, field
from typing import List, Any, Dict
from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.wire_calculator import calculate_length, determine_min_gauge, generate_wire_label
from string import ascii_uppercase


@dataclass
class Circuit:
    """Represents a single electrical circuit with components and wire segments"""
    net_code: str
    net_name: str
    system_code: str
    components: List[Component]
    segments: List[Any] = field(default_factory=list)


def determine_signal_flow(components: List[Component]) -> List[Component]:
    """
    Order components by signal flow direction: source -> passthrough(s) -> load.

    Uses heuristics to determine signal flow:
    1. Load components (has load attribute) go last
    2. Source components (rating with J prefix) go first
    3. Passthrough components (rating, switches, etc.) go in middle

    Args:
        components: Unordered list of components in a circuit

    Returns:
        Ordered list of components by signal flow direction
    """
    if len(components) <= 1:
        return components[:]

    # Categorize components
    loads = []
    sources = []
    passthroughs = []

    for comp in components:
        if comp.is_load:
            loads.append(comp)
        elif comp.is_passthrough:
            # Heuristic: J prefix suggests source (connector)
            if comp.ref.startswith('J'):
                sources.append(comp)
            else:
                passthroughs.append(comp)
        else:
            # Component has neither load nor rating
            passthroughs.append(comp)

    # Assemble in order: sources -> passthroughs -> loads
    return sources + passthroughs + loads


def create_wire_segments(ordered_components: List[Component],
                        system_code: str,
                        circuit_id: str,
                        config: Dict[str, Any]) -> List[WireConnection]:
    """
    Create wire segments between adjacent components in signal flow order.

    Each adjacent pair of components gets a wire segment with a unique label
    using sequential letters (A, B, C, ...).

    Args:
        ordered_components: Components ordered by signal flow
        system_code: System code for wire labels (L, P, U, etc.)
        circuit_id: Circuit identifier for wire labels
        config: Configuration dictionary with slack_length and system_voltage

    Returns:
        List of WireConnection objects representing wire segments
    """
    if len(ordered_components) < 2:
        return []

    segments = []

    for i in range(len(ordered_components) - 1):
        comp1 = ordered_components[i]
        comp2 = ordered_components[i + 1]

        # Generate segment letter: A, B, C, ...
        segment_letter = ascii_uppercase[i]

        # Calculate wire specs
        slack = config['slack_length']
        length = calculate_length(comp1, comp2, slack)

        # Determine current based on component ratings/loads
        # Use the smaller rating if both have ratings
        current = 0
        if comp1.rating is not None and comp2.rating is not None:
            current = min(comp1.rating, comp2.rating)
        elif comp1.rating is not None:
            current = comp1.rating
        elif comp2.rating is not None:
            current = comp2.rating
        elif comp1.load is not None:
            current = comp1.load
        elif comp2.load is not None:
            current = comp2.load

        system_voltage = config['system_voltage']
        wire_gauge = determine_min_gauge(current, length, system_voltage)

        # Generate wire label
        wire_label = generate_wire_label(system_code, circuit_id, segment_letter)

        # Create wire segment
        wire = WireConnection(
            wire_label=wire_label,
            from_ref=comp1.ref,
            to_ref=comp2.ref,
            wire_gauge=wire_gauge,
            wire_color='White',  # Default for Phase 2
            length=length,
            wire_type='Standard',
            warnings=[]
        )
        segments.append(wire)

    return segments


def build_circuits(parsed_netlist: Any, components: List[Component]) -> List[Circuit]:
    """
    Build Circuit objects from parsed netlist and component list.

    Groups components by their net connections to form circuits.
    For Phase 2, this handles simple linear circuits where components
    are connected in series.

    Args:
        parsed_netlist: Parsed netlist from kinparse
        components: List of Component objects with coordinates

    Returns:
        List of Circuit objects, one per net that has components
    """
    if not components:
        return []

    # Create a map of component refs to Component objects for quick lookup
    comp_map = {comp.ref: comp for comp in components}

    circuits = []

    # Iterate through nets and find which components are on each net
    for net in parsed_netlist.nets:
        # Get component refs from this net (kinparse stores nodes as 'pins')
        net_component_refs = set()
        for pin in net.pins:
            net_component_refs.add(pin.ref)

        # Find matching Component objects
        net_components = []
        for ref in net_component_refs:
            if ref in comp_map:
                net_components.append(comp_map[ref])

        # Skip nets with fewer than 2 components
        if len(net_components) < 2:
            continue

        # Create circuit (system_code will be determined later)
        circuit = Circuit(
            net_code=str(net.code),
            net_name=net.name,
            system_code='U',  # Unknown for now, will be detected later
            components=net_components,
            segments=[]
        )
        circuits.append(circuit)

    return circuits
