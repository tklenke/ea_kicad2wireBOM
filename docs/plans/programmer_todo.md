# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Architecture**: Schematic-based parsing (NOT netlist-based)
**Approach**: Test-Driven Development (TDD)
**Status**: Ready to begin implementation

---

## BEFORE YOU START

### Required Reading (In Order)

1. **`docs/plans/ARCHITECTURE_CHANGE.md`** (5 min)
   - Why we're parsing schematics, not netlists
   - High-level context

2. **`docs/plans/programmer_notes.md`** (15 min)
   - Implementation guidance
   - Algorithms, data models, pitfalls

3. **`docs/plans/kicad2wireBOM_design.md` v2.0** (30 min)
   - Complete design specification
   - Reference throughout implementation

4. **Examine test fixtures** (10 min)
   - Open `tests/fixtures/test_01_fixture.kicad_sch` in text editor
   - See s-expression structure
   - Understand wire, label, symbol elements

### Critical Understanding Check

Before writing any code, you must understand:
- ✓ We parse `.kicad_sch` files, NOT `.net` files
- ✓ Wire segments are extracted individually (not collapsed into nets)
- ✓ Labels associate with wires by proximity, not direct linkage
- ✓ Two coordinate systems: schematic (mm) vs aircraft (FS/WL/BL inches)
- ✓ Goal: Generate per-wire BOM with labels, lengths, gauges

**If any checkbox is unclear, re-read the required documents.**

---

## PHASE 0: Project Setup

**Goal**: Create project structure and verify environment

### Task 0.1: Create Package Structure
```bash
mkdir -p kicad2wireBOM
touch kicad2wireBOM/__init__.py
mkdir -p tests
touch tests/__init__.py
```

**Files to create**:
- `kicad2wireBOM/__init__.py` (empty for now)
- `tests/__init__.py` (empty)
- `pyproject.toml` or `setup.py` (project config)
- `requirements.txt` or use pyproject.toml dependencies

**Test**: `python -c "import kicad2wireBOM"` should not error

### Task 0.2: Set Up Dependencies

**DECISION MADE**: Use `sexpdata` library for s-expression parsing

**Install dependencies**:
```bash
pip install sexpdata pytest
```

**Create `requirements.txt`**:
```
sexpdata>=0.0.3
pytest>=7.0.0
```

**Test**: `python -c "import sexpdata"` should work

**IMPORTANT - Circle K Protocol**:
If you encounter problems with `sexpdata` during implementation:
- Parsing errors with KiCAD files
- Data structure issues (Symbol types, nested lists)
- Performance problems
- Any other blockers

**THEN**:
1. Document the specific issue clearly
2. Say "Strange things are afoot at the Circle K"
3. Suggest alternative (custom parser or pyparsing)
4. **Wait for architectural decision** - don't switch libraries without approval

### Task 0.3: Verify Test Fixtures

**Check test fixtures exist**:
```bash
ls tests/fixtures/test_01_fixture.kicad_sch
ls tests/fixtures/test_02_fixture.kicad_sch
ls tests/fixtures/test_03_fixture.kicad_sch
```

**Examine test_01 structure**:
```bash
head -50 tests/fixtures/test_01_fixture.kicad_sch
```

**Verify s-expression format**: Should see `(kicad_sch ...` at top

**Test**: Can read file as text, looks like Lisp-style s-expressions

### Task 0.4: Create First Test File

**Create**: `tests/test_parser.py`

**Write first test** (should FAIL - no implementation yet):
```python
def test_can_read_schematic_file():
    """Verify we can read a .kicad_sch file"""
    from pathlib import Path

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    assert fixture_path.exists(), "Test fixture not found"

    content = fixture_path.read_text()
    assert content.startswith("(kicad_sch"), "Not a valid KiCAD schematic"
```

**Run test**:
```bash
pytest tests/test_parser.py::test_can_read_schematic_file -v
```

**Expected**: PASS (this is a sanity check, not real TDD yet)

**Checkpoint**: ✓ Project structure created, dependencies installed, can read test fixtures

---

## PHASE 1: S-Expression Parsing Foundation

**Goal**: Parse `.kicad_sch` files into Python data structures

### Task 1.1: Parse Schematic File to S-Expressions

**Create**: `kicad2wireBOM/parser.py`

**Write test** (in `tests/test_parser.py`):
```python
def test_parse_schematic_to_sexp():
    """Parse .kicad_sch file into s-expression data structure"""
    from kicad2wireBOM.parser import parse_schematic_file
    from pathlib import Path

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    # Should be a list (s-expression is a list of elements)
    assert isinstance(sexp, list)
    # First element should be the symbol 'kicad_sch'
    assert sexp[0] == 'kicad_sch' or sexp[0] == Symbol('kicad_sch')
```

**Run test**: `pytest tests/test_parser.py::test_parse_schematic_to_sexp -v`

**Expected**: FAIL (no implementation yet)

**Implement** (in `kicad2wireBOM/parser.py`):
```python
# ABOUTME: This module parses KiCAD schematic files into Python data structures
# ABOUTME: Uses s-expression parsing to extract wire, label, component, and junction data

from pathlib import Path
import sexpdata  # If using sexpdata library

def parse_schematic_file(file_path: Path):
    """
    Parse a KiCAD schematic file into s-expression data structure.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        Parsed s-expression as nested Python lists
    """
    content = file_path.read_text(encoding='utf-8')
    sexp = sexpdata.loads(content)
    return sexp
```

**Run test again**: Should PASS

**Checkpoint**: ✓ Can parse schematic file to s-expressions

### Task 1.2: Extract Wire Elements

**Write test**:
```python
def test_extract_wire_elements():
    """Extract all (wire ...) elements from schematic"""
    from kicad2wireBOM.parser import parse_schematic_file, extract_wires
    from pathlib import Path

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    wires = extract_wires(sexp)

    # test_01 has 6 wire segments (verified by inspection)
    assert len(wires) == 6
    # Each wire should be a list starting with 'wire' symbol
    assert all(w[0] == 'wire' or w[0] == Symbol('wire') for w in wires)
```

**Implement** (in `parser.py`):
```python
def extract_wires(sexp):
    """
    Extract all (wire ...) elements from schematic s-expression.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of wire elements (each is an s-expression)
    """
    wires = []

    def walk(node):
        """Recursively walk s-expression tree"""
        if isinstance(node, list):
            # Check if this is a wire element
            if len(node) > 0 and (node[0] == 'wire' or str(node[0]) == 'wire'):
                wires.append(node)
            # Recurse into children
            for child in node:
                walk(child)

    walk(sexp)
    return wires
```

**Run test**: Should PASS

**Checkpoint**: ✓ Can extract wire elements from schematic

### Task 1.3: Extract Label Elements

**Write test**:
```python
def test_extract_label_elements():
    """Extract all (label ...) elements from schematic"""
    from kicad2wireBOM.parser import parse_schematic_file, extract_labels
    from pathlib import Path

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    labels = extract_labels(sexp)

    # test_01 has 2 labels: "G1A" and "P1A"
    assert len(labels) == 2
    assert all(lbl[0] == 'label' or str(lbl[0]) == 'label' for lbl in labels)
```

**Implement** (similar to extract_wires):
```python
def extract_labels(sexp):
    """Extract all (label ...) elements from schematic"""
    labels = []

    def walk(node):
        if isinstance(node, list):
            if len(node) > 0 and (node[0] == 'label' or str(node[0]) == 'label'):
                labels.append(node)
            for child in node:
                walk(child)

    walk(sexp)
    return labels
```

**Checkpoint**: ✓ Can extract wire and label elements

### Task 1.4: Extract Symbol (Component) Elements

**Write test**:
```python
def test_extract_symbol_elements():
    """Extract all (symbol ...) elements from schematic"""
    from kicad2wireBOM.parser import parse_schematic_file, extract_symbols
    from pathlib import Path

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    symbols = extract_symbols(sexp)

    # test_01 has 2 components: BT1 (battery) and L1 (lamp)
    assert len(symbols) == 2
```

**Implement**: Similar pattern as above

**Checkpoint**: ✓ Can extract all major schematic elements

---

## PHASE 2: Data Model Creation

**Goal**: Convert s-expressions into Python data classes

### Task 2.1: Create WireSegment Data Class

**Create**: `kicad2wireBOM/schematic.py`

**Implement**:
```python
# ABOUTME: This module defines data models for schematic elements
# ABOUTME: Includes WireSegment, Label, Component, and Junction classes

from dataclasses import dataclass

@dataclass
class WireSegment:
    """Represents a single wire segment in the schematic"""
    uuid: str
    start_point: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    end_point: tuple[float, float]    # (x, y) in mm
    circuit_id: str | None = None     # Parsed from label (e.g., "P1A")
    system_code: str | None = None    # Extracted from circuit_id (e.g., "P")
    circuit_num: str | None = None    # Extracted from circuit_id (e.g., "1")
    segment_letter: str | None = None # Extracted from circuit_id (e.g., "A")
    labels: list[str] = None          # All labels associated with this wire

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
```

**Write test** (in `tests/test_schematic.py`):
```python
def test_wire_segment_creation():
    """Verify WireSegment data class works"""
    from kicad2wireBOM.schematic import WireSegment

    wire = WireSegment(
        uuid="test-uuid-123",
        start_point=(10.0, 20.0),
        end_point=(30.0, 40.0)
    )

    assert wire.uuid == "test-uuid-123"
    assert wire.start_point == (10.0, 20.0)
    assert wire.end_point == (30.0, 40.0)
    assert wire.circuit_id is None
    assert wire.labels == []
```

**Checkpoint**: ✓ WireSegment data class created and tested

### Task 2.2: Parse Wire S-Expression to WireSegment

**Write test**:
```python
def test_parse_wire_sexp_to_wiresegment():
    """Parse wire s-expression into WireSegment object"""
    from kicad2wireBOM.parser import parse_wire_element

    # Example wire s-expression (from actual fixture)
    wire_sexp = [
        'wire',
        ['pts', ['xy', 83.82, 52.07], ['xy', 92.71, 52.07]],
        ['stroke', ['width', 0], ['type', 'default']],
        ['uuid', '"0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd"']
    ]

    wire = parse_wire_element(wire_sexp)

    assert wire.start_point == (83.82, 52.07)
    assert wire.end_point == (92.71, 52.07)
    assert wire.uuid == "0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd"
```

**Implement** (in `parser.py`):
```python
from kicad2wireBOM.schematic import WireSegment

def parse_wire_element(wire_sexp):
    """
    Parse wire s-expression into WireSegment object.

    Args:
        wire_sexp: S-expression for wire element

    Returns:
        WireSegment object
    """
    # Extract pts element
    pts = find_element(wire_sexp, 'pts')
    xy_points = [e for e in pts if isinstance(e, list) and e[0] == 'xy']

    start_point = (float(xy_points[0][1]), float(xy_points[0][2]))
    end_point = (float(xy_points[1][1]), float(xy_points[1][2]))

    # Extract uuid
    uuid_elem = find_element(wire_sexp, 'uuid')
    uuid = uuid_elem[1].strip('"') if len(uuid_elem) > 1 else None

    return WireSegment(
        uuid=uuid,
        start_point=start_point,
        end_point=end_point
    )

def find_element(sexp, name):
    """Helper: Find first element in sexp list with given name"""
    for elem in sexp:
        if isinstance(elem, list) and len(elem) > 0 and str(elem[0]) == name:
            return elem
    return None
```

**Checkpoint**: ✓ Can parse wire s-expression to WireSegment object

### Task 2.3: Create Label Data Class

**Implement** (in `schematic.py`):
```python
@dataclass
class Label:
    """Represents a label in the schematic"""
    text: str
    position: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    uuid: str
    rotation: float = 0.0
```

**Write test and implementation** similar to wire parsing above.

**Checkpoint**: ✓ Label data class and parsing

### Task 2.4: Create Component Data Class

**Implement** (in `schematic.py`):
```python
@dataclass
class Component:
    """Represents a component in the schematic"""
    ref: str                    # Reference designator (e.g., "BT1", "SW1")
    schematic_position: tuple[float, float]  # (x, y) in mm

    # Aircraft coordinates (from footprint encoding)
    fs: float | None = None     # Fuselage station (inches)
    wl: float | None = None     # Waterline (inches)
    bl: float | None = None     # Buttline (inches)
    source_type: str | None = None  # "L", "R", "S", "B"
    amperage: float | None = None   # Load, rating, or source capacity

    footprint: str | None = None    # Full footprint field
```

**Checkpoint**: ✓ Component data class created

### Task 2.5: Parse Footprint Encoding

**Write test**:
```python
def test_parse_footprint_encoding():
    """Parse footprint encoding: |(fs,wl,bl)<type><amps>"""
    from kicad2wireBOM.parser import parse_footprint_encoding

    # Example: |(10,0,0)S40
    result = parse_footprint_encoding("|(10,0,0)S40")

    assert result['fs'] == 10.0
    assert result['wl'] == 0.0
    assert result['bl'] == 0.0
    assert result['source_type'] == 'S'
    assert result['amperage'] == 40.0
```

**Implement** (in `parser.py`):
```python
import re

def parse_footprint_encoding(footprint: str):
    """
    Parse footprint encoding: |(fs,wl,bl)<type><amps>

    Args:
        footprint: Footprint field string

    Returns:
        Dict with fs, wl, bl, source_type, amperage
        None if no encoding present

    Raises:
        ValueError if encoding malformed
    """
    # Regex: \|([-\d.]+),([-\d.]+),([-\d.]+)\)([LRSB])([\d.]+)
    pattern = r'\|([-\d.]+),([-\d.]+),([-\d.]+)\)([LRSB])([\d.]+)'
    match = re.search(pattern, footprint)

    if not match:
        # No encoding present (no | delimiter)
        if '|' in footprint:
            raise ValueError(f"Malformed footprint encoding: {footprint}")
        return None

    return {
        'fs': float(match.group(1)),
        'wl': float(match.group(2)),
        'bl': float(match.group(3)),
        'source_type': match.group(4),
        'amperage': float(match.group(5))
    }
```

**Checkpoint**: ✓ Can parse footprint encoding

---

## PHASE 3: Label-to-Wire Association

**Goal**: Match labels to wires using spatial proximity

### Task 3.1: Implement Point-to-Segment Distance

**Write test**:
```python
def test_point_to_segment_distance():
    """Calculate perpendicular distance from point to line segment"""
    from kicad2wireBOM.label_association import point_to_segment_distance
    import math

    # Point at (0, 1), segment from (0, 0) to (2, 0) (horizontal)
    # Perpendicular distance should be 1.0
    dist = point_to_segment_distance(0, 1, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001

    # Point at (1, 1), same segment
    # Perpendicular distance should be 1.0
    dist = point_to_segment_distance(1, 1, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001

    # Point at (3, 0), segment from (0, 0) to (2, 0)
    # Beyond segment end, distance should be 1.0 (to endpoint)
    dist = point_to_segment_distance(3, 0, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001
```

**Create**: `kicad2wireBOM/label_association.py`

**Implement**:
```python
# ABOUTME: This module handles label-to-wire association using proximity matching
# ABOUTME: Implements geometric algorithms for distance calculation and label assignment

import math

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """
    Calculate perpendicular distance from point to line segment.

    Args:
        px, py: Point coordinates
        x1, y1: Segment start coordinates
        x2, y2: Segment end coordinates

    Returns:
        Minimum distance from point to segment (float)
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
    # 0 = at start, 1 = at end, between = on segment
    t = max(0, min(1, (dx*sx + dy*sy) / segment_length_sq))

    # Closest point on segment
    closest_x = x1 + t * sx
    closest_y = y1 + t * sy

    # Distance from point to closest point
    dist_x = px - closest_x
    dist_y = py - closest_y

    return math.sqrt(dist_x*dist_x + dist_y*dist_y)
```

**Checkpoint**: ✓ Point-to-segment distance calculation working

### Task 3.2: Associate Labels with Wires

**Write test**:
```python
def test_associate_labels_with_wires():
    """Associate labels with nearest wire segments"""
    from kicad2wireBOM.label_association import associate_labels_with_wires
    from kicad2wireBOM.schematic import WireSegment, Label

    wires = [
        WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0)),
        WireSegment(uuid="w2", start_point=(0, 50), end_point=(100, 50))
    ]

    labels = [
        Label(text="P1A", position=(50, 5), uuid="l1"),   # Near wire 1
        Label(text="G1A", position=(50, 55), uuid="l2")   # Near wire 2
    ]

    associate_labels_with_wires(wires, labels, threshold=10.0)

    assert "P1A" in wires[0].labels
    assert "G1A" in wires[1].labels
    assert wires[0].circuit_id == "P1A"
    assert wires[1].circuit_id == "G1A"
```

**Implement**:
```python
def associate_labels_with_wires(wires, labels, threshold=10.0):
    """
    Associate labels with nearest wire segments using proximity matching.

    Args:
        wires: List of WireSegment objects
        labels: List of Label objects
        threshold: Maximum distance (mm) for association (default: 10.0mm)
                  This value is configurable and can be adjusted if needed.
                  Set in DEFAULT_CONFIG or passed from command line.

    Modifies:
        Updates wire.labels and wire.circuit_id for each wire

    Note:
        The 10mm default threshold was chosen based on typical KiCAD label
        placement. If testing shows labels are missed or incorrectly associated,
        this value can be adjusted via:
        - DEFAULT_CONFIG['label_threshold'] in reference_data.py
        - CLI flag: --label-threshold <mm>
    """
    for label in labels:
        # Check if label text matches circuit ID pattern
        if not is_circuit_id(label.text):
            continue  # Skip non-circuit-ID labels (notes)

        # Find nearest wire
        min_distance = float('inf')
        nearest_wire = None

        for wire in wires:
            dist = point_to_segment_distance(
                label.position[0], label.position[1],
                wire.start_point[0], wire.start_point[1],
                wire.end_point[0], wire.end_point[1]
            )

            if dist < min_distance:
                min_distance = dist
                nearest_wire = wire

        # Associate if within threshold
        if min_distance <= threshold and nearest_wire:
            nearest_wire.labels.append(label.text)
            nearest_wire.circuit_id = label.text
            # Parse circuit ID into components
            parse_circuit_id(nearest_wire)

def is_circuit_id(text):
    """Check if text matches circuit ID pattern: P1A, L-12-B, etc."""
    import re
    # Pattern: Letter, optional dash, digits, optional dash, letter
    pattern = r'^[A-Z]-?\d+-?[A-Z]$'
    return re.match(pattern, text) is not None

def parse_circuit_id(wire):
    """Parse wire.circuit_id into system_code, circuit_num, segment_letter"""
    import re
    if not wire.circuit_id:
        return

    # Pattern: ([A-Z])-?(\d+)-?([A-Z])
    pattern = r'^([A-Z])-?(\d+)-?([A-Z])$'
    match = re.match(pattern, wire.circuit_id)

    if match:
        wire.system_code = match.group(1)
        wire.circuit_num = match.group(2)
        wire.segment_letter = match.group(3)
```

**Checkpoint**: ✓ Label-to-wire association working

---

## PHASE 4: Wire Calculations

**Goal**: Calculate wire length, gauge, color

### Task 4.1: Reference Data Tables

**Create**: `kicad2wireBOM/reference_data.py`

**CRITICAL TASK**: Extract actual values from Aeroelectric Connection reference materials

**Source Locations**:
- Wire resistance: `docs/references/aeroelectric_connection/` - Chapter 5
- Wire ampacity: `docs/references/aeroelectric_connection/` - Bob Nuckolls' bundled wire tables

**Implement**:
```python
# ABOUTME: This module stores reference data for wire calculations
# ABOUTME: Includes wire resistance, ampacity, and color mapping tables

# Wire resistance (ohms per foot)
# SOURCE: Aeroelectric Connection Chapter 5, [page/table reference]
# EXTRACTED: [Your name], [Date]
# NOTE: Use bundled/conduit values (conservative), not free-air
WIRE_RESISTANCE = {
    # TODO: Extract actual values from Aeroelectric Connection Ch5
    # These are placeholder estimates - REPLACE WITH REAL DATA
    22: 0.016,  # TODO: Verify from source
    20: 0.010,  # TODO: Verify from source
    18: 0.0064, # TODO: Verify from source
    16: 0.004,  # TODO: Verify from source
    14: 0.0025, # TODO: Verify from source
    12: 0.0016, # TODO: Verify from source
    10: 0.001,  # TODO: Verify from source
    8: 0.0006,  # TODO: Verify from source
    6: 0.0004,  # TODO: Verify from source
    4: 0.00025, # TODO: Verify from source
    2: 0.00016  # TODO: Verify from source
}

# Wire ampacity (max amps)
# SOURCE: Aeroelectric Connection bundled wire ampacity tables
# EXTRACTED: [Your name], [Date]
# IMPORTANT: Use BUNDLED wire values (conservative), NOT free-air values
WIRE_AMPACITY = {
    # TODO: Extract actual values from Aeroelectric Connection
    # These are placeholder estimates - REPLACE WITH REAL DATA
    22: 5,    # TODO: Verify from source
    20: 7.5,  # TODO: Verify from source
    18: 10,   # TODO: Verify from source
    16: 13,   # TODO: Verify from source
    14: 17,   # TODO: Verify from source
    12: 23,   # TODO: Verify from source
    10: 33,   # TODO: Verify from source
    8: 46,    # TODO: Verify from source
    6: 60,    # TODO: Verify from source
    4: 80,    # TODO: Verify from source
    2: 100    # TODO: Verify from source
}

# System code to wire color mapping - FROM EAWMS DOCS
SYSTEM_COLOR_MAP = {
    'L': 'White',    # Lighting
    'P': 'Red',      # Power
    'G': 'Black',    # Ground
    'R': 'Gray',     # Radio/Nav
    'E': 'Brown',    # Engine Instruments
    'K': 'Orange',   # Engine Control
    'M': 'Yellow',   # Miscellaneous
    'W': 'Green',    # Warning Systems
    'A': 'Blue',     # Avionics
    'F': 'Violet',   # Fuel Systems
    'U': 'Pink'      # Utility
}

# Standard AWG sizes for aircraft wiring
STANDARD_AWG_SIZES = [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]

# Default configuration
DEFAULT_CONFIG = {
    'system_voltage': 12,        # volts
    'slack_length': 24,          # inches
    'voltage_drop_percent': 0.05,  # 5%
    'permissive_mode': False,
    'engineering_mode': False,
    'default_wire_type': 'M22759/16',
    'label_threshold': 10.0      # mm
}
```

**INSTRUCTIONS**:
1. Read Chapter 5 of Aeroelectric Connection (in `docs/references/aeroelectric_connection/`)
2. Find wire resistance table (ohms per foot)
3. Find bundled wire ampacity table (NOT free-air)
4. Extract values for AWG sizes: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22
5. Replace TODO comments with actual values
6. Document source (page/table number) in comments
7. Add your name and date to EXTRACTED comment
8. Remove all TODO comments when complete

**VALIDATION**:
- Compare your values with archived design doc estimates
- If significantly different, double-check source
- Bundled values should be more conservative (lower) than free-air

**Checkpoint**: ✓ Reference data tables created with REAL values from Aeroelectric Connection

### Task 4.2: Wire Length Calculation

**Create**: `kicad2wireBOM/wire_calculator.py`

**Write test**:
```python
def test_calculate_wire_length():
    """Calculate wire length using Manhattan distance"""
    from kicad2wireBOM.wire_calculator import calculate_wire_length
    from kicad2wireBOM.schematic import Component

    comp1 = Component(
        ref="BT1",
        schematic_position=(0, 0),
        fs=10.0, wl=0.0, bl=0.0
    )

    comp2 = Component(
        ref="L1",
        schematic_position=(100, 100),  # Irrelevant for length calc
        fs=20.0, wl=5.0, bl=3.0
    )

    # Manhattan: |20-10| + |5-0| + |3-0| = 10 + 5 + 3 = 18 inches
    # + 24" slack = 42 inches
    length = calculate_wire_length(comp1, comp2, slack=24)
    assert length == 42.0
```

**Implement**:
```python
# ABOUTME: This module handles wire calculations including length, gauge, and voltage drop
# ABOUTME: Implements Manhattan distance and wire gauge selection algorithms

def calculate_wire_length(comp1, comp2, slack=24):
    """
    Calculate wire length using Manhattan distance + slack.

    Args:
        comp1, comp2: Component objects with fs, wl, bl coordinates (inches)
        slack: Additional length for termination/routing (inches)

    Returns:
        Total wire length in inches
    """
    manhattan = abs(comp1.fs - comp2.fs) + \
                abs(comp1.wl - comp2.wl) + \
                abs(comp1.bl - comp2.bl)

    return manhattan + slack
```

**Checkpoint**: ✓ Wire length calculation working

### Task 4.3: Wire Gauge Selection

**Write test**:
```python
def test_select_wire_gauge():
    """Select wire gauge based on voltage drop and ampacity"""
    from kicad2wireBOM.wire_calculator import select_wire_gauge

    # 5A load, 50" wire, 12V system
    # Should select 20 AWG or larger
    result = select_wire_gauge(current=5.0, length=50, system_voltage=12)

    assert result['awg'] in [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
    assert result['voltage_drop_volts'] <= 0.6  # 5% of 12V
    assert result['voltage_drop_percent'] <= 5.0
```

**Implement**:
```python
from kicad2wireBOM.reference_data import WIRE_RESISTANCE, WIRE_AMPACITY

def select_wire_gauge(current, length, system_voltage=12):
    """
    Select minimum wire gauge meeting voltage drop and ampacity constraints.

    Args:
        current: Wire current in amps
        length: Wire length in inches
        system_voltage: System voltage in volts

    Returns:
        Dict with awg, voltage_drop_volts, voltage_drop_percent
    """
    max_voltage_drop = system_voltage * 0.05  # 5%

    # Try each AWG from smallest to largest wire
    for awg in [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]:
        # Check ampacity constraint
        if current > WIRE_AMPACITY[awg]:
            continue  # Wire too small for current

        # Check voltage drop constraint
        resistance_per_foot = WIRE_RESISTANCE[awg]
        voltage_drop = current * resistance_per_foot * (length / 12)

        if voltage_drop <= max_voltage_drop:
            # This AWG meets both constraints
            voltage_drop_percent = (voltage_drop / system_voltage) * 100
            return {
                'awg': awg,
                'voltage_drop_volts': voltage_drop,
                'voltage_drop_percent': voltage_drop_percent
            }

    # If we get here, even 2 AWG is insufficient
    # Return 2 AWG with warning
    awg = 2
    voltage_drop = current * WIRE_RESISTANCE[awg] * (length / 12)
    voltage_drop_percent = (voltage_drop / system_voltage) * 100

    return {
        'awg': awg,
        'voltage_drop_volts': voltage_drop,
        'voltage_drop_percent': voltage_drop_percent,
        'warning': 'Wire gauge insufficient - exceeds voltage drop threshold'
    }
```

**Checkpoint**: ✓ Wire gauge selection working

### Task 4.4: Wire Color Assignment

**Write test**:
```python
def test_assign_wire_color():
    """Assign wire color based on system code"""
    from kicad2wireBOM.wire_calculator import assign_wire_color

    assert assign_wire_color('L') == 'White'   # Lighting
    assert assign_wire_color('P') == 'Red'     # Power
    assert assign_wire_color('G') == 'Black'   # Ground
    assert assign_wire_color('R') == 'Gray'    # Radio
```

**Implement**:
```python
from kicad2wireBOM.reference_data import SYSTEM_COLOR_MAP

def assign_wire_color(system_code):
    """
    Assign wire color based on system code.

    Args:
        system_code: Single letter system code (e.g., 'L', 'P', 'G')

    Returns:
        Color string (e.g., 'White', 'Red', 'Black')
    """
    return SYSTEM_COLOR_MAP.get(system_code, 'White')  # Default to white
```

**Checkpoint**: ✓ Wire color assignment working

---

## PHASE 5: End-to-End Integration

**Goal**: Process complete schematic to wire BOM

### Task 5.1: Integration Test with test_01_fixture

**Write test** (in `tests/test_integration.py`):
```python
def test_process_test_01_fixture():
    """End-to-end test: Process test_01_fixture.kicad_sch to wire BOM"""
    from pathlib import Path
    from kicad2wireBOM.main import process_schematic

    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    bom = process_schematic(fixture_path)

    # test_01 should have 2 wires: P1A and G1A
    assert len(bom.wires) == 2

    # Check wire labels
    wire_labels = [w.wire_label for w in bom.wires]
    assert 'P1A' in wire_labels
    assert 'G1A' in wire_labels

    # Check wire colors
    p_wire = next(w for w in bom.wires if w.wire_label == 'P1A')
    g_wire = next(w for w in bom.wires if w.wire_label == 'G1A')

    assert p_wire.wire_color == 'Red'    # Power = Red
    assert g_wire.wire_color == 'Black'  # Ground = Black
```

**Create**: `kicad2wireBOM/main.py`

**Implement**:
```python
# ABOUTME: This module provides the main orchestration for processing schematics to BOMs
# ABOUTME: Integrates parsing, label association, calculations, and BOM generation

from pathlib import Path
from dataclasses import dataclass
from kicad2wireBOM.parser import (
    parse_schematic_file, extract_wires, extract_labels,
    extract_symbols, parse_wire_element, parse_label_element,
    parse_symbol_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.wire_calculator import (
    calculate_wire_length, select_wire_gauge, assign_wire_color
)
from kicad2wireBOM.reference_data import DEFAULT_CONFIG

@dataclass
class WireConnection:
    """Single wire in the BOM"""
    wire_label: str
    from_ref: str
    to_ref: str
    wire_gauge: str
    wire_color: str
    length: float
    wire_type: str
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

@dataclass
class WireBOM:
    """Complete wire BOM"""
    wires: list[WireConnection]
    config: dict
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

def process_schematic(schematic_path, config=None):
    """
    Process KiCAD schematic to wire BOM.

    Args:
        schematic_path: Path to .kicad_sch file
        config: Configuration dict (uses defaults if None)

    Returns:
        WireBOM object
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    # Parse schematic
    sexp = parse_schematic_file(schematic_path)

    # Extract elements
    wire_sexps = extract_wires(sexp)
    label_sexps = extract_labels(sexp)
    symbol_sexps = extract_symbols(sexp)

    # Convert to data objects
    wires = [parse_wire_element(w) for w in wire_sexps]
    labels = [parse_label_element(l) for l in label_sexps]
    components = [parse_symbol_element(s) for s in symbol_sexps]

    # Associate labels with wires
    associate_labels_with_wires(wires, labels, config['label_threshold'])

    # Build wire connections
    wire_connections = []

    for wire in wires:
        if not wire.circuit_id:
            continue  # Skip unlabeled wires (TODO: handle in permissive mode)

        # Find components at wire endpoints
        # (Simplified: use first 2 components for now)
        # TODO: Implement proper endpoint-to-component matching
        if len(components) < 2:
            continue

        comp1 = components[0]
        comp2 = components[1]

        # Calculate length
        length = calculate_wire_length(comp1, comp2, config['slack_length'])

        # Determine current (use first component's amperage)
        current = comp1.amperage or 0

        # Select gauge
        gauge_result = select_wire_gauge(current, length, config['system_voltage'])

        # Assign color
        color = assign_wire_color(wire.system_code)

        # Create wire connection
        wire_conn = WireConnection(
            wire_label=wire.circuit_id,
            from_ref=f"{comp1.ref}-1",  # TODO: Actual pin number
            to_ref=f"{comp2.ref}-1",
            wire_gauge=f"{gauge_result['awg']} AWG",
            wire_color=color,
            length=length,
            wire_type=config['default_wire_type']
        )

        wire_connections.append(wire_conn)

    return WireBOM(wires=wire_connections, config=config)
```

**NOTE**: This is simplified integration. Full implementation needs:
- Proper endpoint-to-component matching
- Pin number extraction
- Permissive mode handling
- Validation checks

**Run test**: Should PASS (basic integration working)

**Checkpoint**: ✓ End-to-end processing working (basic)

---

## PHASE 6: Output Generation

**Goal**: Generate CSV and Markdown output files

### Task 6.1: CSV Output (Builder Mode)

**Create**: `kicad2wireBOM/output_csv.py`

**Write test**:
```python
def test_write_builder_csv():
    """Generate CSV output in builder mode"""
    from kicad2wireBOM.output_csv import write_builder_csv
    from kicad2wireBOM.main import WireConnection, WireBOM
    from pathlib import Path
    import csv

    wires = [
        WireConnection(
            wire_label="P1A",
            from_ref="BT1-1",
            to_ref="L1-1",
            wire_gauge="20 AWG",
            wire_color="Red",
            length=42.0,
            wire_type="M22759/16"
        )
    ]

    bom = WireBOM(wires=wires, config={})
    output_path = Path("tests/output_test.csv")

    write_builder_csv(bom, output_path)

    # Verify CSV was created
    assert output_path.exists()

    # Verify contents
    with output_path.open('r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['Wire Label'] == 'P1A'
    assert rows[0]['From'] == 'BT1-1'
    assert rows[0]['Wire Gauge'] == '20 AWG'

    # Cleanup
    output_path.unlink()
```

**Implement**:
```python
# ABOUTME: This module generates CSV output files for wire BOMs
# ABOUTME: Supports builder mode (basic) and engineering mode (detailed) outputs

import csv
from pathlib import Path

def write_builder_csv(bom, output_path):
    """
    Write wire BOM to CSV file in builder mode.

    Args:
        bom: WireBOM object
        output_path: Path for output CSV file
    """
    fieldnames = [
        'Wire Label',
        'From',
        'To',
        'Wire Gauge',
        'Wire Color',
        'Length',
        'Wire Type',
        'Warnings'
    ]

    with output_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for wire in bom.wires:
            writer.writerow({
                'Wire Label': wire.wire_label,
                'From': wire.from_ref,
                'To': wire.to_ref,
                'Wire Gauge': wire.wire_gauge,
                'Wire Color': wire.wire_color,
                'Length': f"{wire.length:.1f} inches",
                'Wire Type': wire.wire_type,
                'Warnings': '; '.join(wire.warnings) if wire.warnings else ''
            })
```

**Checkpoint**: ✓ CSV output generation working

### Task 6.2: Markdown Output (Builder Mode)

**Create**: `kicad2wireBOM/output_markdown.py`

**Implement** similar to CSV, but generate Markdown tables

**Checkpoint**: ✓ Markdown output generation working

---

## PHASE 7: CLI and Finalization

**Goal**: Command-line interface and polish

### Task 7.1: Create CLI Entry Point

**Create**: `kicad2wireBOM/__main__.py`

**Implement**:
```python
# ABOUTME: This module provides the command-line interface entry point
# ABOUTME: Handles argument parsing, file I/O, and orchestrates processing

import argparse
from pathlib import Path
from kicad2wireBOM.main import process_schematic
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG

def main():
    parser = argparse.ArgumentParser(
        description='Generate wire BOM from KiCAD schematic'
    )
    parser.add_argument('source', type=Path, help='KiCAD schematic file (.kicad_sch)')
    parser.add_argument('dest', type=Path, nargs='?', help='Output file (CSV or MD)')
    parser.add_argument('--system-voltage', type=float, default=12,
                        help='System voltage (default: 12V)')
    parser.add_argument('--slack-length', type=float, default=24,
                        help='Extra wire length in inches (default: 24")')
    parser.add_argument('--label-threshold', type=float, default=10.0,
                        help='Max distance (mm) for label-to-wire association (default: 10mm)')

    args = parser.parse_args()

    # Verify source file exists
    if not args.source.exists():
        print(f"Error: Schematic file not found: {args.source}")
        return 1

    # Auto-generate output filename if not provided
    if not args.dest:
        args.dest = args.source.with_suffix('.csv').with_stem(
            f"{args.source.stem}_REV001"
        )

    # Process schematic
    config = DEFAULT_CONFIG.copy()
    config['system_voltage'] = args.system_voltage
    config['slack_length'] = args.slack_length
    config['label_threshold'] = args.label_threshold

    bom = process_schematic(args.source, config)

    # Write output
    write_builder_csv(bom, args.dest)

    print(f"Wire BOM generated: {args.dest}")
    print(f"Total wires: {len(bom.wires)}")

    return 0

if __name__ == '__main__':
    exit(main())
```

**Test manually**:
```bash
python -m kicad2wireBOM tests/fixtures/test_01_fixture.kicad_sch output.csv
```

**Checkpoint**: ✓ CLI working

### Task 7.2: Validation and Error Handling

**Add validation checks**:
- Missing labels (strict vs permissive mode)
- Orphaned labels (label far from any wire)
- Duplicate circuit IDs
- Missing component data

**Implement in separate module**: `kicad2wireBOM/validator.py`

**Checkpoint**: ✓ Validation working

### Task 7.3: Documentation

**Create**:
- `README.md` - User documentation
- Module docstrings (already done with ABOUTME comments)
- Usage examples

**Checkpoint**: ✓ Documentation complete

---

## PHASE 8: Testing and Refinement

**Goal**: Comprehensive testing with all fixtures

### Task 8.1: Test with test_02_fixture

**Write integration test** for test_02_fixture.kicad_sch

**Expected**: 3 wires (L2A, L2B, G1A)

**Verify**: Labels associate correctly, calculations accurate

### Task 8.2: Test with test_03_fixture

**Write integration test** for test_03_fixture.kicad_sch

**Expected**: 2 wires (P1A, P2A) both connecting to junction

**This is the critical test** - validates wire granularity preservation!

### Task 8.3: Add Edge Case Tests

**Test scenarios**:
- Missing labels (permissive mode)
- Orphaned labels
- Malformed footprint encoding
- Negative coordinates
- Zero-length wires

**Checkpoint**: ✓ All tests passing

---

## COMPLETION CHECKLIST

### Core Functionality
- [ ] Parse .kicad_sch files to s-expressions
- [ ] Extract wire segments, labels, components
- [ ] Parse footprint encoding
- [ ] Associate labels with wires (proximity)
- [ ] Calculate wire lengths (Manhattan + slack)
- [ ] Select wire gauge (voltage drop + ampacity)
- [ ] Assign wire colors (system code mapping)
- [ ] Generate CSV output (builder mode)
- [ ] Generate Markdown output (builder mode)
- [ ] CLI with argument parsing

### Testing
- [ ] All unit tests pass
- [ ] Integration test with test_01_fixture
- [ ] Integration test with test_02_fixture
- [ ] Integration test with test_03_fixture (critical!)
- [ ] Edge case tests

### Documentation
- [ ] Module docstrings (ABOUTME comments)
- [ ] README.md with usage examples
- [ ] Code comments for complex algorithms

### Polish
- [ ] Validation and error messages
- [ ] Strict vs permissive mode
- [ ] Engineering mode (optional - can defer)
- [ ] Configuration file loading (optional - can defer)

---

## WHEN YOU'RE STUCK

### Check These First
1. Re-read `programmer_notes.md` for algorithm details
2. Examine test fixture files to understand data structure
3. Check `kicad2wireBOM_design.md` for specification

### Common Issues
- **S-expression parsing weird**: Check if using sexpdata correctly, handle Symbol types
- **Labels not associating**: Verify distance calculation, check threshold value
- **Wire calculations wrong**: Double-check units (mm vs inches, feet vs inches)
- **Tests failing**: Read error messages carefully, verify test expectations match fixtures

### Circle K Protocol
If you find **design inconsistencies** or **architectural issues**:
1. Say "Strange things are afoot at the Circle K"
2. Explain the issue clearly
3. Suggest a solution or ask for Tom's input

### Get Help
- Tom can answer questions via `required_from_tom.md`
- Architect left detailed notes in `programmer_notes.md`
- Design spec has algorithm pseudocode

---

## FINAL NOTES

**This is a well-scoped project** with:
- Clear requirements
- Real test fixtures
- Defined algorithms
- Achievable in phases

**Use TDD religiously**:
- Write test first
- Watch it fail
- Write minimal code to pass
- Refactor
- Commit

**Test fixtures are your friends**:
- test_01: Simple case (learning)
- test_02: Multi-segment (complexity)
- test_03: Junction (validates architecture!)

**Success looks like**:
- All three fixtures process correctly
- BOM output is accurate
- Wire granularity preserved (test_03!)
- Tom can generate wire BOMs for his aircraft

**You've got this!** Clear problem, solid design, good test data. Just work through the phases systematically.

---

**Document Version**: 1.0
**Date**: 2025-10-18
**Architect**: Claude
