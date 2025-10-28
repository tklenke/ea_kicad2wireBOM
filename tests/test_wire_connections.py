# ABOUTME: Tests for wire connection identification
# ABOUTME: Tests identifying what each wire endpoint connects to

import pytest
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment
from kicad2wireBOM.wire_connections import identify_wire_connections, is_power_symbol


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


def test_is_power_symbol_gnd_variants():
    """is_power_symbol() identifies GND and GNDn patterns"""
    # Standalone GND
    assert is_power_symbol('GND') == True

    # GNDn where n is 1, 2, 3, 4, 5, 6, 12, or 24
    assert is_power_symbol('GND1') == True
    assert is_power_symbol('GND2') == True
    assert is_power_symbol('GND3') == True
    assert is_power_symbol('GND4') == True
    assert is_power_symbol('GND5') == True
    assert is_power_symbol('GND6') == True
    assert is_power_symbol('GND12') == True
    assert is_power_symbol('GND24') == True

    # GNDREF
    assert is_power_symbol('GNDREF') == True


def test_is_power_symbol_positive_voltages():
    """is_power_symbol() identifies +nV and +nVA patterns"""
    # +nV patterns
    assert is_power_symbol('+1V') == True
    assert is_power_symbol('+2V') == True
    assert is_power_symbol('+3V') == True
    assert is_power_symbol('+5V') == True
    assert is_power_symbol('+12V') == True
    assert is_power_symbol('+24V') == True

    # +nVA patterns (analog)
    assert is_power_symbol('+1VA') == True
    assert is_power_symbol('+5VA') == True
    assert is_power_symbol('+12VA') == True


def test_is_power_symbol_negative_voltages():
    """is_power_symbol() identifies -nV and -nVA patterns"""
    # -nV patterns
    assert is_power_symbol('-5V') == True
    assert is_power_symbol('-12V') == True
    assert is_power_symbol('-24V') == True

    # -nVA patterns (analog)
    assert is_power_symbol('-5VA') == True
    assert is_power_symbol('-12VA') == True


def test_is_power_symbol_vdc_vac():
    """is_power_symbol() identifies VDC and VAC"""
    assert is_power_symbol('VDC') == True
    assert is_power_symbol('VAC') == True


def test_is_power_symbol_false_positives():
    """is_power_symbol() does NOT match regular components"""
    # Regular components that start with GND but aren't power symbols
    assert is_power_symbol('GNDSWITCH') == False
    assert is_power_symbol('GND-RELAY') == False
    assert is_power_symbol('GNDSENSOR') == False
    assert is_power_symbol('GND7') == False  # 7 is not a valid voltage
    assert is_power_symbol('GND99') == False

    # Voltage patterns that don't match our specific list
    assert is_power_symbol('+3V3') == False  # Not in our voltage list
    assert is_power_symbol('+28V') == False  # 28 is not in our list
    assert is_power_symbol('+VCC') == False  # Not a pattern we recognize

    # Regular components
    assert is_power_symbol('SW1') == False
    assert is_power_symbol('J1') == False
    assert is_power_symbol('BT1') == False
    assert is_power_symbol('R1') == False


def test_is_power_symbol_none_and_empty():
    """is_power_symbol() handles None and empty strings"""
    assert is_power_symbol(None) == False
    assert is_power_symbol('') == False
