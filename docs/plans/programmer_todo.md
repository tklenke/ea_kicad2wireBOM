# Programmer TODO: kicad2wireBOM

**Status**: Phase 10 Implementation - Wire Routing Diagrams
**Design**: `docs/plans/wire_routing_diagrams_design.md` v1.0
**Last Updated**: 2025-10-25

---

## CURRENT STATUS

✅ **196/196 tests passing** - Core features complete
🚧 **Phase 10: Wire Routing Diagrams** - Ready to implement

---

## WORKFLOW REMINDERS

**TDD Cycle** (Follow strictly):
1. **RED**: Write failing test
2. **Verify**: Run test, confirm it fails correctly
3. **GREEN**: Write minimal code to pass test
4. **Verify**: Run test, confirm it passes
5. **REFACTOR**: Clean up while keeping tests green
6. **COMMIT**: Commit with updated todo

**Pre-Commit Checklist**:
1. Update this programmer_todo.md with completed tasks
2. Run full test suite (`pytest -v`)
3. Include updated todo in commit

**Circle K Protocol**: If blocked or confused, say "Strange things are afoot at the Circle K"

---

## PHASE 10: SVG ROUTING DIAGRAMS

### Overview

Implement SVG routing diagram generation showing 2D top-down view of wire routing with Manhattan paths. One diagram per system code (L, P, G, etc.).

**Key Files**:
- **New**: `kicad2wireBOM/diagram_generator.py` (~400 lines)
- **Modified**: `kicad2wireBOM/__main__.py` (add CLI flag and integration)
- **New Tests**: `tests/test_diagram_generator.py` (~250 lines)
- **New Tests**: `tests/test_integration_diagrams.py` (~150 lines)
- **New Fixture**: `tests/fixtures/test_08_diagram_fixture.kicad_sch`

**Estimated Total**: ~800 lines code + tests

---

### Task 10.1: Create Data Structures

**File**: `kicad2wireBOM/diagram_generator.py` (new file)
**Status**: [ ]

Create module with ABOUTME comments and core data structures:

```python
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
```

**TDD Steps**:
1. Create test file `tests/test_diagram_generator.py`
2. Write test: `test_diagram_component_creation()`
3. Write test: `test_manhattan_path_calculation()`
   - Test case 1: comp1=(10, 30), comp2=(50, 10) → path [(10,30), (10,10), (50,10)]
   - Test case 2: comp1=(0, 0), comp2=(100, 50) → path [(0,0), (0,50), (100,50)]
4. Verify tests fail
5. Implement data structures
6. Verify tests pass
7. Commit

**Acceptance Criteria**:
- [ ] DiagramComponent stores ref, fs, bl
- [ ] DiagramWireSegment stores label, comp1, comp2
- [ ] manhattan_path property returns 3-point BL-first path
- [ ] SystemDiagram stores system_code, components, wires, bounds
- [ ] Tests pass

---

### Task 10.2: Implement Wire Grouping by System

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to group wires by system code:

```python
def group_wires_by_system(wire_connections: List[WireConnection]) -> Dict[str, List[WireConnection]]:
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
    from collections import defaultdict
    from kicad2wireBOM.net_parser import parse_net_name

    system_groups = defaultdict(list)

    for wire in wire_connections:
        parsed = parse_net_name(wire.label)
        if parsed and parsed.system_code:
            system_groups[parsed.system_code].append(wire)

    return dict(system_groups)
```

**TDD Steps**:
1. Write test: `test_group_wires_by_system()`
   - Create mock WireConnections: L1A, L1B, L2A, P1A, G1A
   - Expected groups: {'L': [L1A, L1B, L2A], 'P': [P1A], 'G': [G1A]}
2. Write test: `test_group_wires_skips_unparseable()`
   - Include wire with unparseable label (e.g., "INVALID")
   - Verify it's not in any group
3. Verify tests fail
4. Implement function
5. Verify tests pass
6. Commit

**Acceptance Criteria**:
- [ ] Groups wires correctly by system code
- [ ] Returns dict with system_code keys
- [ ] Skips wires with no parseable system code
- [ ] Tests pass

---

### Task 10.3: Implement Bounds Calculation

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to calculate bounding box:

```python
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
```

**TDD Steps**:
1. Write test: `test_calculate_bounds_normal()`
   - Components at (0, 0), (100, 50), (50, 25)
   - Expected: (0, 100, 0, 50)
2. Write test: `test_calculate_bounds_negative_coords()`
   - Components at (-10, -20), (30, 40)
   - Expected: (-10, 30, -20, 40)
3. Write test: `test_calculate_bounds_empty_raises()`
   - Empty list raises ValueError
4. Verify tests fail
5. Implement function
6. Verify tests pass
7. Commit

**Acceptance Criteria**:
- [ ] Returns correct (fs_min, fs_max, bl_min, bl_max)
- [ ] Handles negative coordinates
- [ ] Raises ValueError for empty list
- [ ] Tests pass

---

### Task 10.4: Implement Scale Calculation

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to calculate appropriate scale:

```python
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
```

**TDD Steps**:
1. Write test: `test_calculate_scale_normal()`
   - Range 100 inches, target 800px, margin 50px → scale = (800-100)/100 = 7.0
2. Write test: `test_calculate_scale_large_range()`
   - Range 500 inches → scale clamped to MIN_SCALE (2.0)
3. Write test: `test_calculate_scale_small_range()`
   - Range 10 inches → scale clamped to MAX_SCALE (10.0)
4. Write test: `test_calculate_scale_zero_range()`
   - Range 0 (single point) → returns MIN_SCALE
5. Verify tests fail
6. Implement function
7. Verify tests pass
8. Commit

**Acceptance Criteria**:
- [ ] Calculates scale to fit within target width
- [ ] Clamps to MIN_SCALE (2.0) and MAX_SCALE (10.0)
- [ ] Handles zero range (single point)
- [ ] Tests pass

---

### Task 10.5: Implement Coordinate Transformation

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to transform aircraft coordinates to SVG coordinates:

```python
def transform_to_svg(fs: float, bl: float,
                     fs_min: float, bl_min: float, bl_max: float,
                     scale: float, margin: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG coordinates.

    Aircraft coords: FS increases forward (right), BL increases starboard (up)
    SVG coords: X increases right, Y increases down

    Args:
        fs, bl: Aircraft coordinates (inches)
        fs_min: Minimum FS in diagram (for offset)
        bl_min: Minimum BL in diagram (for offset)
        bl_max: Maximum BL in diagram (for Y-axis flip)
        scale: Pixels per inch
        margin: Margin in pixels

    Returns:
        (svg_x, svg_y) in SVG pixel coordinates
    """
    # X: Offset to make all FS positive, scale, add margin
    svg_x = (fs - fs_min) * scale + margin

    # Y: Flip axis (BL up → SVG down), offset, scale, add margin
    svg_y = (bl_max - bl) * scale + margin

    return (svg_x, svg_y)
```

**TDD Steps**:
1. Write test: `test_transform_to_svg_origin()`
   - Transform (0, 0) with bounds (0, 100, 0, 50), scale=2, margin=10
   - Expected: (10, 110)  # X=0*2+10=10, Y=(50-0)*2+10=110
2. Write test: `test_transform_to_svg_max_coords()`
   - Transform (100, 50) with same bounds
   - Expected: (210, 10)  # X=100*2+10=210, Y=(50-50)*2+10=10
3. Write test: `test_transform_to_svg_negative_coords()`
   - Transform (-10, -20) with bounds (-10, 30, -20, 40), scale=2, margin=10
   - Expected: (10, 130)
4. Verify tests fail
5. Implement function
6. Verify tests pass
7. Commit

**Acceptance Criteria**:
- [ ] Transforms FS correctly (offset, scale, margin)
- [ ] Flips BL axis correctly (aircraft up = SVG down)
- [ ] Handles negative coordinates
- [ ] Tests pass

---

### Task 10.6: Implement Wire Label Position Calculation

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to calculate wire label position:

```python
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
```

**TDD Steps**:
1. Write test: `test_label_position_longer_vertical()`
   - Path: [(10, 30), (10, 10), (50, 10)]
   - Vertical segment: 20 inches, Horizontal segment: 40 inches
   - Expected: (30, 10)  # Midpoint of horizontal (longer)
2. Write test: `test_label_position_longer_horizontal()`
   - Path: [(10, 30), (10, 5), (20, 5)]
   - Vertical segment: 25 inches, Horizontal segment: 10 inches
   - Expected: (10, 17.5)  # Midpoint of vertical (longer)
3. Write test: `test_label_position_invalid_path()`
   - Path with 2 points raises ValueError
4. Verify tests fail
5. Implement function
6. Verify tests pass
7. Commit

**Acceptance Criteria**:
- [ ] Returns midpoint of longer segment
- [ ] Handles both vertical-longer and horizontal-longer cases
- [ ] Raises ValueError for invalid path length
- [ ] Tests pass

---

### Task 10.7: Implement System Diagram Builder

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add function to build SystemDiagram from WireConnections:

```python
def build_system_diagram(system_code: str, wires: List[WireConnection]) -> SystemDiagram:
    """
    Build diagram data structure for one system.

    Args:
        system_code: System code (e.g., "L", "P", "G")
        wires: All wire connections for this system

    Returns:
        SystemDiagram with components, wire segments, and bounds
    """
    # Extract unique components from all wires
    component_dict = {}  # {ref: DiagramComponent}

    for wire in wires:
        # Add comp1 if not already present
        if wire.comp1_ref not in component_dict:
            component_dict[wire.comp1_ref] = DiagramComponent(
                ref=wire.comp1_ref,
                fs=wire.comp1_fs,
                bl=wire.comp1_bl
            )

        # Add comp2 if not already present
        if wire.comp2_ref not in component_dict:
            component_dict[wire.comp2_ref] = DiagramComponent(
                ref=wire.comp2_ref,
                fs=wire.comp2_fs,
                bl=wire.comp2_bl
            )

    components = list(component_dict.values())

    # Build wire segments
    wire_segments = []
    for wire in wires:
        segment = DiagramWireSegment(
            label=wire.label,
            comp1=component_dict[wire.comp1_ref],
            comp2=component_dict[wire.comp2_ref]
        )
        wire_segments.append(segment)

    # Calculate bounds
    fs_min, fs_max, bl_min, bl_max = calculate_bounds(components)

    return SystemDiagram(
        system_code=system_code,
        components=components,
        wire_segments=wire_segments,
        fs_min=fs_min,
        fs_max=fs_max,
        bl_min=bl_min,
        bl_max=bl_max
    )
```

**TDD Steps**:
1. Write test: `test_build_system_diagram_single_wire()`
   - One wire L1A: CB1(10,20) → SW1(50,30)
   - Expected: 2 components, 1 wire segment, bounds (10,50,20,30)
2. Write test: `test_build_system_diagram_multiple_wires()`
   - Three wires L1A, L1B, L2A with shared components
   - Verify unique components extracted
   - Verify all wire segments present
3. Verify tests fail
4. Implement function
5. Verify tests pass
6. Commit

**Acceptance Criteria**:
- [ ] Extracts unique components from wires
- [ ] Creates DiagramWireSegment for each wire
- [ ] Calculates bounds correctly
- [ ] Returns complete SystemDiagram
- [ ] Tests pass

---

### Task 10.8: Implement SVG Generation Core

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add core SVG generation function (foundation):

```python
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

    # Calculate SVG dimensions
    svg_width = fs_range * scale + 2 * MARGIN
    svg_height = bl_range * scale + 2 * MARGIN

    # Start building SVG
    svg_lines = []
    svg_lines.append(f'<svg width="{svg_width:.0f}" height="{svg_height:.0f}" xmlns="http://www.w3.org/2000/svg">')

    # Background
    svg_lines.append('  <rect fill="white" width="100%" height="100%"/>')

    # TODO: Grid lines (Task 10.9)
    # TODO: Wire segments (Task 10.10)
    # TODO: Component markers (Task 10.11)
    # TODO: Labels and title (Task 10.12)

    svg_lines.append('</svg>')

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_lines))
```

**TDD Steps**:
1. Write test: `test_generate_svg_creates_file()`
   - Generate SVG for simple diagram
   - Verify file created
   - Verify file contains valid SVG opening tag
2. Write test: `test_generate_svg_dimensions()`
   - Verify SVG width/height calculated correctly
3. Verify tests fail
4. Implement basic SVG generation (background only)
5. Verify tests pass
6. Commit

**Acceptance Criteria**:
- [ ] Creates SVG file at output_path
- [ ] SVG has correct dimensions (auto-scaled)
- [ ] SVG contains white background
- [ ] Valid XML structure
- [ ] Tests pass

---

### Task 10.9: Add Grid Lines to SVG

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Enhance `generate_svg()` to add grid lines (replace TODO comment).

**TDD Steps**:
1. Write test: `test_svg_contains_grid()`
   - Parse generated SVG
   - Verify grid group exists
   - Verify grid lines present
2. Verify test fails
3. Implement grid generation (12-inch spacing, light gray)
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] Grid lines at 12-inch intervals
- [ ] Light gray color (#e0e0e0)
- [ ] Covers full diagram area
- [ ] Test passes

---

### Task 10.10: Add Wire Segments to SVG

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Enhance `generate_svg()` to draw wire segments (replace TODO comment).

**TDD Steps**:
1. Write test: `test_svg_contains_wires()`
   - Generate SVG with 2 wire segments
   - Parse SVG and verify 2 polylines exist
   - Verify polylines have 3 points each (Manhattan routing)
2. Verify test fails
3. Implement wire rendering (black polylines with Manhattan paths)
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] All wire segments drawn as polylines
- [ ] Manhattan routing (3 points: start, corner, end)
- [ ] Black stroke, width 2
- [ ] Test passes

---

### Task 10.11: Add Component Markers to SVG

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Enhance `generate_svg()` to add component markers (replace TODO comment).

**TDD Steps**:
1. Write test: `test_svg_contains_components()`
   - Generate SVG with 3 components
   - Parse SVG and verify 3 circles exist
   - Verify circles at correct positions
2. Verify test fails
3. Implement component markers (blue circles)
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] One circle per component
- [ ] Blue fill, navy stroke
- [ ] Radius 4 pixels
- [ ] Positioned correctly
- [ ] Test passes

---

### Task 10.12: Add Labels and Title to SVG

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Enhance `generate_svg()` to add all text labels (replace TODO comment).

**TDD Steps**:
1. Write test: `test_svg_contains_labels()`
   - Generate SVG
   - Verify wire labels present
   - Verify component labels present
   - Verify title contains system code
2. Verify test fails
3. Implement all labels (wire labels, component labels, title, legend)
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] Wire labels at calculated positions
- [ ] Component labels offset from markers
- [ ] Title shows system code
- [ ] Legend shows scale and coordinate info
- [ ] Test passes

---

### Task 10.13: Implement Main Entry Point

**File**: `kicad2wireBOM/diagram_generator.py`
**Status**: [ ]

Add main function to orchestrate diagram generation:

```python
def generate_routing_diagrams(wire_connections: List[WireConnection],
                              output_dir: Path) -> None:
    """
    Generate routing diagram SVG files for all systems.

    Args:
        wire_connections: All wire connections from BOM
        output_dir: Directory to write SVG files

    Outputs:
        One SVG file per system code (L_routing.svg, P_routing.svg, etc.)
    """
    # Group wires by system
    system_groups = group_wires_by_system(wire_connections)

    # Generate one diagram per system
    for system_code, wires in system_groups.items():
        # Build diagram data structure
        diagram = build_system_diagram(system_code, wires)

        # Generate SVG
        output_path = output_dir / f"{system_code}_routing.svg"
        generate_svg(diagram, output_path)

        print(f"Generated {output_path}")
```

**TDD Steps**:
1. Write integration test: `test_generate_routing_diagrams()` (in test_integration_diagrams.py)
   - Create mock wire connections for multiple systems (L, P, G)
   - Call generate_routing_diagrams()
   - Verify 3 SVG files created: L_routing.svg, P_routing.svg, G_routing.svg
2. Verify test fails
3. Implement main function
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] Generates one SVG per system
- [ ] Files named correctly (e.g., L_routing.svg)
- [ ] Creates output directory if needed
- [ ] Prints generation confirmation
- [ ] Integration test passes

---

### Task 10.14: Add CLI Flag to Main

**File**: `kicad2wireBOM/__main__.py`
**Status**: [ ]

Add `--routing-diagrams` flag to argument parser:

```python
# Add to argument parser (around line 50)
parser.add_argument(
    '--routing-diagrams',
    nargs='?',
    const='',  # Use empty string if flag provided without argument
    metavar='OUTPUT_DIR',
    help='Generate routing diagram SVG files (optional: specify output directory)'
)
```

**TDD Steps**:
1. Write test: `test_cli_routing_diagrams_flag()` (in test_integration_diagrams.py)
   - Run CLI with --routing-diagrams flag
   - Verify CLI accepts flag
2. Verify test fails
3. Add argument parser flag
4. Verify test passes
5. Commit

**Acceptance Criteria**:
- [ ] CLI accepts --routing-diagrams flag
- [ ] Flag accepts optional directory argument
- [ ] Test passes

---

### Task 10.15: Integrate Diagram Generation into Main

**File**: `kicad2wireBOM/__main__.py`
**Status**: [ ]

Call diagram generator when flag provided (add after wire_connections generated, around line 320):

```python
# Generate routing diagrams if requested
if args.routing_diagrams is not None:
    from kicad2wireBOM.diagram_generator import generate_routing_diagrams

    # Determine output directory
    if args.routing_diagrams:
        # User provided explicit directory
        diagram_dir = Path(args.routing_diagrams)
    else:
        # Use same directory as CSV output
        if args.output:
            diagram_dir = Path(args.output).parent
        else:
            diagram_dir = Path.cwd()

    # Generate diagrams
    generate_routing_diagrams(wire_connections, diagram_dir)
```

**TDD Steps**:
1. Enhance test: `test_cli_routing_diagrams_flag()`
   - Verify SVG files actually generated
   - Verify correct output directory used
2. Write test: `test_cli_routing_diagrams_custom_dir()`
   - Run with --routing-diagrams ./custom_dir/
   - Verify SVGs written to custom_dir/
3. Verify tests fail
4. Implement integration
5. Verify tests pass
6. Run full test suite: `pytest -v`
7. Commit

**Acceptance Criteria**:
- [ ] Diagram generation called when flag provided
- [ ] Output directory determined correctly (custom or same as CSV)
- [ ] All integration tests pass
- [ ] Full test suite passes

---

### Task 10.16: Create Test Fixture for Visual Validation

**File**: `tests/fixtures/test_08_diagram_fixture.kicad_sch`
**Status**: [ ]

Create KiCad schematic fixture designed for clear diagram visualization.

**Requirements**:
- Multiple systems (L, P, G)
- Components at nice round coordinates for easy verification
- Mix of short and long wire runs
- Clear Manhattan routing patterns

**Example components**:
```
System L (Lighting):
  CB1 @ (0, 0)
  SW1 @ (0, 50)
  L1 @ (100, 50)
  L2 @ (100, 0)

System P (Power):
  BT1 @ (0, 100)
  BUS1 @ (50, 100)

System G (Ground):
  GND1 @ (75, 75)
```

**TDD Steps**:
1. Create fixture schematic in KiCad
2. Add components with Load/FS/BL fields
3. Connect with wires labeled per EAWMS
4. Export to test_08_diagram_fixture.kicad_sch
5. Write test: `test_diagram_fixture_visual()` (manual verification)
   - Generate SVG from fixture
   - Manually open in browser
   - Verify components at expected positions
   - Verify wire routing follows Manhattan paths
   - Verify labels legible
6. Commit fixture and test

**Acceptance Criteria**:
- [ ] Fixture schematic created
- [ ] Components at round coordinates
- [ ] Multiple systems represented
- [ ] Generated SVG visually correct
- [ ] Test documents visual verification

---

### Task 10.17: End-to-End Integration Test

**File**: `tests/test_integration_diagrams.py`
**Status**: [ ]

Create comprehensive end-to-end test:

```python
def test_end_to_end_diagram_generation():
    """
    End-to-end test: Load fixture, generate BOM, generate diagrams, verify output.

    Uses test_08_diagram_fixture.kicad_sch with known component positions and
    wire segments across multiple systems.
    """
    # Run full BOM generation with diagram flag
    result = subprocess.run([
        'python', '-m', 'kicad2wireBOM',
        'tests/fixtures/test_08_diagram_fixture.kicad_sch',
        '--routing-diagrams', 'tests/output/diagrams/'
    ], capture_output=True, text=True)

    # Verify command succeeded
    assert result.returncode == 0

    # Verify SVG files created
    diagram_dir = Path('tests/output/diagrams')
    assert (diagram_dir / 'L_routing.svg').exists()
    assert (diagram_dir / 'P_routing.svg').exists()
    assert (diagram_dir / 'G_routing.svg').exists()

    # Load and parse one SVG
    svg_content = (diagram_dir / 'L_routing.svg').read_text()

    # Verify SVG structure
    assert '<svg' in svg_content
    assert '</svg>' in svg_content
    assert 'System L Routing Diagram' in svg_content
    assert '<polyline' in svg_content  # Wire segments
    assert '<circle' in svg_content    # Component markers
    assert '<text' in svg_content      # Labels

    # Cleanup
    import shutil
    shutil.rmtree(diagram_dir)
```

**TDD Steps**:
1. Write test as shown above
2. Verify test fails (fixture doesn't exist yet)
3. Complete all previous tasks
4. Create test_08_diagram_fixture.kicad_sch
5. Verify test passes
6. Commit

**Acceptance Criteria**:
- [ ] End-to-end test passes
- [ ] All SVG files generated correctly
- [ ] SVG content validated
- [ ] Full test suite passes: `pytest -v`

---

## IMPLEMENTATION ORDER

Follow this sequence for systematic TDD development:

1. Task 10.1: Data structures (foundation)
2. Task 10.2: Wire grouping (core logic)
3. Task 10.3: Bounds calculation (core logic)
4. Task 10.4: Scale calculation (core logic)
5. Task 10.5: Coordinate transformation (core logic)
6. Task 10.6: Label positioning (core logic)
7. Task 10.7: System diagram builder (integration)
8. Task 10.8: SVG generation core (rendering foundation)
9. Task 10.9: Grid lines (rendering)
10. Task 10.10: Wire segments (rendering)
11. Task 10.11: Component markers (rendering)
12. Task 10.12: Labels and title (rendering)
13. Task 10.13: Main entry point (integration)
14. Task 10.14: CLI flag (CLI integration)
15. Task 10.15: Main integration (CLI integration)
16. Task 10.16: Test fixture (validation)
17. Task 10.17: End-to-end test (validation)

---

## COMMIT STRATEGY

Commit after each task completion:
- Small, focused commits
- Include updated programmer_todo.md in each commit
- Commit message format: "Implement Task 10.X: [description]"

Example:
```
git add kicad2wireBOM/diagram_generator.py tests/test_diagram_generator.py docs/plans/programmer_todo.md
git commit -m "Implement Task 10.1: Data structures for routing diagrams

- Add DiagramComponent, DiagramWireSegment, SystemDiagram dataclasses
- Implement manhattan_path property for BL-first routing
- Add unit tests for data structure creation and path calculation
- All tests passing (3/3)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## ACCEPTANCE CRITERIA (COMPLETE PHASE 10)

Phase 10 is complete when:

1. ✅ All 17 tasks completed and marked [x]
2. ✅ All unit tests pass
3. ✅ All integration tests pass
4. ✅ Full test suite passes: `pytest -v`
5. ✅ Manual visual validation of test_08 SVG diagrams
6. ✅ CLI flag `--routing-diagrams` functional
7. ✅ SVG files generated correctly for all systems
8. ✅ Documentation updated (this todo marked complete)
9. ✅ All commits clean with updated todo list

---

**Ready to begin implementation following TDD discipline.**
