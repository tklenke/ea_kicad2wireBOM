# ABOUTME: Tests for schematic validation module
# ABOUTME: Validates detection of missing labels, duplicates, and malformed circuit IDs

import pytest
from kicad2wireBOM.validator import (
    ValidationError,
    ValidationResult,
    SchematicValidator
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
