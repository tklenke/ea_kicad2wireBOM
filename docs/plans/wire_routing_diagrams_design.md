# Wire Routing Diagrams Design Specification

**Version**: 1.0
**Status**: Design Phase
**Last Updated**: 2025-10-25

---

## 1. Overview

Generate visual wire routing diagrams showing Manhattan-routed wire paths on 2D top-down views (FS vs BL coordinates). One diagram per system code, with component positions and wire segment labels.

### 1.1 Motivation

- Visual verification of wire routing before physical installation
- Documentation for build and maintenance
- Sanity check for component placement and wire lengths
- Foundation for future 3D routing visualization

### 1.2 Key Design Decisions

- **Output Format**: SVG (Scalable Vector Graphics)
  - No additional dependencies required
  - Opens in any web browser
  - Scalable without quality loss
  - Easy to generate with Python string templates
  - Can embed in documentation

- **Coordinate System**: 2D top-down view (FS horizontal, BL vertical)
  - X-axis = FS (Fuselage Station) - increases right (forward)
  - Y-axis = BL (Butt Line) - increases up (right side of aircraft)
  - WL (Water Line) ignored in 2D view (reserved for future 3D)

- **Routing Algorithm**: Manhattan routing (orthogonal)
  - First segment: parallel to BL axis (vertical line)
  - Second segment: parallel to FS axis (horizontal line)
  - Matches current length calculation algorithm

---

## 2. Requirements

### 2.1 Functional Requirements

**FR-1**: Generate one SVG diagram per system code (L, P, G, R, etc.)
**FR-2**: Show component positions as labeled markers
**FR-3**: Draw wire segments as Manhattan-routed paths (BL-axis first, then FS-axis)
**FR-4**: Label wire segments along path (e.g., "L1A", "P3B")
**FR-5**: Auto-scale diagram to fit all components with margins
**FR-6**: Include grid lines for coordinate reference
**FR-7**: Include legend showing scale and coordinate system

### 2.2 Non-Functional Requirements

**NFR-1**: Generate diagrams without additional Python dependencies
**NFR-2**: SVG files viewable in standard web browsers
**NFR-3**: Diagrams legible when printed on standard paper
**NFR-4**: Processing time < 1 second per diagram

### 2.3 Future Enhancements (Out of Scope for v1)

- 3D visualization (add WL dimension)
- Interactive HTML with zoom/pan
- Color coding by wire gauge or current
- Export to PDF or PNG
- Component symbols (boxes, circles, icons)
- Connector pin diagrams

---

## 3. CLI Interface

### 3.1 New Command-Line Flag

```bash
python -m kicad2wireBOM input.kicad_sch --routing-diagrams [output_dir]
```

**Arguments**:
- `--routing-diagrams` (optional): Enable routing diagram generation
- `output_dir` (optional): Directory for SVG files (default: same as CSV output)

**Behavior**:
- If flag not provided: No diagrams generated (backward compatible)
- If flag provided without directory: Use same directory as CSV output
- If flag provided with directory: Create directory if needed, write SVG files there

**Output Files** (one per system code):
- `L_routing.svg` - Lighting system
- `P_routing.svg` - Power system
- `G_routing.svg` - Ground system
- `R_routing.svg` - Radio system
- etc.

### 3.2 Example Usage

```bash
# Generate BOM and routing diagrams in same directory
python -m kicad2wireBOM schematic.kicad_sch --routing-diagrams

# Generate routing diagrams in specific directory
python -m kicad2wireBOM schematic.kicad_sch --routing-diagrams ./diagrams/

# Generate only BOM (no diagrams) - default behavior
python -m kicad2wireBOM schematic.kicad_sch
```

---

## 4. Data Model

### 4.1 Input Data (Already Available)

From existing `WireConnection` objects:
- `label`: Wire segment ID (e.g., "L1A")
- `comp1_ref`, `comp1_fs`, `comp1_bl`, `comp1_wl`: Component 1 data
- `comp2_ref`, `comp2_fs`, `comp2_bl`, `comp2_wl`: Component 2 data
- `length`: Calculated wire length

From existing parsing:
- `system_code`: Extracted from label (e.g., "L" from "L1A")

### 4.2 Intermediate Data Structures

```python
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
        """
        return [
            (self.comp1.fs, self.comp1.bl),           # Start point
            (self.comp1.fs, self.comp2.bl),           # Corner (BL-axis move)
            (self.comp2.fs, self.comp2.bl),           # End point (FS-axis move)
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
```

---

## 5. Algorithm Design

### 5.1 Diagram Generation Pipeline

```
Input: List[WireConnection] from BOM generation
  ↓
Step 1: Group wires by system_code
  ↓
Step 2: For each system, create SystemDiagram
  ↓
Step 3: Calculate bounds (min/max FS and BL)
  ↓
Step 4: Generate SVG with auto-scaling
  ↓
Step 5: Write SVG file
  ↓
Output: One SVG file per system code
```

### 5.2 Grouping Algorithm

```python
def group_wires_by_system(wire_connections: List[WireConnection]) -> Dict[str, List[WireConnection]]:
    """
    Group wire connections by system code.

    Args:
        wire_connections: All wire connections from BOM

    Returns:
        Dict mapping system_code to list of WireConnections
        Example: {'L': [L1A, L1B, L2A], 'P': [P1A, P2A], 'G': [G1A]}
    """
    system_groups = defaultdict(list)

    for wire in wire_connections:
        # Parse system code from label (e.g., "L" from "L1A")
        parsed = parse_net_name(wire.label)
        if parsed and parsed.system_code:
            system_groups[parsed.system_code].append(wire)

    return dict(system_groups)
```

### 5.3 Bounds Calculation

```python
def calculate_bounds(components: List[DiagramComponent]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for all components.

    Returns:
        (fs_min, fs_max, bl_min, bl_max)
    """
    fs_values = [c.fs for c in components]
    bl_values = [c.bl for c in components]

    return (min(fs_values), max(fs_values), min(bl_values), max(bl_values))
```

### 5.4 Coordinate Transformation

SVG coordinate system has origin at top-left, Y increases downward.
Aircraft coordinates have origin at datum, BL increases right (starboard).

Transform aircraft coords → SVG coords:
```python
def transform_to_svg(fs: float, bl: float,
                     fs_min: float, bl_min: float,
                     scale: float, margin: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG coordinates.

    Args:
        fs, bl: Aircraft coordinates
        fs_min, bl_min: Minimum aircraft coordinates (for offset)
        scale: Pixels per inch
        margin: Margin in SVG pixels

    Returns:
        (svg_x, svg_y) in SVG coordinate space
    """
    # Offset to make all coordinates positive, add margin
    svg_x = (fs - fs_min) * scale + margin

    # Flip Y-axis (SVG Y increases down, BL increases up)
    svg_y = -(bl - bl_min) * scale + margin

    # Note: Additional vertical offset needed to account for max BL
    # This is handled in the SVG generator by calculating total height

    return (svg_x, svg_y)
```

---

## 6. SVG Generation

### 6.1 SVG Structure

```xml
<svg width="[calc]" height="[calc]" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect fill="white" width="100%" height="100%"/>

  <!-- Grid lines (light gray) -->
  <g id="grid" stroke="#e0e0e0" stroke-width="0.5">
    <!-- Vertical grid lines (FS axis) -->
    <line x1="..." y1="..." x2="..." y2="..."/>
    ...
    <!-- Horizontal grid lines (BL axis) -->
    <line x1="..." y1="..." x2="..." y2="..."/>
    ...
  </g>

  <!-- Axes (darker gray) -->
  <g id="axes" stroke="#808080" stroke-width="1">
    <line x1="..." y1="..." x2="..." y2="..."/> <!-- FS axis -->
    <line x1="..." y1="..." x2="..." y2="..."/> <!-- BL axis -->
  </g>

  <!-- Wire segments (black lines) -->
  <g id="wires" stroke="black" stroke-width="2" fill="none">
    <polyline points="x1,y1 x2,y2 x3,y3"/> <!-- Manhattan path -->
    ...
  </g>

  <!-- Wire labels (black text) -->
  <g id="wire-labels" font-family="Arial" font-size="12" fill="black">
    <text x="..." y="...">L1A</text>
    ...
  </g>

  <!-- Component markers (blue circles) -->
  <g id="components" fill="blue" stroke="navy" stroke-width="1">
    <circle cx="..." cy="..." r="4"/>
    ...
  </g>

  <!-- Component labels (navy text) -->
  <g id="component-labels" font-family="Arial" font-size="10" fill="navy">
    <text x="..." y="...">CB1</text>
    ...
  </g>

  <!-- Title and legend -->
  <g id="title" font-family="Arial" font-size="16" font-weight="bold">
    <text x="10" y="20">System [X] Routing Diagram</text>
  </g>

  <g id="legend" font-family="Arial" font-size="10">
    <text x="10" y="40">Scale: [X] px/inch</text>
    <text x="10" y="55">Coordinates: FS (horizontal) × BL (vertical)</text>
  </g>
</svg>
```

### 6.2 Styling Constants

```python
# SVG dimensions and scaling
MARGIN = 50          # pixels around edge
MIN_SCALE = 2.0      # minimum pixels per inch
MAX_SCALE = 10.0     # maximum pixels per inch
TARGET_WIDTH = 800   # target diagram width in pixels

# Visual style
GRID_SPACING = 12    # inches between grid lines
GRID_COLOR = "#e0e0e0"
GRID_WIDTH = 0.5

AXIS_COLOR = "#808080"
AXIS_WIDTH = 1.0

WIRE_COLOR = "black"
WIRE_WIDTH = 2.0

COMPONENT_COLOR = "blue"
COMPONENT_STROKE = "navy"
COMPONENT_RADIUS = 4  # pixels

LABEL_FONT = "Arial"
LABEL_SIZE = 10       # points
WIRE_LABEL_SIZE = 12  # points
TITLE_SIZE = 16       # points
```

### 6.3 Wire Label Placement

Place wire label at midpoint of longer segment:

```python
def calculate_wire_label_position(path: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate position for wire segment label.

    Places label at midpoint of longer segment in Manhattan path.

    Args:
        path: [(fs1, bl1), (fs2, bl2), (fs3, bl3)] - 3-point Manhattan path

    Returns:
        (fs, bl) - position for label
    """
    # Path is always 3 points: start, corner, end
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
```

---

## 7. Implementation Plan

### 7.1 Module Structure

Create new module: `kicad2wireBOM/diagram_generator.py`

```python
# ABOUTME: SVG routing diagram generation for wire BOMs
# ABOUTME: Creates 2D top-down view (FS×BL) with Manhattan-routed wires

from dataclasses import dataclass
from typing import List, Dict, Tuple
from pathlib import Path

# Data structures (Section 4.2)
@dataclass
class DiagramComponent:
    ...

@dataclass
class DiagramWireSegment:
    ...

@dataclass
class SystemDiagram:
    ...

# Diagram generation functions
def group_wires_by_system(wire_connections: List[WireConnection]) -> Dict[str, List[WireConnection]]:
    """Group wire connections by system code."""
    ...

def build_system_diagram(system_code: str, wires: List[WireConnection]) -> SystemDiagram:
    """Build diagram data structure for one system."""
    ...

def calculate_bounds(components: List[DiagramComponent]) -> Tuple[float, float, float, float]:
    """Calculate bounding box for auto-scaling."""
    ...

def calculate_scale(fs_range: float, bl_range: float, target_width: int = 800) -> float:
    """Calculate appropriate scale factor (pixels per inch)."""
    ...

def generate_svg(diagram: SystemDiagram, output_path: Path) -> None:
    """Generate SVG file for system diagram."""
    ...

# Main entry point
def generate_routing_diagrams(wire_connections: List[WireConnection], output_dir: Path) -> None:
    """
    Generate routing diagram SVG files for all systems.

    Args:
        wire_connections: All wire connections from BOM
        output_dir: Directory to write SVG files
    """
    ...
```

### 7.2 Integration with Main CLI

Modify `kicad2wireBOM/__main__.py`:

```python
# Add argument parser option
parser.add_argument(
    '--routing-diagrams',
    nargs='?',
    const='',  # Use empty string if flag provided without argument
    metavar='OUTPUT_DIR',
    help='Generate routing diagram SVG files (optional: specify output directory)'
)

# After generating wire_connections list (around line 320):
if args.routing_diagrams is not None:
    from kicad2wireBOM.diagram_generator import generate_routing_diagrams

    # Determine output directory
    if args.routing_diagrams:
        diagram_dir = Path(args.routing_diagrams)
    else:
        # Use same directory as CSV output
        diagram_dir = Path(args.output).parent if args.output else Path.cwd()

    # Generate diagrams
    generate_routing_diagrams(wire_connections, diagram_dir)
    print(f"Routing diagrams written to {diagram_dir}/")
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test File**: `tests/test_diagram_generator.py`

Test cases:
1. `test_group_wires_by_system()` - Verify grouping logic
2. `test_build_system_diagram()` - Verify diagram data structure creation
3. `test_calculate_bounds()` - Verify bounding box calculation
4. `test_calculate_scale()` - Verify scale factor calculation
5. `test_manhattan_path()` - Verify Manhattan routing path generation
6. `test_wire_label_placement()` - Verify label position calculation
7. `test_coordinate_transformation()` - Verify aircraft → SVG coordinate transform

### 8.2 Integration Tests

**Test File**: `tests/test_integration_diagrams.py`

Test cases:
1. `test_generate_diagram_from_test_01()` - Simple 2-component circuit
2. `test_generate_diagram_from_test_03A()` - 3-way multipoint circuit
3. `test_generate_diagram_from_test_07()` - Full system with multiple circuits
4. `test_multiple_systems()` - Verify one SVG per system code
5. `test_svg_validity()` - Parse generated SVG, verify well-formed XML

### 8.3 Visual Validation Tests

Create test fixtures with known coordinates, generate SVGs, manually verify:
- Component positions correct
- Wire routing follows Manhattan paths (BL first, then FS)
- Labels legible and positioned correctly
- Grid and axes display correctly
- Auto-scaling works for various coordinate ranges

### 8.4 Test Fixtures

Reuse existing fixtures:
- `test_01_fixture.kicad_sch` - Simple circuit, verify basic diagram
- `test_03A_fixture.kicad_sch` - Multipoint, verify multiple wires
- `test_07_fixture.kicad_sch` - Multiple systems, verify separate SVGs

Add new fixture for diagram testing:
- `test_08_diagram_fixture.kicad_sch` - Designed for visual clarity:
  - Components at nice round coordinates (0,0), (100,0), (100,50), etc.
  - Multiple systems (L, P, G)
  - Clear Manhattan routing patterns
  - Mix of short and long wire runs

---

## 9. Example Output

### 9.1 Example SVG (Simplified)

For circuit: CB1 @ (10, 30) → SW1 @ (50, 10), wire label "L1A"

```xml
<svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect fill="white" width="100%" height="100%"/>

  <!-- Wire L1A: Manhattan path -->
  <polyline points="70,130 70,170 250,170"
            stroke="black" stroke-width="2" fill="none"/>

  <!-- Wire label -->
  <text x="70" y="150" font-family="Arial" font-size="12">L1A</text>

  <!-- Component CB1 -->
  <circle cx="70" cy="130" r="4" fill="blue" stroke="navy"/>
  <text x="75" y="135" font-family="Arial" font-size="10" fill="navy">CB1</text>

  <!-- Component SW1 -->
  <circle cx="250" cy="170" r="4" fill="blue" stroke="navy"/>
  <text x="255" y="175" font-family="Arial" font-size="10" fill="navy">SW1</text>

  <!-- Title -->
  <text x="10" y="20" font-family="Arial" font-size="16" font-weight="bold">
    System L Routing Diagram
  </text>
</svg>
```

### 9.2 Expected File Output

After running:
```bash
python -m kicad2wireBOM test_07_fixture.kicad_sch --routing-diagrams ./diagrams/
```

Output files:
```
diagrams/
  L_routing.svg   # Lighting circuits (L1, L2, L3)
  G_routing.svg   # Ground returns (G1, G2, G3, G4)
  P_routing.svg   # Power distribution (P1)
```

Each SVG opens in browser and shows:
- All components in that system
- All wire segments with Manhattan routing
- Grid for coordinate reference
- Auto-scaled to fit

---

## 10. Open Questions

**Q1**: Should wire segments be color-coded by gauge or current?
- **Decision**: Not in v1. Keep all wires black for simplicity. Add as future enhancement.

**Q2**: Should we show wire length on the label?
- **Decision**: Not in v1. Label shows wire ID only (e.g., "L1A"). Length is in BOM.

**Q3**: Handle overlapping wire segments?
- **Decision**: Not in v1. Future enhancement could offset parallel wires slightly.

**Q4**: Grid spacing for very large or very small aircraft?
- **Decision**: Fixed 12-inch grid for v1. Auto-adjust grid spacing in future based on coordinate range.

**Q5**: Should components have different symbols (circle for loads, square for switches, etc.)?
- **Decision**: Not in v1. All components use same marker (circle). Add component symbols as future enhancement.

---

## 11. Future Enhancements

See `docs/notes/opportunities_for_improvement.md` for complete list. Key items:

1. **3D Visualization**: Add WL dimension, generate isometric or interactive 3D view
2. **Color Coding**: Color wires by gauge, current, or circuit
3. **Component Symbols**: Different shapes for different component types
4. **Interactive HTML**: Zoom, pan, click for details
5. **PDF Export**: Generate print-ready PDFs
6. **Wire Offset**: Prevent overlapping parallel wire segments
7. **Auto Grid Spacing**: Adjust grid based on coordinate range
8. **Length Annotations**: Show calculated wire length on diagram

---

## 12. Dependencies

**No new dependencies required.**

Uses only Python standard library:
- `dataclasses` - Data structures
- `pathlib` - File path handling
- `typing` - Type hints
- String templates for SVG generation

---

## 13. Deliverables

1. **Code**:
   - `kicad2wireBOM/diagram_generator.py` - New module (350-400 lines estimated)
   - `kicad2wireBOM/__main__.py` - Modified to add CLI flag and call diagram generator

2. **Tests**:
   - `tests/test_diagram_generator.py` - Unit tests (200-250 lines estimated)
   - `tests/test_integration_diagrams.py` - Integration tests (100-150 lines estimated)
   - `tests/fixtures/test_08_diagram_fixture.kicad_sch` - New test fixture

3. **Documentation**:
   - This design document
   - Updated `programmer_todo.md` with implementation tasks
   - Reference in `kicad2wireBOM_design.md`

---

## 14. Acceptance Criteria

Feature is complete when:

1. ✅ CLI flag `--routing-diagrams` implemented
2. ✅ One SVG generated per system code
3. ✅ Components shown at correct (FS, BL) positions
4. ✅ Wires drawn with Manhattan routing (BL-axis first, FS-axis second)
5. ✅ Component labels visible and positioned correctly
6. ✅ Wire segment labels visible along paths
7. ✅ Grid lines and axes display correctly
8. ✅ Auto-scaling works for various coordinate ranges
9. ✅ SVGs open correctly in standard web browsers
10. ✅ All unit tests pass
11. ✅ All integration tests pass
12. ✅ Generated SVGs visually validated against test fixtures

---

**Document Status**: Ready for Programmer Implementation
