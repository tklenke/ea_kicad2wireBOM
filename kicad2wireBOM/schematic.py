# ABOUTME: Data models for schematic elements
# ABOUTME: Defines WireSegment, Label, and Component classes for schematic parsing

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WireSegment:
    """
    Represents a single wire segment in the schematic.

    Wire segments are the physical wires drawn in the schematic,
    each with distinct start and end points. These are preserved
    at wire-level granularity (not collapsed into nets).
    """
    uuid: str
    start_point: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    end_point: tuple[float, float]    # (x, y) in mm
    circuit_id: Optional[str] = None  # Parsed from label (e.g., "P1A")
    system_code: Optional[str] = None # Extracted from circuit_id (e.g., "P")
    circuit_num: Optional[str] = None # Extracted from circuit_id (e.g., "1")
    segment_letter: Optional[str] = None  # Extracted from circuit_id (e.g., "A")
    labels: list[str] = field(default_factory=list)  # All labels associated with this wire
    start_connection: Optional[str] = None  # Connection at start (e.g., "SW1-1", "JUNCTION-abc")
    end_connection: Optional[str] = None    # Connection at end (e.g., "SW2-2", "UNKNOWN")


@dataclass
class Junction:
    """
    Represents a junction in the schematic.

    Junctions are explicit connection points where multiple wires meet.
    Only wires meeting at a junction are electrically connected.
    """
    uuid: str
    position: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    diameter: float = 0.0
    color: tuple[int, int, int, int] = (0, 0, 0, 0)  # RGBA


@dataclass
class Label:
    """
    Represents a label in the schematic.

    Labels are text annotations placed near wires to indicate
    circuit identifiers (e.g., "P1A", "G1A").
    """
    text: str
    position: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    uuid: str
    rotation: float = 0.0  # Rotation in degrees
