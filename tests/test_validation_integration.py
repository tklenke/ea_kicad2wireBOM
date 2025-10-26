# ABOUTME: Integration tests for Phase 6 validation features
# ABOUTME: Tests validation with test_05 fixture variants (missing/duplicate/non-circuit labels)

from pathlib import Path
from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    parse_wire_element,
    parse_label_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.validator import SchematicValidator


def test_05_baseline_passes_validation():
    """
    Test that test_05 (baseline correct fixture) passes validation.

    test_05 should have all 7 circuit IDs correctly labeled.
    """
    fixture_path = Path('tests/fixtures/test_05_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Validate in strict mode
    validator = SchematicValidator(strict_mode=True)
    result = validator.validate_all(wires, labels, [], missing_locload_components=[])

    # Should pass with no errors
    assert not result.has_errors(), \
        f"test_05 baseline should pass validation, got errors: {[e.message for e in result.errors]}"


def test_05C_non_circuit_labels_with_notes():
    """
    Test that test_05C (non-circuit labels) handles notes correctly.

    test_05C has valid circuit IDs plus non-circuit labels like "24AWG".
    Non-circuit labels should go to notes field.
    """
    fixture_path = Path('tests/fixtures/test_05C_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Verify that some wires have notes from non-circuit labels
    wires_with_notes = [w for w in wires if w.notes]
    assert len(wires_with_notes) > 0, "Expected some wires to have notes from non-circuit labels"

    # Verify that wires with circuit IDs exist
    wires_with_circuit_ids = [w for w in wires if w.circuit_id]
    assert len(wires_with_circuit_ids) >= 6, \
        f"Expected at least 6 wires with circuit IDs, got {len(wires_with_circuit_ids)}"


def test_05A_missing_labels_fails_strict_validation():
    """
    Test that test_05A (all labels missing) fails strict validation.

    test_05A has all 7 circuit ID labels removed.
    Should fail with "No circuit ID labels found" error.
    """
    fixture_path = Path('tests/fixtures/test_05A_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Validate in strict mode
    validator = SchematicValidator(strict_mode=True)
    result = validator.validate_all(wires, labels, [], missing_locload_components=[])

    # Should fail validation
    assert result.has_errors(), "test_05A should fail strict validation"

    # Should have "No circuit ID labels found" error
    no_labels_errors = [e for e in result.errors if "No circuit ID labels" in e.message]
    assert len(no_labels_errors) > 0, \
        f"Expected 'No circuit ID labels' error, got: {[e.message for e in result.errors]}"


def test_05A_missing_labels_warns_permissive_mode():
    """
    Test that test_05A produces warnings in permissive mode.

    Permissive mode should warn but not abort.
    """
    fixture_path = Path('tests/fixtures/test_05A_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Validate in permissive mode
    validator = SchematicValidator(strict_mode=False)
    result = validator.validate_all(wires, labels, [], missing_locload_components=[])

    # Should NOT abort (no errors)
    assert not result.has_errors(), "Permissive mode should not have errors"

    # Should have warnings
    assert len(result.warnings) > 0, "Expected warnings in permissive mode"
    assert not result.should_abort(strict_mode=False), "Permissive mode should not abort"


def test_05B_duplicate_labels_fails_strict_validation():
    """
    Test that test_05B (duplicate G3A) fails strict validation.

    test_05B has G3A appearing twice, G4A missing.
    Should fail with "Duplicate circuit ID 'G3A'" error.
    """
    fixture_path = Path('tests/fixtures/test_05B_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Validate in strict mode
    validator = SchematicValidator(strict_mode=True)
    result = validator.validate_all(wires, labels, [], missing_locload_components=[])

    # Should fail validation
    assert result.has_errors(), "test_05B should fail strict validation"

    # Should have "Duplicate circuit ID 'G3A'" error
    dup_errors = [e for e in result.errors if "Duplicate" in e.message and "G3A" in e.message]
    assert len(dup_errors) > 0, \
        f"Expected duplicate G3A error, got: {[e.message for e in result.errors]}"


def test_05B_duplicate_labels_warns_permissive_mode():
    """
    Test that test_05B produces warnings in permissive mode.

    Permissive mode should warn about duplicates but continue.
    """
    fixture_path = Path('tests/fixtures/test_05B_fixture.kicad_sch')
    sexp = parse_schematic_file(fixture_path)

    # Parse wires and labels
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, threshold=10.0)

    # Validate in permissive mode
    validator = SchematicValidator(strict_mode=False)
    result = validator.validate_all(wires, labels, [], missing_locload_components=[])

    # Should NOT abort (no errors)
    assert not result.has_errors(), "Permissive mode should not have errors"

    # Should have warnings about duplicate
    assert len(result.warnings) > 0, "Expected warnings in permissive mode"
    dup_warnings = [w for w in result.warnings if "Duplicate" in w.message and "G3A" in w.message]
    assert len(dup_warnings) > 0, "Expected duplicate G3A warning"
