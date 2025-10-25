# ABOUTME: Validation module for schematic data quality checks
# ABOUTME: Detects missing labels, duplicates, and malformed circuit IDs

from dataclasses import dataclass
from typing import List, Optional, Dict, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph


@dataclass
class ValidationError:
    """Validation error or warning"""
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None
    wire_uuid: Optional[str] = None
    position: Optional[tuple[float, float]] = None


@dataclass
class ValidationResult:
    """Result of validation checks"""
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def should_abort(self, strict_mode: bool) -> bool:
        return strict_mode and self.has_errors()


class SchematicValidator:
    """Validates schematic data for BOM generation"""

    CIRCUIT_ID_PATTERN = re.compile(r'^[A-Z]-?\d+-?[A-Z]$')

    def __init__(self, strict_mode: bool = True, connectivity_graph: Optional['ConnectivityGraph'] = None):
        self.strict_mode = strict_mode
        self.connectivity_graph = connectivity_graph
        self.result = ValidationResult(errors=[], warnings=[])

    def validate_all(self, wires, labels, components) -> ValidationResult:
        """Run all validation checks"""
        self._check_no_labels(wires, labels)
        self._check_wire_labels(wires)
        self._check_duplicate_circuit_ids(wires)
        self._check_orphaned_labels(labels, wires)
        return self.result

    def _format_wire_connections(self, wire) -> str:
        """
        Format wire endpoint connections for error messages.

        Returns a string like "BT1 (pin 1) → FH1 (pin 2)" showing
        what components the wire connects to.

        Args:
            wire: WireSegment to trace connections for

        Returns:
            Formatted string describing wire connections
        """
        if not self.connectivity_graph:
            return "unknown → unknown"

        # Get nodes at wire endpoints
        start_node = self.connectivity_graph.get_node_at_position(wire.start_point)
        end_node = self.connectivity_graph.get_node_at_position(wire.end_point)

        # Trace to components at each endpoint
        start_component = self.connectivity_graph.trace_to_component(start_node, exclude_wire_uuid=wire.uuid)
        end_component = self.connectivity_graph.trace_to_component(end_node, exclude_wire_uuid=wire.uuid)

        # Format start endpoint
        if start_component:
            start_str = f"{start_component['component_ref']} (pin {start_component['pin_number']})"
        elif start_node and start_node.node_type == 'junction':
            start_str = "junction"
        else:
            start_str = "unknown"

        # Format end endpoint
        if end_component:
            end_str = f"{end_component['component_ref']} (pin {end_component['pin_number']})"
        elif end_node and end_node.node_type == 'junction':
            end_str = "junction"
        else:
            end_str = "unknown"

        return f"{start_str} → {end_str}"

    def _check_no_labels(self, wires, labels):
        """Check for schematic with no circuit ID labels"""
        circuit_labels = [l for l in labels if self.CIRCUIT_ID_PATTERN.match(l.text)]
        if len(circuit_labels) == 0:
            self._add_error(
                "No circuit ID labels found in schematic",
                suggestion="Add wire labels matching pattern [SYSTEM][CIRCUIT][SEGMENT] (e.g., L1A, P12B)"
            )

    def _check_wire_labels(self, wires):
        """Check each wire has valid circuit ID"""
        for wire in wires:
            # Only check wires that have attempted labels (in wire.labels list)
            # Skip wires with no labels, or wires with only notes
            if not wire.labels:
                continue

            circuit_ids = [l for l in wire.labels if self.CIRCUIT_ID_PATTERN.match(l)]

            if len(circuit_ids) == 0:
                # Wire has labels but no valid circuit ID
                # This is an error - labels were attempted but none are valid circuit IDs
                self._add_error(
                    f"Wire segment {wire.uuid} has no valid circuit ID label",
                    suggestion="Add circuit ID label to wire",
                    wire_uuid=wire.uuid
                )
            elif len(circuit_ids) > 1:
                self._add_error(
                    f"Wire has multiple circuit IDs: {', '.join(circuit_ids)}",
                    suggestion="Remove extra labels or move to notes",
                    wire_uuid=wire.uuid
                )

    def _check_duplicate_circuit_ids(self, wires):
        """Check for duplicate circuit IDs across wires"""
        circuit_id_counts: Dict[str, int] = {}
        for wire in wires:
            if wire.circuit_id:
                circuit_id_counts[wire.circuit_id] = circuit_id_counts.get(wire.circuit_id, 0) + 1

        for circuit_id, count in circuit_id_counts.items():
            if count > 1:
                self._add_error(
                    f"Duplicate circuit ID '{circuit_id}' found on {count} wire segments",
                    suggestion="Each wire must have unique circuit ID. Check segment letters."
                )

    def _check_orphaned_labels(self, labels, wires, threshold=10.0):
        """Check for labels not associated with wires"""
        # Implementation: Check label-to-wire distances
        pass

    def _add_error(self, message: str, suggestion: Optional[str] = None,
                   wire_uuid: Optional[str] = None):
        """Add error or warning based on strict mode"""
        error = ValidationError(
            severity="error" if self.strict_mode else "warning",
            message=message,
            suggestion=suggestion,
            wire_uuid=wire_uuid
        )

        if self.strict_mode:
            self.result.errors.append(error)
        else:
            self.result.warnings.append(error)


class HierarchicalValidator(SchematicValidator):
    """Validates hierarchical schematics with connectivity-aware duplicate detection"""

    def __init__(self, strict_mode: bool = True, connectivity_graph: Optional['ConnectivityGraph'] = None):
        super().__init__(strict_mode)
        self.connectivity_graph = connectivity_graph

    def _bfs_reachable_nodes(self, start_position: tuple[float, float]) -> set[tuple[float, float]]:
        """
        Find all node positions reachable from start_position using BFS.

        Args:
            start_position: Starting node position (x, y)

        Returns:
            Set of all reachable node positions (including start_position)
        """
        if not self.connectivity_graph:
            return {start_position}

        visited = set()
        queue = [start_position]
        visited.add(start_position)

        while queue:
            current_pos = queue.pop(0)

            # Get node at current position
            node = self.connectivity_graph.get_node_at_position(current_pos)
            if not node:
                continue

            # Traverse all wires connected to this node
            for wire_uuid in node.connected_wire_uuids:
                # Get both nodes connected by this wire
                node1, node2 = self.connectivity_graph.get_connected_nodes(wire_uuid)

                # Add unvisited neighbor to queue (with rounded position)
                for neighbor in [node1, node2]:
                    rounded_pos = (round(neighbor.position[0], 2), round(neighbor.position[1], 2))
                    if rounded_pos not in visited:
                        visited.add(rounded_pos)
                        queue.append(rounded_pos)

        return visited

    def _are_all_wires_connected(self, wires: List) -> bool:
        """
        Check if all wire segments are electrically connected.

        Uses BFS to check if all wire endpoints are in the same connected component.

        Args:
            wires: List of WireSegment objects

        Returns:
            True if all wires are electrically connected, False otherwise
        """
        if not wires or not self.connectivity_graph:
            return True

        if len(wires) == 1:
            return True

        # Collect all unique endpoint positions from all wires (rounded to match graph precision)
        all_positions = set()
        for wire in wires:
            # Round to 0.01mm precision to match graph node position rounding
            all_positions.add((round(wire.start_point[0], 2), round(wire.start_point[1], 2)))
            all_positions.add((round(wire.end_point[0], 2), round(wire.end_point[1], 2)))

        # Start BFS from the first position
        start_position = next(iter(all_positions))
        reachable = self._bfs_reachable_nodes(start_position)

        # Check if all positions are reachable from start
        return all_positions.issubset(reachable)

    def _check_duplicate_circuit_ids(self, wires):
        """
        Check for duplicate circuit IDs with connectivity awareness.

        Allows same circuit ID on multiple segments if they are electrically
        connected (valid for hierarchical schematics with cross-sheet connections).
        Flags as error if same ID appears on unconnected segments.
        """
        if not self.connectivity_graph:
            # Fall back to base class behavior if no graph
            super()._check_duplicate_circuit_ids(wires)
            return

        # Group wires by circuit ID (handling multiple IDs per wire via circuit_ids)
        circuit_id_groups: Dict[str, List] = {}
        for wire in wires:
            # Use circuit_ids if available, otherwise fall back to circuit_id
            ids = wire.circuit_ids if wire.circuit_ids else ([wire.circuit_id] if wire.circuit_id else [])
            for cid in ids:
                if cid not in circuit_id_groups:
                    circuit_id_groups[cid] = []
                circuit_id_groups[cid].append(wire)

        # Check each group with 2+ wires
        for circuit_id, wire_group in circuit_id_groups.items():
            if len(wire_group) > 1:
                # Check if all wires in group are connected
                if not self._are_all_wires_connected(wire_group):
                    self._add_error(
                        f"Duplicate circuit ID '{circuit_id}' found on {len(wire_group)} UNCONNECTED wire segments",
                        suggestion="Circuit IDs must be unique unless segments are electrically connected."
                    )
