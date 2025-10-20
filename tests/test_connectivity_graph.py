# ABOUTME: Tests for connectivity graph data structures and algorithms
# ABOUTME: Tests NetworkNode and ConnectivityGraph for wire tracing

import pytest
from kicad2wireBOM.connectivity_graph import NetworkNode, ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment


def test_network_node_creation():
    """Create a network node"""
    node = NetworkNode(
        position=(100.0, 100.0),
        node_type='component_pin',
        component_ref='SW1',
        pin_number='1',
        junction_uuid=None
    )

    assert node.position == (100.0, 100.0)
    assert node.node_type == 'component_pin'
    assert node.component_ref == 'SW1'
    assert node.pin_number == '1'
    assert len(node.connected_wire_uuids) == 0


def test_network_node_junction():
    """Create a junction node"""
    node = NetworkNode(
        position=(120.0, 80.0),
        node_type='junction',
        component_ref=None,
        pin_number=None,
        junction_uuid='abc-123'
    )

    assert node.node_type == 'junction'
    assert node.junction_uuid == 'abc-123'


def test_connectivity_graph_create():
    """Create empty connectivity graph"""
    graph = ConnectivityGraph()

    assert len(graph.nodes) == 0
    assert len(graph.wires) == 0
    assert len(graph.junctions) == 0
    assert len(graph.component_pins) == 0


def test_get_or_create_node():
    """Get or create node at position"""
    graph = ConnectivityGraph()

    # Create new node
    node1 = graph.get_or_create_node((100.0, 100.0), 'wire_endpoint')

    assert node1.position == (100.0, 100.0)
    assert node1.node_type == 'wire_endpoint'
    assert len(graph.nodes) == 1

    # Get existing node (within tolerance)
    node2 = graph.get_or_create_node((100.005, 100.005), 'wire_endpoint')

    # Should be same node due to rounding to 0.01mm
    assert node2 is node1
    assert len(graph.nodes) == 1


def test_get_or_create_node_different_positions():
    """Nodes at different positions are separate"""
    graph = ConnectivityGraph()

    node1 = graph.get_or_create_node((100.0, 100.0), 'wire_endpoint')
    node2 = graph.get_or_create_node((100.5, 100.0), 'wire_endpoint')

    assert node1 is not node2
    assert len(graph.nodes) == 2


def test_add_wire_creates_endpoint_nodes():
    """Adding wire creates nodes at endpoints"""
    graph = ConnectivityGraph()

    wire = WireSegment(
        uuid='wire-1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )

    graph.add_wire(wire)

    assert len(graph.nodes) == 2  # Two endpoint nodes
    assert len(graph.wires) == 1
    assert 'wire-1' in graph.wires

    # Check nodes were created at endpoints
    start_node = graph.get_node_at_position((100.0, 100.0))
    end_node = graph.get_node_at_position((120.0, 100.0))

    assert start_node is not None
    assert end_node is not None
    assert 'wire-1' in start_node.connected_wire_uuids
    assert 'wire-1' in end_node.connected_wire_uuids


def test_add_junction():
    """Add junction to graph"""
    graph = ConnectivityGraph()

    junction_uuid = 'junction-abc'
    position = (110.0, 90.0)

    graph.add_junction(junction_uuid, position)

    assert len(graph.junctions) == 1
    assert junction_uuid in graph.junctions

    # Check junction node created
    node = graph.get_node_at_position(position)
    assert node is not None
    assert node.node_type == 'junction'
    assert node.junction_uuid == junction_uuid


def test_add_component_pin():
    """Add component pin to graph"""
    graph = ConnectivityGraph()

    pin_key = 'SW1-1'
    position = (100.0, 105.0)

    graph.add_component_pin(pin_key, 'SW1', '1', position)

    assert len(graph.component_pins) == 1
    assert pin_key in graph.component_pins

    # Check pin node created
    node = graph.get_node_at_position(position)
    assert node is not None
    assert node.node_type == 'component_pin'
    assert node.component_ref == 'SW1'
    assert node.pin_number == '1'


def test_get_connected_nodes():
    """Get nodes connected by a wire"""
    graph = ConnectivityGraph()

    wire = WireSegment(
        uuid='wire-1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )

    graph.add_wire(wire)

    start, end = graph.get_connected_nodes('wire-1')

    assert start.position == (100.0, 100.0)
    assert end.position == (120.0, 100.0)


def test_wire_connects_to_existing_node():
    """Wire endpoint connects to existing component pin"""
    graph = ConnectivityGraph()

    # Add component pin first
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))

    # Add wire with endpoint at same position
    wire = WireSegment(
        uuid='wire-1',
        start_point=(100.0, 100.0),
        end_point=(120.0, 100.0)
    )
    graph.add_wire(wire)

    # Should only have 2 nodes (pin node + wire end node)
    assert len(graph.nodes) == 2

    # Pin node should have wire connected
    pin_node = graph.get_node_at_position((100.0, 100.0))
    assert pin_node.node_type == 'component_pin'
    assert 'wire-1' in pin_node.connected_wire_uuids


def test_multiple_wires_connect_at_junction():
    """Multiple wires connect at junction node"""
    graph = ConnectivityGraph()

    # Add junction
    graph.add_junction('j1', (110.0, 100.0))

    # Add three wires meeting at junction
    wire1 = WireSegment(uuid='w1', start_point=(100.0, 100.0), end_point=(110.0, 100.0))
    wire2 = WireSegment(uuid='w2', start_point=(110.0, 100.0), end_point=(120.0, 100.0))
    wire3 = WireSegment(uuid='w3', start_point=(110.0, 90.0), end_point=(110.0, 100.0))

    graph.add_wire(wire1)
    graph.add_wire(wire2)
    graph.add_wire(wire3)

    # Junction node should have all three wires
    junction_node = graph.get_node_at_position((110.0, 100.0))
    assert junction_node.node_type == 'junction'
    assert len(junction_node.connected_wire_uuids) == 3
    assert 'w1' in junction_node.connected_wire_uuids
    assert 'w2' in junction_node.connected_wire_uuids
    assert 'w3' in junction_node.connected_wire_uuids


def test_get_node_at_position_with_tolerance():
    """Get node at position with tolerance"""
    graph = ConnectivityGraph()

    graph.get_or_create_node((100.0, 100.0), 'wire_endpoint')

    # Within tolerance (0.01mm rounding)
    node = graph.get_node_at_position((100.005, 100.005))
    assert node is not None

    # Outside tolerance
    node = graph.get_node_at_position((100.5, 100.0))
    assert node is None


def test_trace_to_component_direct_pin():
    """Trace from wire endpoint directly to component pin"""
    graph = ConnectivityGraph()

    # Add component pin
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))

    # Get the node
    node = graph.get_node_at_position((100.0, 100.0))

    # Trace should return component pin info
    result = graph.trace_to_component(node)

    assert result is not None
    assert result['component_ref'] == 'SW1'
    assert result['pin_number'] == '1'


def test_trace_to_component_through_junction():
    """Trace through junction to find component pin"""
    graph = ConnectivityGraph()

    # Add component pin
    graph.add_component_pin('SW1-1', 'SW1', '1', (100.0, 100.0))

    # Add junction
    graph.add_junction('j1', (110.0, 100.0))

    # Add component pin on other side
    graph.add_component_pin('J1-1', 'J1', '1', (120.0, 100.0))

    # Add wires: SW1 -> junction -> J1
    wire1 = WireSegment(uuid='w1', start_point=(100.0, 100.0), end_point=(110.0, 100.0))
    wire2 = WireSegment(uuid='w2', start_point=(110.0, 100.0), end_point=(120.0, 100.0))

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    # Start from wire1's endpoint at junction
    junction_node = graph.get_node_at_position((110.0, 100.0))

    # Trace from junction through wire2 to find J1-1
    result = graph.trace_to_component(junction_node, exclude_wire_uuid='w1')

    assert result is not None
    assert result['component_ref'] == 'J1'
    assert result['pin_number'] == '1'


def test_trace_to_component_no_component_found():
    """Trace returns None if no component pin found"""
    graph = ConnectivityGraph()

    # Add junction with wire endpoint (no component)
    graph.add_junction('j1', (110.0, 100.0))

    wire = WireSegment(uuid='w1', start_point=(100.0, 100.0), end_point=(110.0, 100.0))
    graph.add_wire(wire)

    # Start from junction
    junction_node = graph.get_node_at_position((110.0, 100.0))

    # Trace should return None (only wire_endpoint on other side)
    result = graph.trace_to_component(junction_node, exclude_wire_uuid='w1')

    assert result is None


def test_trace_to_component_through_wire_endpoint():
    """Trace through wire_endpoint node to find component pin"""
    graph = ConnectivityGraph()

    # Add component pin
    graph.add_component_pin('J1-1', 'J1', '1', (100.0, 100.0))

    # Add component pin on other side
    graph.add_component_pin('SW1-3', 'SW1', '3', (130.0, 100.0))

    # Add two wires that connect at a wire_endpoint node (no junction symbol)
    # Wire 1: J1-1 to wire_endpoint at (115.0, 100.0)
    wire1 = WireSegment(uuid='w1', start_point=(100.0, 100.0), end_point=(115.0, 100.0))
    # Wire 2: wire_endpoint at (115.0, 100.0) to SW1-3
    wire2 = WireSegment(uuid='w2', start_point=(115.0, 100.0), end_point=(130.0, 100.0))

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    # Get the wire_endpoint node (middle point where wires connect)
    wire_endpoint_node = graph.get_node_at_position((115.0, 100.0))

    # Verify it's a wire_endpoint, not a junction
    assert wire_endpoint_node.node_type == 'wire_endpoint'
    assert len(wire_endpoint_node.connected_wire_uuids) == 2

    # Trace from wire_endpoint through wire2 to find SW1-3
    result = graph.trace_to_component(wire_endpoint_node, exclude_wire_uuid='w1')

    assert result is not None
    assert result['component_ref'] == 'SW1'
    assert result['pin_number'] == '3'
