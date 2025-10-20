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

    def trace_to_component(
        self,
        node: Optional[NetworkNode],
        exclude_wire_uuid: Optional[str] = None
    ) -> Optional[dict[str, str]]:
        """
        Trace from a node through junctions to find a component pin.

        Args:
            node: Starting node to trace from
            exclude_wire_uuid: Wire UUID to exclude from tracing (the wire we came from)

        Returns:
            Dictionary with 'component_ref' and 'pin_number' if component found, else None
        """
        if node is None:
            return None

        # If this node is a component pin, return it
        if node.node_type == 'component_pin':
            return {
                'component_ref': node.component_ref,
                'pin_number': node.pin_number
            }

        # If this node is a junction, trace through connected wires
        if node.node_type == 'junction':
            # Get all wires connected to this junction
            for wire_uuid in node.connected_wire_uuids:
                # Skip the wire we came from
                if wire_uuid == exclude_wire_uuid:
                    continue

                # Get the wire's endpoints
                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                start_node = self.nodes[start_key]
                end_node = self.nodes[end_key]

                # Find which end is NOT this junction node
                node_key = (round(node.position[0], 2), round(node.position[1], 2))

                if start_key == node_key:
                    # Trace to the other end
                    result = self.trace_to_component(end_node, exclude_wire_uuid=wire_uuid)
                elif end_key == node_key:
                    # Trace to the other end
                    result = self.trace_to_component(start_node, exclude_wire_uuid=wire_uuid)
                else:
                    continue

                # If we found a component, return it
                if result is not None:
                    return result

        # If this node is a wire_endpoint, trace through connected wires
        if node.node_type == 'wire_endpoint':
            # Get all wires connected to this wire_endpoint
            for wire_uuid in node.connected_wire_uuids:
                # Skip the wire we came from
                if wire_uuid == exclude_wire_uuid:
                    continue

                # Get the wire's endpoints
                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                start_node = self.nodes[start_key]
                end_node = self.nodes[end_key]

                # Find which end is NOT this wire_endpoint node
                node_key = (round(node.position[0], 2), round(node.position[1], 2))

                if start_key == node_key:
                    # Trace to the other end
                    result = self.trace_to_component(end_node, exclude_wire_uuid=wire_uuid)
                elif end_key == node_key:
                    # Trace to the other end
                    result = self.trace_to_component(start_node, exclude_wire_uuid=wire_uuid)
                else:
                    continue

                # If we found a component, return it
                if result is not None:
                    return result

        # No component found
        return None
