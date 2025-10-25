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
