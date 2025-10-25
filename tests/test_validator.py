# ABOUTME: Tests for schematic validation module
# ABOUTME: Validates detection of missing labels, duplicates, and malformed circuit IDs

import pytest
from kicad2wireBOM.validator import (
    ValidationError,
    ValidationResult,
    SchematicValidator,
    HierarchicalValidator
)


def test_validation_result_has_errors():
    """Test ValidationResult.has_errors()"""
    result = ValidationResult(errors=[], warnings=[])
    assert not result.has_errors()

    result_with_error = ValidationResult(
        errors=[ValidationError(severity='error', message='Test error')],
        warnings=[]
    )
    assert result_with_error.has_errors()


def test_validation_result_should_abort_strict_mode():
    """Test should_abort returns True when errors exist in strict mode"""
    result = ValidationResult(
        errors=[ValidationError(severity='error', message='Test error')],
        warnings=[]
    )
    assert result.should_abort(strict_mode=True)


def test_validation_result_should_not_abort_permissive_mode():
    """Test should_abort returns False in permissive mode"""
    result = ValidationResult(
        errors=[ValidationError(severity='error', message='Test error')],
        warnings=[]
    )
    assert not result.should_abort(strict_mode=False)


def test_schematic_validator_creation():
    """Test creating a SchematicValidator"""
    validator = SchematicValidator(strict_mode=True)
    assert validator.strict_mode is True

    validator_permissive = SchematicValidator(strict_mode=False)
    assert validator_permissive.strict_mode is False


def test_schematic_validator_accepts_connectivity_graph():
    """Test SchematicValidator accepts optional connectivity_graph parameter"""
    # Test with no graph (default)
    validator = SchematicValidator(strict_mode=True)
    assert validator.connectivity_graph is None

    # Test with graph=None (explicit)
    validator_explicit_none = SchematicValidator(strict_mode=True, connectivity_graph=None)
    assert validator_explicit_none.connectivity_graph is None

    # Test with a mock graph object
    mock_graph = object()  # Simple mock for testing
    validator_with_graph = SchematicValidator(strict_mode=True, connectivity_graph=mock_graph)
    assert validator_with_graph.connectivity_graph is mock_graph


def test_format_wire_connections_both_ends_to_components():
    """Test _format_wire_connections with both wire ends connecting to components"""
    from kicad2wireBOM.schematic import WireSegment
    from kicad2wireBOM.connectivity_graph import NetworkNode

    # Create mock graph that returns component pins at both endpoints
    class MockGraph:
        def get_node_at_position(self, position):
            # Return mock nodes
            if position == (0.0, 0.0):
                return NetworkNode(position=(0.0, 0.0), node_type='component_pin',
                                 component_ref='BT1', pin_number='1')
            elif position == (100.0, 0.0):
                return NetworkNode(position=(100.0, 0.0), node_type='component_pin',
                                 component_ref='FH1', pin_number='2')
            return None

        def trace_to_component(self, node, exclude_wire_uuid=None):
            if node and node.node_type == 'component_pin':
                return {'component_ref': node.component_ref, 'pin_number': node.pin_number}
            return None

    wire = WireSegment(uuid="w1", start_point=(0.0, 0.0), end_point=(100.0, 0.0))
    validator = SchematicValidator(strict_mode=True, connectivity_graph=MockGraph())

    result = validator._format_wire_connections(wire)

    assert result == "BT1 (pin 1) → FH1 (pin 2)"


def test_format_wire_connections_one_end_to_junction():
    """Test _format_wire_connections with one end to component, one to junction"""
    from kicad2wireBOM.schematic import WireSegment
    from kicad2wireBOM.connectivity_graph import NetworkNode

    class MockGraph:
        def get_node_at_position(self, position):
            if position == (0.0, 0.0):
                return NetworkNode(position=(0.0, 0.0), node_type='component_pin',
                                 component_ref='BT1', pin_number='1')
            elif position == (100.0, 0.0):
                return NetworkNode(position=(100.0, 0.0), node_type='junction')
            return None

        def trace_to_component(self, node, exclude_wire_uuid=None):
            if node and node.node_type == 'component_pin':
                return {'component_ref': node.component_ref, 'pin_number': node.pin_number}
            return None

    wire = WireSegment(uuid="w1", start_point=(0.0, 0.0), end_point=(100.0, 0.0))
    validator = SchematicValidator(strict_mode=True, connectivity_graph=MockGraph())

    result = validator._format_wire_connections(wire)

    assert result == "BT1 (pin 1) → junction"


def test_format_wire_connections_both_unknown():
    """Test _format_wire_connections with both endpoints unknown"""
    from kicad2wireBOM.schematic import WireSegment

    class MockGraph:
        def get_node_at_position(self, position):
            return None

        def trace_to_component(self, node, exclude_wire_uuid=None):
            return None

    wire = WireSegment(uuid="w1", start_point=(0.0, 0.0), end_point=(100.0, 0.0))
    validator = SchematicValidator(strict_mode=True, connectivity_graph=MockGraph())

    result = validator._format_wire_connections(wire)

    assert result == "unknown → unknown"


def test_circuit_id_pattern_matches_valid():
    """Test CIRCUIT_ID_PATTERN matches valid circuit IDs"""
    validator = SchematicValidator()

    # Valid patterns
    assert validator.CIRCUIT_ID_PATTERN.match('L1A')
    assert validator.CIRCUIT_ID_PATTERN.match('P12B')
    assert validator.CIRCUIT_ID_PATTERN.match('G105C')
    assert validator.CIRCUIT_ID_PATTERN.match('L-1-A')
    assert validator.CIRCUIT_ID_PATTERN.match('P-12-B')


def test_circuit_id_pattern_rejects_invalid():
    """Test CIRCUIT_ID_PATTERN rejects invalid circuit IDs"""
    validator = SchematicValidator()

    # Invalid patterns
    assert not validator.CIRCUIT_ID_PATTERN.match('24AWG')
    assert not validator.CIRCUIT_ID_PATTERN.match('10AWG')
    assert not validator.CIRCUIT_ID_PATTERN.match('HIGH_CURRENT')
    assert not validator.CIRCUIT_ID_PATTERN.match('SHIELDED')
    assert not validator.CIRCUIT_ID_PATTERN.match('L1')  # Missing segment letter
    assert not validator.CIRCUIT_ID_PATTERN.match('1A')  # Missing system code


def test_check_no_labels_strict_mode():
    """Test validation detects schematic with no circuit ID labels (strict mode)"""
    from kicad2wireBOM.schematic import WireSegment, Label

    validator = SchematicValidator(strict_mode=True)

    wires = [
        WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    ]
    labels = [
        Label(text="24AWG", position=(50, 2), uuid="l1")  # Not a circuit ID
    ]

    result = validator.validate_all(wires, labels, [])

    assert result.has_errors()
    assert len(result.errors) > 0
    assert "No circuit ID labels found" in result.errors[0].message


def test_check_no_labels_permissive_mode():
    """Test validation warns about no circuit ID labels (permissive mode)"""
    from kicad2wireBOM.schematic import WireSegment, Label

    validator = SchematicValidator(strict_mode=False)

    wires = [
        WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    ]
    labels = [
        Label(text="24AWG", position=(50, 2), uuid="l1")
    ]

    result = validator.validate_all(wires, labels, [])

    assert not result.has_errors()
    assert len(result.warnings) > 0
    assert "No circuit ID labels found" in result.warnings[0].message


def test_check_wire_missing_label_strict():
    """Test detection of wire with non-circuit ID labels only (strict mode)"""
    from kicad2wireBOM.schematic import WireSegment, Label

    validator = SchematicValidator(strict_mode=True)

    # Wire with labels but no valid circuit ID (has invalid label in wire.labels)
    wire = WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    wire.labels = ["INVALID_LABEL"]  # Not a circuit ID pattern
    wires = [wire]
    labels = []

    result = validator.validate_all(wires, labels, [])

    assert result.has_errors()
    # Should have error about wire w1 having no valid circuit ID label
    wire_errors = [e for e in result.errors if e.wire_uuid == "w1"]
    assert len(wire_errors) > 0
    assert "no valid circuit ID label" in wire_errors[0].message


def test_check_wire_multiple_circuit_ids():
    """Test detection of wire with multiple circuit ID labels"""
    from kicad2wireBOM.schematic import WireSegment, Label

    validator = SchematicValidator(strict_mode=True)

    # Wire with multiple circuit ID labels
    wire = WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    wire.labels = ["P1A", "P2B"]  # Two circuit IDs
    wires = [wire]
    labels = []

    result = validator.validate_all(wires, labels, [])

    assert result.has_errors()
    wire_errors = [e for e in result.errors if e.wire_uuid == "w1"]
    assert len(wire_errors) > 0
    assert "multiple circuit IDs" in wire_errors[0].message


def test_check_duplicate_circuit_ids_strict():
    """Test detection of duplicate circuit IDs across wires (strict mode)"""
    from kicad2wireBOM.schematic import WireSegment

    validator = SchematicValidator(strict_mode=True)

    # Two wires with same circuit_id
    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    wire1.circuit_id = "G3A"

    wire2 = WireSegment(uuid="w2", start_point=(0, 100), end_point=(100, 100))
    wire2.circuit_id = "G3A"

    wires = [wire1, wire2]

    result = validator.validate_all(wires, [], [])

    assert result.has_errors()
    dup_errors = [e for e in result.errors if "Duplicate" in e.message]
    assert len(dup_errors) > 0
    assert "G3A" in dup_errors[0].message
    assert "2 wire segments" in dup_errors[0].message


def test_check_duplicate_circuit_ids_permissive():
    """Test duplicate circuit IDs produce warnings in permissive mode"""
    from kicad2wireBOM.schematic import WireSegment

    validator = SchematicValidator(strict_mode=False)

    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    wire1.circuit_id = "G3A"

    wire2 = WireSegment(uuid="w2", start_point=(0, 100), end_point=(100, 100))
    wire2.circuit_id = "G3A"

    wires = [wire1, wire2]

    result = validator.validate_all(wires, [], [])

    assert not result.has_errors()
    assert len(result.warnings) > 0
    dup_warnings = [w for w in result.warnings if "Duplicate" in w.message]
    assert len(dup_warnings) > 0
    assert "G3A" in dup_warnings[0].message


def test_hierarchical_validator_creation():
    """Test creating a HierarchicalValidator with connectivity graph"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph

    graph = ConnectivityGraph()
    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)

    assert validator.strict_mode is True
    assert validator.connectivity_graph is graph


def test_bfs_reachable_nodes():
    """Test BFS traversal finds all connected nodes"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph, NetworkNode
    from kicad2wireBOM.schematic import WireSegment

    # Create a simple connected graph: A -- B -- C
    graph = ConnectivityGraph()

    wire_ab = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire_bc = WireSegment(uuid="w2", start_point=(10, 0), end_point=(20, 0))

    graph.add_wire(wire_ab)
    graph.add_wire(wire_bc)

    node_a = graph.get_node_at_position((0, 0))
    node_b = graph.get_node_at_position((10, 0))
    node_c = graph.get_node_at_position((20, 0))

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)

    # BFS from node_a should find a, b, c
    reachable = validator._bfs_reachable_nodes(node_a.position)
    assert node_a.position in reachable
    assert node_b.position in reachable
    assert node_c.position in reachable
    assert len(reachable) == 3


def test_bfs_reachable_nodes_disconnected():
    """Test BFS does not reach disconnected nodes"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph
    from kicad2wireBOM.schematic import WireSegment

    # Create disconnected graph: A -- B    C -- D
    graph = ConnectivityGraph()

    wire_ab = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire_cd = WireSegment(uuid="w2", start_point=(100, 0), end_point=(110, 0))

    graph.add_wire(wire_ab)
    graph.add_wire(wire_cd)

    node_a = graph.get_node_at_position((0, 0))
    node_b = graph.get_node_at_position((10, 0))
    node_c = graph.get_node_at_position((100, 0))
    node_d = graph.get_node_at_position((110, 0))

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)

    # BFS from node_a should find a, b but not c, d
    reachable = validator._bfs_reachable_nodes(node_a.position)
    assert node_a.position in reachable
    assert node_b.position in reachable
    assert node_c.position not in reachable
    assert node_d.position not in reachable
    assert len(reachable) == 2


def test_are_all_wires_connected_true():
    """Test checking if all wires are connected - connected case"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph
    from kicad2wireBOM.schematic import WireSegment

    # Create connected graph: wire1 (0,0)-(10,0) connected to wire2 (10,0)-(20,0)
    graph = ConnectivityGraph()

    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire2 = WireSegment(uuid="w2", start_point=(10, 0), end_point=(20, 0))

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)

    # Both wires should be connected
    result = validator._are_all_wires_connected([wire1, wire2])
    assert result is True


def test_are_all_wires_connected_false():
    """Test checking if all wires are connected - disconnected case"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph
    from kicad2wireBOM.schematic import WireSegment

    # Create disconnected graph: wire1 and wire2 not connected
    graph = ConnectivityGraph()

    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire2 = WireSegment(uuid="w2", start_point=(100, 0), end_point=(110, 0))

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)

    # Wires should NOT be connected
    result = validator._are_all_wires_connected([wire1, wire2])
    assert result is False


def test_connectivity_aware_duplicate_detection_connected():
    """Test that same circuit ID on connected wires is NOT an error"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph
    from kicad2wireBOM.schematic import WireSegment, Label

    # Create connected wires with same circuit ID (valid for hierarchical)
    graph = ConnectivityGraph()

    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire1.circuit_id = "L2B"
    wire1.circuit_ids = ["L2B"]
    wire1.labels = ["L2B"]

    wire2 = WireSegment(uuid="w2", start_point=(10, 0), end_point=(20, 0))
    wire2.circuit_id = "L2B"
    wire2.circuit_ids = ["L2B"]
    wire2.labels = ["L2B"]

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    # Create labels for validation
    labels = [
        Label(text="L2B", position=(5, 0), uuid="l1"),
        Label(text="L2B", position=(15, 0), uuid="l2")
    ]

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)
    result = validator.validate_all([wire1, wire2], labels, [])

    # Should NOT have errors - connected wires can share circuit ID
    assert not result.has_errors()


def test_connectivity_aware_duplicate_detection_unconnected():
    """Test that same circuit ID on unconnected wires IS an error"""
    from kicad2wireBOM.connectivity_graph import ConnectivityGraph
    from kicad2wireBOM.schematic import WireSegment, Label

    # Create disconnected wires with same circuit ID (invalid)
    graph = ConnectivityGraph()

    wire1 = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 0))
    wire1.circuit_id = "L2B"
    wire1.circuit_ids = ["L2B"]
    wire1.labels = ["L2B"]

    wire2 = WireSegment(uuid="w2", start_point=(100, 0), end_point=(110, 0))
    wire2.circuit_id = "L2B"
    wire2.circuit_ids = ["L2B"]
    wire2.labels = ["L2B"]

    graph.add_wire(wire1)
    graph.add_wire(wire2)

    # Create labels for validation
    labels = [
        Label(text="L2B", position=(5, 0), uuid="l1"),
        Label(text="L2B", position=(105, 0), uuid="l2")
    ]

    validator = HierarchicalValidator(strict_mode=True, connectivity_graph=graph)
    result = validator.validate_all([wire1, wire2], labels, [])

    # Should have errors - unconnected wires cannot share circuit ID
    assert result.has_errors()
    dup_errors = [e for e in result.errors if "UNCONNECTED" in e.message]
    assert len(dup_errors) > 0
    assert "L2B" in dup_errors[0].message
