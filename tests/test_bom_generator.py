# ABOUTME: Unit tests for unified BOM entry generation
# ABOUTME: Tests the generate_bom_entries function with various fixture types

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
from kicad2wireBOM.bom_generator import generate_bom_entries, collect_circuit_notes


def test_generate_bom_entries_with_2point_connections():
    """
    Test BOM generation with only regular 2-point connections.

    Uses test_01 fixture which has no multipoint connections.
    Verifies that each labeled wire produces one BOM entry.
    """
    fixture_path = Path('tests/fixtures/test_01_fixture.kicad_sch')
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

    # Generate BOM entries using unified function
    bom_entries = generate_bom_entries(wires, graph)

    # test_01 fixture has 2 labeled wires (G1A, P1A)
    assert len(bom_entries) == 2, \
        f"Expected 2 BOM entries for test_01, got {len(bom_entries)}"

    # Verify all entries have required fields
    for entry in bom_entries:
        assert 'circuit_id' in entry
        assert 'from_component' in entry
        assert 'from_pin' in entry
        assert 'to_component' in entry
        assert 'to_pin' in entry
        assert 'notes' in entry
        assert entry['circuit_id'] is not None and entry['circuit_id'] != ''

    # Verify we have the expected circuit IDs
    circuit_ids = {entry['circuit_id'] for entry in bom_entries}
    assert circuit_ids == {'G1A', 'P1A'}, \
        f"Expected circuit IDs G1A and P1A, got {circuit_ids}"


def test_generate_bom_entries_with_3way_connection():
    """
    Test BOM generation with 3-way multipoint connections.

    Uses test_03A fixture which has:
    - 2 multipoint entries (P4A, P4B) from 3-way connection
    - 3 regular 2-point entries (P1A, P2A, P3A)

    Expected total: 5 entries
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

    # Generate BOM entries using unified function
    bom_entries = generate_bom_entries(wires, graph)

    # Verify we have 5 total entries (P1A, P2A, P3A, P4A, P4B)
    assert len(bom_entries) == 5, \
        f"Expected 5 BOM entries, got {len(bom_entries)}"

    # Build lookup by circuit_id
    entries_by_label = {entry['circuit_id']: entry for entry in bom_entries}

    # Verify multipoint entries (P4A, P4B) exist
    assert 'P4A' in entries_by_label, "Expected P4A entry"
    p4a = entries_by_label['P4A']
    assert p4a['from_component'] == 'SW2' and p4a['from_pin'] == '2'
    assert p4a['to_component'] == 'J1' and p4a['to_pin'] == '2'

    assert 'P4B' in entries_by_label, "Expected P4B entry"
    p4b = entries_by_label['P4B']
    assert p4b['from_component'] == 'SW1' and p4b['from_pin'] == '2'
    assert p4b['to_component'] == 'J1' and p4b['to_pin'] == '2'

    # Verify regular 2-point entries exist
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


def test_generate_bom_entries_with_4way_connection():
    """
    Test BOM generation with 4-way multipoint connections.

    Uses test_04 fixture which has:
    - 3 multipoint entries (G1A, G2A, G3A) from 4-way ground connection
    - 4 regular power circuit entries (L1A, L2A, L3A, L4A)

    Expected total: 7 entries
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

    # Generate BOM entries using unified function
    bom_entries = generate_bom_entries(wires, graph)

    # Should have 7 entries: G1A, G2A, G3A (grounds) + L1A, L2A, L3A, L4A (loads)
    assert len(bom_entries) == 7, \
        f"Expected 7 BOM entries, got {len(bom_entries)}: {[e['circuit_id'] for e in bom_entries]}"

    # Build lookup
    entries_by_label = {entry['circuit_id']: entry for entry in bom_entries}

    # Verify ground entries (multipoint) with specific connections
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

    # Verify power entries exist
    assert 'L1A' in entries_by_label, "Expected L1A entry"
    assert 'L2A' in entries_by_label, "Expected L2A entry"
    assert 'L3A' in entries_by_label, "Expected L3A entry"
    assert 'L4A' in entries_by_label, "Expected L4A entry"


def test_collect_circuit_notes_single_fragment_with_notes():
    """
    Test notes collection from a single wire fragment.

    Uses test_01 fixture - simple 2-wire circuit with no notes on wires.
    """
    fixture_path = Path('tests/fixtures/test_01_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Build graph
    graph = build_connectivity_graph(sexp)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Store wires in graph
    graph.wires = {wire.uuid: wire for wire in wires}

    # Find a wire with a circuit_id
    test_wire = next(w for w in wires if w.circuit_id)

    # Get component positions at endpoints
    from_pos = test_wire.start_point
    to_pos = test_wire.end_point

    # Manually add notes to the wire for testing
    test_wire.notes = ['TEST_NOTE']

    # Collect notes
    notes = collect_circuit_notes(graph, test_wire.circuit_id, from_pos, to_pos)

    # Should get the note
    assert notes == 'TEST_NOTE', f"Expected 'TEST_NOTE', got '{notes}'"


def test_collect_circuit_notes_multiple_fragments():
    """
    Test notes collection across multiple wire fragments forming a circuit.

    Uses test_05C fixture which has:
    - Circuit G4A: BT1-2 to GB1-1 via junction
      - Vertical fragment (BT1-2 to junction): has "10AWG" label
      - Horizontal fragment (junction to GB1-1): has "G4A" circuit ID
    """
    fixture_path = Path('tests/fixtures/test_05C_fixture.kicad_sch')
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
    graph.wires = {wire.uuid: wire for wire in wires}

    # Find the G4A wire (horizontal fragment with circuit ID)
    g4a_wire = next(w for w in wires if w.circuit_id == 'G4A')

    # Get the component pin positions (BT1-2 and GB1-1)
    # We need to trace to component pins to get actual endpoints
    from kicad2wireBOM.wire_connections import identify_wire_connections
    from_conn, to_conn = identify_wire_connections(g4a_wire, graph)

    # Get positions from component pins in graph
    from_pos = graph.component_pins['BT1-2']
    to_pos = graph.component_pins['GB1-1']

    # Collect notes across all fragments forming the circuit
    notes = collect_circuit_notes(graph, 'G4A', from_pos, to_pos)

    # Should collect "10AWG" from the vertical fragment
    assert notes == '10AWG', f"Expected '10AWG', got '{notes}'"


def test_collect_circuit_notes_deduplication():
    """
    Test that duplicate notes are deduplicated.

    Uses test_01 fixture but manually adds duplicate notes to test deduplication.
    """
    fixture_path = Path('tests/fixtures/test_01_fixture.kicad_sch')
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
    graph.wires = {wire.uuid: wire for wire in wires}

    # Find a wire with a circuit_id
    test_wire = next(w for w in wires if w.circuit_id)

    # Add duplicate notes
    test_wire.notes = ['AWG10', 'SHIELD', 'AWG10']

    # Collect notes
    notes = collect_circuit_notes(graph, test_wire.circuit_id,
                                   test_wire.start_point, test_wire.end_point)

    # Should deduplicate
    assert 'AWG10' in notes and 'SHIELD' in notes
    assert notes.count('AWG10') == 1, "AWG10 should appear only once"


def test_collect_circuit_notes_no_notes():
    """
    Test notes collection when wire has no notes.
    """
    fixture_path = Path('tests/fixtures/test_01_fixture.kicad_sch')
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
    graph.wires = {wire.uuid: wire for wire in wires}

    # Find a wire with a circuit_id
    test_wire = next(w for w in wires if w.circuit_id)

    # Ensure no notes
    test_wire.notes = []

    # Collect notes
    notes = collect_circuit_notes(graph, test_wire.circuit_id,
                                   test_wire.start_point, test_wire.end_point)

    # Should return empty string
    assert notes == '', f"Expected empty string, got '{notes}'"
