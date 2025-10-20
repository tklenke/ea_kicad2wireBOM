# ABOUTME: Tests for wire connection identification
# ABOUTME: Tests identifying what each wire endpoint connects to

import pytest
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment
from kicad2wireBOM.wire_connections import identify_wire_connections


def test_identify_connection_to_component_pin():
    """Wire connects to component pin (direct connection)"""
    graph = ConnectivityGraph()

    # Add component pin
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))

    # Add wire with endpoint at pin
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn is not None
    assert start_conn['component_ref'] == 'SW1'
    assert start_conn['pin_number'] == '1'
    assert end_conn is None


def test_identify_connection_through_junction():
    """Wire connects to component pin through junction (junction transparency)"""
    graph = ConnectivityGraph()

    # Add component pins
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))
    graph.add_component_pin('J1-1', 'J1', '1', (130.0, 100.0))

    # Add junction
    graph.add_junction('j-uuid-123', (110.0, 100.0))

    # Add wires: SW1 -> junction, junction -> J1
    wire1 = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(110.0, 100.0)
    )
    wire2 = WireSegment(
        uuid='w2',
        start_point=(110.0, 100.0),
        end_point=(130.0, 100.0)
    )
    graph.add_wire(wire1)
    graph.add_wire(wire2)

    # Identify connections for wire1 - should trace through junction to find J1
    start_conn, end_conn = identify_wire_connections(wire1, graph)

    assert start_conn is not None
    assert start_conn['component_ref'] == 'SW1'
    assert start_conn['pin_number'] == '1'
    assert end_conn is not None
    assert end_conn['component_ref'] == 'J1'
    assert end_conn['pin_number'] == '1'


def test_identify_both_endpoints():
    """Wire connects pin to pin (direct connection)"""
    graph = ConnectivityGraph()

    # Add two pins
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))
    graph.add_component_pin('SW2-2', 'SW2', '2', (120.0, 100.0))

    # Add wire between pins
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn is not None
    assert start_conn['component_ref'] == 'SW1'
    assert start_conn['pin_number'] == '1'
    assert end_conn is not None
    assert end_conn['component_ref'] == 'SW2'
    assert end_conn['pin_number'] == '2'


def test_identify_unknown_endpoint():
    """Wire endpoint not connected to anything"""
    graph = ConnectivityGraph()

    # Add wire with no connections
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn is None
    assert end_conn is None


def test_identify_pin_to_junction_with_no_component():
    """Wire connects component pin to junction with no component on other side"""
    graph = ConnectivityGraph()

    # Add pin and junction
    graph.add_component_pin('SW1-3', 'SW1', '3', (100.0, 100.0))
    graph.add_junction('j-abc', (120.0, 100.0))

    # Add wire between them (no other wires at junction)
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn is not None
    assert start_conn['component_ref'] == 'SW1'
    assert start_conn['pin_number'] == '3'
    # Junction with no component on other side returns None
    assert end_conn is None
