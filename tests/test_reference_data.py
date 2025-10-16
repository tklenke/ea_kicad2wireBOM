# ABOUTME: Tests for reference data module
# ABOUTME: Validates wire resistance, ampacity, and configuration data

import pytest
from kicad2wireBOM.reference_data import (
    WIRE_RESISTANCE,
    WIRE_AMPACITY,
    STANDARD_AWG_SIZES,
    DEFAULT_CONFIG
)


def test_wire_resistance_exists():
    """Test that WIRE_RESISTANCE dict is defined with stub data"""
    assert isinstance(WIRE_RESISTANCE, dict)
    assert len(WIRE_RESISTANCE) >= 3  # At least 3-4 AWG sizes for stub

    # Check format: AWG size -> ohms per foot
    for awg, resistance in WIRE_RESISTANCE.items():
        assert isinstance(awg, int)
        assert isinstance(resistance, float)
        assert resistance > 0


def test_wire_ampacity_exists():
    """Test that WIRE_AMPACITY dict is defined with stub data"""
    assert isinstance(WIRE_AMPACITY, dict)
    assert len(WIRE_AMPACITY) >= 3  # At least 3-4 AWG sizes for stub

    # Check format: AWG size -> max amps
    for awg, ampacity in WIRE_AMPACITY.items():
        assert isinstance(awg, int)
        assert isinstance(ampacity, float)
        assert ampacity > 0


def test_wire_resistance_and_ampacity_match():
    """Test that WIRE_RESISTANCE and WIRE_AMPACITY have same AWG sizes"""
    assert set(WIRE_RESISTANCE.keys()) == set(WIRE_AMPACITY.keys())


def test_standard_awg_sizes_exists():
    """Test that STANDARD_AWG_SIZES list is defined"""
    assert isinstance(STANDARD_AWG_SIZES, list)
    assert len(STANDARD_AWG_SIZES) >= 3

    # Should be sorted from smallest (largest wire) to largest (smallest wire)
    for i in range(len(STANDARD_AWG_SIZES) - 1):
        assert STANDARD_AWG_SIZES[i] < STANDARD_AWG_SIZES[i + 1]


def test_default_config_exists():
    """Test that DEFAULT_CONFIG dict has required keys"""
    assert isinstance(DEFAULT_CONFIG, dict)
    assert 'system_voltage' in DEFAULT_CONFIG
    assert 'slack_length' in DEFAULT_CONFIG
    assert 'voltage_drop_percent' in DEFAULT_CONFIG

    # Validate values
    assert DEFAULT_CONFIG['system_voltage'] > 0
    assert DEFAULT_CONFIG['slack_length'] > 0
    assert 0 < DEFAULT_CONFIG['voltage_drop_percent'] < 100


def test_wire_data_reasonable_values():
    """Test that stub data has reasonable values"""
    # AWG 20 is a common small wire, should have reasonable resistance
    if 20 in WIRE_RESISTANCE:
        # AWG 20 is about 0.01 ohm/ft
        assert 0.005 < WIRE_RESISTANCE[20] < 0.02

    # AWG 12 is a common medium wire
    if 12 in WIRE_RESISTANCE:
        # AWG 12 is about 0.0016 ohm/ft
        assert 0.001 < WIRE_RESISTANCE[12] < 0.003

    # Check ampacity makes sense (larger AWG = smaller capacity)
    awg_sizes = sorted(WIRE_AMPACITY.keys())
    if len(awg_sizes) >= 2:
        assert WIRE_AMPACITY[awg_sizes[0]] > WIRE_AMPACITY[awg_sizes[-1]]
