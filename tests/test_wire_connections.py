# ABOUTME: Tests for wire connection identification
# ABOUTME: Tests identifying what each wire endpoint connects to

import pytest
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment
from kicad2wireBOM.wire_connections import identify_wire_connections


def test_identify_connection_to_component_pin():
    """Wire connects to component pin"""
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

    assert start_conn == 'SW1-1'
    assert end_conn == 'UNKNOWN'


def test_identify_connection_to_junction():
    """Wire connects to junction"""
    graph = ConnectivityGraph()

    # Add junction
    graph.add_junction('j-uuid-123', (110.0, 100.0))

    # Add wire with endpoint at junction
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(110.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn == 'UNKNOWN'
    assert end_conn == 'JUNCTION-j-uuid-123'


def test_identify_both_endpoints():
    """Wire connects pin to pin"""
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

    assert start_conn == 'SW1-1'
    assert end_conn == 'SW2-2'


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

    assert start_conn == 'UNKNOWN'
    assert end_conn == 'UNKNOWN'


def test_identify_pin_to_junction():
    """Wire connects component pin to junction"""
    graph = ConnectivityGraph()

    # Add pin and junction
    graph.add_component_pin('SW1-3', 'SW1', '3', (100.0, 100.0))
    graph.add_junction('j-abc', (120.0, 100.0))

    # Add wire between them
    wire = WireSegment(
        uuid='w1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Identify connections
    start_conn, end_conn = identify_wire_connections(wire, graph)

    assert start_conn == 'SW1-3'
    assert end_conn == 'JUNCTION-j-abc'
