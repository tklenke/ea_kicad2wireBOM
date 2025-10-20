# ABOUTME: Tests for pin position calculation with rotation and mirroring
# ABOUTME: Tests absolute pin position calculation from component placement

import math
import pytest
from dataclasses import dataclass
from kicad2wireBOM.pin_calculator import calculate_pin_position, ComponentPin
from kicad2wireBOM.symbol_library import PinDefinition


@dataclass
class SimpleComponent:
    """Simple component with schematic position for testing"""
    x: float
    y: float


def test_calculate_pin_position_no_rotation():
    """Pin position with no rotation or mirroring"""
    # Pin at (-6.35, 0) in symbol, component at (119.38, 105.41)
    pin_def = PinDefinition(
        number='2',
        position=(-6.35, 0),
        angle=0,
        length=2.54,
        name='IN'
    )

    component = SimpleComponent(x=119.38, y=105.41)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=0)

    # Expected: (119.38 + (-6.35), 105.41 + 0) = (113.03, 105.41)
    assert abs_x == pytest.approx(113.03, abs=0.01)
    assert abs_y == pytest.approx(105.41, abs=0.01)


def test_calculate_pin_position_90_degree_rotation():
    """Pin position with 90 degree rotation"""
    # Pin at (-6.35, 0), rotated 90 degrees, becomes (0, -6.35) after rotation
    pin_def = PinDefinition(
        number='2',
        position=(-6.35, 0),
        angle=0,
        length=2.54,
        name='IN'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=90)

    # After 90° rotation: x' = 0*cos(90) - (-6.35)*sin(90) = 0 - (-6.35)*1 = 6.35
    #                     y' = 0*sin(90) + (-6.35)*cos(90) = 0 + (-6.35)*0 = 0
    # Wait, let me recalculate:
    # x' = x*cos(θ) - y*sin(θ) = (-6.35)*cos(90) - 0*sin(90) = 0
    # y' = x*sin(θ) + y*cos(θ) = (-6.35)*sin(90) + 0*cos(90) = -6.35
    # So rotated pin is at (0, -6.35), then translate to (100, 100-6.35) = (100, 93.65)
    assert abs_x == pytest.approx(100.0, abs=0.01)
    assert abs_y == pytest.approx(93.65, abs=0.01)


def test_calculate_pin_position_180_degree_rotation():
    """Pin position with 180 degree rotation"""
    pin_def = PinDefinition(
        number='2',
        position=(-6.35, 0),
        angle=0,
        length=2.54,
        name='IN'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=180)

    # After 180° rotation: (-6.35, 0) becomes (6.35, 0)
    # Then translate to (106.35, 100)
    assert abs_x == pytest.approx(106.35, abs=0.01)
    assert abs_y == pytest.approx(100.0, abs=0.01)


def test_calculate_pin_position_270_degree_rotation():
    """Pin position with 270 degree rotation"""
    pin_def = PinDefinition(
        number='2',
        position=(-6.35, 0),
        angle=0,
        length=2.54,
        name='IN'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=270)

    # After 270° rotation: (-6.35, 0) becomes (0, 6.35)
    # Then translate to (100, 106.35)
    assert abs_x == pytest.approx(100.0, abs=0.01)
    assert abs_y == pytest.approx(106.35, abs=0.01)


def test_calculate_pin_position_with_x_mirror():
    """Pin position with X-axis mirroring"""
    pin_def = PinDefinition(
        number='2',
        position=(-6.35, 0),
        angle=0,
        length=2.54,
        name='IN'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=0, mirror_x=True)

    # After X-mirror: (-6.35, 0) becomes (6.35, 0)
    # Then translate to (106.35, 100)
    assert abs_x == pytest.approx(106.35, abs=0.01)
    assert abs_y == pytest.approx(100.0, abs=0.01)


def test_calculate_pin_position_with_y_mirror():
    """Pin position with Y-axis mirroring"""
    pin_def = PinDefinition(
        number='1',
        position=(6.35, 2.54),
        angle=180,
        length=2.54,
        name='ON'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(pin_def, component, rotation=0, mirror_y=True)

    # After Y-mirror: (6.35, 2.54) becomes (6.35, -2.54)
    # Then translate to (106.35, 97.46)
    assert abs_x == pytest.approx(106.35, abs=0.01)
    assert abs_y == pytest.approx(97.46, abs=0.01)


def test_calculate_pin_position_complex_transform():
    """Pin position with both mirroring and rotation"""
    pin_def = PinDefinition(
        number='1',
        position=(6.35, 2.54),
        angle=180,
        length=2.54,
        name='ON'
    )

    component = SimpleComponent(x=100.0, y=100.0)

    abs_x, abs_y = calculate_pin_position(
        pin_def, component, rotation=90, mirror_x=True
    )

    # Step 1: Mirror X: (6.35, 2.54) -> (-6.35, 2.54)
    # Step 2: Rotate 90°:
    #   x' = (-6.35)*cos(90) - 2.54*sin(90) = 0 - 2.54 = -2.54
    #   y' = (-6.35)*sin(90) + 2.54*cos(90) = -6.35 + 0 = -6.35
    # Step 3: Translate: (100 - 2.54, 100 - 6.35) = (97.46, 93.65)
    assert abs_x == pytest.approx(97.46, abs=0.01)
    assert abs_y == pytest.approx(93.65, abs=0.01)
