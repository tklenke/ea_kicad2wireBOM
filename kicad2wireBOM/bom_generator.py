# ABOUTME: Unified BOM entry generation for wire connections
# ABOUTME: Handles both multipoint (3+way) and regular 2-point connections

from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment
from kicad2wireBOM.wire_connections import (
    identify_wire_connections,
    generate_multipoint_bom_entries
)


def generate_bom_entries(
    wires: list[WireSegment],
    graph: ConnectivityGraph
) -> list[dict[str, str]]:
    """
    Generate BOM entries for all wire connections.

    Handles both multipoint (3+way) connections and regular 2-point connections.
    This is the single source of truth for BOM entry generation used by both
    the CLI and integration tests.

    Algorithm:
    1. Store wires in graph for multipoint processing
    2. Detect multipoint connection groups (N ≥ 3 pins)
    3. Generate BOM entries for multipoint connections
    4. Track which circuit IDs are used by multipoint connections
    5. Generate BOM entries for regular 2-point connections (excluding multipoint labels)
    6. Return combined list of all BOM entries

    Args:
        wires: List of wire segments with circuit_id labels
        graph: Connectivity graph containing all network nodes and connections

    Returns:
        List of BOM entry dicts, each with keys:
        - circuit_id: Wire label (e.g., "P4A")
        - from_component: Component reference (e.g., "SW1")
        - from_pin: Pin number (e.g., "2")
        - to_component: Component reference (e.g., "J1")
        - to_pin: Pin number (e.g., "2")
    """
    # Step 1: Store wires in graph (for multipoint processing)
    graph.wires = {wire.uuid: wire for wire in wires}

    # Step 2: Detect multipoint connection groups (N ≥ 3 pins)
    multipoint_groups = graph.detect_multipoint_connections()

    # Step 3: Generate BOM entries for multipoint connections
    multipoint_entries = []
    for group in multipoint_groups:
        entries = generate_multipoint_bom_entries(graph, group)
        multipoint_entries.extend(entries)

    # Step 4: Track which circuit_ids are used by multipoint
    multipoint_labels = {entry['circuit_id'] for entry in multipoint_entries}

    # Step 5: Generate BOM entries for regular 2-point connections
    regular_entries = []
    for wire in wires:
        # Skip if no label
        if not wire.circuit_id:
            continue

        # Skip if this label was handled by multipoint logic
        if wire.circuit_id in multipoint_labels:
            continue

        # Identify 2-point connection
        from_conn, to_conn = identify_wire_connections(wire, graph)

        # Both endpoints must be found
        if from_conn and to_conn:
            # Concatenate notes with space separator
            notes_str = ' '.join(wire.notes) if wire.notes else ''

            entry = {
                'circuit_id': wire.circuit_id,
                'from_component': from_conn['component_ref'],
                'from_pin': from_conn['pin_number'],
                'to_component': to_conn['component_ref'],
                'to_pin': to_conn['pin_number'],
                'notes': notes_str
            }
            regular_entries.append(entry)

    # Step 6: Return combined list (multipoint + regular entries)
    return multipoint_entries + regular_entries
