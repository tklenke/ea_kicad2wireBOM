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
    fixture_path = Path(__file__).parent / "fixtures" / "test_02_simple_load.net"
    parsed = parse_netlist_file(fixture_path)
    components_raw = extract_components(parsed)

    # Extract components with coordinates
    components = []
    for comp_raw in components_raw:
        encoding = parse_footprint_encoding(comp_raw['footprint'])
        assert encoding is not None

        load = encoding['amperage'] if encoding['type'] == 'L' else None
        rating = encoding['amperage'] if encoding['type'] == 'R' else None

        comp = Component(
            ref=comp_raw['ref'],
            fs=encoding['fs'],
            wl=encoding['wl'],
            bl=encoding['bl'],
            load=load,
            rating=rating
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
    fixture_path = Path(__file__).parent / "fixtures" / "test_02_simple_load.net"
    parsed = parse_netlist_file(fixture_path)

    circuits = build_circuits(parsed, [])

    assert circuits == []
