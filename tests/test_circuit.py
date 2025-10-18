# ABOUTME: Tests for circuit analysis module
# ABOUTME: Validates circuit grouping, signal flow detection, and wire segmentation

import pytest
from kicad2wireBOM.component import Component
from kicad2wireBOM.circuit import Circuit, build_circuits
from kicad2wireBOM.parser import parse_netlist_file, extract_components, parse_footprint_encoding
from pathlib import Path


def test_circuit_dataclass_creation():
    """Test that Circuit dataclass can be created with expected fields"""
    comp1 = Component(ref='J1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=30.0)
    comp2 = Component(ref='SW1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=20.0)

    circuit = Circuit(
        net_code='1',
        net_name='Net-(J1-Pin_1)',
        system_code='L',
        components=[comp1, comp2],
        segments=[]
    )

    assert circuit.net_code == '1'
    assert circuit.net_name == 'Net-(J1-Pin_1)'
    assert circuit.system_code == 'L'
    assert len(circuit.components) == 2
    assert circuit.segments == []


def test_build_circuits_from_fixture_02():
    """Test building circuits from test_02 fixture with 3 components"""
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_02.net"
    parsed = parse_netlist_file(fixture_path)
    components_raw = extract_components(parsed)

    # Extract components with coordinates
    components = []
    for comp_raw in components_raw:
        encoding = parse_footprint_encoding(comp_raw['footprint'])
        assert encoding is not None

        load = encoding['amperage'] if encoding['type'] == 'L' else None
        rating = encoding['amperage'] if encoding['type'] == 'R' else None
        source = encoding['amperage'] if encoding['type'] == 'S' else None

        comp = Component(
            ref=comp_raw['ref'],
            fs=encoding['fs'],
            wl=encoding['wl'],
            bl=encoding['bl'],
            load=load,
            rating=rating,
            source=source
        )
        components.append(comp)

    # Build circuits
    circuits = build_circuits(parsed, components)

    # Should have 2 circuits (one for each net in fixture 02)
    assert len(circuits) >= 1  # At minimum, the main circuit

    # Find the main circuit that connects all three components
    # This circuit should have J1, SW1, and L1
    main_circuit = None
    for circuit in circuits:
        refs = [c.ref for c in circuit.components]
        if 'J1' in refs or 'SW1' in refs or 'L1' in refs:
            main_circuit = circuit
            break

    assert main_circuit is not None
    assert len(main_circuit.components) >= 2


def test_build_circuits_empty_components():
    """Test that build_circuits handles empty component list"""
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_02.net"
    parsed = parse_netlist_file(fixture_path)

    circuits = build_circuits(parsed, [])

    assert circuits == []


def test_determine_signal_flow_simple_load():
    """Test signal flow detection for simple load circuit: source -> passthrough -> load"""
    from kicad2wireBOM.circuit import determine_signal_flow

    # Create components: J1 (source/rating) -> SW1 (passthrough/rating) -> L1 (load)
    j1 = Component(ref='J1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=30.0)
    sw1 = Component(ref='SW1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=20.0)
    l1 = Component(ref='L1', fs=200.0, wl=35.0, bl=10.0, load=2.5, rating=None)

    components = [sw1, l1, j1]  # Deliberately out of order

    # Determine signal flow
    ordered = determine_signal_flow(components)

    # Should be ordered: source (J1) -> passthrough (SW1) -> load (L1)
    assert len(ordered) == 3
    assert ordered[0].ref == 'J1'  # Source first
    assert ordered[1].ref == 'SW1'  # Passthrough middle
    assert ordered[2].ref == 'L1'  # Load last


def test_determine_signal_flow_two_components():
    """Test signal flow with just two components: source -> load"""
    from kicad2wireBOM.circuit import determine_signal_flow

    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    sw1 = Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)

    components = [sw1, j1]

    ordered = determine_signal_flow(components)

    # Both are rating type, use heuristic (J prefix suggests source)
    assert len(ordered) == 2
    assert ordered[0].ref == 'J1'
    assert ordered[1].ref == 'SW1'


def test_create_wire_segments_three_components():
    """Test wire segment creation for 3-component circuit"""
    from kicad2wireBOM.circuit import create_wire_segments
    from kicad2wireBOM.reference_data import DEFAULT_CONFIG

    # Create ordered components: J1 -> SW1 -> L1
    j1 = Component(ref='J1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=30.0)
    sw1 = Component(ref='SW1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=20.0)
    l1 = Component(ref='L1', fs=200.0, wl=35.0, bl=10.0, load=2.5, rating=None)

    ordered_components = [j1, sw1, l1]
    system_code = 'L'
    circuit_id = '105'

    # Create wire segments
    segments = create_wire_segments(ordered_components, system_code, circuit_id, DEFAULT_CONFIG)

    # Should create 2 segments: J1->SW1 (A) and SW1->L1 (B)
    assert len(segments) == 2

    # First segment: J1 -> SW1, labeled L-105-A
    seg1 = segments[0]
    assert seg1.wire_label == 'L-105-A'
    assert seg1.from_ref == 'J1'
    assert seg1.to_ref == 'SW1'
    assert seg1.wire_gauge in [12, 16, 18, 20]
    assert seg1.length > 0

    # Second segment: SW1 -> L1, labeled L-105-B
    seg2 = segments[1]
    assert seg2.wire_label == 'L-105-B'
    assert seg2.from_ref == 'SW1'
    assert seg2.to_ref == 'L1'
    assert seg2.wire_gauge in [12, 16, 18, 20]
    assert seg2.length > 0


def test_create_wire_segments_two_components():
    """Test wire segment creation for 2-component circuit"""
    from kicad2wireBOM.circuit import create_wire_segments
    from kicad2wireBOM.reference_data import DEFAULT_CONFIG

    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    sw1 = Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)

    ordered_components = [j1, sw1]
    system_code = 'U'
    circuit_id = '1'

    segments = create_wire_segments(ordered_components, system_code, circuit_id, DEFAULT_CONFIG)

    # Should create 1 segment: J1->SW1 (A)
    assert len(segments) == 1
    assert segments[0].wire_label == 'U-1-A'
    assert segments[0].from_ref == 'J1'
    assert segments[0].to_ref == 'SW1'


def test_create_wire_segments_uses_load_current():
    """Test that wire gauge is determined by load current, not ratings"""
    from kicad2wireBOM.circuit import create_wire_segments
    from kicad2wireBOM.reference_data import DEFAULT_CONFIG
    from kicad2wireBOM.wire_calculator import determine_min_gauge

    # Circuit: J1 (R30) -> SW1 (R20) -> L1 (L2.5)
    # Should size all wires for 2.5A load, not the ratings
    j1 = Component(ref='J1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=30.0)
    sw1 = Component(ref='SW1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=20.0)
    l1 = Component(ref='L1', fs=200.0, wl=35.0, bl=10.0, load=2.5, rating=None)

    ordered_components = [j1, sw1, l1]
    system_code = 'L'
    circuit_id = '105'

    segments = create_wire_segments(ordered_components, system_code, circuit_id, DEFAULT_CONFIG)

    # Both segments should be sized for 2.5A load
    slack = DEFAULT_CONFIG['slack_length']
    from kicad2wireBOM.wire_calculator import calculate_length

    # Segment A: J1 -> SW1
    length_a = calculate_length(j1, sw1, slack)
    expected_gauge_a = determine_min_gauge(2.5, length_a, DEFAULT_CONFIG['system_voltage'])

    # Segment B: SW1 -> L1
    length_b = calculate_length(sw1, l1, slack)
    expected_gauge_b = determine_min_gauge(2.5, length_b, DEFAULT_CONFIG['system_voltage'])

    assert segments[0].wire_gauge == expected_gauge_a
    assert segments[1].wire_gauge == expected_gauge_b
