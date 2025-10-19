# Programmer Implementation Notes

**Date**: 2025-10-18
**Architect**: Claude
**For**: Programmer Role (future Claude session)

---

## CRITICAL: Architecture Changed from Netlist to Schematic Parsing

**Old documents archived** to `docs/archive/` - don't reference them.

**New approach**: Parse KiCAD schematic files (`.kicad_sch`), NOT netlists (`.net`)

**Why**: Wire harness manufacturing needs physical wire-level granularity. Netlists collapse wires into nets. Schematics preserve individual wire segments.

---

## Quick Start

### What to Read First

1. **This document** - Overview and critical notes
2. **`docs/plans/kicad2wireBOM_design.md` v2.0** - Complete design specification
3. **`docs/plans/required_from_tom.md`** - Open questions and decisions needed
4. **Test fixtures** in `tests/fixtures/` - Actual KiCAD schematics to work with

### What Not to Read

- Anything in `docs/archive/` - Those are the OLD netlist-based designs

---

## Core Concept: Wire-Centric Data Model

**Traditional PCB tool thinking**: Nets are primary (electrical connectivity)

**Wire harness thinking**: Individual wires are primary (physical manufacturing)

### Example Problem We're Solving

```
Schematic shows:
  Wire labeled "P1A": SW1 pin 1 → TB1 pin 1
  Wire labeled "P2A": SW2 pin 1 → TB1 pin 1

These are electrically the same net (connected at TB1).
But they're TWO PHYSICAL WIRES that need:
  - Separate labels (P1A, P2A)
  - Separate BOM entries
  - Individual length calculations
  - Distinct wire marking

A netlist would collapse this to:
  Net "Power": {SW1-1, SW2-1, TB1-1}  ← LOSES wire-level info
```

**Your job**: Extract individual wire segments from schematic, each with its own label and BOM entry.

---

## Data Flow Overview

```
KiCAD Schematic (.kicad_sch)
  ↓
S-Expression Parser
  ↓
Extract:
  - Wire segments (start/end coordinates, UUID)
  - Labels (text, position)
  - Components (position, footprint encoding)
  - Junctions (position, connected wires)
  ↓
Associate labels with wires (proximity matching)
  ↓
Build wire-to-component connections (endpoint matching)
  ↓
Calculate for each wire:
  - Length (Manhattan distance + slack)
  - Gauge (voltage drop + ampacity constraints)
  - Color (system code mapping)
  ↓
Generate BOM (CSV or Markdown)
```

---

## Critical Algorithms

### 1. S-Expression Parsing

**Input**: KiCAD `.kicad_sch` file (text, Lisp-style format)

**Example structure**:
```lisp
(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (wire
    (pts (xy 83.82 52.07) (xy 92.71 52.07))
    (stroke (width 0) (type default))
    (uuid "0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd")
  )
  (label "G1A"
    (at 107.95 60.96 0)
    (effects (font (size 1.27 1.27)))
    (uuid "4c75cce0-2c4a-4ce2-be43-76f5f6f3eb7b")
  )
  (symbol
    (lib_id "Device:Battery")
    (at 95.25 77.47 90)
    (property "Reference" "BT1" ...)
    (property "Footprint" "|(10,0,0)S40" ...)
  )
)
```

**Library Options**:
- **sexpdata**: Simple, mature (recommended)
- **Custom parser**: More work but no dependencies
- **Decision needed from Tom** - see `required_from_tom.md`

**Output**: Nested Python data structures (lists/dicts)

**Test fixtures available**: `tests/fixtures/test_*_fixture.kicad_sch` (real KiCAD files)

### 2. Label-to-Wire Association (Proximity Matching)

**Challenge**: Labels are placed near wires in schematic, but not explicitly linked.

**Algorithm**:

1. For each label with circuit ID pattern (e.g., "P1A", "G1A"):
   - Get label position: `(x, y)`

2. For each wire segment:
   - Get wire start: `(x1, y1)`
   - Get wire end: `(x2, y2)`

3. Calculate perpendicular distance from label to wire segment:
   - Point-to-line-segment distance
   - Handle cases where perpendicular falls outside segment (use endpoint distance)

4. Find minimum distance:
   - If `distance <= threshold` (default 10mm): Associate label with that wire
   - If `distance > threshold`: Warning (orphaned label)

5. Handle multiple labels on same wire:
   - If multiple circuit IDs: Warning (ambiguous)
   - If circuit ID + notes: Keep circuit ID only

**Point-to-Segment Distance Formula**:
```python
def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """
    Calculate perpendicular distance from point (px, py) to line segment (x1,y1)-(x2,y2)
    """
    # Vector from segment start to point
    dx = px - x1
    dy = py - y1

    # Vector along segment
    sx = x2 - x1
    sy = y2 - y1

    # Segment length squared
    segment_length_sq = sx*sx + sy*sy

    if segment_length_sq == 0:
        # Segment is a point
        return math.sqrt(dx*dx + dy*dy)

    # Parameter t = projection of point onto segment (0 to 1)
    t = max(0, min(1, (dx*sx + dy*sy) / segment_length_sq))

    # Closest point on segment
    closest_x = x1 + t * sx
    closest_y = y1 + t * sy

    # Distance from point to closest point
    dist_x = px - closest_x
    dist_y = py - closest_y

    return math.sqrt(dist_x*dist_x + dist_y*dist_y)
```

**Important**: Label positions and wire coordinates are in schematic units (mm). Aircraft coordinates (FS/WL/BL) are separate (inches) and used only for length calculation.

### 3. Footprint Field Parsing

**Format**: `<original_footprint>|(<fs>,<wl>,<bl>)<type><value>`

**Examples**:
- `|(10,0,0)S40` - Battery at FS=10, WL=0, BL=0, 40A source
- `|(200,35,10)L2.5` - Lamp at FS=200, WL=35, BL=10, 2.5A load
- `|(150,30,0)R20` - Switch at FS=150, WL=30, BL=0, 20A rating

**Regex**: `\|([-\d.]+),([-\d.]+),([-\d.]+)\)([LRSB])([\d.]+)`

**Captures**:
1. FS (fuselage station) - float
2. WL (waterline) - float
3. BL (buttline) - float
4. Type letter: L (load), R (rating), S (source), B (battery)
5. Amperage - float

**Edge Cases**:
- Missing `|` delimiter: No encoding present (permissive mode: default values)
- Malformed encoding: Parse error with helpful message
- Negative coordinates: Valid (left side of aircraft, aft of datum, below datum)

### 4. Wire Length Calculation

**Method**: Manhattan distance in aircraft coordinates + slack

**Formula**:
```python
def calculate_wire_length(comp1, comp2, slack_inches=24):
    """
    Calculate wire length between two components using Manhattan distance.

    Args:
        comp1: Component with (fs, wl, bl) in inches
        comp2: Component with (fs, wl, bl) in inches
        slack_inches: Extra length for termination/routing (default 24")

    Returns:
        Total wire length in inches
    """
    manhattan = abs(comp1.fs - comp2.fs) + \
                abs(comp1.wl - comp2.wl) + \
                abs(comp1.bl - comp2.bl)

    return manhattan + slack_inches
```

**Why Manhattan**: Conservative estimate for rectilinear routing through aircraft structure (more realistic than straight-line distance).

**Slack**: Default 24" (12" per end) for termination, strain relief, routing adjustments. Configurable via `--slack-length`.

### 5. Wire Gauge Selection

**Constraints**:
1. **Voltage drop**: Max 5% of system voltage (default 12V)
2. **Ampacity**: Wire must carry required current safely

**Algorithm**:
```python
def select_wire_gauge(current_amps, length_inches, system_voltage=12):
    """
    Select minimum wire gauge meeting voltage drop and ampacity constraints.

    Returns:
        (selected_awg, calculated_min_awg, voltage_drop_volts, voltage_drop_percent)
    """
    max_voltage_drop = system_voltage * 0.05  # 5%

    # Try each AWG size from largest (smallest wire) to smallest (largest wire)
    for awg in [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]:
        # Check ampacity constraint
        if current_amps > WIRE_AMPACITY[awg]:
            continue  # Wire too small for current

        # Check voltage drop constraint
        resistance_per_foot = WIRE_RESISTANCE[awg]
        voltage_drop = current_amps * resistance_per_foot * (length_inches / 12)

        if voltage_drop <= max_voltage_drop:
            # This AWG size meets both constraints
            voltage_drop_percent = (voltage_drop / system_voltage) * 100
            return awg, awg, voltage_drop, voltage_drop_percent

    # If we get here, even 2 AWG is too small
    # Return 2 AWG with warning
    awg = 2
    resistance_per_foot = WIRE_RESISTANCE[awg]
    voltage_drop = current_amps * resistance_per_foot * (length_inches / 12)
    voltage_drop_percent = (voltage_drop / system_voltage) * 100

    # Warning will be added by validator
    return awg, awg, voltage_drop, voltage_drop_percent
```

**Reference Data Needed** (Tom to provide or Programmer to extract):
- `WIRE_RESISTANCE = {awg: ohms_per_foot, ...}` - From Aeroelectric Connection Ch5
- `WIRE_AMPACITY = {awg: max_amps, ...}` - From Aeroelectric Connection (bundled wire values)

---

## Data Models

### WireSegment
```python
@dataclass
class WireSegment:
    uuid: str                           # From KiCAD
    start_point: tuple[float, float]    # (x, y) in mm (schematic coords)
    end_point: tuple[float, float]      # (x, y) in mm (schematic coords)
    circuit_id: str | None              # Parsed from label (e.g., "P1A")
    system_code: str | None             # Extracted from circuit_id (e.g., "P")
    circuit_num: str | None             # Extracted from circuit_id (e.g., "1")
    segment_letter: str | None          # Extracted from circuit_id (e.g., "A")
    connected_components: list[tuple[str, str]]  # [(ref, pin), ...] at endpoints
```

### Component
```python
@dataclass
class Component:
    ref: str                # Reference designator (e.g., "BT1", "SW1")
    fs: float               # Fuselage station (inches)
    wl: float               # Waterline (inches)
    bl: float               # Buttline (inches)
    source_type: str        # "L", "R", "S", "B"
    amperage: float         # Load, rating, or source capacity (amps)
    schematic_position: tuple[float, float]  # (x, y) in mm (for pin matching)
    pins: dict[str, tuple[float, float]]     # {pin_number: (x, y)} if needed
```

### WireBOM
```python
@dataclass
class WireBOM:
    """Complete wire BOM with all wires and metadata"""
    wires: list[WireConnection]
    config: dict  # System voltage, slack, etc.
    warnings: list[str]  # All validation warnings

    def sort_by_circuit_id(self):
        """Sort wires by system code, circuit number, segment letter"""
        pass

    def get_purchasing_summary(self) -> dict:
        """Return {(awg, color): total_length_inches}"""
        pass
```

### WireConnection
```python
@dataclass
class WireConnection:
    """Single wire in the BOM"""
    wire_label: str         # EAWMS format (e.g., "P1A", "L-12-B")
    from_ref: str           # Component-pin (e.g., "BT1-1")
    to_ref: str             # Component-pin (e.g., "SW1-2")
    wire_gauge: str         # Selected AWG (e.g., "20 AWG")
    wire_color: str         # Assigned color
    length: float           # Total length in inches
    wire_type: str          # Specification (e.g., "M22759/16")
    warnings: list[str]     # Any warnings for this wire

    # Engineering mode fields
    calculated_min_gauge: float | None
    voltage_drop_volts: float | None
    voltage_drop_percent: float | None
    current: float | None
    from_coords: tuple[float, float, float] | None  # (FS, WL, BL)
    to_coords: tuple[float, float, float] | None
    calculated_length: float | None  # Before slack
```

---

## Testing Strategy

### Test-Driven Development Approach

**Recommended**: Hybrid TDD
- Core algorithms (label association, wire calculations): Strict TDD
- Parsing/I/O: Spike-then-test (explore first, then write tests)

### Test Fixtures Available

You have three real KiCAD schematics:

**test_01_fixture.kicad_sch**:
- Simple: Battery → Lamp
- 6 wire segments
- 2 labels: "G1A", "P1A"
- Components with footprint encoding

**test_02_fixture.kicad_sch**:
- Multi-segment: Battery → Switch → Lamp
- 7 wire segments
- 3 labels: "L2B", "L2A", "G1A"
- More complex routing

**test_03_fixture.kicad_sch**:
- Junction example: 2 switches → 1 connector
- 4 wire segments
- 1 junction (exactly the problem we're solving!)
- 2 labels: "P1A", "P2A"
- **Perfect test case for wire granularity**

### Suggested Test Sequence

1. **Parse test_01_fixture.kicad_sch**:
   - Extract wire segments
   - Extract labels
   - Extract components
   - Verify data structures

2. **Associate labels with wires**:
   - Test proximity matching
   - Verify "G1A" and "P1A" associate correctly

3. **Parse footprint encoding**:
   - Extract FS/WL/BL coordinates
   - Extract source type and amperage
   - Handle missing/malformed encodings

4. **Calculate wire length**:
   - Manhattan distance between components
   - Add slack
   - Verify against hand calculation

5. **Select wire gauge**:
   - Given current and length
   - Check voltage drop constraint
   - Check ampacity constraint
   - Verify correct AWG selected

6. **Generate BOM output**:
   - CSV format
   - Markdown format
   - Verify formatting and sorting

7. **Test with test_02 and test_03**:
   - More complex cases
   - Junction handling
   - Multiple circuits

---

## Implementation Sequence Suggestion

### Phase 0: Project Setup
- Create `kicad2wireBOM/` package directory
- Set up `pyproject.toml` or `setup.py`
- Install dependencies (`sexpdata` or chosen parser, `pytest`)
- Create basic module structure

### Phase 1: S-Expression Parsing
- Write function to read `.kicad_sch` file
- Parse s-expressions into Python data structures
- Extract wire, label, symbol, junction elements
- Test with test_01_fixture.kicad_sch

### Phase 2: Data Extraction
- Extract wire segments (start/end points, UUID)
- Extract labels (text, position)
- Extract component data (ref, position, footprint)
- Parse footprint encoding (FS/WL/BL, type, amperage)
- Create data model classes

### Phase 3: Label Association
- Implement point-to-segment distance calculation
- Associate labels with nearest wire segments
- Handle orphaned labels, multiple labels per wire
- Test with all three fixtures

### Phase 4: Wire Calculations
- Implement Manhattan distance length calculation
- Implement voltage drop calculation
- Implement wire gauge selection
- Test with hand-calculated examples

### Phase 5: BOM Generation
- Create WireConnection objects for each wire
- Sort by circuit ID
- Generate CSV output (builder mode)
- Generate Markdown output (builder mode)
- Test output formatting

### Phase 6: Validation and Engineering Mode
- Add validation checks (missing data, orphaned labels, etc.)
- Implement strict vs permissive modes
- Add engineering mode fields and output
- Test validation logic

### Phase 7: CLI and Integration
- Command-line interface with argparse
- File I/O and error handling
- Configuration file loading
- Auto-generated output filenames (REVnnn)
- End-to-end integration tests

---

## Common Pitfalls to Avoid

### 1. Coordinate System Confusion

**Two separate coordinate systems**:
- **Schematic coordinates**: mm, used for label-to-wire proximity matching
- **Aircraft coordinates**: inches (FS/WL/BL), used for wire length calculation

**Don't**: Try to convert between them (they're unrelated)
**Do**: Keep them separate and use each for its specific purpose

### 2. S-Expression Parsing Edge Cases

**Watch out for**:
- Deeply nested structures (recursion depth)
- Optional elements (may be absent)
- Quoted strings with special characters
- Floating-point precision in coordinates

**Defensive parsing**: Always check element exists before accessing.

### 3. Label Association Ambiguity

**Edge cases**:
- Label equidistant from two wires
- Label far from all wires (orphaned)
- Multiple circuit ID labels on same wire
- No labels on wire (unlabeled)

**Handle gracefully**: Warn user, make best guess or use fallback.

### 4. Pin Position Calculation

**Challenge**: Symbol rotation/mirroring affects pin positions.

**Initial approach**: Use component center position, ignore pin-level precision.

**Later enhancement**: If needed, calculate exact pin positions with transforms.

### 5. Floating-Point Comparison

**Don't**: `if wire_end == component_pos`
**Do**: `if distance(wire_end, component_pos) < tolerance`

**Tolerance**: 0.1mm suggested for coordinate matching

---

## Open Questions for Tom

See `docs/plans/required_from_tom.md` for:
- Label association distance threshold (10mm suggested)
- S-expression parser library choice (sexpdata recommended)
- Pin position calculation precision (simple vs precise)
- Hierarchical schematic support (now or later)
- TDD approach (strict, spike-then-test, or hybrid)

---

## Success Criteria

**You're done when**:
- Tool parses all three test fixtures successfully
- Labels associate with correct wires
- Wire lengths calculated correctly (verify by hand)
- Wire gauges meet voltage drop and ampacity constraints
- CSV and Markdown outputs are well-formatted
- All validation checks work as specified
- Strict and permissive modes behave correctly
- All tests pass

---

## Getting Started Checklist

- [ ] Read this document completely
- [ ] Read `docs/plans/kicad2wireBOM_design.md` v2.0
- [ ] Check `docs/plans/required_from_tom.md` for open questions
- [ ] Examine test fixture files in `tests/fixtures/`
- [ ] Choose s-expression parser library (or confirm with Tom)
- [ ] Set up project structure
- [ ] Write first failing test (parse test_01_fixture.kicad_sch)
- [ ] Begin TDD cycle: RED → GREEN → REFACTOR

---

## Final Notes

**This is a well-defined problem** with real test fixtures and clear success criteria.

**The core challenge** is label-to-wire proximity matching - everything else is straightforward data extraction and calculation.

**Test-driven approach works great here** because:
- Test fixtures are actual KiCAD files (real data)
- Expected outputs can be hand-calculated
- Algorithm correctness is verifiable

**If you get stuck**:
- Check the design document for algorithm details
- Look at test fixtures to understand data structure
- Ask Tom via Circle K protocol if design has issues
- Use permissive mode to skip over blockers temporarily

**Good luck!** This is a solid architectural foundation. The schematic-based approach solves the wire granularity problem correctly.

---

**Architect Sign-off**: Claude (Architect role), 2025-10-18
