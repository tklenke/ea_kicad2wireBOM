# Routing Diagram Enhancements v2.0

**Version**: 2.0
**Status**: Design Phase
**Last Updated**: 2025-10-27
**Architect**: Claude

---

## 1. Overview

Enhance existing routing diagrams (implemented in Phase 10) with improved layout and labeling for better readability when reviewing large aircraft electrical systems.

### 1.1 Motivation

Current diagrams (portrait, 8.5×11) work well but have limitations:
- Components cluster in fuselage (BL≈0) while wingtips spread far out (BL=200+)
- Current compression makes centerline crowded
- Need better visual grouping of circuits at each component
- Wire stroke width should be configurable for different printing needs

### 1.2 Key Changes

1. **Landscape orientation** (11×8.5) - More horizontal space for BL axis
2. **Centered origin** - FS=0, BL=0 positioned ~1 inch below title, in center
3. **Reversed coordinate system** - Aircraft points UP (FS increases upward toward rear)
4. **Reversed non-linear BL scaling** - MORE space at centerline, LESS at wingtips
5. **Configurable wire stroke width** - Move to reference_data.py
6. **Circuit labels under components** - Group all circuit IDs connected to each component

---

## 2. Requirements

### 2.1 Functional Requirements

**FR-1**: Generate landscape SVG (width > height)
**FR-2**: Position origin (FS=0, BL=0) centered horizontally, ~1 inch below title area
**FR-3**: Orient diagram with aircraft pointing UP (FS=0 at bottom, increasing upward)
**FR-4**: Apply reversed non-linear BL scaling (expand centerline, compress wingtips)
**FR-5**: Make wire stroke width configurable via reference_data.py
**FR-6**: Add circuit ID labels grouped under each component (in addition to wire labels)
**FR-7**: Draw stroke-1 box around grouped component circuit labels

### 2.2 Non-Functional Requirements

**NFR-1**: Maintain backward compatibility with existing SVG generation
**NFR-2**: Diagrams legible when printed on 11×8.5 paper (landscape)
**NFR-3**: No changes to CLI interface or file naming

---

## 3. Coordinate System Changes

### 3.1 Current System (v1.0)

**Orientation**: Portrait (750×950 px)
**Aircraft coordinate system**:
- FS: 0 at nose, increases forward (toward tail)
- BL: 0 at centerline, increases starboard (right)

**SVG mapping**:
- FS → SVG Y (front at top)
- BL → SVG X (starboard at right)

**Scaling**: Non-linear compression (centerline linear, wingtips compressed)

### 3.2 New System (v2.0)

**Orientation**: Landscape (e.g., 1100×700 px)
**Aircraft coordinate system** (unchanged in data):
- FS: 0 at nose, increases TOWARD REAR (aft)
- BL: 0 at centerline, increases starboard (right)

**SVG mapping** (CHANGED):
- FS → SVG Y, **but inverted** (FS=0 at origin, FS increases UPWARD on page = rear/aft)
- BL → SVG X (BL negative to left, BL=0 at center, BL positive to right)

**Origin placement**:
- Horizontal: Center of SVG width
- Vertical: ~1 inch (100px at typical scale) below title area

**Scaling** (REVERSED):
- Non-linear expansion near centerline (BL≈0): MORE pixels per inch
- Non-linear compression at wingtips (BL→±200): FEWER pixels per inch

---

## 4. Detailed Design Changes

### 4.1 Page Layout

```
┌─────────────────────────────────────────────────┐
│  Title Block (Project info, system name)       │ ← 80px height
│  Legend (Scale, FS range, BL range)            │
├─────────────────────────────────────────────────┤ ← Separator line
│                                                 │
│         ↑ Rear (FS+)                            │
│         │                                       │
│    ─────┼─────  (FS=0, BL=0) ← Origin           │ ← 100px below separator
│         │                                       │
│         ↓ Nose (FS-)                            │
│    ←BL- │ BL+→                                  │
│                                                 │
└─────────────────────────────────────────────────┘

SVG size: 1100 × 700 (landscape)
```

### 4.2 Reversed Non-Linear BL Scaling

**Current function** (`scale_bl_nonlinear`):
```python
# Compresses large BL values
scaled = sign * compression_factor * log(1 + abs_bl / compression_factor)
# Example: BL=200 → ~55 (compressed)
```

**New function** (`scale_bl_nonlinear_v2`):
```python
# Expands small BL values (near centerline)
# Compresses large BL values (at wingtips) even more aggressively
# Goal: Give centerline components MORE space, wingtips LESS space

# Approach: Inverse of current scaling
# For BL near 0: Want output > input (expansion)
# For BL at max: Want output << input (aggressive compression)

# Example strategy: Use sinh or polynomial expansion near center
def scale_bl_nonlinear_v2(bl: float, center_expansion: float = 3.0,
                           tip_compression: float = 10.0) -> float:
    """
    Apply reversed non-linear scaling to BL coordinate.

    Expands coordinates near centerline (BL≈0) to give more space.
    Compresses coordinates at wingtips (BL>>0) to reduce space.

    Args:
        bl: BL coordinate in inches
        center_expansion: Expansion factor near centerline (default: 3.0)
        tip_compression: Compression factor at tips (default: 10.0)

    Returns:
        Scaled BL coordinate (sign preserved)

    Example:
        scale_bl_nonlinear_v2(10.0) ≈ 30   (expanded 3x)
        scale_bl_nonlinear_v2(200.0) ≈ 80  (compressed heavily)
    """
    if bl == 0.0:
        return 0.0

    sign = 1 if bl >= 0 else -1
    abs_bl = abs(bl)

    # Piecewise function:
    # - Small BL (< 30"): Linear expansion by center_expansion
    # - Large BL (> 30"): Logarithmic compression

    if abs_bl <= 30.0:
        # Expand centerline region
        scaled = abs_bl * center_expansion
    else:
        # Compress tip region
        # Start at 30 * center_expansion = 90 for BL=30
        # Then add compressed distance beyond 30
        base = 30.0 * center_expansion
        excess = abs_bl - 30.0
        compressed_excess = tip_compression * math.log(1 + excess / tip_compression)
        scaled = base + compressed_excess

    return sign * scaled
```

**Tuning parameters** (move to reference_data.py):
- `BL_CENTER_EXPANSION = 3.0`: How much to expand centerline (30" becomes 90")
- `BL_TIP_COMPRESSION = 10.0`: How aggressively to compress tips
- `BL_CENTER_THRESHOLD = 30.0`: BL value where expansion transitions to compression

### 4.3 Configurable Wire Stroke Width

**Current**: Hardcoded in `generate_svg()`:
```python
svg_lines.append('  <g id="wires" stroke="black" stroke-width="3" fill="none">')
```

**New**: Move to reference_data.py:
```python
# reference_data.py
DIAGRAM_CONFIG: Dict[str, any] = {
    'wire_stroke_width': 3.0,        # Wire line thickness in pixels
    'component_radius': 6.0,         # Component marker radius in pixels
    'component_stroke_width': 2.0,   # Component marker border thickness
    'svg_width': 1100,               # Landscape width
    'svg_height': 700,               # Landscape height
    'margin': 40,                    # Page margins
    'title_height': 80,              # Title block height
    'origin_offset_y': 100,          # Distance from title to origin (FS=0, BL=0)
}
```

**Usage in diagram_generator.py**:
```python
from kicad2wireBOM.reference_data import DIAGRAM_CONFIG

wire_width = DIAGRAM_CONFIG['wire_stroke_width']
svg_lines.append(f'  <g id="wires" stroke="black" stroke-width="{wire_width}" fill="none">')
```

### 4.4 Circuit Labels Under Components

**Feature**: Show all circuit IDs connected to each component, grouped below component marker.

**Data structure**:
```python
# Build mapping: component_ref → list of circuit labels
component_circuits: Dict[str, List[str]] = defaultdict(list)

for segment in diagram.wire_segments:
    # Each wire segment connects two components
    # Add circuit label to both components
    component_circuits[segment.comp1.ref].append(segment.label)
    component_circuits[segment.comp2.ref].append(segment.label)

# Sort and deduplicate
for comp_ref in component_circuits:
    component_circuits[comp_ref] = sorted(set(component_circuits[comp_ref]))
```

**Rendering**:
```python
# For each component, render grouped labels below marker
for comp in diagram.components:
    x, y = transform_to_svg(comp.fs, comp.bl, ...)  # Component position

    circuit_labels = component_circuits.get(comp.ref, [])

    if circuit_labels:
        # Calculate text block size
        label_text = ", ".join(circuit_labels)
        text_width = len(label_text) * 7  # Approximate width
        text_height = 16  # Font size + padding

        # Draw box below component marker
        box_x = x - text_width / 2
        box_y = y + 20  # Offset below marker
        svg_lines.append(
            f'<rect x="{box_x}" y="{box_y}" width="{text_width}" '
            f'height="{text_height}" fill="white" stroke="navy" stroke-width="1"/>'
        )

        # Draw text inside box
        text_x = x  # Centered
        text_y = box_y + 12  # Vertically centered in box
        svg_lines.append(
            f'<text x="{text_x}" y="{text_y}" font-size="10" '
            f'fill="navy" text-anchor="middle">{label_text}</text>'
        )
```

**Layout**:
```
        ○ CB1  ← Component marker and label
    ┌─────────┐
    │ L1A,L2B │  ← Circuit labels in box
    └─────────┘
```

### 4.5 Origin Positioning

**Calculate origin position in SVG coordinates**:
```python
# Origin should be at:
# - Horizontal center of SVG
# - origin_offset_y below title separator line

origin_svg_x = svg_width / 2
origin_svg_y = title_height + origin_offset_y

# When transforming aircraft coordinates to SVG:
# For BL=0, output should be origin_svg_x
# For FS=0, output should be origin_svg_y

def transform_to_svg_v2(fs: float, bl: float,
                        origin_svg_x: float, origin_svg_y: float,
                        scale_x: float, scale_y: float) -> Tuple[float, float]:
    """
    Transform aircraft coordinates to SVG with centered origin.

    Args:
        fs, bl: Aircraft coordinates (inches)
        origin_svg_x, origin_svg_y: SVG position of origin (FS=0, BL=0)
        scale_x: Pixels per scaled-inch for BL dimension
        scale_y: Pixels per inch for FS dimension

    Returns:
        (svg_x, svg_y) in SVG pixel coordinates
    """
    # Apply non-linear scaling to BL
    bl_scaled = scale_bl_nonlinear_v2(bl)

    # X: Scaled BL maps to horizontal offset from center
    svg_x = origin_svg_x + (bl_scaled * scale_x)

    # Y: FS maps to vertical offset from origin (FS+ goes UP = negative Y)
    # FS=0 at origin_svg_y, FS+ decreases SVG Y (up), FS- increases SVG Y (down)
    svg_y = origin_svg_y - (fs * scale_y)

    return (svg_x, svg_y)
```

---

## 5. Implementation Tasks

### 5.1 Phase 1: Configuration Setup

**Task 1.1**: Add diagram configuration constants to `reference_data.py`
- Add `DIAGRAM_CONFIG` dict with all layout constants
- Add BL scaling parameters (`BL_CENTER_EXPANSION`, `BL_TIP_COMPRESSION`, `BL_CENTER_THRESHOLD`)

**Task 1.2**: Update imports in `diagram_generator.py`
- Import `DIAGRAM_CONFIG` from reference_data
- Replace hardcoded constants with config values

### 5.2 Phase 2: Coordinate System Changes

**Task 2.1**: Implement `scale_bl_nonlinear_v2()` function
- Piecewise scaling with expansion at center, compression at tips
- Tunable parameters for expansion/compression factors
- Unit tests for various BL values

**Task 2.2**: Update `transform_to_svg()` function signature and logic
- Accept `origin_svg_x, origin_svg_y` instead of min/max bounds
- Use centered origin for coordinate transformation
- Invert FS axis (FS+ goes up = negative SVG Y)
- Call `scale_bl_nonlinear_v2()` instead of `scale_bl_nonlinear()`

**Task 2.3**: Update `generate_svg()` layout calculations
- Change to landscape dimensions (1100×700)
- Calculate origin position (centered horizontally, offset below title)
- Update all coordinate transformations to use new `transform_to_svg()`

### 5.3 Phase 3: Scaling Calculations

**Task 3.1**: Update scale calculation logic
- Calculate scale factors based on landscape dimensions
- Account for reversed BL scaling in scale calculations
- Determine max BL in scaled space (after expansion/compression)

**Task 3.2**: Update bounds calculation
- Apply new BL scaling to all components
- Determine min/max in scaled BL space
- Update FS bounds for inverted axis

### 5.4 Phase 4: Circuit Labels Under Components

**Task 4.1**: Build component-to-circuits mapping
- Create dict mapping each component ref to list of circuit labels
- Extract from wire_segments before rendering
- Sort and deduplicate circuit labels per component

**Task 4.2**: Implement circuit label rendering
- Calculate text bounding box for each component's circuit list
- Render white background rectangle with navy stroke
- Render centered text inside rectangle
- Position below component marker

**Task 4.3**: Handle label collisions
- Detect overlapping circuit label boxes
- Offset colliding boxes vertically or horizontally
- Ensure labels remain readable

### 5.5 Phase 5: Testing

**Task 5.1**: Unit tests for coordinate transformations
- Test `scale_bl_nonlinear_v2()` with various BL values
- Verify expansion at centerline, compression at tips
- Test `transform_to_svg_v2()` with origin-centered coordinates
- Verify FS+ goes up (negative SVG Y), BL± spreads left/right

**Task 5.2**: Integration tests for SVG generation
- Generate test diagrams with new layout
- Verify landscape orientation
- Verify origin placement
- Verify circuit labels appear under components

**Task 5.3**: Visual validation
- Generate diagrams from test fixtures
- Manually verify aircraft pointing up
- Check centerline components have adequate spacing
- Check wingtip components compressed appropriately
- Verify circuit labels grouped and boxed correctly

---

## 6. Acceptance Criteria

Feature complete when:

1. ✅ Diagrams generated in landscape orientation (1100×700 or similar)
2. ✅ Origin (FS=0, BL=0) positioned at horizontal center, ~1" below title
3. ✅ Aircraft points UP on page (FS increases upward toward rear)
4. ✅ BL scaling gives MORE space near centerline, LESS at wingtips
5. ✅ Wire stroke width configurable via `reference_data.py`
6. ✅ Circuit labels grouped under each component with stroke-1 box
7. ✅ All existing tests still pass
8. ✅ New tests pass for coordinate transformations and layout
9. ✅ Generated SVGs open correctly in browsers
10. ✅ Diagrams legible when printed landscape on 11×8.5 paper

---

## 7. Example Output

### Before (v1.0 - Portrait):
```
750×950 portrait
Front at top, starboard at right
Centerline crowded, wingtips spread
Wire labels only
```

### After (v2.0 - Landscape):
```
1100×700 landscape
┌─────────────────────────────────────────┐
│ Title: Lighting (L) System              │
├─────────────────────────────────────────┤
│                                         │
│              ↑ Rear (FS+)               │
│              │                          │
│    ─────────┼─────────  (0,0)          │ ← Origin
│              │                          │
│         ○────┼────○                     │ ← Components spread at centerline
│        CB1   │   SW1                    │
│      ┌────┐      ┌────┐                │
│      │L1A │      │L1B │                │ ← Circuit labels in boxes
│      └────┘      └────┘                │
│              ○ Wingtip (compressed)     │
│              │                          │
│              ↓ Nose (FS-)               │
└─────────────────────────────────────────┘
```

---

## 8. Dependencies

**No new external dependencies.**

Existing modules:
- `kicad2wireBOM/reference_data.py` - Modified to add config constants
- `kicad2wireBOM/diagram_generator.py` - Modified for all layout changes

---

## 9. Backward Compatibility

**Breaking changes**: None at API level
- CLI interface unchanged
- File naming unchanged
- Output format unchanged (still SVG)

**Visual changes**: All diagrams will look different
- New orientation and layout
- Different spacing and scaling
- Additional circuit labels

**Migration**: Regenerate all diagrams with updated tool

---

## 10. Future Enhancements

Deferred for later:
- Allow user to toggle between portrait/landscape via CLI flag
- Allow user to choose v1 vs v2 coordinate system
- Auto-detect best orientation based on FS/BL ranges
- Interactive SVG with hover tooltips showing circuit details

---

## 11. Component Star Diagrams (NEW)

### 11.1 Overview

Generate logical connectivity diagrams showing each component and its first-hop neighbors in a radial/star layout. One diagram per component, focusing on what connects to what rather than physical routing.

**Motivation**:
- Quick visual reference for component connections during wiring
- Easy to see all circuits connected to a specific component
- Complements spatial routing diagrams with logical view
- Useful for troubleshooting and wire tracing

### 11.2 Layout Design

```
         Portrait (750×950 px)
┌─────────────────────────────────────┐
│  Title: CB1 Component Star          │
│  CB1 = Circuit Breaker, 25A         │
├─────────────────────────────────────┤
│                                     │
│         ┌────────┐                  │
│         │  SW3   │                  │
│         │ Switch │                  │
│         └────────┘                  │
│              │ L2A                  │
│              │                      │
│  ┌────────┐  ○  ┌────────┐         │
│  │  BUS1  │─────│  CB1   │─────────│ P1A
│  │ Power  │ P1B │Circuit │         │
│  │  Bus   │     │Breaker │         │
│  └────────┘     │  25A   │         │
│                 └────────┘          │
│                      │ L1A          │
│                 ┌────────┐          │
│                 │ LIGHT1 │          │
│                 │Landing │          │
│                 │ Light  │          │
│                 └────────┘          │
└─────────────────────────────────────┘

Center: Target component with ref, value, desc
Outer: First-hop neighbors with ref, desc
Lines: Wires labeled with circuit IDs
```

### 11.3 Requirements

**FR-STAR-1**: Generate one SVG per component (excluding power symbols)
**FR-STAR-2**: Center circle shows: component ref, value, description
**FR-STAR-3**: Outer circles show: component ref, description (no value)
**FR-STAR-4**: Lines connect center to outer circles, labeled with circuit ID
**FR-STAR-5**: Radial layout: arrange outer circles evenly around center
**FR-STAR-6**: Auto-size circles based on text content
**FR-STAR-7**: Portrait orientation (750×950 or similar)

### 11.4 Layout Algorithm

**Radial/Polar Layout**:
- Center component at origin (center of SVG)
- Outer components arranged in circle around center
- Angular spacing: `θ = 360° / N` where N = number of neighbors
- Radius: Fixed distance from center (e.g., 250px)

```python
def calculate_star_layout(center_comp: Component,
                          neighbors: List[Component],
                          radius: float = 250.0) -> Dict[str, Tuple[float, float]]:
    """
    Calculate polar coordinates for star diagram.

    Args:
        center_comp: Center component
        neighbors: List of connected neighbor components
        radius: Distance from center to neighbors (pixels)

    Returns:
        Dict mapping component ref to (x, y) SVG coordinates
    """
    layout = {}

    # Center component at origin
    center_x = svg_width / 2
    center_y = svg_height / 2
    layout[center_comp.ref] = (center_x, center_y)

    # Arrange neighbors in circle
    n = len(neighbors)
    angle_step = 360.0 / n if n > 0 else 0

    for i, neighbor in enumerate(neighbors):
        angle = i * angle_step
        angle_rad = math.radians(angle)

        x = center_x + radius * math.cos(angle_rad)
        y = center_y + radius * math.sin(angle_rad)

        layout[neighbor.ref] = (x, y)

    return layout
```

### 11.5 Circle Sizing

**Dynamic sizing based on text**:
- Measure text content (ref, value, desc)
- Calculate required width and height
- Use larger of width or height to ensure circular shape
- Minimum radius: 40px
- Maximum radius: 80px

```python
def calculate_circle_radius(texts: List[str],
                           font_size: int = 12) -> float:
    """
    Calculate circle radius needed to fit text.

    Args:
        texts: List of text strings to fit (ref, value, desc)
        font_size: Font size in points

    Returns:
        Circle radius in pixels
    """
    # Estimate text width (rough approximation)
    max_text_width = max(len(text) * font_size * 0.6 for text in texts)

    # Height for N lines of text with padding
    text_height = len(texts) * (font_size + 4) + 10

    # Circle must fit the larger dimension
    required = max(max_text_width, text_height) * 0.6  # Factor for circular fit

    # Clamp to reasonable range
    return max(40.0, min(80.0, required))
```

### 11.6 Data Structures

```python
@dataclass
class StarDiagramComponent:
    """Component in star diagram."""
    ref: str              # Component reference
    value: str            # Component value (center only)
    desc: str             # Component description
    x: float              # SVG X position
    y: float              # SVG Y position
    radius: float         # Circle radius

@dataclass
class StarDiagramWire:
    """Wire connection in star diagram."""
    circuit_id: str       # Circuit label (e.g., "L1A")
    from_ref: str         # Source component ref
    to_ref: str           # Destination component ref

@dataclass
class ComponentStarDiagram:
    """Star diagram for one component."""
    center: StarDiagramComponent          # Center component
    neighbors: List[StarDiagramComponent] # Outer components
    wires: List[StarDiagramWire]          # Connecting wires
```

### 11.7 SVG Generation

**Structure**:
```xml
<svg width="750" height="950">
  <!-- Background -->
  <rect fill="white" width="100%" height="100%"/>

  <!-- Title block -->
  <text>CB1 Component Star</text>
  <text>CB1 = Circuit Breaker, 25A</text>

  <!-- Wire lines (drawn first, behind circles) -->
  <g id="wires">
    <line x1="375" y1="475" x2="375" y2="225" stroke="black" stroke-width="2"/>
  </g>

  <!-- Wire labels -->
  <g id="wire-labels">
    <text x="375" y="350">L1A</text>
  </g>

  <!-- Circles -->
  <g id="circles">
    <!-- Center circle (larger, blue fill) -->
    <circle cx="375" cy="475" r="60" fill="lightblue" stroke="navy" stroke-width="3"/>

    <!-- Outer circles (smaller, white fill) -->
    <circle cx="375" cy="225" r="50" fill="white" stroke="blue" stroke-width="2"/>
  </g>

  <!-- Text inside circles -->
  <g id="circle-text">
    <!-- Center circle text (3 lines: ref, value, desc) -->
    <text x="375" y="460">CB1</text>
    <text x="375" y="475">25A</text>
    <text x="375" y="490">Circuit Breaker</text>

    <!-- Outer circle text (2 lines: ref, desc) -->
    <text x="375" y="220">LIGHT1</text>
    <text x="375" y="235">Landing Light</text>
  </g>
</svg>
```

### 11.8 Text Wrapping

**Handle long text**:
- Component descriptions may be long (e.g., "Left Landing Light Switch")
- Need to wrap text inside circles
- Break at word boundaries
- Adjust circle size if needed

```python
def wrap_text(text: str, max_width: int) -> List[str]:
    """
    Wrap text to fit within max width.

    Args:
        text: Text to wrap
        max_width: Maximum characters per line

    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= max_width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(' '.join(current_line))

    return lines
```

### 11.9 Handling Power Symbols

**Exclude power symbols from star diagrams**:
- GND, +12V, +5V, +28V, etc. connect to many components
- Would clutter star diagrams
- Already shown in routing diagrams

**Filter logic**:
```python
def should_generate_star_diagram(comp_ref: str) -> bool:
    """
    Determine if component should have star diagram.

    Power symbols excluded (too many connections).
    """
    power_symbols = ['GND', '+12V', '+5V', '+3V3', '+28V']

    if comp_ref in power_symbols:
        return False

    if comp_ref.startswith('GND') or comp_ref.startswith('+'):
        return False

    return True
```

### 11.10 File Naming

**Output files**:
- `CB1_Star.svg` - Star diagram for CB1
- `SW2_Star.svg` - Star diagram for SW2
- etc.

**Differentiate from other diagrams**:
- System diagrams: `L_System.svg`, `P_System.svg`
- Component routing: `CB1_Component.svg`, `SW2_Component.svg`
- Component star: `CB1_Star.svg`, `SW2_Star.svg`

### 11.11 Implementation Tasks Summary

**Phase 13.6: Component Star Diagrams** (to be added to programmer_todo.md):

1. **Task 13.6.1**: Implement star layout algorithm
   - `calculate_star_layout()` function
   - Polar coordinate calculations
   - TEST: Verify even angular distribution

2. **Task 13.6.2**: Implement circle sizing logic
   - `calculate_circle_radius()` function
   - Text measurement and wrapping
   - TEST: Verify circles fit text content

3. **Task 13.6.3**: Create `ComponentStarDiagram` data structures
   - `StarDiagramComponent`, `StarDiagramWire` dataclasses
   - `ComponentStarDiagram` builder function
   - TEST: Verify data structure creation

4. **Task 13.6.4**: Implement `generate_star_svg()` function
   - Portrait SVG with title block
   - Draw wires first (background)
   - Draw circles (foreground)
   - Render text inside circles
   - TEST: Generate test star diagram

5. **Task 13.6.5**: Integrate with main diagram generation
   - Add to `generate_routing_diagrams()` function
   - Generate one star diagram per component
   - Skip power symbols
   - TEST: Verify star diagrams generated for all components

6. **Task 13.6.6**: Handle edge cases
   - Components with 1 neighbor (still show as star)
   - Components with 20+ neighbors (may need smaller circles or multiple rings)
   - Long component descriptions (text wrapping)
   - TEST: Test with varying neighbor counts

---

**Document Status**: ✅ Ready for Implementation
