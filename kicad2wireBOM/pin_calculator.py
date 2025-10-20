# ABOUTME: Pin position calculation with rotation and mirroring transforms
# ABOUTME: Calculates absolute schematic positions for component pins

import math
from dataclasses import dataclass
from kicad2wireBOM.symbol_library import PinDefinition


@dataclass
class ComponentPin:
    """A specific pin on a component instance"""
    component_ref: str              # "SW1"
    pin_number: str                 # "1"
    position: tuple[float, float]   # Absolute (x, y) in schematic
    uuid: str                       # Pin UUID from schematic
    connected_wires: list[str]      # Wire UUIDs (populated later)


def calculate_pin_position(
    pin_def: PinDefinition,
    component,  # Any object with x, y attributes
    rotation: float = 0,
    mirror_x: bool = False,
    mirror_y: bool = False
) -> tuple[float, float]:
    """
    Calculate absolute schematic position of a pin.

    Steps:
    1. Start with pin relative position from symbol library
    2. Apply mirroring (if component is mirrored)
    3. Apply rotation (component rotation angle)
    4. Translate to component position

    Args:
        pin_def: Pin definition from symbol library
        component: Component instance
        rotation: Rotation angle in degrees (0, 90, 180, 270)
        mirror_x: Whether component is mirrored on X axis
        mirror_y: Whether component is mirrored on Y axis

    Returns:
        (abs_x, abs_y): Absolute position in schematic coordinates
    """
    x, y = pin_def.position

    # Step 1: Apply mirroring
    if mirror_x:
        x = -x
    if mirror_y:
        y = -y

    # Step 2: Apply rotation (2D rotation matrix)
    # x' = x*cos(θ) - y*sin(θ)
    # y' = x*sin(θ) + y*cos(θ)
    theta_rad = math.radians(rotation)
    x_rot = x * math.cos(theta_rad) - y * math.sin(theta_rad)
    y_rot = x * math.sin(theta_rad) + y * math.cos(theta_rad)

    # Step 3: Translate to component position
    abs_x = component.x + x_rot
    abs_y = component.y + y_rot

    return (abs_x, abs_y)
