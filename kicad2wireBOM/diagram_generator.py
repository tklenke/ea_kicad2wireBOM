# ABOUTME: SVG routing diagram generation for wire BOMs
# ABOUTME: Creates 2D top-down view (FS×BL) with Manhattan-routed wires

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path


@dataclass
class DiagramComponent:
    """Component position for diagram rendering."""
    ref: str           # Component reference (e.g., "CB1", "SW2")
    fs: float          # Fuselage Station coordinate
    bl: float          # Butt Line coordinate


@dataclass
class DiagramWireSegment:
    """Wire segment path for diagram rendering."""
    label: str         # Wire label (e.g., "L1A")
    comp1: DiagramComponent
    comp2: DiagramComponent

    @property
    def manhattan_path(self) -> List[Tuple[float, float]]:
        """
        Return Manhattan-routed path as list of (FS, BL) points.

        Returns:
            [(start_fs, start_bl), (mid_fs, mid_bl), (end_fs, end_bl)]

        Example:
            comp1=(10, 30), comp2=(50, 10)
            Returns: [(10, 30), (10, 10), (50, 10)]
            First move along BL axis (30→10), then along FS axis (10→50)
        """
        return [
            (self.comp1.fs, self.comp1.bl),           # Start
            (self.comp1.fs, self.comp2.bl),           # Corner (BL move)
            (self.comp2.fs, self.comp2.bl),           # End (FS move)
        ]


@dataclass
class SystemDiagram:
    """Complete diagram for one system code."""
    system_code: str                        # "L", "P", "G", etc.
    components: List[DiagramComponent]      # All unique components
    wire_segments: List[DiagramWireSegment] # All wire segments in system

    # Calculated bounds for auto-scaling
    fs_min: float
    fs_max: float
    bl_min: float
    bl_max: float
