# ABOUTME: Unified BOM entry generation for wire connections
# ABOUTME: Handles both multipoint (3+way) and regular 2-point connections

from collections import deque
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment
from kicad2wireBOM.wire_connections import (
    identify_wire_connections,
    generate_multipoint_bom_entries
)


def collect_circuit_notes(
    graph: ConnectivityGraph,
    circuit_id: str,
    from_pos: tuple[float, float],
    to_pos: tuple[float, float]
) -> str:
    """
    Aggregate notes from all wire fragments forming a circuit.

    Traverses connectivity graph to find all wire segments between
    from_pos and to_pos, collecting notes from each segment.

    Args:
        graph: Connectivity graph with wires and nodes
        circuit_id: Circuit identifier (e.g., "G4A")
        from_pos: Starting component pin position
        to_pos: Ending component pin position

    Returns:
        Space-separated string of unique notes (deduplicated)
    """
    # Normalize positions to match graph keys
    from_key = (round(from_pos[0], 2), round(from_pos[1], 2))
    to_key = (round(to_pos[0], 2), round(to_pos[1], 2))

    # BFS to find all wire segments between from_pos and to_pos
    visited_nodes = set()
    visited_wires = set()
    queue = deque([from_key])
    visited_nodes.add(from_key)

    # Collect all notes from wire segments encountered
    all_notes = []

    while queue:
        current_key = queue.popleft()

        # Stop if we reached the destination
        if current_key == to_key:
            continue

        # Get node at current position
        if current_key not in graph.nodes:
            continue

        node = graph.nodes[current_key]

        # Explore all connected wires
        for wire_uuid in node.connected_wire_uuids:
            if wire_uuid in visited_wires:
                continue

            visited_wires.add(wire_uuid)

            # Skip if wire not in dict (e.g., virtual cross-sheet wires)
            if wire_uuid not in graph.wires:
                continue

            wire = graph.wires[wire_uuid]

            # Collect notes from this wire
            if hasattr(wire, 'notes') and wire.notes:
                all_notes.extend(wire.notes)

            # Get the other end of this wire
            wire_start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
            wire_end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

            # Add unvisited endpoint to queue
            if wire_start_key == current_key and wire_end_key not in visited_nodes:
                visited_nodes.add(wire_end_key)
                queue.append(wire_end_key)
            elif wire_end_key == current_key and wire_start_key not in visited_nodes:
                visited_nodes.add(wire_start_key)
                queue.append(wire_start_key)

    # Deduplicate notes while preserving order
    seen = set()
    unique_notes = []
    for note in all_notes:
        if note not in seen:
            seen.add(note)
            unique_notes.append(note)

    # Return space-separated string
    return ' '.join(unique_notes)


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
    # Update (don't overwrite) to preserve virtual cross-sheet wires already in graph
    graph.wires.update({wire.uuid: wire for wire in wires})

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
    # Track which circuit_ids we've already processed to avoid duplicates
    processed_circuit_ids = set()
    regular_entries = []
    for wire in wires:
        # Get all circuit IDs for this wire (handles pipe notation)
        # Use circuit_ids if available, otherwise fall back to circuit_id
        circuit_ids = wire.circuit_ids if wire.circuit_ids else ([wire.circuit_id] if wire.circuit_id else [])

        # Skip if no labels
        if not circuit_ids:
            continue

        # Skip wires with pipe notation (multiple circuit_ids)
        # These are parent sheet wires carrying multiple circuits to sheet pins
        # BOM entries should be generated from child sheet wires with single IDs
        if len(circuit_ids) > 1:
            continue

        # Generate BOM entry for this circuit ID
        for circuit_id in circuit_ids:
            # Skip if this label was handled by multipoint logic
            if circuit_id in multipoint_labels:
                continue

            # Skip if we've already processed this circuit_id
            # This avoids duplicate BOM entries when same ID appears on multiple sheets
            if circuit_id in processed_circuit_ids:
                continue
            processed_circuit_ids.add(circuit_id)

            # Identify 2-point connection
            from_conn, to_conn = identify_wire_connections(wire, graph)

            # Both endpoints must be found
            if from_conn and to_conn:
                # Get component pin positions
                from_pin_key = f"{from_conn['component_ref']}-{from_conn['pin_number']}"
                to_pin_key = f"{to_conn['component_ref']}-{to_conn['pin_number']}"

                # Get positions from component pins in graph
                from_pos = graph.component_pins.get(from_pin_key)
                to_pos = graph.component_pins.get(to_pin_key)

                # Collect notes from all wire fragments forming this circuit
                if from_pos and to_pos:
                    notes_str = collect_circuit_notes(graph, circuit_id, from_pos, to_pos)
                else:
                    # Fallback to single wire notes if positions not found
                    notes_str = ' '.join(wire.notes) if wire.notes else ''

                entry = {
                    'circuit_id': circuit_id,
                    'from_component': from_conn['component_ref'],
                    'from_pin': from_conn['pin_number'],
                    'to_component': to_conn['component_ref'],
                    'to_pin': to_conn['pin_number'],
                    'notes': notes_str
                }
                regular_entries.append(entry)

    # Step 6: Return combined list (multipoint + regular entries)
    return multipoint_entries + regular_entries
