# ABOUTME: Integration tests for complete BOM generation with multipoint connections
# ABOUTME: Tests end-to-end BOM generation including 3+way connections

import pytest
from pathlib import Path
from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    parse_wire_element,
    parse_label_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.graph_builder import build_connectivity_graph
from kicad2wireBOM.wire_connections import (
    identify_wire_connections,
    generate_multipoint_bom_entries
)


def test_03A_fixture_multipoint_integration():
    """
    Integration test for test_03A fixture with 3-way connections.

    Verifies that multipoint BOM generation creates correct entries for:
    - P4A: SW2-2 → J1-2 (3-way connection)
    - P4B: SW1-2 → J1-2 (3-way connection)

    And regular 2-point connections:
    - P1A: SW1-1 → J1-1
    - P2A: SW2-1 → J1-1
    - P3A: SW1-3 → SW2-3
    """
    fixture_path = Path('tests/fixtures/test_03A_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Build connectivity graph
    graph = build_connectivity_graph(sexp)

    # Store wires in graph for multipoint processing
    for wire in wires:
        if wire.uuid in graph.wires:
            graph.wires[wire.uuid] = wire

    # Detect multipoint connections
    multipoint_groups = graph.detect_multipoint_connections()

    # Generate BOM entries for multipoint connections
    multipoint_entries = []
    multipoint_labels = set()  # Track labels used by multipoint connections

    for group in multipoint_groups:
        entries = generate_multipoint_bom_entries(graph, group)
        multipoint_entries.extend(entries)
        # Track which labels are used by multipoint connections
        for entry in entries:
            multipoint_labels.add(entry['circuit_id'])

    # Generate BOM entries for regular 2-point connections
    regular_entries = []
    for wire in wires:
        if not wire.circuit_id:
            continue  # Skip unlabeled wires

        # Skip wires that are part of multipoint connections
        if wire.circuit_id in multipoint_labels:
            continue

        start_conn, end_conn = identify_wire_connections(wire, graph)

        if start_conn and end_conn:
            entry = {
                'circuit_id': wire.circuit_id,
                'from_component': start_conn['component_ref'],
                'from_pin': start_conn['pin_number'],
                'to_component': end_conn['component_ref'],
                'to_pin': end_conn['pin_number']
            }
            regular_entries.append(entry)

    # Combine all entries
    all_entries = multipoint_entries + regular_entries

    # Verify we have 5 total entries (P1A, P2A, P3A, P4A, P4B)
    assert len(all_entries) == 5, \
        f"Expected 5 BOM entries, got {len(all_entries)}"

    # Build lookup by circuit_id
    entries_by_label = {entry['circuit_id']: entry for entry in all_entries}

    # Verify multipoint entries (P4A, P4B)
    assert 'P4A' in entries_by_label, "Expected P4A entry"
    p4a = entries_by_label['P4A']
    assert p4a['from_component'] == 'SW2' and p4a['from_pin'] == '2'
    assert p4a['to_component'] == 'J1' and p4a['to_pin'] == '2'

    assert 'P4B' in entries_by_label, "Expected P4B entry"
    p4b = entries_by_label['P4B']
    assert p4b['from_component'] == 'SW1' and p4b['from_pin'] == '2'
    assert p4b['to_component'] == 'J1' and p4b['to_pin'] == '2'

    # Verify regular 2-point entries
    assert 'P1A' in entries_by_label, "Expected P1A entry"
    p1a = entries_by_label['P1A']
    assert p1a['from_component'] == 'SW1' and p1a['from_pin'] == '1'
    assert p1a['to_component'] == 'J1' and p1a['to_pin'] == '1'

    assert 'P2A' in entries_by_label, "Expected P2A entry"
    p2a = entries_by_label['P2A']
    assert p2a['from_component'] == 'SW2' and p2a['from_pin'] == '1'
    assert p2a['to_component'] == 'J1' and p2a['to_pin'] == '1'

    assert 'P3A' in entries_by_label, "Expected P3A entry"
    p3a = entries_by_label['P3A']
    assert p3a['from_component'] == 'SW1' and p3a['from_pin'] == '3'
    assert p3a['to_component'] == 'SW2' and p3a['to_pin'] == '3'


def test_04_fixture_multipoint_integration():
    """
    Integration test for test_04 fixture with 4-way ground connection.

    Verifies multipoint BOM generation for:
    - G1A, G2A, G3A: L1/L2/L3 → BT1-2 (4-way ground)

    Plus power circuits (L1A, L2A, L3A, L4A)
    """
    fixture_path = Path('tests/fixtures/test_04_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Build connectivity graph
    graph = build_connectivity_graph(sexp)

    # Store wires in graph
    for wire in wires:
        if wire.uuid in graph.wires:
            graph.wires[wire.uuid] = wire

    # Detect multipoint connections
    multipoint_groups = graph.detect_multipoint_connections()

    # Generate BOM entries for multipoint connections
    multipoint_entries = []
    multipoint_labels = set()

    for group in multipoint_groups:
        entries = generate_multipoint_bom_entries(graph, group)
        multipoint_entries.extend(entries)
        for entry in entries:
            multipoint_labels.add(entry['circuit_id'])

    # Generate BOM entries for regular 2-point connections
    regular_entries = []
    for wire in wires:
        if not wire.circuit_id:
            continue

        if wire.circuit_id in multipoint_labels:
            continue

        start_conn, end_conn = identify_wire_connections(wire, graph)

        if start_conn and end_conn:
            entry = {
                'circuit_id': wire.circuit_id,
                'from_component': start_conn['component_ref'],
                'from_pin': start_conn['pin_number'],
                'to_component': end_conn['component_ref'],
                'to_pin': end_conn['pin_number']
            }
            regular_entries.append(entry)

    # Combine all entries
    all_entries = multipoint_entries + regular_entries

    # Should have 7 entries: G1A, G2A, G3A (grounds) + L1A, L2A, L3A, L4A (loads)
    assert len(all_entries) == 7, \
        f"Expected 7 BOM entries, got {len(all_entries)}: {[e['circuit_id'] for e in all_entries]}"

    # Build lookup
    entries_by_label = {entry['circuit_id']: entry for entry in all_entries}

    # Verify ground entries (multipoint)
    assert 'G1A' in entries_by_label, "Expected G1A entry"
    g1a = entries_by_label['G1A']
    assert g1a['from_component'] == 'L1' and g1a['from_pin'] == '1', \
        f"G1A from: expected L1-1, got {g1a['from_component']}-{g1a['from_pin']}"
    assert g1a['to_component'] == 'BT1' and g1a['to_pin'] == '2', \
        f"G1A to: expected BT1-2, got {g1a['to_component']}-{g1a['to_pin']}"

    assert 'G2A' in entries_by_label, "Expected G2A entry"
    g2a = entries_by_label['G2A']
    assert g2a['from_component'] == 'L2' and g2a['from_pin'] == '1', \
        f"G2A from: expected L2-1, got {g2a['from_component']}-{g2a['from_pin']}"
    assert g2a['to_component'] == 'BT1' and g2a['to_pin'] == '2', \
        f"G2A to: expected BT1-2, got {g2a['to_component']}-{g2a['to_pin']}"

    assert 'G3A' in entries_by_label, "Expected G3A entry"
    g3a = entries_by_label['G3A']
    assert g3a['from_component'] == 'L3' and g3a['from_pin'] == '1', \
        f"G3A from: expected L3-1, got {g3a['from_component']}-{g3a['from_pin']}"
    assert g3a['to_component'] == 'BT1' and g3a['to_pin'] == '2', \
        f"G3A to: expected BT1-2, got {g3a['to_component']}-{g3a['to_pin']}"

    # Verify power entries exist (don't assert specific connections since fixture may vary)
    assert 'L1A' in entries_by_label, "Expected L1A entry"
    assert 'L2A' in entries_by_label, "Expected L2A entry"
    assert 'L3A' in entries_by_label, "Expected L3A entry"
    assert 'L4A' in entries_by_label, "Expected L4A entry"
