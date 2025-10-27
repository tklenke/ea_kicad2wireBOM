# ABOUTME: SVG routing diagram generation for wire BOMs
# ABOUTME: Creates 2D top-down view (FS×BL) with Manhattan-routed wires

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import math

from kicad2wireBOM.reference_data import DIAGRAM_CONFIG


# System code to full name mapping (per MIL-W-5088L and EAWMS)
SYSTEM_NAMES = {
    'A': 'Avionics',
    'E': 'Engine Instrument',
    'F': 'Flight Instrument',
    'G': 'Ground',
    'K': 'Engine Control',
    'L': 'Lighting',
    'M': 'Miscellaneous Electrical',
    'P': 'Power',
    'R': 'Radio',
    'U': 'Miscellaneous Electronic',
    'V': 'AC Power',
    'W': 'Warning and Emergency',
}


def project_3d_to_2d(fs: float, wl: float, bl: float, wl_scale: float, angle: float) -> Tuple[float, float]:
    """
    Project 3D aircraft coordinates to 2D screen coordinates using elongated orthographic projection.

    Shows all three aircraft axes (FS, WL, BL) on 2D printed output by projecting
    the WL (vertical) axis at an angle.

    Args:
        fs: Fuselage Station coordinate (inches, forward is positive)
        wl: Water Line coordinate (inches, up is positive)
        bl: Butt Line coordinate (inches, starboard/right is positive)
        wl_scale: Scale factor for WL axis (default: 3.0 makes WL 3x more visible)
        angle: Projection angle in degrees (default: 30°)

    Returns:
        (screen_x, screen_y) in projected 2D coordinates

    Projection formula:
        screen_x = FS + (WL × wl_scale) × cos(angle)
        screen_y = BL + (WL × wl_scale) × sin(angle)
    """
    angle_rad = math.radians(angle)
    wl_scaled = wl * wl_scale

    screen_x = fs + wl_scaled * math.cos(angle_rad)
    screen_y = bl + wl_scaled * math.sin(angle_rad)

    return (screen_x, screen_y)


@dataclass
class DiagramComponent:
    """Component position for diagram rendering."""
    ref: str           # Component reference (e.g., "CB1", "SW2")
    fs: float          # Fuselage Station coordinate
    wl: float          # Water Line coordinate
    bl: float          # Butt Line coordinate


@dataclass
class DiagramWireSegment:
    """Wire segment path for diagram rendering."""
    label: str         # Wire label (e.g., "L1A")
    comp1: DiagramComponent
    comp2: DiagramComponent

    @property
    def manhattan_path(self) -> List[Tuple[float, float, float]]:
        """
        Return 3D Manhattan-routed path as list of (FS, WL, BL) points.

        Returns 5 points following BL → FS → WL routing order:
            [(FS1, WL1, BL1), (FS1, WL1, BL2), (FS2, WL1, BL2),
             (FS2, WL2, BL2), (FS2, WL2, BL2)]

        Routing sequence (from outer component C1 to inner component C2):
            1. Start at C1: (FS1, WL1, BL1)
            2. BL move: (FS1, WL1, BL2) - horizontal at C1's WL
            3. FS move: (FS2, WL1, BL2) - still horizontal at C1's WL
            4. WL move: (FS2, WL2, BL2) - vertical drop/rise at C2's location
            5. End at C2: (FS2, WL2, BL2) - same as point 4

        Example:
            comp1=(FS=10, WL=5, BL=30), comp2=(FS=50, WL=15, BL=10)
            Returns: [(10, 5, 30), (10, 5, 10), (50, 5, 10), (50, 15, 10), (50, 15, 10)]
        """
        return [
            (self.comp1.fs, self.comp1.wl, self.comp1.bl),  # Point 1: Start at C1
            (self.comp1.fs, self.comp1.wl, self.comp2.bl),  # Point 2: BL move
            (self.comp2.fs, self.comp1.wl, self.comp2.bl),  # Point 3: FS move
            (self.comp2.fs, self.comp2.wl, self.comp2.bl),  # Point 4: WL move
            (self.comp2.fs, self.comp2.wl, self.comp2.bl),  # Point 5: End at C2
        ]


@dataclass
class SystemDiagram:
    """Complete diagram for one system code."""
    system_code: str                        # "L", "P", "G", etc.
    components: List[DiagramComponent]      # All unique components
    wire_segments: List[DiagramWireSegment] # All wire segments in system

    # Projected bounds for SVG coordinate system (after 3D projection)
    fs_min: float           # Min screen_x after projection (used for SVG transform)
    fs_max: float           # Max screen_x after projection (used for SVG transform)
    bl_min_scaled: float    # Min screen_y after projection and scaling (used for SVG transform)
    bl_max_scaled: float    # Max screen_y after projection and scaling (used for SVG transform)

    # Original bounds for legend display
    fs_min_original: float  # Minimum FS in original coordinates (for legend)
    fs_max_original: float  # Maximum FS in original coordinates (for legend)
    bl_min_original: float  # Minimum BL in original coordinates (for legend)
    bl_max_original: float  # Maximum BL in original coordinates (for legend)


@dataclass
class StarDiagramComponent:
    """Component for star diagram rendering (Phase 13.6.3)."""
    ref: str           # Component reference (e.g., "CB1", "SW2")
    value: str         # Component value (e.g., "5A", "SPDT")
    desc: str          # Component description (e.g., "Circuit Breaker")
    x: float           # SVG X coordinate (pixels)
    y: float           # SVG Y coordinate (pixels)
    radius: float      # Circle radius (pixels, 40-80)


@dataclass
class StarDiagramWire:
    """Wire connection for star diagram (Phase 13.6.3)."""
    circuit_id: str    # Circuit identifier (e.g., "L1A")
    from_ref: str      # Source component reference
    to_ref: str        # Destination component reference


@dataclass
class ComponentStarDiagram:
    """Complete star diagram for one component and its neighbors (Phase 13.6.3)."""
    center: StarDiagramComponent              # Center component
    neighbors: List[StarDiagramComponent]     # Neighbor components (arranged in star)
    wires: List[StarDiagramWire]              # Wire connections between center and neighbors


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


def scale_bl_nonlinear(bl: float, compression_factor: float = 25.0) -> float:
    """
    Apply non-linear scaling to BL coordinate to compress large values.

    Uses logarithmic compression to make diagrams more readable when
    components span large BL ranges (e.g., tip lights far from centerline).

    For small BL values (near centerline), scaling is mostly linear.
    For large BL values (far from centerline), scaling compresses significantly.

    Args:
        bl: BL coordinate in inches
        compression_factor: Compression strength (default: 25.0)
                           Smaller values = more aggressive compression

    Returns:
        Scaled BL coordinate (sign preserved)

    Example:
        scale_bl_nonlinear(10.0) ≈ 8.5   (slightly compressed)
        scale_bl_nonlinear(200.0) ≈ 55.5 (heavily compressed)
    """
    if bl == 0.0:
        return 0.0

    sign = 1 if bl >= 0 else -1
    abs_bl = abs(bl)

    # Logarithmic compression: compresses large values while keeping small values similar
    scaled = sign * compression_factor * math.log(1 + abs_bl / compression_factor)

    return scaled


def scale_bl_nonlinear_v2(bl: float) -> float:
    """
    Apply reversed non-linear scaling to BL coordinate (Phase 13 v2).

    Expands coordinates near centerline (BL≈0) to give more space.
    Compresses coordinates at wingtips (BL>>0) to reduce space.

    This is the opposite of scale_bl_nonlinear() - centerline components
    get MORE space, wingtip components get LESS space.

    Args:
        bl: BL coordinate in inches

    Returns:
        Scaled BL coordinate (sign preserved)

    Piecewise function:
        - BL < 30": Linear expansion by BL_CENTER_EXPANSION (3x)
        - BL ≥ 30": Logarithmic compression with BL_TIP_COMPRESSION

    Example:
        scale_bl_nonlinear_v2(10.0) = 30.0   (expanded 3x)
        scale_bl_nonlinear_v2(30.0) = 90.0   (threshold)
        scale_bl_nonlinear_v2(200.0) ≈ 119   (heavily compressed)
    """
    from kicad2wireBOM.reference_data import (
        BL_CENTER_EXPANSION,
        BL_TIP_COMPRESSION,
        BL_CENTER_THRESHOLD
    )

    if bl == 0.0:
        return 0.0

    sign = 1 if bl >= 0 else -1
    abs_bl = abs(bl)

    if abs_bl <= BL_CENTER_THRESHOLD:
        # Expand centerline region
        scaled = abs_bl * BL_CENTER_EXPANSION
    else:
        # Compress tip region
        # Start at threshold * expansion = 90 for BL=30
        # Then add compressed distance beyond threshold
        base = BL_CENTER_THRESHOLD * BL_CENTER_EXPANSION
        excess = abs_bl - BL_CENTER_THRESHOLD
        compressed_excess = BL_TIP_COMPRESSION * math.log(1 + excess / BL_TIP_COMPRESSION)
        scaled = base + compressed_excess

    return sign * scaled


def calculate_bounds(components: List[DiagramComponent]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for all components after 3D projection.

    Projects all 3D component positions to 2D screen coordinates, then calculates
    bounds on those projected coordinates. Ensures all projected coordinates will
    fit within SVG bounds (no negative coordinates).

    Args:
        components: List of components with FS/WL/BL coordinates

    Returns:
        (screen_x_min, screen_x_max, screen_y_min, screen_y_max) in projected 2D space

    Raises:
        ValueError: If components list is empty
    """
    if not components:
        raise ValueError("Cannot calculate bounds for empty component list")

    from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE

    # Project all components to 2D screen coordinates
    screen_coords = []
    for c in components:
        screen_x, screen_y = project_3d_to_2d(c.fs, c.wl, c.bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
        screen_coords.append((screen_x, screen_y))

    screen_x_values = [x for x, y in screen_coords]
    screen_y_values = [y for x, y in screen_coords]

    # Apply non-linear scaling to screen_y values (which contain BL component)
    screen_y_scaled = [scale_bl_nonlinear(y) for y in screen_y_values]

    return (min(screen_x_values), max(screen_x_values), min(screen_y_scaled), max(screen_y_scaled))


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


def transform_to_svg(fs: float, bl: float,
                     fs_min: float, fs_max: float, bl_scaled_min: float,
                     scale_x: float, scale_y: float, margin: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG coordinates with independent X/Y scaling.

    Aircraft coords: FS increases forward, BL increases starboard (right)
    SVG coords: X increases right, Y increases down
    Diagram orientation: Front (high FS) at top of page

    Applies non-linear scaling to BL to handle large ranges (e.g., tip lights).
    Uses independent scale factors for X and Y to fill available space.

    Args:
        fs, bl: Aircraft coordinates (inches)
        fs_min: Minimum FS in diagram (for offset)
        fs_max: Maximum FS in diagram (for Y-axis flip)
        bl_scaled_min: Minimum scaled BL in diagram (for offset)
        scale_x: Horizontal scale (pixels per inch for BL dimension)
        scale_y: Vertical scale (pixels per inch for FS dimension)
        margin: Margin in pixels

    Returns:
        (svg_x, svg_y) in SVG pixel coordinates
    """
    # Apply non-linear scaling to BL
    bl_scaled = scale_bl_nonlinear(bl)

    # X: Scaled BL maps to horizontal (right), offset, scale, add margin
    svg_x = (bl_scaled - bl_scaled_min) * scale_x + margin

    # Y: FS maps to vertical (up), flip axis (FS up → SVG down), offset, scale, add margin
    svg_y = (fs_max - fs) * scale_y + margin

    return (svg_x, svg_y)


def transform_to_svg_v2(fs: float, bl: float,
                        origin_svg_x: float, origin_svg_y: float,
                        scale_x: float, scale_y: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG coordinates with origin-centered layout (Phase 13 v2).

    Maps aircraft coordinates relative to an origin point (FS=0, BL=0), using
    reversed non-linear BL scaling and inverted FS axis.

    Aircraft coords: FS increases aft (rear), BL increases starboard (right)
    SVG coords: X increases right, Y increases down
    Diagram orientation: Nose (low FS) at TOP, Rear (high FS) at BOTTOM

    Args:
        fs, bl: Aircraft coordinates (inches)
        origin_svg_x: SVG X coordinate of origin (FS=0, BL=0)
        origin_svg_y: SVG Y coordinate of origin (FS=0, BL=0)
        scale_x: Horizontal scale (pixels per inch for BL dimension)
        scale_y: Vertical scale (pixels per inch for FS dimension)

    Returns:
        (svg_x, svg_y) in SVG pixel coordinates

    Coordinate mapping:
        - BL → SVG X: BL=0 at origin_x, BL+ right, BL- left
        - FS → SVG Y: FS=0 at origin_y, FS+ down (higher Y), FS- up (lower Y)
    """
    # Apply reversed non-linear scaling to BL (expands center, compresses tips)
    bl_scaled = scale_bl_nonlinear_v2(bl)

    # X: Scaled BL offset from origin (positive BL → right, negative BL → left)
    svg_x = origin_svg_x + (bl_scaled * scale_x)

    # Y: FS offset from origin (positive FS → down = higher svg_y)
    svg_y = origin_svg_y + (fs * scale_y)

    return (svg_x, svg_y)


def calculate_wire_label_position(path: List[Tuple[float, float, float]]) -> Tuple[float, float, float, str]:
    """
    Calculate position for wire segment label in 3D Manhattan path.

    Places label at midpoint of longest segment in the 3D path.

    Args:
        path: 5-point 3D Manhattan path [(fs1,wl1,bl1), (fs1,wl1,bl2), (fs2,wl1,bl2),
                                         (fs2,wl2,bl2), (fs2,wl2,bl2)]

    Returns:
        (fs, wl, bl, axis) - position for label in 3D aircraft coordinates and axis name
        axis is one of: 'BL', 'FS', 'WL'
    """
    if len(path) != 5:
        raise ValueError("Manhattan path must have exactly 5 points")

    p0, p1, p2, p3, p4 = path

    # Calculate lengths of the three meaningful segments
    # Segment 1 (p0→p1): BL axis move
    seg1_length = abs(p1[2] - p0[2])

    # Segment 2 (p1→p2): FS axis move
    seg2_length = abs(p2[0] - p1[0])

    # Segment 3 (p2→p3): WL axis move
    seg3_length = abs(p3[1] - p2[1])

    # Place label on longest segment
    if seg1_length >= seg2_length and seg1_length >= seg3_length:
        # Midpoint of BL segment (p0→p1) - horizontal segment
        return (p0[0], p0[1], (p0[2] + p1[2]) / 2, 'BL')
    elif seg2_length >= seg3_length:
        # Midpoint of FS segment (p1→p2) - vertical segment (maps to SVG Y)
        return ((p1[0] + p2[0]) / 2, p1[1], p1[2], 'FS')
    else:
        # Midpoint of WL segment (p2→p3)
        return (p2[0], (p2[1] + p3[1]) / 2, p2[2], 'WL')


def build_system_diagram(system_code: str, wires: List, components: Dict) -> SystemDiagram:
    """
    Build diagram data structure for one system.

    Args:
        system_code: System code (e.g., "L", "P", "G")
        wires: All wire connections for this system
        components: Dict mapping component ref to Component object

    Returns:
        SystemDiagram with components, wire segments, and bounds
    """
    # Extract unique components from all wires
    component_dict = {}  # {ref: DiagramComponent}

    for wire in wires:
        # Add from_component if not already present
        if wire.from_component and wire.from_component in components:
            if wire.from_component not in component_dict:
                comp = components[wire.from_component]
                component_dict[wire.from_component] = DiagramComponent(
                    ref=comp.ref,
                    fs=comp.fs,
                    wl=comp.wl,
                    bl=comp.bl
                )

        # Add to_component if not already present
        if wire.to_component and wire.to_component in components:
            if wire.to_component not in component_dict:
                comp = components[wire.to_component]
                component_dict[wire.to_component] = DiagramComponent(
                    ref=comp.ref,
                    fs=comp.fs,
                    wl=comp.wl,
                    bl=comp.bl
                )

    diagram_components = list(component_dict.values())

    # Build wire segments
    wire_segments = []
    for wire in wires:
        if wire.from_component in component_dict and wire.to_component in component_dict:
            segment = DiagramWireSegment(
                label=wire.wire_label,
                comp1=component_dict[wire.from_component],
                comp2=component_dict[wire.to_component]
            )
            wire_segments.append(segment)

    # Calculate projected screen bounds (for SVG coordinate system)
    screen_x_min, screen_x_max, screen_y_min, screen_y_max = calculate_bounds(diagram_components)

    # Also calculate original FS/BL bounds for legend display
    fs_values = [c.fs for c in diagram_components]
    bl_values = [c.bl for c in diagram_components]
    fs_min_original = min(fs_values)
    fs_max_original = max(fs_values)
    bl_min_original = min(bl_values)
    bl_max_original = max(bl_values)

    return SystemDiagram(
        system_code=system_code,
        components=diagram_components,
        wire_segments=wire_segments,
        fs_min=screen_x_min,
        fs_max=screen_x_max,
        bl_min_scaled=screen_y_min,
        bl_max_scaled=screen_y_max,
        fs_min_original=fs_min_original,
        fs_max_original=fs_max_original,
        bl_min_original=bl_min_original,
        bl_max_original=bl_max_original
    )


def generate_svg(diagram: SystemDiagram, output_path: Path, title_block: dict = None, component_value: str = None, component_desc: str = None, use_2d: bool = False) -> None:
    """
    Generate SVG file for system or component diagram in landscape layout (Phase 13 v2).

    Args:
        diagram: SystemDiagram with all data
        output_path: Path to write SVG file
        title_block: Optional dict with title, date, rev from schematic title_block
        component_value: Optional component value (for component diagrams)
        component_desc: Optional component description (for component diagrams)
        use_2d: If True, generate 2D diagram (FS/BL only); if False, use 3D projection (default)

    Creates SVG with:
    - Background (white)
    - Wire segments (black lines, Manhattan routing, configurable width)
    - Wire labels (12pt bold black text)
    - Component markers (blue circles, configurable radius)
    - Component labels (12pt navy text)
    - Title (18pt bold) with project info and legend (11pt)
    - For component diagrams: includes component value and description

    Layout (Phase 13 v2):
    - Landscape orientation (1100×700px from DIAGRAM_CONFIG)
    - Origin-centered coordinate system (FS=0, BL=0 at center)
    - FS+ points down (nose at top, rear at bottom), BL+ points right (starboard)
    - Non-linear BL scaling v2: expands centerline, compresses wingtips
    """
    # Use diagram configuration constants
    MARGIN = DIAGRAM_CONFIG['margin']
    TITLE_HEIGHT = DIAGRAM_CONFIG['title_height']
    FIXED_WIDTH = DIAGRAM_CONFIG['svg_width']
    FIXED_HEIGHT = DIAGRAM_CONFIG['svg_height']

    # Get bounds based on projection mode (Phase 13 v2: use scale_bl_nonlinear_v2)
    if use_2d:
        # Recalculate bounds for 2D mode (FS/BL only, no WL projection)
        fs_values = [c.fs for c in diagram.components]
        bl_values = [c.bl for c in diagram.components]
        fs_min = min(fs_values)
        fs_max = max(fs_values)
        bl_scaled_values = [scale_bl_nonlinear_v2(bl) for bl in bl_values]
        bl_min_scaled = min(bl_scaled_values)
        bl_max_scaled = max(bl_scaled_values)
    else:
        # Use 3D projected bounds from diagram (need to recalculate with v2 scaling)
        fs_min = diagram.fs_min
        fs_max = diagram.fs_max
        # Recalculate BL bounds with v2 scaling
        bl_values = [c.bl for c in diagram.components]
        bl_scaled_values = [scale_bl_nonlinear_v2(bl) for bl in bl_values]
        bl_min_scaled = min(bl_scaled_values)
        bl_max_scaled = max(bl_scaled_values)

    # Calculate independent scales for X and Y to fill available space (Phase 13 v2)
    fs_range = fs_max - fs_min
    bl_scaled_range = bl_max_scaled - bl_min_scaled

    # Available space after margins, title, and origin offset
    origin_offset_y = DIAGRAM_CONFIG['origin_offset_y']
    available_width = FIXED_WIDTH - 2 * MARGIN
    available_height = FIXED_HEIGHT - TITLE_HEIGHT - origin_offset_y - MARGIN

    # Independent scaling for each axis
    scale_x = available_width / bl_scaled_range if bl_scaled_range > 0 else 1.0
    scale_y = available_height / fs_range if fs_range > 0 else 1.0

    # Use fixed dimensions for all diagrams
    svg_width = FIXED_WIDTH
    svg_height = FIXED_HEIGHT

    # Calculate origin position (Phase 13 v2: centered horizontally, below title)
    origin_svg_x = svg_width / 2.0
    origin_svg_y = TITLE_HEIGHT + origin_offset_y

    # Start building SVG
    svg_lines = []
    svg_lines.append(f'<svg width="{svg_width:.0f}" height="{svg_height:.0f}" xmlns="http://www.w3.org/2000/svg">')

    # Background
    svg_lines.append('  <rect fill="white" width="100%" height="100%"/>')

    # Title (larger fonts for print)
    # Detect if this is a component diagram or system diagram
    is_component_diagram = diagram.system_code not in SYSTEM_NAMES

    svg_lines.append('  <g id="title" font-family="Arial">')

    # Add project title_block info if available
    y_offset = 20
    if title_block:
        project_title = title_block.get('title', 'Untitled')
        project_rev = title_block.get('rev', 'N/A')
        project_date = title_block.get('date', 'N/A')
        svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="{y_offset}" font-size="11" text-anchor="middle">{project_title} - Rev {project_rev} - {project_date}</text>')
        y_offset += 20

    # Add component info for component diagrams
    if is_component_diagram and (component_value or component_desc):
        comp_info_parts = []
        if component_value:
            comp_info_parts.append(component_value)
        if component_desc:
            comp_info_parts.append(component_desc)
        comp_info = " - ".join(comp_info_parts)
        svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="{y_offset}" font-size="11" text-anchor="middle">{diagram.system_code}: {comp_info}</text>')
        y_offset += 20

    # Main title
    if is_component_diagram:
        svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="{y_offset + 15}" font-size="18" font-weight="bold" text-anchor="middle">{diagram.system_code} Component Diagram</text>')
    else:
        system_name = SYSTEM_NAMES.get(diagram.system_code, diagram.system_code)
        svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="{y_offset + 15}" font-size="18" font-weight="bold" text-anchor="middle">{system_name} ({diagram.system_code}) System Diagram</text>')

    svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="{y_offset + 35}" font-size="11" text-anchor="middle">Scale: {scale_y:.1f}×{scale_x:.1f} px/inch (Y×X) | FS: {diagram.fs_min_original:.0f}"-{diagram.fs_max_original:.0f}" | BL: {diagram.bl_min_original:.0f}"-{diagram.bl_max_original:.0f}" (compressed)</text>')
    svg_lines.append('  </g>')

    # Separator line below title/legend (fixed width for all diagrams)
    svg_lines.append('  <g id="separator">')
    svg_lines.append(f'    <line x1="{MARGIN}" y1="{TITLE_HEIGHT - 10}" x2="{svg_width - MARGIN}" y2="{TITLE_HEIGHT - 10}" stroke="black" stroke-width="1"/>')
    svg_lines.append('  </g>')

    # Build component-to-circuits mapping (Phase 13.4.1)
    component_circuits = {}
    for segment in diagram.wire_segments:
        # Add to comp1
        if segment.comp1.ref not in component_circuits:
            component_circuits[segment.comp1.ref] = []
        component_circuits[segment.comp1.ref].append(segment.label)

        # Add to comp2
        if segment.comp2.ref not in component_circuits:
            component_circuits[segment.comp2.ref] = []
        component_circuits[segment.comp2.ref].append(segment.label)

    # Sort and deduplicate each component's circuit list
    for ref in component_circuits:
        component_circuits[ref] = sorted(set(component_circuits[ref]))

    # Wire segments (Manhattan routing - thicker for print visibility)
    svg_lines.append(f'  <g id="wires" stroke="black" stroke-width="{DIAGRAM_CONFIG["wire_stroke_width"]}" fill="none">')
    for segment in diagram.wire_segments:
        path = segment.manhattan_path
        points = []
        for fs, wl, bl in path:
            if use_2d:
                # 2D mode: use FS/BL directly (ignore WL)
                screen_x, screen_y = fs, bl
            else:
                # 3D mode: project 3D aircraft coordinates to 2D screen coordinates
                from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
                screen_x, screen_y = project_3d_to_2d(fs, wl, bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
            # Transform to SVG coordinates (Phase 13 v2: origin-centered)
            x, y = transform_to_svg_v2(screen_x, screen_y, origin_svg_x, origin_svg_y, scale_x, scale_y)
            points.append(f"{x:.1f},{y:.1f}")
        svg_lines.append(f'    <polyline points="{" ".join(points)}"/>')
    svg_lines.append('  </g>')

    # Wire labels (larger font for print readability)
    # Track label positions to avoid overlaps
    used_label_positions = []
    COLLISION_THRESHOLD = 20  # pixels - labels closer than this are considered overlapping

    svg_lines.append('  <g id="wire-labels" font-family="Arial" font-size="12" font-weight="bold" fill="black" text-anchor="middle">')
    for segment in diagram.wire_segments:
        path = segment.manhattan_path
        label_fs, label_wl, label_bl, axis = calculate_wire_label_position(path)
        if use_2d:
            # 2D mode: use FS/BL directly (ignore WL)
            screen_x, screen_y = label_fs, label_bl
        else:
            # 3D mode: project 3D label position to 2D screen coordinates
            from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
            screen_x, screen_y = project_3d_to_2d(label_fs, label_wl, label_bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
        # Transform to SVG coordinates (Phase 13 v2: origin-centered)
        x, y = transform_to_svg_v2(screen_x, screen_y, origin_svg_x, origin_svg_y, scale_x, scale_y)

        # Choose offset based on axis orientation
        # FS segments are vertical (Y-axis in SVG), need more horizontal offset
        # BL segments are horizontal (X-axis in SVG), current offset is fine
        # WL segments depend on projection angle
        if axis == 'FS':
            # Vertical wire - offset more to the right
            dx, dy = "25", "-4"
        elif axis == 'BL':
            # Horizontal wire - offset up
            dx, dy = "10", "-10"
        else:  # WL
            # Diagonal wire - offset to upper right
            dx, dy = "15", "-8"

        # Check for collision with existing labels
        collision_offset_y = 0
        for existing_x, existing_y in used_label_positions:
            distance = ((x - existing_x)**2 + (y - existing_y)**2)**0.5
            if distance < COLLISION_THRESHOLD:
                # Collision detected - offset this label upward (negative y = up in SVG)
                collision_offset_y -= 18  # Move up by font size + spacing to stay above wires

        # Apply collision offset
        final_y = y + collision_offset_y
        used_label_positions.append((x, final_y))

        svg_lines.append(f'    <text x="{x:.1f}" y="{final_y:.1f}" dx="{dx}" dy="{dy}">{segment.label}</text>')
    svg_lines.append('  </g>')

    # Component markers (larger for print visibility)
    svg_lines.append('  <g id="components">')
    for comp in diagram.components:
        if use_2d:
            # 2D mode: use FS/BL directly (ignore WL)
            screen_x, screen_y = comp.fs, comp.bl
        else:
            # 3D mode: project 3D component position to 2D screen coordinates
            from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
            screen_x, screen_y = project_3d_to_2d(comp.fs, comp.wl, comp.bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
        # Transform to SVG coordinates (Phase 13 v2: origin-centered)
        x, y = transform_to_svg_v2(screen_x, screen_y, origin_svg_x, origin_svg_y, scale_x, scale_y)
        svg_lines.append(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{DIAGRAM_CONFIG["component_radius"]}" fill="blue" stroke="navy" stroke-width="{DIAGRAM_CONFIG["component_stroke_width"]}"/>')
    svg_lines.append('  </g>')

    # Component labels (larger font, offset down and to the right to avoid wire overlap)
    # Track component label positions to avoid overlaps
    used_comp_label_positions = []
    COMP_COLLISION_THRESHOLD = 30  # pixels - component labels closer than this are considered overlapping

    svg_lines.append('  <g id="component-labels" font-family="Arial" font-size="12" fill="navy" text-anchor="start">')
    for comp in diagram.components:
        if use_2d:
            # 2D mode: use FS/BL directly (ignore WL)
            screen_x, screen_y = comp.fs, comp.bl
        else:
            # 3D mode: project 3D component position to 2D screen coordinates
            from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
            screen_x, screen_y = project_3d_to_2d(comp.fs, comp.wl, comp.bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
        # Transform to SVG coordinates (Phase 13 v2: origin-centered)
        x, y = transform_to_svg_v2(screen_x, screen_y, origin_svg_x, origin_svg_y, scale_x, scale_y)

        # Check for collision with existing component labels
        collision_offset_y = 0
        for existing_x, existing_y in used_comp_label_positions:
            distance = ((x - existing_x)**2 + (y - existing_y)**2)**0.5
            if distance < COMP_COLLISION_THRESHOLD:
                # Collision detected - offset this label further downward
                collision_offset_y += 18  # Move down by font size + spacing

        # Apply collision offset
        final_y = y + collision_offset_y
        used_comp_label_positions.append((x, final_y))

        # Offset down and right: works well for both 2D and 3D modes
        svg_lines.append(f'    <text x="{x:.1f}" y="{final_y:.1f}" dx="12" dy="18">{comp.ref}</text>')
    svg_lines.append('  </g>')

    # Circuit label boxes under components (Phase 13.4.2/13.4.3)
    svg_lines.append('  <g id="component-circuits" font-family="Arial" font-size="10" fill="navy">')
    used_circuit_box_positions = []  # Track boxes to detect collisions
    for comp in diagram.components:
        # Skip components with no circuits
        if comp.ref not in component_circuits or not component_circuits[comp.ref]:
            continue

        # Get component position in SVG
        if use_2d:
            screen_x, screen_y = comp.fs, comp.bl
        else:
            from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
            screen_x, screen_y = project_3d_to_2d(comp.fs, comp.wl, comp.bl, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)
        x, y = transform_to_svg_v2(screen_x, screen_y, origin_svg_x, origin_svg_y, scale_x, scale_y)

        # Format circuit labels
        circuit_text = ", ".join(component_circuits[comp.ref])

        # Estimate box dimensions
        text_width = len(circuit_text) * 7 + 10  # Approximate
        text_height = 16

        # Calculate initial box position (below component marker)
        box_x = x - text_width / 2
        box_y = y + 12  # Offset below component marker

        # Check for collisions with existing boxes (Phase 13.4.3)
        collision_offset = 0
        max_attempts = 10  # Prevent infinite loops
        attempts = 0
        while attempts < max_attempts:
            current_box_y = box_y + collision_offset
            collision_detected = False

            # Check against all previously rendered boxes
            for existing_x, existing_y, existing_width, existing_height in used_circuit_box_positions:
                # Simple rectangle overlap detection
                if not (box_x + text_width < existing_x or  # This box is left of existing
                        box_x > existing_x + existing_width or  # This box is right of existing
                        current_box_y + text_height < existing_y or  # This box is above existing
                        current_box_y > existing_y + existing_height):  # This box is below existing
                    # Collision detected
                    collision_detected = True
                    break

            if not collision_detected:
                # No collision, use this position
                box_y = current_box_y
                break

            # Move box down to avoid collision
            collision_offset += text_height + 4
            attempts += 1

        # Track this box position
        used_circuit_box_positions.append((box_x, box_y, text_width, text_height))

        # Render white background rect with navy stroke
        svg_lines.append(f'    <rect x="{box_x:.1f}" y="{box_y:.1f}" width="{text_width}" height="{text_height}" fill="white" stroke="navy" stroke-width="1"/>')

        # Render centered text inside box
        text_x = x  # Center of box
        text_y = box_y + text_height / 2 + 3  # Vertical center + slight adjustment for baseline
        svg_lines.append(f'    <text x="{text_x:.1f}" y="{text_y:.1f}" text-anchor="middle">{circuit_text}</text>')
    svg_lines.append('  </g>')

    svg_lines.append('</svg>')

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_lines))


def generate_star_svg(diagram: ComponentStarDiagram, output_path: Path) -> None:
    """
    Generate star SVG diagram for one component and its neighbors (Phase 13.6.4).

    Args:
        diagram: ComponentStarDiagram with center, neighbors, and wires
        output_path: Path to write SVG file

    Creates portrait SVG (750×950px) with:
    - Title block with center component ref, value, description
    - Wires (lines from center to neighbors)
    - Wire labels at midpoint
    - Center circle (lightblue fill, navy stroke 3px)
    - Outer circles (white fill, blue stroke 2px)
    - Multi-line centered text in each circle

    Render order: background → wires → wire labels → circles → circle text
    """
    # Portrait dimensions
    svg_width = 750
    svg_height = 950
    title_height = 100
    margin = 40

    # Start building SVG
    svg_lines = []
    svg_lines.append(f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">')

    # Background
    svg_lines.append('  <rect fill="white" width="100%" height="100%"/>')

    # Title block
    svg_lines.append('  <g id="title" font-family="Arial" text-anchor="middle">')
    svg_lines.append(f'    <text x="{svg_width/2}" y="30" font-size="24" font-weight="bold" fill="black">')
    svg_lines.append(f'      Component Star Diagram: {diagram.center.ref}')
    svg_lines.append('    </text>')
    svg_lines.append(f'    <text x="{svg_width/2}" y="55" font-size="14" fill="navy">')
    svg_lines.append(f'      {diagram.center.value}')
    svg_lines.append('    </text>')
    svg_lines.append(f'    <text x="{svg_width/2}" y="75" font-size="12" fill="navy">')
    svg_lines.append(f'      {diagram.center.desc}')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')

    # Create mapping of component ref to coordinates for wire drawing
    comp_positions = {diagram.center.ref: (diagram.center.x, diagram.center.y)}
    for neighbor in diagram.neighbors:
        comp_positions[neighbor.ref] = (neighbor.x, neighbor.y)

    # Wires (lines between components)
    svg_lines.append('  <g id="wires" stroke="black" stroke-width="2">')
    for wire in diagram.wires:
        if wire.from_ref in comp_positions and wire.to_ref in comp_positions:
            x1, y1 = comp_positions[wire.from_ref]
            x2, y2 = comp_positions[wire.to_ref]
            svg_lines.append(f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    svg_lines.append('  </g>')

    # Wire labels (at midpoint of each line)
    svg_lines.append('  <g id="wire-labels" font-family="Arial" font-size="12" font-weight="bold" fill="black" text-anchor="middle">')
    for wire in diagram.wires:
        if wire.from_ref in comp_positions and wire.to_ref in comp_positions:
            x1, y1 = comp_positions[wire.from_ref]
            x2, y2 = comp_positions[wire.to_ref]
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            svg_lines.append(f'    <text x="{mid_x:.1f}" y="{mid_y:.1f}">{wire.circuit_id}</text>')
    svg_lines.append('  </g>')

    # Circles
    svg_lines.append('  <g id="circles">')

    # Center circle (lightblue fill, navy stroke, 3px)
    svg_lines.append(f'    <circle cx="{diagram.center.x:.1f}" cy="{diagram.center.y:.1f}" r="{diagram.center.radius:.1f}" ')
    svg_lines.append('      fill="lightblue" stroke="navy" stroke-width="3"/>')

    # Outer circles (white fill, blue stroke, 2px)
    for neighbor in diagram.neighbors:
        svg_lines.append(f'    <circle cx="{neighbor.x:.1f}" cy="{neighbor.y:.1f}" r="{neighbor.radius:.1f}" ')
        svg_lines.append('      fill="white" stroke="blue" stroke-width="2"/>')

    svg_lines.append('  </g>')

    # Circle text (multi-line, centered)
    svg_lines.append('  <g id="circle-text" font-family="Arial" font-size="10" text-anchor="middle" fill="black">')

    # Center component text
    svg_lines.append(f'    <text x="{diagram.center.x:.1f}" y="{diagram.center.y - 10:.1f}" font-weight="bold">{diagram.center.ref}</text>')
    svg_lines.append(f'    <text x="{diagram.center.x:.1f}" y="{diagram.center.y + 5:.1f}">{diagram.center.value}</text>')
    svg_lines.append(f'    <text x="{diagram.center.x:.1f}" y="{diagram.center.y + 20:.1f}" font-size="8">{diagram.center.desc}</text>')

    # Neighbor component text
    for neighbor in diagram.neighbors:
        svg_lines.append(f'    <text x="{neighbor.x:.1f}" y="{neighbor.y - 10:.1f}" font-weight="bold">{neighbor.ref}</text>')
        svg_lines.append(f'    <text x="{neighbor.x:.1f}" y="{neighbor.y + 5:.1f}">{neighbor.value}</text>')
        svg_lines.append(f'    <text x="{neighbor.x:.1f}" y="{neighbor.y + 20:.1f}" font-size="8">{neighbor.desc}</text>')

    svg_lines.append('  </g>')

    svg_lines.append('</svg>')

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_lines))


def calculate_star_layout(center_x: float, center_y: float, neighbor_refs: List[str], radius: float = 250.0) -> Dict[str, Tuple[float, float]]:
    """
    Calculate polar star layout for neighbor components around a center point (Phase 13.6.1).

    Distributes neighbors evenly around a circle at specified radius from center.
    First neighbor at 0° (right/east), continuing counter-clockwise.

    Args:
        center_x: X coordinate of center point (pixels)
        center_y: Y coordinate of center point (pixels)
        neighbor_refs: List of component references to position
        radius: Distance from center to neighbors (default 250px)

    Returns:
        Dict mapping component ref to (x, y) SVG coordinates

    Example:
        1 neighbor: 0° (right)
        2 neighbors: 0° (right), 180° (left)
        4 neighbors: 0° (right), 90° (down), 180° (left), 270° (up)

    Coordinates in SVG space (Y increases downward):
        0° = right (+X)
        90° = down (+Y)
        180° = left (-X)
        270° = up (-Y)
    """
    layout = {}
    n = len(neighbor_refs)

    if n == 0:
        return layout

    # Angular step between neighbors
    angle_step = 360.0 / n

    for i, ref in enumerate(neighbor_refs):
        # Calculate angle in degrees (starting at 0° = right)
        angle_deg = i * angle_step
        angle_rad = math.radians(angle_deg)

        # Calculate position (SVG: Y increases downward, so +sin for Y)
        x = center_x + radius * math.cos(angle_rad)
        y = center_y + radius * math.sin(angle_rad)

        layout[ref] = (x, y)

    return layout


def wrap_text(text: str, max_width: int) -> List[str]:
    """
    Wrap text at word boundaries to fit within max_width characters (Phase 13.6.2).

    Args:
        text: Text string to wrap
        max_width: Maximum characters per line

    Returns:
        List of wrapped text lines
    """
    if not text or len(text) <= max_width:
        return [text]

    lines = []
    words = text.split()
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # Add space if not first word
        space_length = 1 if current_line else 0

        if current_length + space_length + word_length <= max_width:
            current_line.append(word)
            current_length += space_length + word_length
        else:
            # Start new line
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length

    # Add remaining words
    if current_line:
        lines.append(' '.join(current_line))

    return lines if lines else [""]


def calculate_circle_radius(text_lines: List[str], font_size: int = 10) -> float:
    """
    Calculate circle radius needed to fit text (Phase 13.6.2).

    Estimates text dimensions and returns appropriate circle radius.
    Minimum radius: 40px, Maximum radius: 80px.

    Args:
        text_lines: List of text strings (e.g., ref, value, description)
        font_size: Font size in pixels (default 10)

    Returns:
        Circle radius in pixels (40-80)
    """
    if not text_lines:
        return 40.0

    # Estimate character width (monospace approximation: ~0.6 * font_size)
    char_width = 0.6 * font_size

    # Find longest line
    max_text_length = max(len(line) for line in text_lines)
    estimated_text_width = max_text_length * char_width

    # Estimate text height (font_size + line spacing)
    line_height = font_size + 4
    estimated_text_height = len(text_lines) * line_height

    # Calculate radius to fit text (use diagonal + padding)
    # Diagonal of text bounding box
    diagonal = math.sqrt(estimated_text_width**2 + estimated_text_height**2)
    # Add padding (20% of diagonal)
    required_radius = diagonal / 2 * 1.2

    # Clamp to min/max
    radius = max(40.0, min(80.0, required_radius))

    return radius


def build_component_diagram(component_ref: str, wires: List, components: Dict) -> SystemDiagram:
    """
    Build diagram data structure for one component and its first-hop neighbors.

    Args:
        component_ref: Component reference (e.g., "CB1", "SW2")
        wires: All wire connections involving this component
        components: Dict mapping component ref to Component object

    Returns:
        SystemDiagram with component, its neighbors, wire segments, and bounds
        (Reuses SystemDiagram structure with component_ref as system_code)
    """
    # Helper function to check if a component is a power symbol
    def is_power_symbol(comp_ref):
        return comp_ref and (comp_ref.startswith('GND') or comp_ref.startswith('+') or
                            comp_ref in ['GND', '+12V', '+5V', '+3V3', '+28V'])

    # Extract unique components from all wires (component + all neighbors)
    component_dict = {}  # {ref: DiagramComponent}

    for wire in wires:
        # Add from_component if not already present
        if wire.from_component and wire.from_component in components:
            if wire.from_component not in component_dict:
                comp = components[wire.from_component]
                component_dict[wire.from_component] = DiagramComponent(
                    ref=comp.ref,
                    fs=comp.fs,
                    wl=comp.wl,
                    bl=comp.bl
                )

        # Add to_component if not already present
        if wire.to_component and wire.to_component in components:
            if wire.to_component not in component_dict:
                comp = components[wire.to_component]
                component_dict[wire.to_component] = DiagramComponent(
                    ref=comp.ref,
                    fs=comp.fs,
                    wl=comp.wl,
                    bl=comp.bl
                )

    diagram_components = list(component_dict.values())

    # Build wire segments
    wire_segments = []
    for wire in wires:
        if wire.from_component in component_dict and wire.to_component in component_dict:
            # Skip wires that connect two non-center components through a power net
            # (These are indirect connections, not direct point-to-point wires)
            from_is_center = wire.from_component == component_ref
            to_is_center = wire.to_component == component_ref
            from_is_power = is_power_symbol(wire.from_component)
            to_is_power = is_power_symbol(wire.to_component)

            # Skip if neither endpoint is the center component
            # This filters out cross-connections between non-center components
            if not from_is_center and not to_is_center:
                continue

            segment = DiagramWireSegment(
                label=wire.wire_label,
                comp1=component_dict[wire.from_component],
                comp2=component_dict[wire.to_component]
            )
            wire_segments.append(segment)

    # Calculate projected screen bounds (for SVG coordinate system)
    screen_x_min, screen_x_max, screen_y_min, screen_y_max = calculate_bounds(diagram_components)

    # Also calculate original FS/BL bounds for legend display
    fs_values = [c.fs for c in diagram_components]
    bl_values = [c.bl for c in diagram_components]
    fs_min_original = min(fs_values)
    fs_max_original = max(fs_values)
    bl_min_original = min(bl_values)
    bl_max_original = max(bl_values)

    return SystemDiagram(
        system_code=component_ref,  # Reuse system_code field for component ref
        components=diagram_components,
        wire_segments=wire_segments,
        fs_min=screen_x_min,
        fs_max=screen_x_max,
        bl_min_scaled=screen_y_min,
        bl_max_scaled=screen_y_max,
        fs_min_original=fs_min_original,
        fs_max_original=fs_max_original,
        bl_min_original=bl_min_original,
        bl_max_original=bl_max_original
    )


def generate_component_diagrams(wire_connections: List, components: Dict, output_dir: Path, title_block: dict = None, use_2d: bool = False) -> None:
    """
    Generate component wiring diagram SVG files for all components.

    Args:
        wire_connections: All wire connections from BOM
        components: Dict mapping component ref to Component object
        output_dir: Directory to write SVG files
        title_block: Optional dict with title, date, rev from schematic title_block
        use_2d: If True, generate 2D diagrams (FS/BL only); if False, use 3D projection (default)

    Outputs:
        One component diagram SVG per component (CB1_Component.svg, SW2_Component.svg, etc.)
        Shows component and all first-hop neighbor components
    """
    # Group wires by component (find all wires connected to each component)
    component_wires = defaultdict(list)

    for wire in wire_connections:
        # Add wire to both source and destination component groups
        if wire.from_component:
            component_wires[wire.from_component].append(wire)
        if wire.to_component and wire.to_component != wire.from_component:
            component_wires[wire.to_component].append(wire)

    # Generate one diagram per component
    for comp_ref, wires in component_wires.items():
        # Skip power symbols (they connect to many components)
        # Match GND, GND1, GND2, etc. and power rails like +12V, +5V, etc.
        if comp_ref in ['GND', '+12V', '+5V', '+3V3', '+28V'] or comp_ref.startswith('GND') or comp_ref.startswith('+'):
            continue

        # Build diagram for this component
        diagram = build_component_diagram(comp_ref, wires, components)

        # Get component value and description
        comp = components.get(comp_ref)
        comp_value = comp.value if comp else None
        comp_desc = comp.desc if comp else None

        # Generate SVG with component info
        output_path = output_dir / f"{comp_ref}_Component.svg"
        generate_svg(diagram, output_path, title_block, comp_value, comp_desc, use_2d)

        print(f"Generated {output_path}")


def generate_routing_diagrams(wire_connections: List, components: Dict, output_dir: Path, title_block: dict = None, use_2d: bool = False) -> None:
    """
    Generate routing diagram SVG files for all systems and components.

    Args:
        wire_connections: All wire connections from BOM
        components: Dict mapping component ref to Component object
        output_dir: Directory to write SVG files
        title_block: Optional dict with title, date, rev from schematic title_block
        use_2d: If True, generate 2D diagrams (FS/BL only); if False, use 3D projection (default)

    Outputs:
        One system diagram SVG per system code (L_System.svg, P_System.svg, etc.)
        One component diagram SVG per component (CB1_Component.svg, SW2_Component.svg, etc.)
    """
    # Group wires by system
    system_groups = group_wires_by_system(wire_connections)

    # Generate one system diagram per system
    for system_code, wires in system_groups.items():
        # Build diagram data structure
        diagram = build_system_diagram(system_code, wires, components)

        # Generate SVG with new naming convention
        output_path = output_dir / f"{system_code}_System.svg"
        generate_svg(diagram, output_path, title_block, use_2d=use_2d)

        print(f"Generated {output_path}")

    # Generate component diagrams
    generate_component_diagrams(wire_connections, components, output_dir, title_block, use_2d)
