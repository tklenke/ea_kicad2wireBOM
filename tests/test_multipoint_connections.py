# ABOUTME: Tests for 3+way connection detection and validation
# ABOUTME: Tests multipoint connection detection algorithm for N >= 3 connected component pins

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


def test_detect_3way_connection_with_3_pins():
    """
    Detect 3-way connection in test_03A fixture (P4A/P4B case).

    Expected: 3-pin group {SW1-pin2, SW2-pin2, J1-pin2} connected through junction.
    - 2 labels: P4A (SW2-pin2 side), P4B (SW1-pin2 side)
    - 1 unlabeled pin: J1-pin2 (common endpoint - terminal block)
    """
    # Parse schematic
    fixture_path = Path('tests/fixtures/test_03A_fixture.kicad_sch')
    schematic = parse_schematic_file(fixture_path)
    graph = build_connectivity_graph(schematic)

    # Detect multipoint connections (N >= 3)
    multipoint_groups = graph.detect_multipoint_connections()

    # Should find at least 1 multipoint connection
    # (test_03A has multiple 3-way connections)
    assert len(multipoint_groups) >= 1, \
        f"Expected at least 1 multipoint connection, found {len(multipoint_groups)}"

    # Find the specific 3-way group we're testing: SW1-2, SW2-2, J1-2 (P4A/P4B)
    target_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'SW1-2', 'SW2-2', 'J1-2'}:
            target_group = group
            break

    assert target_group is not None, \
        "Expected to find 3-way group with pins SW1-2, SW2-2, J1-2"

    # Should have exactly 3 pins
    assert len(target_group) == 3, \
        f"Expected 3 pins in group, found {len(target_group)}"


def test_detect_4way_connection():
    """
    Detect 4-way connection in test_04 fixture (G1A/G2A/G3A case).

    Expected: 4-pin group {L1-pin1, L2-pin1, L3-pin1, BT1-pin2} connected through junctions.
    - 3 labels: G1A (L1-pin1 side), G2A (L2-pin1 side), G3A (L3-pin1 side)
    - 1 unlabeled pin: BT1-pin2 (battery negative - common ground return)
    - 2 junctions forming backbone to common pin
    """
    # Parse schematic
    fixture_path = Path('tests/fixtures/test_04_fixture.kicad_sch')
    schematic = parse_schematic_file(fixture_path)
    graph = build_connectivity_graph(schematic)

    # Detect multipoint connections (N >= 3)
    multipoint_groups = graph.detect_multipoint_connections()

    # Should find at least 1 multipoint connection (the 4-way ground group)
    # Note: There may be other multipoint connections in this fixture (power circuits)
    assert len(multipoint_groups) >= 1, \
        f"Expected at least 1 multipoint connection, found {len(multipoint_groups)}"

    # Find the 4-way ground connection group
    # Look for a group with 4 pins that includes BT1-pin2
    ground_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if 'BT1-2' in component_pins and len(group) == 4:
            ground_group = group
            break

    assert ground_group is not None, \
        "Expected to find 4-pin ground group with BT1-2"

    # Extract component references from group
    component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in ground_group}

    # Expected pins: L1-1, L2-1, L3-1, BT1-2
    expected_pins = {'L1-1', 'L2-1', 'L3-1', 'BT1-2'}
    assert component_pins == expected_pins, \
        f"Expected pins {expected_pins}, found {component_pins}"


def test_count_labels_in_3way_connection():
    """
    Count circuit ID labels in multipoint connection groups.

    Test cases:
    - test_03A P4A/P4B: 3 pins, expect 2 labels
    - test_04 grounds: 4 pins, expect 3 labels
    """
    # Test case 1: test_03A (3-way connection)
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
            # Update the wire in the graph with label information
            graph.wires[wire.uuid] = wire

    # Find the 3-way group {SW1-2, SW2-2, J1-2}
    multipoint_groups = graph.detect_multipoint_connections()
    target_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'SW1-2', 'SW2-2', 'J1-2'}:
            target_group = group
            break

    assert target_group is not None, "Expected to find 3-way group SW1-2, SW2-2, J1-2"

    # Count labels in this group
    label_count = graph.count_labels_in_group(target_group)

    # 3 pins should have 2 labels (N-1)
    assert label_count == 2, \
        f"Expected 2 labels for 3-pin group, found {label_count}"

    # Test case 2: test_04 (4-way ground connection)
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

    # Store wires in graph for label counting
    for wire in wires:
        if wire.uuid in graph.wires:
            # Update the wire in the graph with label information
            graph.wires[wire.uuid] = wire

    # Find the 4-way ground group {L1-1, L2-1, L3-1, BT1-2}
    multipoint_groups = graph.detect_multipoint_connections()
    ground_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'L1-1', 'L2-1', 'L3-1', 'BT1-2'}:
            ground_group = group
            break

    assert ground_group is not None, "Expected to find 4-way ground group"

    # Count labels in this group
    label_count = graph.count_labels_in_group(ground_group)

    # 4 pins should have 3 labels (N-1)
    assert label_count == 3, \
        f"Expected 3 labels for 4-pin group, found {label_count}"


def test_identify_common_pin_in_3way():
    """
    Identify the common (unlabeled) pin in multipoint connections.

    The common pin is the one NOT reached by any labeled wire segment.

    Test cases:
    - test_03A P4A/P4B: J1-pin2 should be common pin (terminal block)
    - test_04 grounds: BT1-pin2 should be common pin (battery negative)
    """
    # Test case 1: test_03A (3-way connection)
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

    # Find the 3-way group {SW1-2, SW2-2, J1-2}
    multipoint_groups = graph.detect_multipoint_connections()
    target_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'SW1-2', 'SW2-2', 'J1-2'}:
            target_group = group
            break

    assert target_group is not None, "Expected to find 3-way group SW1-2, SW2-2, J1-2"

    # Identify common pin
    common_pin = graph.identify_common_pin(target_group)

    assert common_pin is not None, "Expected to identify a common pin"
    assert common_pin['component_ref'] == 'J1', \
        f"Expected J1 as common component, got {common_pin['component_ref']}"
    assert common_pin['pin_number'] == '2', \
        f"Expected pin 2 as common pin, got {common_pin['pin_number']}"

    # Test case 2: test_04 (4-way ground connection)
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

    # Find the 4-way ground group {L1-1, L2-1, L3-1, BT1-2}
    multipoint_groups = graph.detect_multipoint_connections()
    ground_group = None
    for group in multipoint_groups:
        component_pins = {f"{pin['component_ref']}-{pin['pin_number']}" for pin in group}
        if component_pins == {'L1-1', 'L2-1', 'L3-1', 'BT1-2'}:
            ground_group = group
            break

    assert ground_group is not None, "Expected to find 4-way ground group"

    # Identify common pin
    common_pin = graph.identify_common_pin(ground_group)

    assert common_pin is not None, "Expected to identify a common pin"
    assert common_pin['component_ref'] == 'BT1', \
        f"Expected BT1 as common component, got {common_pin['component_ref']}"
    assert common_pin['pin_number'] == '2', \
        f"Expected pin 2 as common pin, got {common_pin['pin_number']}"


def test_validate_3way_connection_correct_labels():
    """
    Validate that a correctly labeled 3+way connection passes validation.

    Test case: test_03A P4A/P4B connection
    - 3 pins connected
    - 2 labels (N-1 = 3-1 = 2) ✓
    - 1 common pin identified ✓
    - Should pass validation without errors
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

    # Validate the connection
    from kicad2wireBOM.connectivity_graph import validate_multipoint_connection

    is_valid, message = validate_multipoint_connection(graph, target_group, strict=True)

    assert is_valid, f"Expected valid connection, but got: {message}"
    assert "valid" in message.lower() or "correct" in message.lower(), \
        f"Expected success message, got: {message}"


def test_validate_3way_connection_too_many_labels():
    """
    Validate that a 3+way connection with too many labels fails validation.

    This test creates a scenario where a 3-pin connection has 3 labels
    instead of the expected 2 (N-1).

    Note: Since our fixtures are correct, we'll need to create a synthetic
    test case by manipulating the label count.
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

    # Store wires in graph
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

    # Artificially add an extra label to one of the unlabeled wires to create
    # a "too many labels" scenario
    # Find J1-pin2 position and add a fake label to one of its wires
    j1_pin2_pos = graph.component_pins.get('J1-2')
    if j1_pin2_pos:
        j1_key = (round(j1_pin2_pos[0], 2), round(j1_pin2_pos[1], 2))
        j1_node = graph.nodes.get(j1_key)
        if j1_node and j1_node.connected_wire_uuids:
            # Add a fake circuit_id to one of the unlabeled wires
            for wire_uuid in j1_node.connected_wire_uuids:
                wire = graph.wires[wire_uuid]
                if not hasattr(wire, 'circuit_id') or not wire.circuit_id:
                    wire.circuit_id = 'FAKE_LABEL'
                    break

    # Validate the connection - should fail due to too many labels
    from kicad2wireBOM.connectivity_graph import validate_multipoint_connection

    is_valid, message = validate_multipoint_connection(graph, target_group, strict=True)

    assert not is_valid, "Expected invalid connection due to too many labels"
    assert "too many" in message.lower() or "label" in message.lower(), \
        f"Expected 'too many labels' error, got: {message}"


def test_validate_3way_connection_too_few_labels():
    """
    Validate that a 3+way connection with too few labels fails validation.

    This test creates a scenario where a 3-pin connection has 1 label
    instead of the expected 2 (N-1).
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

    # Store wires in graph
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

    # Remove one of the labels to create "too few labels" scenario
    # Find and remove P4A label from SW2-pin2 segment
    sw2_pin2_pos = graph.component_pins.get('SW2-2')
    if sw2_pin2_pos:
        sw2_key = (round(sw2_pin2_pos[0], 2), round(sw2_pin2_pos[1], 2))
        sw2_node = graph.nodes.get(sw2_key)
        if sw2_node:
            for wire_uuid in sw2_node.connected_wire_uuids:
                wire = graph.wires[wire_uuid]
                if hasattr(wire, 'circuit_id') and wire.circuit_id == 'P4A':
                    wire.circuit_id = None
                    break

    # Validate the connection - should fail due to too few labels
    from kicad2wireBOM.connectivity_graph import validate_multipoint_connection

    is_valid, message = validate_multipoint_connection(graph, target_group, strict=True)

    assert not is_valid, "Expected invalid connection due to too few labels"
    assert "too few" in message.lower() or "label" in message.lower() or "missing" in message.lower(), \
        f"Expected 'too few labels' error, got: {message}"
