# ABOUTME: Circuit analysis module for grouping components and analyzing signal flow
# ABOUTME: Builds circuits from netlist data and manages wire segmentation

from dataclasses import dataclass, field
from typing import List, Any
from kicad2wireBOM.component import Component


@dataclass
class Circuit:
    """Represents a single electrical circuit with components and wire segments"""
    net_code: str
    net_name: str
    system_code: str
    components: List[Component]
    segments: List[Any] = field(default_factory=list)


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
