# ABOUTME: Wire connection identification
# ABOUTME: Identifies what each wire endpoint connects to (pins, junctions, etc)

from typing import Optional
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment


def is_power_symbol(comp_ref: Optional[str]) -> bool:
    """
    Check if a component reference is a power symbol.

    Power symbols represent global nets (GND, voltage rails) and are not
    physical components in the wire harness.

    KiCad power symbol patterns used in EA schematics:
    - GND, GND1-6, GND12, GND24, GNDREF
    - +nV, +nVA where n is 1, 2, 3, 4, 5, 6, 12, or 24
    - -nV, -nVA (same voltage values)
    - VDC, VAC

    Args:
        comp_ref: Component reference designator (e.g., 'GND', '+12V', 'SW1')

    Returns:
        True if component is a power symbol, False otherwise
    """
    if not comp_ref:
        return False

    # Exact matches
    if comp_ref in ('GND', 'GNDREF', 'VDC', 'VAC'):
        return True

    # GNDn patterns (n = 1, 2, 3, 4, 5, 6, 12, 24)
    if comp_ref in ('GND1', 'GND2', 'GND3', 'GND4', 'GND5', 'GND6', 'GND12', 'GND24'):
        return True

    # Voltage patterns: +nV, +nVA, -nV, -nVA where n is 1, 2, 3, 4, 5, 6, 12, or 24
    valid_voltages = ('1', '2', '3', '4', '5', '6', '12', '24')
    for voltage in valid_voltages:
        if comp_ref in (f'+{voltage}V', f'+{voltage}VA', f'-{voltage}V', f'-{voltage}VA'):
            return True

    return False


def identify_wire_connections(
    wire: WireSegment,
    graph: ConnectivityGraph
) -> tuple[Optional[dict[str, str]], Optional[dict[str, str]]]:
    """
    Identify what components this wire connects.

    Traces through junctions to find component pins at both ends.

    For hierarchical schematics, ensures direction flows from local component
    to cross-sheet component (child → parent).

    Args:
        wire: Wire segment to identify connections for
        graph: Connectivity graph with all nodes

    Returns:
        Tuple of (from_pin, to_pin) where each is:
        - dict with 'component_ref' and 'pin_number' (e.g., {'component_ref': 'SW1', 'pin_number': '3'})
        - None if endpoint has no component connection
    """
    # Get nodes at wire endpoints
    start_node, end_node = graph.get_connected_nodes(wire.uuid)

    # Trace through junctions to find component pins
    start_conn = graph.trace_to_component(start_node, exclude_wire_uuid=wire.uuid)
    end_conn = graph.trace_to_component(end_node, exclude_wire_uuid=wire.uuid)

    # For cross-sheet connections, swap direction so local component (child) is FROM
    # and cross-sheet component (parent) is TO
    if start_node and end_node:
        start_is_cross = start_node.node_type in ('hierarchical_label', 'sheet_pin')
        end_is_cross = end_node.node_type in ('hierarchical_label', 'sheet_pin')

        # Check if either endpoint is a junction or wire_endpoint leading to a cross-sheet node
        # This handles wires that connect: component → junction/wire_endpoint → hierarchical_label/sheet_pin
        def leads_to_cross_sheet(node) -> bool:
            """Check if junction/wire_endpoint node leads to hierarchical_label/sheet_pin"""
            if node.node_type in ('junction', 'wire_endpoint'):
                # Get all connected wires except the current wire
                connected_wires = [uuid for uuid in node.connected_wire_uuids if uuid != wire.uuid]
                # Check if any connected wire leads to hierarchical_label/sheet_pin
                for other_wire_uuid in connected_wires:
                    if other_wire_uuid in graph.wires:
                        other_wire = graph.wires[other_wire_uuid]
                        # Get the other endpoint of this wire
                        node_key = (round(node.position[0], 2), round(node.position[1], 2))
                        start_key = (round(other_wire.start_point[0], 2), round(other_wire.start_point[1], 2))
                        end_key = (round(other_wire.end_point[0], 2), round(other_wire.end_point[1], 2))

                        other_end_key = end_key if start_key == node_key else start_key
                        if other_end_key in graph.nodes:
                            other_end = graph.nodes[other_end_key]
                            if other_end.node_type in ('hierarchical_label', 'sheet_pin'):
                                return True
            return False

        start_leads_cross = leads_to_cross_sheet(start_node)
        end_leads_cross = leads_to_cross_sheet(end_node)

        # Swap direction if either endpoint is or leads to cross-sheet
        # This ensures correct direction for both parent and child wires:
        # - Parent wires: cross-sheet component (via sheet_pin) → local component
        # - Child wires: parent component (via hierarchical_label) → local component
        if (start_is_cross or start_leads_cross) and not (end_is_cross or end_leads_cross):
            # Start is cross-sheet, swap so cross-sheet component is TO
            return (end_conn, start_conn)
        if (end_is_cross or end_leads_cross) and not (start_is_cross or start_leads_cross):
            # End is cross-sheet, swap so cross-sheet component is TO
            return (end_conn, start_conn)

    return (start_conn, end_conn)


def generate_multipoint_bom_entries(
    graph: ConnectivityGraph,
    group: list[dict[str, str]]
) -> list[dict[str, str]]:
    """
    Generate BOM entries for a multipoint (3+way) connection.

    For each labeled segment in the group, generates an entry from
    the labeled pin to the common pin.

    Algorithm:
    1. Check if group contains a power symbol - if so, skip (these are separate 2-point wires)
    2. Identify the common pin in the group
    3. For each pin in the group (except common pin):
       - Trace segment from pin to find if it has a label
       - If labeled, create BOM entry: labeled-pin → common-pin

    Args:
        graph: The connectivity graph
        group: List of component pins in the multipoint connection

    Returns:
        List of BOM entry dicts with keys:
        - circuit_id: The wire label
        - from_component: Source component reference
        - from_pin: Source pin number
        - to_component: Destination component reference
        - to_pin: Destination pin number
    """
    bom_entries = []

    # Check if this group contains a power symbol
    # Power symbols (GND, +12V, etc.) represent global nets, not physical junctions
    # If present, the power symbol IS the common pin (all other pins connect to it)
    power_pins = [pin for pin in group if is_power_symbol(pin['component_ref'])]

    if power_pins:
        # Power symbol multipoint: treat power symbol as common pin
        # All other pins connect to the power symbol with separate labeled wires
        if len(power_pins) > 1:
            # Multiple power symbols in group - ambiguous, skip
            return []
        common_pin = power_pins[0]
    else:
        # Regular multipoint: identify common pin using label analysis
        common_pin = graph.identify_common_pin(group)

    if common_pin is None:
        # Cannot identify common pin (only applies to non-power symbol groups)
        return []

    common_pin_key = f"{common_pin['component_ref']}-{common_pin['pin_number']}"

    # Get all pin positions in the group
    group_pin_positions = {}
    for pin in group:
        pin_key = f"{pin['component_ref']}-{pin['pin_number']}"
        if pin_key in graph.component_pins:
            pos = graph.component_pins[pin_key]
            group_pin_positions[pin_key] = (round(pos[0], 2), round(pos[1], 2))

    # Build fragment count map to identify junctions
    fragment_count_at_position = {}
    for wire_uuid in graph.wires:
        wire = graph.wires[wire_uuid]
        start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
        end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

        fragment_count_at_position[start_key] = fragment_count_at_position.get(start_key, 0) + 1
        fragment_count_at_position[end_key] = fragment_count_at_position.get(end_key, 0) + 1

    # For each non-common pin, trace its segment and find label
    for pin in group:
        pin_key = f"{pin['component_ref']}-{pin['pin_number']}"

        # Skip common pin
        if pin_key == common_pin_key:
            continue

        if pin_key not in group_pin_positions:
            continue

        pin_pos_key = group_pin_positions[pin_key]

        # Trace segment from this pin to find labels and notes
        visited_positions = set()
        visited_wires = set()
        queue = [pin_pos_key]
        visited_positions.add(pin_pos_key)
        segment_labels = []
        segment_notes = []

        while queue:
            current_pos = queue.pop(0)

            # Check if this is a junction (3+ fragments) - stop here
            if current_pos != pin_pos_key:
                fragment_count = fragment_count_at_position.get(current_pos, 0)
                if fragment_count >= 3:
                    # Junction - stop tracing
                    continue

            # Get node at current position
            node = graph.nodes.get(current_pos)
            if not node:
                continue

            # Explore all connected wires in this segment
            for wire_uuid in node.connected_wire_uuids:
                if wire_uuid in visited_wires:
                    continue
                visited_wires.add(wire_uuid)

                wire = graph.wires[wire_uuid]

                # Check if this wire has a label
                if hasattr(wire, 'circuit_id') and wire.circuit_id:
                    segment_labels.append(wire.circuit_id)

                # Collect notes from this wire
                if hasattr(wire, 'notes') and wire.notes:
                    segment_notes.extend(wire.notes)

                # Find the other end of the wire
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                if current_pos == start_key:
                    other_key = end_key
                elif current_pos == end_key:
                    other_key = start_key
                else:
                    continue

                # Check if other end is another group pin - if so, stop
                if other_key in group_pin_positions.values() and other_key != pin_pos_key:
                    # Reached another pin in the group - stop
                    continue

                # Continue tracing through connections
                if other_key not in visited_positions:
                    visited_positions.add(other_key)
                    queue.append(other_key)

        # If this segment has a label, create BOM entry
        if segment_labels:
            # Use first label found (should only be one per segment)
            circuit_id = segment_labels[0]

            # Concatenate notes with space separator
            notes_str = ' '.join(segment_notes) if segment_notes else ''

            bom_entry = {
                'circuit_id': circuit_id,
                'from_component': pin['component_ref'],
                'from_pin': pin['pin_number'],
                'to_component': common_pin['component_ref'],
                'to_pin': common_pin['pin_number'],
                'notes': notes_str
            }
            bom_entries.append(bom_entry)

    return bom_entries
