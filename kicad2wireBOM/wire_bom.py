# ABOUTME: Wire Bill of Materials data model
# ABOUTME: Defines WireConnection and WireBOM classes for wire specifications

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class WireConnection:
    """
    Represents a single wire connection in the BOM.

    Attributes:
        wire_label: Wire label in EAWMS format (e.g., "L-105-A")
        from_ref: Source component reference (e.g., "J1")
        to_ref: Destination component reference (e.g., "SW1")
        wire_gauge: AWG wire size
        wire_color: Wire color (from system code mapping)
        length: Wire length in inches
        wire_type: Wire type (e.g., "Standard")
        warnings: List of warning messages for this wire
    """
    wire_label: str
    from_ref: str
    to_ref: str
    wire_gauge: int
    wire_color: str
    length: float
    wire_type: str
    warnings: List[str]


@dataclass
class WireBOM:
    """
    Represents a complete wire Bill of Materials.

    Attributes:
        wires: List of WireConnection objects
        config: Configuration dict used to generate the BOM
    """
    config: Dict[str, Any]
    wires: List[WireConnection] = field(default_factory=list)

    def add_wire(self, wire: WireConnection) -> None:
        """Add a wire to the BOM"""
        self.wires.append(wire)
