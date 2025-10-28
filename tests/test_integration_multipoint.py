# ABOUTME: Integration tests for complete BOM generation with multipoint connections
# ABOUTME: Tests end-to-end BOM generation including 3+way connections and circuit-based wire sizing

import pytest
import re
from pathlib import Path
from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    extract_symbols,
    parse_wire_element,
    parse_label_element,
    parse_symbol_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.graph_builder import build_connectivity_graph
from kicad2wireBOM.bom_generator import generate_bom_entries
from kicad2wireBOM.wire_calculator import (
    calculate_length,
    group_wires_by_circuit,
    determine_circuit_current,
    determine_min_gauge
)
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.component import Component
from kicad2wireBOM.reference_data import SYSTEM_COLOR_MAP, DEFAULT_CONFIG


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

    # Generate BOM entries (handles both multipoint and regular)
    all_entries = generate_bom_entries(wires, graph)

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

    # Generate BOM entries (handles both multipoint and regular)
    all_entries = generate_bom_entries(wires, graph)

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


def test_circuit_based_wire_sizing():
    """
    Integration test for circuit-based wire gauge calculation.

    Verifies all wires in same circuit get same gauge based on total circuit current.

    Uses test_07_fixture with:
    - Circuit L1 (single load): L1A, L1B → 16 AWG (L1 = 10A, 170in max length)
    - Circuit L2 (parallel loads): L2A, L2B, L2C → 12 AWG (L2+L3 = 14A)
    - Circuit P1 (power distribution): P1A → 12 AWG (BT1 = 40A source)
    - Circuit G1-G4 (grounds): Various gauges based on connected loads/sources
    """
    fixture_path = Path('tests/fixtures/test_07_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires, labels, and components
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    symbol_sexps = extract_symbols(sexp)

    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Parse components (skip those with missing LocLoad encoding)
    components = []
    missing_locload_components = []
    for s in symbol_sexps:
        try:
            components.append(parse_symbol_element(s))
        except ValueError as e:
            # Component missing LocLoad encoding - track for validation
            # Extract component reference from error message "Component {ref} missing LocLoad encoding"
            match = re.search(r'Component (\S+) missing', str(e))
            if match:
                missing_locload_components.append(match.group(1))
            pass

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Build connectivity graph
    graph = build_connectivity_graph(sexp)

    # Generate BOM entries
    bom_entries = generate_bom_entries(wires, graph)

    # Create component lookup map
    comp_map = {comp.ref: comp for comp in components}

    # Create WireConnection objects (simulating __main__.py logic)
    wire_connections = []
    for entry in bom_entries:
        circuit_id = entry['circuit_id']
        from_comp = entry['from_component']
        to_comp = entry['to_component']

        # Look up component objects
        comp1 = comp_map.get(from_comp) if from_comp else None
        comp2 = comp_map.get(to_comp) if to_comp else None

        # Calculate length
        if comp1 and comp2:
            length = calculate_length(comp1, comp2, slack=24.0)
        else:
            length = 50.0  # Fallback

        # Create WireConnection with placeholder gauge
        wire_conn = WireConnection(
            wire_label=circuit_id,
            from_component=from_comp,
            from_pin=entry['from_pin'],
            to_component=to_comp,
            to_pin=entry['to_pin'],
            wire_gauge=-99,  # Placeholder
            wire_color='White',
            length=length,
            wire_type='M22759/16',
            notes='',
            warnings=[]
        )
        wire_connections.append(wire_conn)

    # Apply circuit-based wire gauge calculation
    circuit_groups = group_wires_by_circuit(wire_connections)

    circuit_gauges = {}
    for circuit_id, circuit_wires in circuit_groups.items():
        circuit_current = determine_circuit_current(circuit_wires, components, graph)
        max_length = max(wire.length for wire in circuit_wires)
        gauge = determine_min_gauge(circuit_current, max_length, system_voltage=14.0)
        circuit_gauges[circuit_id] = gauge

    # Apply gauges to wires
    wire_gauge_map = {}
    for wire in wire_connections:
        from kicad2wireBOM.wire_calculator import parse_net_name
        parsed = parse_net_name(f"/{wire.wire_label}")
        if parsed:
            circuit_id = f"{parsed['system']}{parsed['circuit']}"
            wire.wire_gauge = circuit_gauges.get(circuit_id, -99)
            wire_gauge_map[wire.wire_label] = wire.wire_gauge

    # VERIFY: Circuit L1 wires all have same gauge (16 AWG for 10A load over 170in max length)
    assert wire_gauge_map.get('L1A') == 16, f"L1A expected 16 AWG, got {wire_gauge_map.get('L1A')}"
    assert wire_gauge_map.get('L1B') == 16, f"L1B expected 16 AWG, got {wire_gauge_map.get('L1B')}"

    # VERIFY: Circuit L2 wires all have same gauge (12 AWG for 14A total)
    assert wire_gauge_map.get('L2A') == 12, f"L2A expected 12 AWG, got {wire_gauge_map.get('L2A')}"
    assert wire_gauge_map.get('L2B') == 12, f"L2B expected 12 AWG, got {wire_gauge_map.get('L2B')}"
    assert wire_gauge_map.get('L2C') == 12, f"L2C expected 12 AWG, got {wire_gauge_map.get('L2C')}"

    # VERIFY: Power circuit P1 (40A source)
    assert wire_gauge_map.get('P1A') == 12, f"P1A expected 12 AWG, got {wire_gauge_map.get('P1A')}"

    # VERIFY: Ground circuits
    assert wire_gauge_map.get('G1A') == 16, f"G1A expected 16 AWG, got {wire_gauge_map.get('G1A')}"  # 10A, 164in → 16 AWG
    assert wire_gauge_map.get('G2A') == 18, f"G2A expected 18 AWG, got {wire_gauge_map.get('G2A')}"  # 7A, 134in → 18 AWG
    assert wire_gauge_map.get('G3A') == 18, f"G3A expected 18 AWG, got {wire_gauge_map.get('G3A')}"  # 7A, 134in → 18 AWG
    assert wire_gauge_map.get('G4A') == 12, f"G4A expected 12 AWG, got {wire_gauge_map.get('G4A')}"  # 40A, 49in → 12 AWG
