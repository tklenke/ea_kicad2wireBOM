# ABOUTME: Tests for 3+way connection detection and validation
# ABOUTME: Tests multipoint connection detection algorithm for N >= 3 connected component pins

import pytest
from pathlib import Path
from kicad2wireBOM.parser import parse_schematic_file
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
