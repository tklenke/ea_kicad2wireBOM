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
    # Y-axis inverted, so: abs_y = 100 - (-6.35) = 106.35
    assert abs_x == pytest.approx(100.0, abs=0.01)
    assert abs_y == pytest.approx(106.35, abs=0.01)


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
    # Y-axis inverted, so: abs_y = 100 - 6.35 = 93.65
    assert abs_x == pytest.approx(100.0, abs=0.01)
    assert abs_y == pytest.approx(93.65, abs=0.01)


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
    # Y-axis inverted, so: abs_y = 100 - (-2.54) = 102.54
    assert abs_x == pytest.approx(106.35, abs=0.01)
    assert abs_y == pytest.approx(102.54, abs=0.01)


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
    # Step 3: Translate with Y-axis inversion: (100 + (-2.54), 100 - (-6.35)) = (97.46, 106.35)
    assert abs_x == pytest.approx(97.46, abs=0.01)
    assert abs_y == pytest.approx(106.35, abs=0.01)


def test_calculate_pin_position_y_axis_inversion():
    """
    Verify Y-axis inversion for KiCad coordinate system.

    KiCad uses graphics convention where +Y is DOWN (inverted from mathematical Y-axis).
    This test uses actual data from test_03A_fixture.kicad_sch to verify correct calculation.

    SW1 at (119.38, 76.2) with rotation 0:
    - Pin 1 symbol offset: (6.35, +2.54) - positive Y means "up" in symbol
    - Pin 1 expected position: (125.73, 73.66) - LOWER Y value because +Y is DOWN

    J1 at (143.51, 85.09) with rotation 0:
    - Pin 2 symbol offset: (5.08, -3.81) - negative Y means "down" in symbol
    - Pin 2 expected position: (148.59, 88.90) - HIGHER Y value because -Y is UP
    """
    # Test SW1 pin 1
    sw1_pin1 = PinDefinition(
        number='1',
        position=(6.35, 2.54),
        angle=180,
        length=2.54,
        name='ON'
    )
    sw1_component = SimpleComponent(x=119.38, y=76.2)

    sw1_x, sw1_y = calculate_pin_position(sw1_pin1, sw1_component, rotation=0)

    # X: 119.38 + 6.35 = 125.73 ✓
    # Y: 76.2 - 2.54 = 73.66 (Y-axis inverted, so subtract instead of add)
    assert sw1_x == pytest.approx(125.73, abs=0.01)
    assert sw1_y == pytest.approx(73.66, abs=0.01), f"Expected Y=73.66 for SW1 pin 1, got {sw1_y}"

    # Test J1 pin 2
    j1_pin2 = PinDefinition(
        number='2',
        position=(5.08, -3.81),
        angle=0,
        length=2.54,
        name='PWR'
    )
    j1_component = SimpleComponent(x=143.51, y=85.09)

    j1_x, j1_y = calculate_pin_position(j1_pin2, j1_component, rotation=0)

    # X: 143.51 + 5.08 = 148.59 ✓
    # Y: 85.09 - (-3.81) = 88.90 (Y-axis inverted, so subtract, but double negative = add)
    assert j1_x == pytest.approx(148.59, abs=0.01)
    assert j1_y == pytest.approx(88.90, abs=0.01), f"Expected Y=88.90 for J1 pin 2, got {j1_y}"
