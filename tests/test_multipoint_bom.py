# ABOUTME: Tests for BOM generation with 3+way connections
# ABOUTME: Tests that multipoint connections generate correct BOM entries

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
from kicad2wireBOM.wire_connections import generate_multipoint_bom_entries


def test_generate_bom_for_3way_connection():
    """
    Generate BOM entries for a 3-way connection.

    Test case: test_03A P4A/P4B connection
    - 3 pins: SW1-2, SW2-2, J1-2
    - 2 labels: P4A (SW2-pin2 side), P4B (SW1-pin2 side)
    - Common pin: J1-2

    Expected BOM entries:
    - P4A: SW2-2 → J1-2
    - P4B: SW1-2 → J1-2
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

    # Store wires in graph for label counting
    for wire in wires:
        if wire.uuid in graph.wires:
            graph.wires[wire.uuid] = wire

    # Find the 3-way group
    multipoint_groups = graph.detect_multipoint_connections()
    target_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'SW1-2', 'SW2-2', 'J1-2'}:
            target_group = group
            break

    assert target_group is not None, "Expected to find 3-way group"

    # Generate BOM entries for this multipoint connection
    bom_entries = generate_multipoint_bom_entries(graph, target_group)

    # Should have 2 entries (one for each labeled segment)
    assert len(bom_entries) == 2, \
        f"Expected 2 BOM entries for 3-way connection, got {len(bom_entries)}"

    # Extract entry info
    entries_by_label = {entry['circuit_id']: entry for entry in bom_entries}

    # Check P4A entry: SW2-2 → J1-2
    assert 'P4A' in entries_by_label, "Expected P4A entry"
    p4a = entries_by_label['P4A']
    assert p4a['from_component'] == 'SW2', f"P4A from: expected SW2, got {p4a['from_component']}"
    assert p4a['from_pin'] == '2', f"P4A from pin: expected 2, got {p4a['from_pin']}"
    assert p4a['to_component'] == 'J1', f"P4A to: expected J1, got {p4a['to_component']}"
    assert p4a['to_pin'] == '2', f"P4A to pin: expected 2, got {p4a['to_pin']}"

    # Check P4B entry: SW1-2 → J1-2
    assert 'P4B' in entries_by_label, "Expected P4B entry"
    p4b = entries_by_label['P4B']
    assert p4b['from_component'] == 'SW1', f"P4B from: expected SW1, got {p4b['from_component']}"
    assert p4b['from_pin'] == '2', f"P4B from pin: expected 2, got {p4b['from_pin']}"
    assert p4b['to_component'] == 'J1', f"P4B to: expected J1, got {p4b['to_component']}"
    assert p4b['to_pin'] == '2', f"P4B to pin: expected 2, got {p4b['to_pin']}"


def test_generate_bom_for_4way_connection():
    """
    Generate BOM entries for a 4-way ground connection.

    Test case: test_04 ground connection
    - 4 pins: L1-1, L2-1, L3-1, BT1-2
    - 3 labels: G1A, G2A, G3A
    - Common pin: BT1-2 (battery negative)

    Expected BOM entries:
    - G1A: L1-1 → BT1-2
    - G2A: L2-1 → BT1-2
    - G3A: L3-1 → BT1-2
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

    # Find the 4-way ground group
    multipoint_groups = graph.detect_multipoint_connections()
    ground_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'L1-1', 'L2-1', 'L3-1', 'BT1-2'}:
            ground_group = group
            break

    assert ground_group is not None, "Expected to find 4-way ground group"

    # Generate BOM entries for this multipoint connection
    bom_entries = generate_multipoint_bom_entries(graph, ground_group)

    # Should have 3 entries (one for each labeled segment)
    assert len(bom_entries) == 3, \
        f"Expected 3 BOM entries for 4-way connection, got {len(bom_entries)}"

    # Extract entry info
    entries_by_label = {entry['circuit_id']: entry for entry in bom_entries}

    # Check G1A: L1-1 → BT1-2
    assert 'G1A' in entries_by_label, "Expected G1A entry"
    g1a = entries_by_label['G1A']
    assert g1a['from_component'] == 'L1', f"G1A from: expected L1, got {g1a['from_component']}"
    assert g1a['from_pin'] == '1', f"G1A from pin: expected 1, got {g1a['from_pin']}"
    assert g1a['to_component'] == 'BT1', f"G1A to: expected BT1, got {g1a['to_component']}"
    assert g1a['to_pin'] == '2', f"G1A to pin: expected 2, got {g1a['to_pin']}"

    # Check G2A: L2-1 → BT1-2
    assert 'G2A' in entries_by_label, "Expected G2A entry"
    g2a = entries_by_label['G2A']
    assert g2a['from_component'] == 'L2', f"G2A from: expected L2, got {g2a['from_component']}"
    assert g2a['from_pin'] == '1', f"G2A from pin: expected 1, got {g2a['from_pin']}"
    assert g2a['to_component'] == 'BT1', f"G2A to: expected BT1, got {g2a['to_component']}"
    assert g2a['to_pin'] == '2', f"G2A to pin: expected 2, got {g2a['to_pin']}"

    # Check G3A: L3-1 → BT1-2
    assert 'G3A' in entries_by_label, "Expected G3A entry"
    g3a = entries_by_label['G3A']
    assert g3a['from_component'] == 'L3', f"G3A from: expected L3, got {g3a['from_component']}"
    assert g3a['from_pin'] == '1', f"G3A from pin: expected 1, got {g3a['from_pin']}"
    assert g3a['to_component'] == 'BT1', f"G3A to: expected BT1, got {g3a['to_component']}"
    assert g3a['to_pin'] == '2', f"G3A to pin: expected 2, got {g3a['to_pin']}"
