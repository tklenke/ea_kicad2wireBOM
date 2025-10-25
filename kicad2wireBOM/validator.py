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

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.result = ValidationResult(errors=[], warnings=[])

    def validate_all(self, wires, labels, components) -> ValidationResult:
        """Run all validation checks"""
        self._check_no_labels(wires, labels)
        self._check_wire_labels(wires)
        self._check_duplicate_circuit_ids(wires)
        self._check_orphaned_labels(labels, wires)
        return self.result

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

                # Add unvisited neighbor to queue
                for neighbor in [node1, node2]:
                    if neighbor.position not in visited:
                        visited.add(neighbor.position)
                        queue.append(neighbor.position)

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

        # Collect all unique endpoint positions from all wires
        all_positions = set()
        for wire in wires:
            all_positions.add(wire.start_point)
            all_positions.add(wire.end_point)

        # Start BFS from the first position
        start_position = next(iter(all_positions))
        reachable = self._bfs_reachable_nodes(start_position)

        # Check if all positions are reachable from start
        return all_positions.issubset(reachable)
