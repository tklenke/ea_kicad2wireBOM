# ABOUTME: Wire connection identification
# ABOUTME: Identifies what each wire endpoint connects to (pins, junctions, etc)

from typing import Optional
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment


def identify_wire_connections(
    wire: WireSegment,
    graph: ConnectivityGraph
) -> tuple[Optional[dict[str, str]], Optional[dict[str, str]]]:
    """
    Identify what components this wire connects.

    Traces through junctions to find component pins at both ends.

    Args:
        wire: Wire segment to identify connections for
        graph: Connectivity graph with all nodes

    Returns:
        Tuple of (from_pin, to_pin) where each is:
        - dict with 'component_ref' and 'pin_number' (e.g., {'component_ref': 'SW1', 'pin_number': '3'})
        - None if endpoint has no component connection
    """
    # Get nodes at wire endpoints
    start_node, end_node = graph.get_connected_nodes(wire.uuid)

    # Trace through junctions to find component pins
    start_conn = graph.trace_to_component(start_node, exclude_wire_uuid=wire.uuid)
    end_conn = graph.trace_to_component(end_node, exclude_wire_uuid=wire.uuid)

    return (start_conn, end_conn)
