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
            node_key = (round(node.position[0], 2), round(node.position[1], 2))

            # FIRST PASS: Check for direct component_pin connections
            # This ensures we prioritize nearby components (like connectors)
            # over distant components reachable through wire_endpoints
            for wire_uuid in node.connected_wire_uuids:
                if wire_uuid == exclude_wire_uuid:
                    continue

                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                # Get the node at the OTHER end of this wire
                if start_key == node_key:
                    other_node = self.nodes[end_key]
                elif end_key == node_key:
                    other_node = self.nodes[start_key]
                else:
                    continue

                # If the other end is a component_pin, return it immediately
                if other_node.node_type == 'component_pin':
                    return {
                        'component_ref': other_node.component_ref,
                        'pin_number': other_node.pin_number
                    }

            # SECOND PASS: No direct component_pin found, recurse through junctions/wire_endpoints
            for wire_uuid in node.connected_wire_uuids:
                if wire_uuid == exclude_wire_uuid:
                    continue

                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                # Get the node at the OTHER end of this wire
                if start_key == node_key:
                    other_node = self.nodes[end_key]
                elif end_key == node_key:
                    other_node = self.nodes[start_key]
                else:
                    continue

                # Recurse through junctions and wire_endpoints
                if other_node.node_type in ('junction', 'wire_endpoint'):
                    result = self.trace_to_component(other_node, exclude_wire_uuid=wire_uuid)
                    if result is not None:
                        return result

        # If this node is a wire_endpoint, trace through connected wires
        if node.node_type == 'wire_endpoint':
            node_key = (round(node.position[0], 2), round(node.position[1], 2))

            # FIRST PASS: Check for direct component_pin connections
            # This ensures we prioritize nearby components (like connectors)
            # over distant components reachable through other wire_endpoints
            for wire_uuid in node.connected_wire_uuids:
                if wire_uuid == exclude_wire_uuid:
                    continue

                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                # Get the node at the OTHER end of this wire
                if start_key == node_key:
                    other_node = self.nodes[end_key]
                elif end_key == node_key:
                    other_node = self.nodes[start_key]
                else:
                    continue

                # If the other end is a component_pin, return it immediately
                if other_node.node_type == 'component_pin':
                    return {
                        'component_ref': other_node.component_ref,
                        'pin_number': other_node.pin_number
                    }

            # SECOND PASS: No direct component_pin found, recurse through junctions/wire_endpoints
            for wire_uuid in node.connected_wire_uuids:
                if wire_uuid == exclude_wire_uuid:
                    continue

                wire = self.wires[wire_uuid]
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                # Get the node at the OTHER end of this wire
                if start_key == node_key:
                    other_node = self.nodes[end_key]
                elif end_key == node_key:
                    other_node = self.nodes[start_key]
                else:
                    continue

                # Recurse through junctions and wire_endpoints
                if other_node.node_type in ('junction', 'wire_endpoint'):
                    result = self.trace_to_component(other_node, exclude_wire_uuid=wire_uuid)
                    if result is not None:
                        return result

        # No component found
        return None

    def detect_multipoint_connections(self) -> list[list[dict[str, str]]]:
        """
        Detect all multipoint connections (N >= 3 component pins connected).

        Uses graph traversal to find all connected component pin groups.
        Returns groups where N >= 3.

        Returns:
            List of component pin groups, where each group is a list of dicts
            with 'component_ref' and 'pin_number' keys.
        """
        # Track which pins we've already visited
        visited_pins = set()
        multipoint_groups = []

        # Iterate through all component pins
        for pin_key, position in self.component_pins.items():
            if pin_key in visited_pins:
                continue

            # Start BFS/DFS from this pin to find all connected pins
            connected_pins = self._find_connected_pins(pin_key, position)

            # Mark all pins in this group as visited
            for pin in connected_pins:
                pin_key_str = f"{pin['component_ref']}-{pin['pin_number']}"
                visited_pins.add(pin_key_str)

            # If N >= 3, this is a multipoint connection
            if len(connected_pins) >= 3:
                multipoint_groups.append(connected_pins)

        return multipoint_groups

    def _find_connected_pins(
        self,
        start_pin_key: str,
        start_position: tuple[float, float]
    ) -> list[dict[str, str]]:
        """
        Find all component pins connected to the starting pin using BFS.

        Args:
            start_pin_key: Component pin key like "SW1-1"
            start_position: Position of starting pin

        Returns:
            List of connected component pins (including the starting pin)
        """
        # BFS queue: tuples of (position, visited_nodes)
        queue = [(start_position, set())]
        visited_positions = {(round(start_position[0], 2), round(start_position[1], 2))}
        connected_pins = []

        while queue:
            current_pos, visited_nodes = queue.pop(0)
            current_key = (round(current_pos[0], 2), round(current_pos[1], 2))

            # Get node at current position
            node = self.nodes.get(current_key)
            if node is None:
                continue

            # If this is a component pin, add it to results
            if node.node_type == 'component_pin':
                connected_pins.append({
                    'component_ref': node.component_ref,
                    'pin_number': node.pin_number
                })

            # Explore all wires connected to this node
            for wire_uuid in node.connected_wire_uuids:
                wire = self.wires[wire_uuid]

                # Get both endpoints of the wire
                start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                # Visit the OTHER end of the wire
                if current_key == start_key:
                    other_key = end_key
                    other_pos = wire.end_point
                elif current_key == end_key:
                    other_key = start_key
                    other_pos = wire.start_point
                else:
                    continue

                # Add to queue if not visited
                if other_key not in visited_positions:
                    visited_positions.add(other_key)
                    queue.append((other_pos, visited_nodes | {current_key}))

        return connected_pins

    def count_labels_in_group(self, group: list[dict[str, str]]) -> int:
        """
        Count circuit ID labels within a multipoint connection group.

        Traverses all wires within the connected group and counts unique
        circuit ID labels found.

        Args:
            group: List of component pins (dicts with 'component_ref' and 'pin_number')

        Returns:
            Count of unique circuit ID labels in the group
        """
        # Get all pin positions in the group
        group_pin_positions = set()
        for pin in group:
            pin_key = f"{pin['component_ref']}-{pin['pin_number']}"
            if pin_key in self.component_pins:
                pos = self.component_pins[pin_key]
                group_pin_positions.add((round(pos[0], 2), round(pos[1], 2)))

        # Track visited nodes and wires
        visited_nodes = set()
        visited_wires = set()
        unique_labels = set()

        # BFS from each pin position to explore entire connected component
        for start_pos in group_pin_positions:
            if start_pos in visited_nodes:
                continue

            queue = [start_pos]
            visited_nodes.add(start_pos)

            while queue:
                current_pos = queue.pop(0)

                # Get node at current position
                node = self.nodes.get(current_pos)
                if node is None:
                    continue

                # Check all wires connected to this node
                for wire_uuid in node.connected_wire_uuids:
                    if wire_uuid in visited_wires:
                        continue
                    visited_wires.add(wire_uuid)

                    wire = self.wires[wire_uuid]

                    # If wire has a circuit_id label, add it to our set
                    if hasattr(wire, 'circuit_id') and wire.circuit_id:
                        unique_labels.add(wire.circuit_id)

                    # Explore the other end of the wire
                    start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                    end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                    # Add other endpoint to queue if not visited
                    if current_pos == start_key:
                        other_key = end_key
                    elif current_pos == end_key:
                        other_key = start_key
                    else:
                        continue

                    # Add to queue if not visited
                    # Keep exploring until we've covered the whole connected component
                    if other_key not in visited_nodes:
                        # Check if this leads to a pin in our group (keeps us in the multipoint connection)
                        other_node = self.nodes.get(other_key)
                        if other_node and other_node.node_type == 'component_pin':
                            # Only continue if this pin is in our group
                            if other_key in group_pin_positions:
                                visited_nodes.add(other_key)
                                queue.append(other_key)
                        else:
                            # It's a junction or wire_endpoint, continue exploring
                            visited_nodes.add(other_key)
                            queue.append(other_key)

        return len(unique_labels)

    def identify_common_pin(self, group: list[dict[str, str]]) -> dict[str, str] | None:
        """
        Identify the common (unlabeled) pin in a multipoint connection using
        segment-level analysis.

        A pin is "reached by a labeled segment" if the SEGMENT (chain of fragments)
        from that pin to a junction contains at least one labeled fragment.

        Algorithm:
        - Fragment: A single wire element (what KiCad calls a wire)
        - Connection: A point where exactly 2 fragments meet (trace through these)
        - Junction: A point where 3+ fragments meet (stop at these)
        - Segment: Chain of fragments from a pin to a junction

        For each pin:
        1. Trace the segment from pin toward junction:
           - Follow fragments through connections (2-fragment points)
           - Stop at junctions (3+ fragment points) or other group pins
        2. Check if ANY fragment in segment has a label
        3. Pin whose segment has NO labels is the common pin

        Args:
            group: List of component pins (dicts with 'component_ref' and 'pin_number')

        Returns:
            The common pin dict, or None if cannot identify unambiguously
        """
        # Get all pin positions in the group
        group_pin_positions = {}
        for pin in group:
            pin_key = f"{pin['component_ref']}-{pin['pin_number']}"
            if pin_key in self.component_pins:
                pos = self.component_pins[pin_key]
                group_pin_positions[pin_key] = (round(pos[0], 2), round(pos[1], 2))

        # Build fragment count map: position -> number of fragments at that position
        fragment_count_at_position = {}
        for wire_uuid in self.wires:
            wire = self.wires[wire_uuid]
            start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
            end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

            fragment_count_at_position[start_key] = fragment_count_at_position.get(start_key, 0) + 1
            fragment_count_at_position[end_key] = fragment_count_at_position.get(end_key, 0) + 1

        # For each pin, trace its segment and check for labels
        pins_with_unlabeled_segments = []

        for pin in group:
            pin_key = f"{pin['component_ref']}-{pin['pin_number']}"
            if pin_key not in group_pin_positions:
                continue

            pin_pos_key = group_pin_positions[pin_key]

            # Trace segment from this pin
            # Stop at: junctions (3+ fragments), other group pins, or dead ends
            visited_positions = set()
            visited_wires = set()
            queue = [pin_pos_key]
            visited_positions.add(pin_pos_key)
            segment_has_label = False

            while queue:
                current_pos = queue.pop(0)

                # Check if this is a junction (3+ fragments) - stop here
                if current_pos != pin_pos_key:
                    fragment_count = fragment_count_at_position.get(current_pos, 0)
                    if fragment_count >= 3:
                        # Junction - stop tracing
                        continue

                # Get node at current position
                node = self.nodes.get(current_pos)
                if not node:
                    continue

                # Explore all connected wires in this segment
                for wire_uuid in node.connected_wire_uuids:
                    if wire_uuid in visited_wires:
                        continue
                    visited_wires.add(wire_uuid)

                    wire = self.wires[wire_uuid]

                    # Check if this wire has a label
                    if hasattr(wire, 'circuit_id') and wire.circuit_id:
                        segment_has_label = True

                    # Find the other end of the wire
                    start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
                    end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

                    if current_pos == start_key:
                        other_key = end_key
                    elif current_pos == end_key:
                        other_key = start_key
                    else:
                        continue

                    # Check if other end is another group pin - if so, stop
                    if other_key in group_pin_positions.values() and other_key != pin_pos_key:
                        # Reached another pin in the group - stop
                        continue

                    # Continue tracing through connections (but stop at junctions)
                    if other_key not in visited_positions:
                        visited_positions.add(other_key)
                        queue.append(other_key)

            # Record whether this pin's segment has a label
            if not segment_has_label:
                pins_with_unlabeled_segments.append(pin)

        # Return the one pin with an unlabeled segment
        if len(pins_with_unlabeled_segments) == 1:
            return pins_with_unlabeled_segments[0]
        else:
            # Multiple or zero candidates - ambiguous
            return None
