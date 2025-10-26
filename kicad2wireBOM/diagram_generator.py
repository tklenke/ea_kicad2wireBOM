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


def transform_to_svg(fs: float, bl: float,
                     fs_min: float, fs_max: float, bl_min: float,
                     scale: float, margin: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG coordinates.

    Aircraft coords: FS increases forward, BL increases starboard (right)
    SVG coords: X increases right, Y increases down
    Diagram orientation: Front (high FS) at top of page

    Args:
        fs, bl: Aircraft coordinates (inches)
        fs_min: Minimum FS in diagram (for offset)
        fs_max: Maximum FS in diagram (for Y-axis flip)
        bl_min: Minimum BL in diagram (for offset)
        scale: Pixels per inch
        margin: Margin in pixels

    Returns:
        (svg_x, svg_y) in SVG pixel coordinates
    """
    # X: BL maps to horizontal (right), offset, scale, add margin
    svg_x = (bl - bl_min) * scale + margin

    # Y: FS maps to vertical (up), flip axis (FS up → SVG down), offset, scale, add margin
    svg_y = (fs_max - fs) * scale + margin

    return (svg_x, svg_y)


def calculate_wire_label_position(path: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate position for wire segment label.

    Places label at midpoint of longer segment in Manhattan path.

    Args:
        path: [(fs1, bl1), (fs2, bl2), (fs3, bl3)] - 3-point Manhattan path

    Returns:
        (fs, bl) - position for label in aircraft coordinates
    """
    if len(path) != 3:
        raise ValueError("Manhattan path must have exactly 3 points")

    p1, p2, p3 = path

    # Segment 1: p1 → p2 (vertical, along BL axis)
    seg1_length = abs(p2[1] - p1[1])

    # Segment 2: p2 → p3 (horizontal, along FS axis)
    seg2_length = abs(p3[0] - p2[0])

    # Place label on longer segment
    if seg1_length > seg2_length:
        # Midpoint of vertical segment
        return (p1[0], (p1[1] + p2[1]) / 2)
    else:
        # Midpoint of horizontal segment
        return ((p2[0] + p3[0]) / 2, p2[1])


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
                    bl=comp.bl
                )

        # Add to_component if not already present
        if wire.to_component and wire.to_component in components:
            if wire.to_component not in component_dict:
                comp = components[wire.to_component]
                component_dict[wire.to_component] = DiagramComponent(
                    ref=comp.ref,
                    fs=comp.fs,
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

    # Calculate bounds
    fs_min, fs_max, bl_min, bl_max = calculate_bounds(diagram_components)

    return SystemDiagram(
        system_code=system_code,
        components=diagram_components,
        wire_segments=wire_segments,
        fs_min=fs_min,
        fs_max=fs_max,
        bl_min=bl_min,
        bl_max=bl_max
    )


def generate_svg(diagram: SystemDiagram, output_path: Path) -> None:
    """
    Generate SVG file for system diagram.

    Args:
        diagram: SystemDiagram with all data
        output_path: Path to write SVG file

    Creates SVG with:
    - Background (white)
    - Grid lines (light gray, 12-inch spacing)
    - Axes (dark gray)
    - Wire segments (black lines, Manhattan routing)
    - Wire labels (black text)
    - Component markers (blue circles)
    - Component labels (navy text)
    - Title and legend
    """
    # Constants
    MARGIN = 50
    TARGET_WIDTH = 800
    GRID_SPACING = 12  # inches

    # Calculate scale
    fs_range = diagram.fs_max - diagram.fs_min
    bl_range = diagram.bl_max - diagram.bl_min
    scale = calculate_scale(fs_range, bl_range, TARGET_WIDTH, MARGIN)

    # Calculate SVG dimensions (BL->width/X, FS->height/Y)
    svg_width = bl_range * scale + 2 * MARGIN
    svg_height = fs_range * scale + 2 * MARGIN

    # Start building SVG
    svg_lines = []
    svg_lines.append(f'<svg width="{svg_width:.0f}" height="{svg_height:.0f}" xmlns="http://www.w3.org/2000/svg">')

    # Background
    svg_lines.append('  <rect fill="white" width="100%" height="100%"/>')

    # Grid lines (12-inch spacing)
    svg_lines.append('  <g id="grid" stroke="#e0e0e0" stroke-width="0.5">')
    # Vertical grid lines (BL axis - now horizontal on page)
    bl_start = int(diagram.bl_min / GRID_SPACING) * GRID_SPACING
    bl = bl_start
    while bl <= diagram.bl_max:
        x, _ = transform_to_svg(diagram.fs_min, bl, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
        svg_lines.append(f'    <line x1="{x:.1f}" y1="{MARGIN}" x2="{x:.1f}" y2="{svg_height - MARGIN}"/>')
        bl += GRID_SPACING
    # Horizontal grid lines (FS axis - now vertical on page)
    fs_start = int(diagram.fs_min / GRID_SPACING) * GRID_SPACING
    fs = fs_start
    while fs <= diagram.fs_max:
        _, y = transform_to_svg(fs, diagram.bl_min, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
        svg_lines.append(f'    <line x1="{MARGIN}" y1="{y:.1f}" x2="{svg_width - MARGIN}" y2="{y:.1f}"/>')
        fs += GRID_SPACING
    svg_lines.append('  </g>')

    # Wire segments (Manhattan routing)
    svg_lines.append('  <g id="wires" stroke="black" stroke-width="2" fill="none">')
    for segment in diagram.wire_segments:
        path = segment.manhattan_path
        points = []
        for fs, bl in path:
            x, y = transform_to_svg(fs, bl, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
            points.append(f"{x:.1f},{y:.1f}")
        svg_lines.append(f'    <polyline points="{" ".join(points)}"/>')
    svg_lines.append('  </g>')

    # Wire labels
    svg_lines.append('  <g id="wire-labels" font-family="Arial" font-size="10" fill="black" text-anchor="middle">')
    for segment in diagram.wire_segments:
        path = segment.manhattan_path
        label_fs, label_bl = calculate_wire_label_position(path)
        x, y = transform_to_svg(label_fs, label_bl, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
        svg_lines.append(f'    <text x="{x:.1f}" y="{y:.1f}" dx="8" dy="-3">{segment.label}</text>')
    svg_lines.append('  </g>')

    # Component markers (blue circles)
    svg_lines.append('  <g id="components">')
    for comp in diagram.components:
        x, y = transform_to_svg(comp.fs, comp.bl, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
        svg_lines.append(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="blue" stroke="navy" stroke-width="1"/>')
    svg_lines.append('  </g>')

    # Component labels
    svg_lines.append('  <g id="component-labels" font-family="Arial" font-size="10" fill="navy" text-anchor="middle">')
    for comp in diagram.components:
        x, y = transform_to_svg(comp.fs, comp.bl, diagram.fs_min, diagram.fs_max, diagram.bl_min, scale, MARGIN)
        svg_lines.append(f'    <text x="{x:.1f}" y="{y:.1f}" dy="15">{comp.ref}</text>')
    svg_lines.append('  </g>')

    # Title
    svg_lines.append('  <g id="title" font-family="Arial">')
    svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="30" font-size="16" font-weight="bold" text-anchor="middle">System {diagram.system_code} Routing Diagram</text>')
    svg_lines.append(f'    <text x="{svg_width/2:.1f}" y="45" font-size="10" text-anchor="middle">Scale: {scale:.1f} px/inch | FS: {diagram.fs_min:.0f}"-{diagram.fs_max:.0f}" | BL: {diagram.bl_min:.0f}"-{diagram.bl_max:.0f}"</text>')
    svg_lines.append('  </g>')

    svg_lines.append('</svg>')

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_lines))


def generate_routing_diagrams(wire_connections: List, components: Dict, output_dir: Path) -> None:
    """
    Generate routing diagram SVG files for all systems.

    Args:
        wire_connections: All wire connections from BOM
        components: Dict mapping component ref to Component object
        output_dir: Directory to write SVG files

    Outputs:
        One SVG file per system code (L_routing.svg, P_routing.svg, etc.)
    """
    # Group wires by system
    system_groups = group_wires_by_system(wire_connections)

    # Generate one diagram per system
    for system_code, wires in system_groups.items():
        # Build diagram data structure
        diagram = build_system_diagram(system_code, wires, components)

        # Generate SVG
        output_path = output_dir / f"{system_code}_routing.svg"
        generate_svg(diagram, output_path)

        print(f"Generated {output_path}")
