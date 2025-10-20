# ABOUTME: Connectivity graph for wire network tracing
# ABOUTME: NetworkNode and ConnectivityGraph classes for schematic connectivity

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetworkNode:
    """A point where connections meet in the schematic"""
    position: tuple[float, float]  # (x, y) in schematic
    node_type: str                  # "component_pin", "junction", "wire_endpoint"

    # If node_type == "component_pin":
    component_ref: Optional[str] = None  # "SW1", "J1", etc.
    pin_number: Optional[str] = None     # "1", "2", etc.

    # If node_type == "junction":
    junction_uuid: Optional[str] = None  # UUID of junction element

    # Connectivity:
    connected_wire_uuids: set[str] = field(default_factory=set)


class ConnectivityGraph:
    """Network connectivity for entire schematic"""

    def __init__(self):
        self.nodes: dict[tuple[float, float], NetworkNode] = {}
        self.wires: dict[str, object] = {}  # uuid -> WireSegment
        self.junctions: dict[str, tuple[float, float]] = {}  # uuid -> position
        self.component_pins: dict[str, tuple[float, float]] = {}  # "SW1-1" -> position

    def get_or_create_node(
        self,
        position: tuple[float, float],
        node_type: str = "wire_endpoint",
        component_ref: Optional[str] = None,
        pin_number: Optional[str] = None,
        junction_uuid: Optional[str] = None
    ) -> NetworkNode:
        """Get existing node at position or create new one"""
        # Round position to 0.01mm precision to handle float matching
        key = (round(position[0], 2), round(position[1], 2))

        if key not in self.nodes:
            self.nodes[key] = NetworkNode(
                position=position,
                node_type=node_type,
                component_ref=component_ref,
                pin_number=pin_number,
                junction_uuid=junction_uuid
            )

        return self.nodes[key]

    def add_wire(self, wire) -> None:
        """Add wire to graph, creating nodes at endpoints"""
        # Store wire
        self.wires[wire.uuid] = wire

        # Get or create nodes at endpoints
        start_node = self.get_or_create_node(wire.start_point)
        end_node = self.get_or_create_node(wire.end_point)

        # Connect wire to nodes
        start_node.connected_wire_uuids.add(wire.uuid)
        end_node.connected_wire_uuids.add(wire.uuid)

    def add_junction(self, junction_uuid: str, position: tuple[float, float]) -> None:
        """Add junction to graph, creating junction node"""
        # Store junction
        self.junctions[junction_uuid] = position

        # Create or upgrade node to junction type
        key = (round(position[0], 2), round(position[1], 2))

        if key in self.nodes:
            # Upgrade existing node to junction
            node = self.nodes[key]
            node.node_type = 'junction'
            node.junction_uuid = junction_uuid
        else:
            # Create new junction node
            self.nodes[key] = NetworkNode(
                position=position,
                node_type='junction',
                junction_uuid=junction_uuid
            )

    def add_component_pin(
        self,
        pin_key: str,
        component_ref: str,
        pin_number: str,
        position: tuple[float, float]
    ) -> None:
        """Add component pin to graph, creating pin node"""
        # Store pin
        self.component_pins[pin_key] = position

        # Create or upgrade node to component_pin type
        key = (round(position[0], 2), round(position[1], 2))

        if key in self.nodes:
            # Upgrade existing node to component_pin
            node = self.nodes[key]
            node.node_type = 'component_pin'
            node.component_ref = component_ref
            node.pin_number = pin_number
        else:
            # Create new component_pin node
            self.nodes[key] = NetworkNode(
                position=position,
                node_type='component_pin',
                component_ref=component_ref,
                pin_number=pin_number
            )

    def get_connected_nodes(self, wire_uuid: str) -> tuple[NetworkNode, NetworkNode]:
        """Get the two nodes connected by a wire"""
        wire = self.wires[wire_uuid]

        start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
        end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

        return (self.nodes[start_key], self.nodes[end_key])

    def get_node_at_position(
        self,
        position: tuple[float, float],
        tolerance: float = 0.01
    ) -> Optional[NetworkNode]:
        """Find node at position (within tolerance)"""
        key = (round(position[0], 2), round(position[1], 2))
        return self.nodes.get(key)
