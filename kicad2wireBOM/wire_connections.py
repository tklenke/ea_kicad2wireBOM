# ABOUTME: Wire connection identification
# ABOUTME: Identifies what each wire endpoint connects to (pins, junctions, etc)

from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.schematic import WireSegment


def identify_wire_connections(wire: WireSegment, graph: ConnectivityGraph) -> tuple[str, str]:
    """
    Identify what each wire endpoint connects to.

    Args:
        wire: Wire segment to identify connections for
        graph: Connectivity graph with all nodes

    Returns:
        Tuple of (start_connection, end_connection) where each is:
        - "REF-PIN" for component pins (e.g., "SW1-1")
        - "JUNCTION-uuid" for junctions (e.g., "JUNCTION-abc123")
        - "UNKNOWN" for unconnected endpoints
    """
    # Get nodes at wire endpoints
    start_node, end_node = graph.get_connected_nodes(wire.uuid)

    # Convert nodes to connection strings
    start_conn = _node_to_connection_string(start_node)
    end_conn = _node_to_connection_string(end_node)

    return (start_conn, end_conn)


def _node_to_connection_string(node) -> str:
    """
    Convert network node to connection reference string.

    Args:
        node: NetworkNode object

    Returns:
        Connection string:
        - "REF-PIN" for component_pin nodes
        - "JUNCTION-uuid" for junction nodes
        - "UNKNOWN" for wire_endpoint nodes or None
    """
    if node is None:
        return "UNKNOWN"

    if node.node_type == 'component_pin':
        # Format: "SW1-1"
        return f"{node.component_ref}-{node.pin_number}"
    elif node.node_type == 'junction':
        # Format: "JUNCTION-uuid"
        return f"JUNCTION-{node.junction_uuid}"
    else:
        # wire_endpoint or unknown
        return "UNKNOWN"
