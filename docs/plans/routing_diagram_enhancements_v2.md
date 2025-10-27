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

**Document Status**: ✅ Ready for Implementation
