# ABOUTME: SVG routing diagram generation for wire BOMs
# ABOUTME: Creates 2D top-down view (FS×BL) with Manhattan-routed wires

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict


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


def group_wires_by_system(wire_connections: List) -> Dict[str, List]:
    """
    Group wire connections by system code.

    Args:
        wire_connections: All wire connections from BOM

    Returns:
        Dict mapping system_code to list of WireConnections
        Example: {'L': [L1A, L1B, L2A], 'P': [P1A], 'G': [G1A, G2A]}

    Note:
        Uses parse_net_name() to extract system_code from wire label.
        Wires that fail to parse are skipped (no system code available).
    """
    from kicad2wireBOM.wire_calculator import parse_net_name

    system_groups = defaultdict(list)

    for wire in wire_connections:
        # Add leading slash for parse_net_name compatibility
        net_name = f"/{wire.wire_label}"
        parsed = parse_net_name(net_name)
        if parsed and parsed.get('system'):
            system_groups[parsed['system']].append(wire)

    return dict(system_groups)


def calculate_bounds(components: List[DiagramComponent]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for all components.

    Args:
        components: List of components with FS/BL coordinates

    Returns:
        (fs_min, fs_max, bl_min, bl_max)

    Raises:
        ValueError: If components list is empty
    """
    if not components:
        raise ValueError("Cannot calculate bounds for empty component list")

    fs_values = [c.fs for c in components]
    bl_values = [c.bl for c in components]

    return (min(fs_values), max(fs_values), min(bl_values), max(bl_values))


def calculate_scale(fs_range: float, bl_range: float,
                    target_width: int = 800, margin: int = 50) -> float:
    """
    Calculate appropriate scale factor (pixels per inch).

    Args:
        fs_range: FS coordinate range (fs_max - fs_min)
        bl_range: BL coordinate range (bl_max - bl_min)
        target_width: Target diagram width in pixels (default: 800)
        margin: Margin around diagram in pixels (default: 50)

    Returns:
        Scale factor in pixels per inch (clamped to MIN_SCALE...MAX_SCALE)

    Note:
        Calculates scale to fit larger dimension within target width,
        then clamps to reasonable range (2.0 to 10.0 px/inch).
    """
    MIN_SCALE = 2.0   # pixels per inch
    MAX_SCALE = 10.0  # pixels per inch

    # Available space for diagram (subtract margins)
    available = target_width - (2 * margin)

    # Calculate scale based on larger dimension
    max_range = max(fs_range, bl_range)

    if max_range == 0:
        # Single point or all components at same location
        return MIN_SCALE

    scale = available / max_range

    # Clamp to reasonable range
    return max(MIN_SCALE, min(MAX_SCALE, scale))
