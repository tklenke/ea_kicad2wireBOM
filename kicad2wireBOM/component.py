# ABOUTME: Component data model for electrical components
# ABOUTME: Defines Component dataclass with coordinate and electrical properties

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Component:
    """
    Represents an electrical component from a KiCad schematic.

    Attributes:
        ref: Component reference designator (e.g., "J1", "SW1", "LIGHT1")
        fs: Fuselage Station coordinate (inches)
        wl: Water Line coordinate (inches)
        bl: Butt Line coordinate (inches)
        load: Load current in amps (for consuming devices), None if not a load
        rating: Current rating in amps (for pass-through devices), None if not pass-through
    """
    ref: str
    fs: float
    wl: float
    bl: float
    load: Optional[float]
    rating: Optional[float]

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        """Return component coordinates as (fs, wl, bl) tuple"""
        return (self.fs, self.wl, self.bl)

    @property
    def is_load(self) -> bool:
        """Return True if component has a load value (consuming device)"""
        return self.load is not None

    @property
    def is_passthrough(self) -> bool:
        """Return True if component has a rating value (pass-through device)"""
        return self.rating is not None

    @property
    def is_source(self) -> bool:
        """Return True if component is a source (connector with J prefix and rating)"""
        return self.ref.startswith('J') and self.rating is not None
