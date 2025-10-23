# kicad2wireBOM: Design Specification

## Document Overview

**Purpose**: Comprehensive design specification for kicad2wireBOM tool - a wire Bill of Materials generator for experimental aircraft electrical systems.

**Version**: 2.7 (LocLoad Custom Field)
**Date**: 2025-10-23
**Status**: Phase 1-6 Complete - All Core Features Implemented ✅

## Design Revision History

### Version 2.7 (2025-10-23)
**Changed**: Migrated from Footprint field to dedicated LocLoad custom field

**Sections Modified**:
- Section 2.2: Component Data Encoding (field name, format, examples)
- All references throughout document updated from Footprint to LocLoad

**Rationale**: Using KiCad's built-in Footprint field for custom data was an overload. A dedicated custom field named `LocLoad` provides cleaner separation and clearer intent. Format simplified by removing leading `|` delimiter and adding `G` type for ground points.

**Format Change**:
- Old: `|(FS,WL,BL){S|L|R}<value>` in Footprint field
- New: `(FS,WL,BL){S|L|R|G}<value>` in LocLoad custom field
- Added G type for ground connection points (value optional)

**Impact**:
- Parser reads from LocLoad custom field instead of Footprint
- Component dataclass unchanged (still stores parsed values: fs, wl, bl, load, rating, source)
- All 150 tests passing with updated fixtures

### Version 2.6 (2025-10-21)
**Changed**: Added unified BOM generation architecture to integrate multipoint logic into CLI

**Sections Modified**:
- Section 4.5: New section defining unified BOM entry generation
- Section 10.1: Added `bom_generator.py` to module structure

**Problem Identified**: Multipoint connection logic exists and passes integration tests, but CLI (`__main__.py`) doesn't use it. This creates a gap where tests pass but CSV output is incorrect for 3+way connections.

**Rationale**: Code duplication between CLI and integration tests creates maintenance burden and correctness issues. A single unified function ensures both CLI and tests use identical logic, eliminating the gap between tested code and production code.

**Impact**:
- Creates new module `bom_generator.py` with `generate_bom_entries()` function
- CLI will correctly handle 3+way connections in CSV output
- Integration tests will verify same code path as CLI uses
- Eliminates code duplication and tech debt

### Version 2.5 (2025-10-21)
**Changed**: Corrected common pin identification to use segment-level analysis (not fragment-level)

**Sections Modified**:
- Section 4.4: Rewrote algorithm using fragment/connection/junction/segment terminology

**Rationale**: Initial algorithm worked at wrong abstraction level (individual wire fragments). Correct approach: trace SEGMENTS (chains of fragments from pin to junction), checking if segment contains labeled fragments. Connections (2-fragment points) are transparent; junctions (3+ fragment points) are segment boundaries.

**Impact**: Algorithm now correctly identifies common pin by analyzing segments, not individual fragments.

### Version 2.4 (2025-10-21)
**Changed**: Clarified common pin identification algorithm for 3+way connections (SUPERSEDED by v2.5)

**Sections Modified**:
- Section 4.4: Added detailed algorithm for identifying common pin with BFS stopping constraint

**Rationale**: Original design said "pin NOT reached by any labeled segment" but didn't specify how to determine this in tree topology. Clarified that BFS must stop at other group pins to check only the pin's immediate branch, not the entire connected component.

**Impact**: Provides unambiguous algorithm for Programmer to implement `identify_common_pin()` method.

### Version 2.3 (2025-10-21)
**Changed**: Added 3+way connection detection, validation, and BOM generation architecture

**Sections Modified**:
- Section 4.4: New section defining 3+way connections (N ≥ 3 pins connected through junctions)

**Rationale**: Real aircraft schematics have multi-point connections (multiple grounds to battery, multiple feeds from distribution point). The (N-1) labeling convention provides an intuitive, unambiguous way to specify which pin is the common endpoint.

**Impact**: Enables correct BOM generation for multi-point connections. Example: 4 pins with 3 labels → each labeled wire shows branch-pin → common-unlabeled-pin.

**Key Design**:
- N pins → (N-1) labels required
- Unlabeled pin is the common endpoint
- Unlabeled segments form backbone structure
- Each labeled wire generates one BOM entry to common pin

### Version 2.2 (2025-10-20)
**Changed**: Added wire_endpoint tracing to trace_to_component() algorithm

**Sections Modified**:
- Section 4.3: Wire-to-Component Matching - Added third case to handle wire_endpoint nodes

**Rationale**: Labeled wire segments often connect to unlabeled wire segments, creating wire_endpoint nodes. The tracing algorithm must continue through these nodes to find component pins, using the same recursive pattern as junction tracing.

**Impact**: Completes the graph traversal algorithm to handle all three node types (component_pin, junction, wire_endpoint).

### Version 2.1 (2025-10-20)
**Changed**: BOM output format for junction handling and component/pin separation

**Sections Modified**:
- Section 4.3: Wire-to-Component Matching - Changed to trace through junctions to show component-to-component connections
- Section 7.3: Builder Mode CSV Columns - Split "From/To" into separate component and pin columns

**Rationale**: In experimental aircraft, junctions in schematics represent electrical connections but must become physical components (terminal blocks, connectors) in the actual build. BOM output now shows component-to-component connections with junctions being transparent, and separates component references from pin numbers for clarity.

**Example Impact** (test_03A fixture):
- OLD: `P1A,UNKNOWN,SW1-3,...`
- NEW: `P1A,J1,1,SW1,3,...` (traces through junction to show J1-pin1 ↔ SW1-pin3)

---

## Critical Architectural Decision

**INPUT FORMAT CHANGE**: This tool parses **KiCAD schematic files** (`.kicad_sch`), NOT netlists (`.net`).

**Why**: KiCAD netlists collapse wires into nets based on electrical connectivity. For wire harness manufacturing, we need **physical wire-level granularity**:
- Two wires connecting to the same terminal are electrically one net
- But they are physically two distinct wires requiring separate labels, lengths, and BOM entries
- The schematic preserves wire segment information before net consolidation

**Example Problem**:
```
Schematic shows:
  Wire 1 (labeled P1A): SW1 pin 1 → TB1 pin 1
  Wire 2 (labeled P2A): SW2 pin 1 → TB1 pin 1

Netlist collapses to:
  Net "Power_1": {SW1-1, SW2-1, TB1-1}  ← Wire-level info LOST
```

---

## 1. Overview and Goals

### 1.1 Purpose

Generate comprehensive wire Bills of Materials (BOMs) from KiCAD schematic files for experimental aircraft electrical systems. The tool automates wire specification by parsing individual wire segments with their labels and calculating appropriate wire gauges, lengths, and colors based on physical installation requirements.

### 1.2 Key Innovation

**Wire-Level Parsing**: Unlike PCB tools that work with nets, kicad2wireBOM extracts individual wire segments from schematics, preserving:
- Wire labels placed directly on wire segments in the schematic
- Physical routing between component pins
- Multiple wires on the same electrical net (common at junction points)

**Custom LocLoad Field**: Physical installation data is encoded in component LocLoad custom fields:
- Aircraft coordinates (FS/WL/BL) for wire length calculations
- Electrical load/rating for wire gauge calculations
- Source type identification for special handling

### 1.3 Target Users

Experimental aircraft builders using KiCAD for electrical system design who need accurate wire harness BOMs for construction and regulatory compliance.

### 1.4 Core Philosophy

**Automate what can be calculated, validate what can be checked, warn about uncertainties, but always produce usable output.**

Default to strict validation (encourage complete schematics) with permissive mode available for iterative design work.

---

## 2. Input Requirements

### 2.1 Primary Input

KiCAD schematic file (`.kicad_sch` format, KiCAD v8+) in s-expression format.

**Format**: Lisp-style s-expressions, human-readable text format.

**File Structure**:
```lisp
(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (lib_symbols ...)
  (wire ...)
  (wire ...)
  (label ...)
  (junction ...)
  (symbol ...)
)
```

### 2.2 Component Data Encoding in LocLoad Custom Field

Component physical location and electrical characteristics are encoded in a custom KiCad field named **LocLoad** using a compact, human-readable format.

**Format**: `(<fs>,<wl>,<bl>)<type><value>`

**Components**:
- **Coordinates**: `(fs,wl,bl)` - aircraft coordinates in inches (decimals supported, negative values for left side)
  - **FS** (Fuselage Station): Longitudinal position from datum (+forward/-aft)
  - **WL** (Waterline): Vertical position from datum (+above/-below)
  - **BL** (Buttline): Lateral position from centerline (+right/-left)
- **Type Letter**: Single character indicating electrical role/type
  - **L**: Load - component consumes power (lights, radios, motors)
  - **R**: Rating - pass-through device capacity (switches, breakers, connectors)
  - **S**: Source - power source (battery, alternator, generator)
  - **G**: Ground - ground connection point (value optional)
- **Value**: Numeric amperage value for load/rating/source capacity (optional for G type)

**Examples**:
```
(200.0,35.5,10.0)L2.5
  → Light at FS=200.0, WL=35.5, BL=10.0, drawing 2.5A

(150.0,30.0,0.0)R20
  → Switch at FS=150.0, WL=30.0, BL=0.0 (centerline), rated 20A

(10,0,0)S40
  → Battery at FS=10, WL=0, BL=0, 40A capacity

(0,10,0)G
  → Ground point at FS=0, WL=10, BL=0
```

**Parsing**:
- Regex pattern: `\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\)([LRSG])([\d.]*)`
- Missing LocLoad field: Component has no physical data (handled in permissive mode)
- Invalid encoding: Parse error with helpful message
- Parsed values stored in Component dataclass (fs, wl, bl, load, rating, source)

**Design Rationale**:
- **Dedicated field**: Clean separation from KiCad built-in fields
- **Compact**: ~20 chars for typical encoding
- **Human-typeable**: Minimal special characters, logical grouping
- **Unambiguous**: Simple regex parsing, clear structure

### 2.3 Wire Segment Labels

Wires in the schematic have labels attached that identify the circuit per EAWMS (Experimental Aircraft Wire Marking Standard) format.

**Label Format**: Circuit IDs following pattern `[SYSTEM][CIRCUIT][SEGMENT]`

**Components**:
- **SYSTEM**: Single letter system code (L, P, G, R, E, K, M, W, A, F, U)
- **CIRCUIT**: Numeric circuit identifier (1, 2, 3... or 001, 002...)
- **SEGMENT**: Single letter segment identifier (A, B, C...)

**Examples**:
- `L1A` → Lighting system, circuit 1, segment A
- `P12B` → Power system, circuit 12, segment B
- `G1A` → Ground system, circuit 1, segment A

**Label Placement**:
- Labels are placed on wire segments in the KiCAD schematic
- A wire segment may have multiple labels (circuit ID + notes)
- Only labels matching circuit ID pattern are used for wire marking
- Other labels are treated as notes/comments

**Label Association**:
- Tool calculates spatial proximity between label positions and wire segments
- Label is associated with closest wire segment (within threshold)
- Distance threshold: 10mm in schematic units (configurable)

**Multiple Labels on Same Wire**:
- If multiple circuit ID labels on one wire: Warning (ambiguous)
- If circuit ID + note labels: Use circuit ID, ignore notes
- Circuit ID detection: Regex pattern `^[A-Z]\d+[A-Z]$` (compact) or `^[A-Z]-\d+-[A-Z]$` (dashes)

---

## 3. Schematic Data Extraction

### 3.1 S-Expression Parsing

**Library**: Use Python `sexpdata` library or write custom recursive parser.

**Parsing Strategy**:
1. Read `.kicad_sch` file as text
2. Parse s-expressions into nested Python data structures
3. Extract relevant top-level elements: `wire`, `label`, `junction`, `symbol`

**Data Structures**:
```python
# Wire segment from schematic
(wire
  (pts
    (xy 83.82 52.07)
    (xy 92.71 52.07)
  )
  (stroke (width 0) (type default))
  (uuid "0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd")
)

# Label from schematic
(label "G1A"
  (at 107.95 60.96 0)
  (effects (font (size 1.27 1.27)) (justify left bottom))
  (uuid "4c75cce0-2c4a-4ce2-be43-76f5f6f3eb7b")
)

# Junction point (where multiple wires meet)
(junction
  (at 144.78 86.36)
  (diameter 0)
  (color 0 0 0 0)
  (uuid "51609a84-6043-4d22-9ef7-15e32380f2f0")
)

# Component symbol with pins
(symbol
  (lib_id "Device:Battery")
  (at 95.25 77.47 90)
  (uuid "028846d9-a6f8-4001-a8de-13fb5c844305")
  (property "Reference" "BT1" ...)
  (property "LocLoad" "(10,0,0)S40" ...)
  (pin "1" (uuid "..."))
  (pin "2" (uuid "..."))
)
```

### 3.2 Wire Segment Extraction

**Parse Wire Elements**:
- Extract all `(wire ...)` blocks from schematic
- Each wire has:
  - Start point: `(xy x1 y1)`
  - End point: `(xy x2 y2)`
  - UUID: Unique identifier
  - Stroke properties (optional)

**Create WireSegment Objects**:
```python
@dataclass
class WireSegment:
    uuid: str
    start_point: tuple[float, float]  # (x, y) in mm
    end_point: tuple[float, float]    # (x, y) in mm
    labels: list[str]                 # Associated labels
    connected_pins: list[ComponentPin] # Pins at endpoints
    circuit_id: str | None            # Extracted circuit ID
```

**Endpoint Detection**:
- Wire endpoints may connect to:
  - Component pins (match pin coordinates)
  - Other wire segments (match coordinates)
  - Junction points (match junction coordinates)

### 3.3 Component and Pin Extraction

**Parse Symbol Elements**:
- Extract all `(symbol ...)` blocks from schematic
- Each symbol has:
  - Reference designator: `(property "Reference" "BT1" ...)`
  - LocLoad custom field with encoded data: `(property "LocLoad" "(10,0,0)S40" ...)`
  - Position: `(at x y rotation)`
  - Pin definitions with numbers

**Create Component Objects**:
```python
@dataclass
class Component:
    ref: str                    # Reference designator (e.g., "BT1", "SW1")
    fs: float                   # Fuselage station (inches)
    wl: float                   # Waterline (inches)
    bl: float                   # Buttline (inches)
    source_type: str | None     # "L", "R", "S", "B"
    amperage: float             # Load, rating, or source capacity
    schematic_position: tuple[float, float]  # (x, y) in schematic

    # Symbol information for pin calculation (added 2025-10-19)
    lib_id: str                 # "AeroElectricConnectionSymbols:S700-1-1"
    rotation: float             # 0, 90, 180, 270 degrees
    mirror_x: bool              # Mirrored across X axis
    mirror_y: bool              # Mirrored across Y axis

    pins: list[ComponentPin]    # Calculated pin positions and connections
```

**Pin Position Calculation**:
- See Section 4.1 for detailed pin position calculation algorithm with rotation/mirroring
- Briefly: Apply mirror transform → Apply rotation matrix → Translate to component position

### 3.4 Label Extraction and Association

**[REVISED - 2025-10-22]**: Clarified handling of non-circuit labels (notes) and aggregation across wire fragments

**Parse Label Elements**:
- Extract all `(label ...)` blocks from schematic
- Each label has:
  - Text content
  - Position: `(at x y rotation)`
  - UUID: Unique identifier

**Label to Wire Association Algorithm**:

1. **For each label**:
   - Check if text matches circuit ID pattern: `^[A-Z]\d+[A-Z]$` or `^[A-Z]-\d+-[A-Z]$`
   - **Circuit ID label**: Store in wire.circuit_id
   - **Non-circuit label** (e.g., "24AWG", "SHIELDED"): Store in wire.notes list

2. **Calculate distance to each wire segment**:
   - Point-to-line-segment distance formula
   - Find minimum distance from label position to wire

3. **Associate label with closest wire fragment**:
   - If distance ≤ threshold (default 10mm): Associate label with that wire fragment
   - If distance > threshold: Warning (orphaned label)
   - **IMPORTANT**: Labels associate with individual wire fragments during parsing

4. **Handle multiple labels on same wire fragment**:
   - If multiple circuit ID labels on one wire fragment: Warning (ambiguous)
   - If circuit ID + note labels: Store circuit ID in wire.circuit_id, notes in wire.notes list

**Notes Aggregation During BOM Generation**:
- **Labels associate at wire fragment level** (proximity-based, during parsing)
- **Notes aggregate at circuit level** (during BOM generation)
- When creating BOM entry for a circuit, collect notes from ALL wire fragments forming that circuit
- Multiple wire fragments may connect to form a single electrical circuit (e.g., through junctions)
- **Example**: Circuit G4A from BT1-2 to GB1-1:
  - Vertical fragment: has "10AWG" note
  - Horizontal fragment: has "G4A" circuit ID
  - BOM entry for G4A must include "10AWG" note from vertical fragment

**Distance Calculation**:
```python
def point_to_segment_distance(point, seg_start, seg_end):
    # Calculate perpendicular distance from point to line segment
    # Handle cases where perpendicular falls outside segment endpoints
    # Return minimum distance (to segment or endpoints)
```

### 3.5 Junction Detection

**Parse Junction Elements**:
- Extract all `(junction ...)` blocks from schematic
- Junction position: `(at x y)`
- Junction UUID for unique identification

**CRITICAL SEMANTICS**:
- **Junction present**: Wires meeting at that (x,y) ARE electrically connected
- **Junction absent**: Wires crossing at that (x,y) are NOT connected
  - Like PCB traces on different layers passing over each other
  - KiCad uses explicit junctions to indicate electrical connection
  - Do NOT infer connections from coordinate overlap alone

**Example from test_03A_fixture**:
- Wire P3A crosses wire P2A in 2D space
- No junction at crossing point → wires are NOT connected
- Wire P1A and P2A meet at junction (144.78, 86.36) → ARE connected

**Create Junction Objects**:
```python
@dataclass
class Junction:
    uuid: str                       # Unique identifier
    position: tuple[float, float]   # (x, y) in schematic
    diameter: float                 # Visual diameter
    color: tuple[int, int, int, int]  # RGBA color
```

**S-Expression Format**:
```lisp
(junction
  (at 144.78 86.36)
  (diameter 0)
  (color 0 0 0 0)
  (uuid "51609a84-6043-4d22-9ef7-15e32380f2f0")
)
```

---

## 4. Wire Connection Analysis

### 4.1 Pin Position Calculation

**REVISED - 2025-10-19**: Implement precise pin position calculation with rotation and mirroring support.

**Problem**: Component symbols have pins at relative positions. Component instances are placed with rotation and mirror transformations. Must calculate absolute pin positions in schematic coordinates.

**Data from Schematic**:

Symbol library defines pins relative to symbol origin:
```lisp
(symbol "S700-1-1_1_1"
  (pin passive line
    (at -6.35 0 0)      ; Pin 2: position (-6.35, 0), angle 0
    (number "2" ...)
  )
  (pin passive line
    (at 6.35 2.54 180)  ; Pin 1: position (6.35, 2.54), angle 180
    (number "1" ...)
  )
)
```

Component instance specifies placement:
```lisp
(symbol
  (lib_id "AeroElectricConnectionSymbols:S700-1-1")
  (at 119.38 105.41 0)  ; Position (x, y), rotation angle
  (pin "2" (uuid "..."))
  (pin "1" (uuid "..."))
)
```

**Pin Position Calculation Algorithm**:

```python
def calculate_pin_position(
    pin_def: PinDefinition,
    component: ComponentInstance
) -> tuple[float, float]:
    """
    Calculate absolute schematic position of a pin.

    Steps:
    1. Start with pin relative position from symbol library
    2. Apply mirroring (if component is mirrored)
    3. Apply rotation (component rotation angle)
    4. Translate to component position
    """
    x, y = pin_def.position

    # Step 1: Apply mirroring
    if component.mirror_x:
        x = -x
    if component.mirror_y:
        y = -y

    # Step 2: Apply rotation (2D rotation matrix)
    # x' = x*cos(θ) - y*sin(θ)
    # y' = x*sin(θ) + y*cos(θ)
    theta_rad = math.radians(component.rotation)
    x_rot = x * math.cos(theta_rad) - y * math.sin(theta_rad)
    y_rot = x * math.sin(theta_rad) + y * math.cos(theta_rad)

    # Step 3: Translate to component position
    abs_x = component.position[0] + x_rot
    abs_y = component.position[1] + y_rot

    return (abs_x, abs_y)
```

**New Data Structures**:

```python
@dataclass
class PinDefinition:
    """Pin definition from symbol library"""
    number: str                    # "1", "2", "3"
    position: tuple[float, float]  # (x, y) relative to symbol origin
    angle: float                   # Pin direction in degrees
    length: float                  # Pin length
    name: str                      # "IN", "ON", etc.

@dataclass
class ComponentPin:
    """A specific pin on a component instance"""
    component_ref: str              # "SW1"
    pin_number: str                 # "1"
    position: tuple[float, float]   # Absolute (x, y) in schematic
    uuid: str                       # Pin UUID from schematic
    connected_wires: list[str]      # Wire UUIDs (populated later)
```

**Implementation Notes**:
- Parse symbol library definitions at startup, cache by lib_id
- Component instances reference lib_id to look up pin definitions
- Rotation values: 0, 90, 180, 270 degrees
- Mirror detection may require transform analysis in some schematics
- Coordinate matching tolerance: 0.1mm for "same position"

### 4.2 Building Connectivity Graph

**Data Structure - NetworkNode**:

A connection point in the schematic where wires meet:

```python
@dataclass
class NetworkNode:
    """A point where connections meet"""
    position: tuple[float, float]  # (x, y) in schematic
    node_type: str                  # "component_pin", "junction", "wire_endpoint"

    # If node_type == "component_pin":
    component_ref: str | None       # "SW1", "J1", etc.
    pin_number: str | None          # "1", "2", etc.

    # If node_type == "junction":
    junction_uuid: str | None       # UUID of junction element

    # Connectivity:
    connected_wire_uuids: set[str]  # UUIDs of wires at this node
```

**Data Structure - ConnectivityGraph**:

```python
class ConnectivityGraph:
    """Network connectivity for entire schematic"""

    def __init__(self):
        self.nodes: dict[tuple[float, float], NetworkNode] = {}
        self.wires: dict[str, WireSegment] = {}
        self.junctions: dict[str, Junction] = {}
        self.component_pins: dict[str, ComponentPin] = {}  # Key: "SW1-1"

    def get_or_create_node(
        self,
        position: tuple[float, float],
        node_type: str = "wire_endpoint"
    ) -> NetworkNode:
        """Get existing node at position or create new one"""
        # Round position to 0.01mm precision to handle float matching
        key = (round(position[0], 2), round(position[1], 2))

        if key not in self.nodes:
            self.nodes[key] = NetworkNode(
                position=position,
                node_type=node_type,
                component_ref=None,
                pin_number=None,
                junction_uuid=None,
                connected_wire_uuids=set()
            )
        return self.nodes[key]

    def add_wire(self, wire: WireSegment):
        """Add wire and update node connections"""
        self.wires[wire.uuid] = wire

        # Get or create nodes at wire endpoints
        start_node = self.get_or_create_node(wire.start_point)
        end_node = self.get_or_create_node(wire.end_point)

        # Connect wire to nodes
        start_node.connected_wire_uuids.add(wire.uuid)
        end_node.connected_wire_uuids.add(wire.uuid)

    def add_junction(self, junction: Junction):
        """Add junction and mark node as junction type"""
        self.junctions[junction.uuid] = junction

        node = self.get_or_create_node(
            junction.position,
            node_type="junction"
        )
        node.junction_uuid = junction.uuid

    def add_component_pin(self, pin: ComponentPin):
        """Add component pin and mark node as component_pin type"""
        key = f"{pin.component_ref}-{pin.pin_number}"
        self.component_pins[key] = pin

        node = self.get_or_create_node(
            pin.position,
            node_type="component_pin"
        )
        node.component_ref = pin.component_ref
        node.pin_number = pin.pin_number

    def get_connected_nodes(self, wire_uuid: str) -> tuple[NetworkNode, NetworkNode]:
        """Get the two nodes this wire connects"""
        wire = self.wires[wire_uuid]
        start_node = self.get_node_at_position(wire.start_point)
        end_node = self.get_node_at_position(wire.end_point)
        return (start_node, end_node)
```

**Graph Building Algorithm**:

1. **Parse schematic elements**: wires, junctions, symbols, symbol libraries
2. **Build pin definitions** from symbol libraries (cache by lib_id)
3. **Calculate component pin positions** using pin calculation algorithm
4. **Add junctions to graph** (establishes junction nodes)
5. **Add component pins to graph** (establishes pin nodes)
6. **Add wires to graph** (connects to existing nodes or creates wire_endpoint nodes)

**Coordinate Matching Tolerance**:
- Exact match unlikely due to floating-point precision
- Use tolerance: `distance < 0.1mm` for "same position"
- Round positions to 0.01mm for dictionary keys

### 4.3 Wire-to-Component Matching **[REVISED - 2025-10-20]**

**CRITICAL TERMINOLOGY CLARIFICATION**:

There are TWO different things both called "junction":

1. **Junction ELEMENT** `(junction ...)`: Schematic drawing element (appears as a dot at wire intersections). This indicates wires are electrically connected. **TRANSPARENT in tracing** - we trace through these to find component pins.

2. **Junction/Connector COMPONENT** (e.g., J1, J2, TB1): Real physical components with reference designators and pins (terminal blocks, connectors, splice blocks). **NOT TRANSPARENT** - these are endpoints. Wires terminate at their pins.

**Algorithm**: For each labeled wire segment, identify the component pins it connects by:
- **Tracing through junction ELEMENTS** (schematic dots)
- **Stopping at component pins** (including junction/connector components like J1)

**Rationale**: Junction elements are just schematic notation showing electrical connectivity. But any component with a reference designator (J1, SW1, BT1, etc.) is a physical part where wires terminate.

```python
def identify_wire_connections(
    wire: WireSegment,
    graph: ConnectivityGraph
) -> tuple[ComponentPin, ComponentPin]:
    """
    Identify what components this wire connects.

    Traces through junctions to find component pins at both ends.

    Returns:
        Tuple of (from_pin, to_pin) where each is:
        - ComponentPin(component_ref, pin_number) (e.g., SW1, pin 3)
        - None if endpoint has no component connection
    """
    start_node, end_node = graph.get_connected_nodes(wire.uuid)

    def trace_to_component(node: NetworkNode, exclude_wire_uuid: str = None) -> Optional[ComponentPin]:
        """Trace from wire endpoint through junctions and wire_endpoints to find component pin."""
        if node is None:
            return None

        if node.node_type == "component_pin":
            return ComponentPin(node.component_ref, node.pin_number)

        elif node.node_type == "junction":
            # Find other wires connected to this junction
            for other_wire_uuid in node.connected_wire_uuids:
                if other_wire_uuid == exclude_wire_uuid:
                    continue  # Skip the wire we came from

                # Recursively trace the other wire's endpoints
                other_start, other_end = graph.get_connected_nodes(other_wire_uuid)

                # Find which end is NOT this junction node
                if other_start.position == node.position:
                    result = trace_to_component(other_end, exclude_wire_uuid=other_wire_uuid)
                elif other_end.position == node.position:
                    result = trace_to_component(other_start, exclude_wire_uuid=other_wire_uuid)
                else:
                    continue

                if result is not None:
                    return result

        elif node.node_type == "wire_endpoint":
            # **[DESIGN ONLY - NOT YET IMPLEMENTED]**
            # Wire endpoints occur when labeled wire segments connect to unlabeled segments
            # Trace through connected wires to find component or junction
            for other_wire_uuid in node.connected_wire_uuids:
                if other_wire_uuid == exclude_wire_uuid:
                    continue  # Skip the wire we came from

                # Recursively trace the other wire's endpoints
                other_start, other_end = graph.get_connected_nodes(other_wire_uuid)

                # Find which end is NOT this wire_endpoint node
                if other_start.position == node.position:
                    result = trace_to_component(other_end, exclude_wire_uuid=other_wire_uuid)
                elif other_end.position == node.position:
                    result = trace_to_component(other_start, exclude_wire_uuid=other_wire_uuid)
                else:
                    continue

                if result is not None:
                    return result

        return None

    from_pin = trace_to_component(start_node)
    to_pin = trace_to_component(end_node)

    return (from_pin, to_pin)
```

**BOM Generation with Junction Elements and Connector Components**:

For circuits with junction elements (schematic dots) and connector components like J1:

**Example - test_03A_fixture**:
- Has junction ELEMENTS (dots showing wire connectivity in schematic)
- Has J1 connector COMPONENT (2-pin connector - a real physical part)
- Wires connect switches to the J1 connector

**Expected BOM Output** (from `docs/input/test_03A_out_expected.csv`):
- **P1A**: SW1-pin1 ↔ J1-pin1 (wire from switch to connector)
- **P2A**: SW2-pin1 ↔ J1-pin1 (wire from switch to connector)
- **P3A**: SW1-pin3 ↔ SW2-pin3 (direct switch-to-switch connection)
- **P4A**: SW2-pin2 ↔ J1-pin2 (wire from switch to connector)
- **P4B**: SW1-pin2 ↔ J1-pin2 (wire from switch to connector)

**Builder Interpretation**: Each wire shows which two component pins to physically connect. J1 is a real connector/terminal block where multiple wires terminate.

### 4.4 3+Way Connections **[NEW - 2025-10-21]**

**Definition**: A **3+way connection** is a multi-point electrical connection where N component pins (N ≥ 3) are connected together through one or more junction elements, forming a tree topology.

**Topology Pattern**:
```
Pin1 ────label1──── (junction) ────unlabeled──── Common Pin (unlabeled)
                         │
Pin2 ────label2──────────┘
                         │
Pin3 ────label3──────────┘
```

For larger N or multiple junctions:
```
Pin1 ────label1──── (J1) ────unlabeled──── (J2) ────unlabeled──── Common Pin
                      │                      │
Pin2 ────label2───────┘                      │
                                             │
Pin3 ────label3──────────────────────────────┘
```

**Labeling Convention**:

For N pins in a 3+way connection, expect exactly **(N-1) circuit ID labels**:
- **Labeled segments**: Each wire segment connecting a branch pin to a junction MUST have a circuit ID label
- **Unlabeled segments**: Wire segments forming the backbone (junction-to-junction, junction-to-common-pin) have NO labels
- **Common pin identification**: The one pin NOT reached by any labeled segment is the common endpoint

**Physical Reality**: In experimental aircraft, 3+way connections represent:
- Multiple grounds returning to battery negative or ground bus
- Multiple power feeds from a distribution point
- Multiple circuits connecting to a common terminal block

**BOM Output**: Each labeled wire appears as one BOM entry:
- **From**: The component pin with the labeled segment
- **To**: The common endpoint pin (unlabeled in schematic)

**Example 1 - 3-way connection (test_03A: P4A/P4B)**:
- 3 pins: SW1-pin2, SW2-pin2, J1-pin2
- 2 labels: P4A (on SW2-pin2 side), P4B (on SW1-pin2 side)
- 1 unlabeled pin: J1-pin2 (common endpoint - terminal block)
- BOM output:
  - P4A: SW2-pin2 → J1-pin2
  - P4B: SW1-pin2 → J1-pin2

**Example 2 - 4-way connection (test_04: G1A/G2A/G3A)**:
- 4 pins: L1-pin1, L2-pin1, L3-pin1, BT1-pin2
- 3 labels: G1A, G2A, G3A
- 1 unlabeled pin: BT1-pin2 (battery negative - common ground return)
- 2 junctions forming backbone to common pin
- BOM output:
  - G1A: L1-pin1 → BT1-pin2
  - G2A: L2-pin1 → BT1-pin2
  - G3A: L3-pin1 → BT1-pin2

**Validation Rules**:

**Strict Mode**:
1. If N pins detected in connected group AND N ≥ 3:
   - **Error** if label count ≠ (N-1): "3+way connection with N pins requires exactly (N-1) labels, found X"
   - **Error** if cannot identify single common pin: "Cannot determine common endpoint - ambiguous labeling in 3+way connection"
2. If label count = N (all pins labeled): **Error** - "3+way connection has too many labels - one pin must be unlabeled to indicate common endpoint"
3. If label count < (N-1): **Error** - "3+way connection has too few labels - expected (N-1) labels for N pins"

**Permissive Mode**:
- Same checks produce **Warnings** instead of errors
- Attempt best-effort tracing with unclear results flagged in BOM warnings column

**Implementation Algorithm**:
1. **Detect 3+way connections**: After building connectivity graph, identify all connected component groups with N ≥ 3 pins
2. **Count labels**: For each group, count circuit ID labels on wire segments within the group
3. **Validate**: Check that label count = (N-1)
4. **Identify common pin**: The pin NOT reached by any labeled segment is the common endpoint (see below)
5. **Generate BOM entries**: For each labeled segment, create entry from labeled-pin → common-pin

**Common Pin Identification Detail**:

Uses **segment-level analysis**. Key terminology:
- **Fragment**: Single KiCad wire element
- **Connection**: Point where exactly 2 fragments meet (transparent, trace through)
- **Junction**: Point where 3+ fragments meet (segment boundary, stop point)
- **Segment**: Chain of fragments between pin and junction

Algorithm for each pin:
1. Trace the segment from pin toward junction/backbone
2. Follow fragments through connections (2-fragment points)
3. Stop at junctions (3+ fragment points) or other group pins
4. Check if ANY fragment in the segment has a circuit_id label
5. Pin is "reached by labeled segment" if segment contains labeled fragment

The common pin is the ONE pin whose segment has NO labeled fragments.

**Example**: SW1-pin2 → (connection) → Junction: If either fragment has label, pin is reached by label.

### 4.5 Unified BOM Generation **[NEW - 2025-10-21]** **[REVISED - 2025-10-22]**

**[REVISED - 2025-10-22]**: Added notes aggregation across wire fragments specification.

**Problem**: The multipoint connection logic exists in `wire_connections.py` (`generate_multipoint_bom_entries()`) and is tested in integration tests, but the CLI (`__main__.py`) doesn't use it. This creates a gap between tested functionality and actual CSV output.

**Root Cause**: The CLI only processes wires individually using `identify_wire_connections()` for 2-point connections. It never:
1. Calls `detect_multipoint_connections()` to find 3+way groups
2. Calls `generate_multipoint_bom_entries()` to generate multipoint BOM entries
3. Filters labeled wires that are part of multipoint connections
4. Combines multipoint and regular BOM entries

**Architectural Decision**: Create a unified BOM entry generation function that handles both multipoint and regular 2-point connections, eliminating code duplication between CLI and integration tests.

**Design**:

**New Module**: `kicad2wireBOM/bom_generator.py`

**New Function**: `generate_bom_entries(wires: list[WireSegment], graph: ConnectivityGraph) -> list[dict]`

**Algorithm**:
1. Store wires in graph for multipoint processing
2. Detect multipoint connection groups (N ≥ 3 pins)
3. Generate BOM entries for multipoint connections
4. Track which circuit IDs are used by multipoint connections
5. Generate BOM entries for regular 2-point connections (excluding multipoint labels)
6. Return combined list of all BOM entries

**Return Format**: Each entry is a dict with:
- `circuit_id`: Wire label (e.g., "P4A")
- `from_component`: Component reference (e.g., "SW1")
- `from_pin`: Pin number (e.g., "2")
- `to_component`: Component reference (e.g., "J1")
- `to_pin`: Pin number (e.g., "2")
- `notes`: **[REVISED - 2025-10-22]** Aggregated notes from all wire fragments forming this circuit

**Benefits**:
1. **Single Source of Truth**: One function for all BOM entry generation
2. **DRY**: Eliminates duplication between `__main__.py` and integration tests
3. **Testable**: Integration tests can verify the same code path the CLI uses
4. **Maintainable**: Future changes only need to be made in one place
5. **Correct**: CLI will automatically use multipoint logic

**Usage in CLI** (`__main__.py`):
```python
# After building graph and associating labels:
bom_entries = generate_bom_entries(wires, graph)

# For each entry, calculate wire properties and add to WireBOM:
for entry in bom_entries:
    # Calculate length, gauge, color (existing logic)
    # Create WireConnection and add to bom
```

**Usage in Integration Tests**:
```python
# Simplified integration tests:
bom_entries = generate_bom_entries(wires, graph)
assert len(bom_entries) == 5
assert bom_entries contains expected P4A, P4B entries
```

**Migration Path**:
1. Create `bom_generator.py` with `generate_bom_entries()` function
2. Write unit tests for the new function
3. Update integration tests to use new function (verify output unchanged)
4. Update `__main__.py` to use new function
5. Run all tests to verify correctness
6. Verify CLI output matches expected CSV files

**Implementation Priority**: HIGH - This is blocking correct CSV output for 3+way connections.

**Notes Aggregation Algorithm** **[NEW - 2025-10-22]**:

When generating each BOM entry, collect notes from all wire fragments forming the circuit:

```python
def collect_circuit_notes(graph: ConnectivityGraph,
                          circuit_id: str,
                          from_pos: tuple[float, float],
                          to_pos: tuple[float, float]) -> str:
    """
    Aggregate notes from all wire fragments forming a circuit.

    Traverses connectivity graph to find all wire segments between
    from_pos and to_pos, collecting notes from each segment.

    Args:
        graph: Connectivity graph with wires and nodes
        circuit_id: Circuit identifier (e.g., "G4A")
        from_pos: Starting component pin position
        to_pos: Ending component pin position

    Returns:
        Space-separated string of unique notes (deduplicated)
    """
    # BFS/DFS traversal from from_pos to to_pos
    # For each wire segment encountered:
    #   - Collect notes from wire.notes list
    # Deduplicate notes (same label on multiple fragments)
    # Return space-separated string
```

**Key Points**:
- Labels associate with individual wire fragments during parsing (proximity-based)
- Notes aggregate across all fragments forming a circuit during BOM generation
- Deduplication ensures same note doesn't appear multiple times
- Example: Circuit G4A with vertical and horizontal fragments:
  - Vertical fragment has notes=["10AWG"]
  - Horizontal fragment has notes=[]
  - BOM entry for G4A gets notes="10AWG"

### 4.6 Circuit Identification

**Extract Circuit ID from Label**:
- Parse label text: `L1A` → system="L", circuit="1", segment="A"
- Regex: `^([A-Z])-?(\d+)-?([A-Z])$`
- Captures: system code, circuit number, segment letter

**Validate System Code**:
- Check against known codes: L, P, G, R, E, K, M, W, A, F, U
- If unrecognized: Warning, continue processing

**Handle Missing Labels**:
- **Strict mode**: Error - wire has no circuit ID label
- **Permissive mode**: Warning - generate fallback label
  - Fallback format: `UNK{wire_index}A` (e.g., UNK1A, UNK2A)

---

## 5. Wire Calculation Logic

### 5.1 Wire Length Calculation

**Method**: Manhattan distance (sum of absolute differences in each axis) between component FS/WL/BL coordinates.

**Formula**:
```
Length = |FS₁ - FS₂| + |WL₁ - WL₂| + |BL₁ - BL₂| + slack
```

**Slack Allowance**:
- Default: 24 inches (12" per end for termination/routing flexibility)
- Configurable via command-line parameter `--slack-length`
- Documented in output and `--schematic-requirements`

**Rationale**:
- Manhattan distance is conservative (accounts for rectilinear routing through aircraft structure)
- More realistic than straight-line distance for actual wire runs
- Slack ensures adequate wire for termination, strain relief, and routing adjustments

**Pin-to-Pin Calculation**:
- Wire connects component1-pin_A to component2-pin_B
- Use component1 coordinates and component2 coordinates (not individual pin positions)
- Pin-level routing is sub-inch scale; component positions determine overall wire run

### 5.2 Wire Gauge Calculation

**Basis**: Aeroelectric Connection (Bob Nuckolls) ampacity tables and voltage drop guidelines.

**Primary Constraint**: Maximum 5% voltage drop at system voltage
- Default system voltage: 12V (configurable via `--system-voltage`)
- 5% of 12V = 0.6V max drop
- 5% of 14V = 0.7V max drop

**Calculation Method**:

1. **Determine wire current**:
   - For load wires: Use load component's amperage
   - For source wires: Use source component's capacity
   - For passthrough wires: Use downstream load (requires tracing)

2. **Calculate voltage drop for each AWG size**:
   - `Vdrop = Current × Resistance_per_foot × (Length_inches / 12)`
   - Use wire resistance values from Aeroelectric Connection

3. **Select minimum gauge**:
   - Find smallest AWG where `Vdrop ≤ 0.05 × Vsystem`
   - Verify gauge also meets ampacity constraint (current ≤ max amps for AWG)
   - Round up to next standard AWG size if needed

**Standard AWG Sizes**: 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2

**Result**:
- Minimum required gauge (e.g., "18.7 AWG calculated")
- Round up to next standard AWG size (e.g., 18 AWG selected)
- Document both calculated and selected values in engineering mode

### 5.3 Wire Color Assignment

**Method**: Auto-assign based on system code using standard mapping from EAWMS documentation.

**System Code to Color Mapping**:
- Implemented as configurable lookup table in `reference_data.py`
- Source: `docs/ea_wire_marking_standard.md`

**Examples** (from EAWMS):
- `L` (Lighting) → White
- `P` (Power) → Red
- `G` (Ground) → Black
- `R` (Radio/Nav) → Gray
- (Complete mapping extracted from EAWMS docs)

**Fallback**: If system code unmapped, flag warning and assign default color (white or user-specified in config).

### 5.4 Wire Label Generation (EAWMS Format)

**Format**: `SYSTEM-CIRCUIT-SEGMENT` or `SYSTEMCIRCUITSEGMENT`

**Examples**:
- Compact (default): `L1A`, `P12B`, `G1A`
- Dashes (optional): `L-1-A`, `P-12-B`, `G-1-A`

**Output Format Control**:
- Controlled by `--label-format` CLI flag:
  - `compact` (default): `L1A` (no separators)
  - `dashes`: `L-1-A` (dash separators)
- Standardizes output regardless of input label variations

---

## 6. Validation and Error Handling

### 6.1 Operating Modes

**Strict Mode** (default):
- Error and abort on missing required data (labels, coordinates, load/rating)
- Ensures complete, validated schematics
- Recommended for final BOMs

**Permissive Mode** (`--permissive` flag):
- Use defaults with warnings for missing data
- Missing coordinates: Default to (-9, -9, -9) with warning
- Missing labels: Generate fallback labels (UNK1A, UNK2A, ...)
- Missing load/rating: Default to 0A with warning
- Continue processing and generate BOM with warning annotations
- Useful for iterative design and draft BOMs

### 6.2 Validation Checks

#### 6.2.1 Wire Label Validation

**Check**: All wires have circuit ID labels

**In Strict Mode**:
- Error if wire has no label
- Error message: "Wire segment {uuid} has no circuit ID label"
- Suggestion: "Add label to wire in schematic (e.g., L1A, P12B)"
- Abort processing with exit code 1

**In Permissive Mode**:
- Warning if wire has no label
- Generate fallback label: `UNK{index}A`
- Continue processing with warning in output

#### 6.2.2 Duplicate Wire Label Detection

**Check**: No two wires should have identical circuit IDs

**In Strict Mode**:
- Error if duplicate labels detected
- Error message: "Duplicate circuit ID 'L1A' found on multiple wire segments"
- Suggestion: "Each wire must have unique label. Check segment letters."
- Abort processing with exit code 1

**In Permissive Mode**:
- Warning if duplicate labels detected
- Append suffix to make unique: `L1A`, `L1A-2`, `L1A-3`
- Continue processing with warning in output

#### 6.2.3 Orphaned Label Detection

**Check**: All circuit ID labels are associated with a wire

**Action**: Always warn (both modes)
- Warning message: "Label 'L1A' at position (x, y) is not close to any wire segment"
- Suggestion: "Move label closer to wire or check wire routing"
- Distance threshold: 10mm (configurable)
- Continue processing

#### 6.2.4 Required Field Validation

**Check**: All components have required data

**In Strict Mode**:
- Error if component missing FS, WL, BL coordinates
- Error if component missing source type or amperage
- Error message identifies specific components
- Abort processing with exit code 1

**In Permissive Mode**:
- Log warnings for missing fields
- Apply defaults: coordinates (-9, -9, -9), amperage 0A
- Continue processing

#### 6.2.5 Wire Connection Validation

**Check**: Each wire segment connects exactly 2 component pins

**Action**: Warn if wire has 0, 1, or 3+ connections
- 0 connections: "Wire {circuit_id} is not connected to any components"
- 1 connection: "Wire {circuit_id} is only connected at one end"
- 3+ connections: "Wire {circuit_id} connects to {N} pins - may need junction splitting"

**Note**: Unlike netlists, schematics can show complex topologies. Multiple wires meeting at a junction is normal and expected.

### 6.3 Error Output

All warnings and errors include:
- Wire circuit ID or UUID
- Component reference designators involved
- Specific issue description
- Suggested correction (when applicable)

Format enables easy schematic correction by designer.

---

## 7. Output Formats and Modes

### 7.1 Output Formats

Two primary output formats:

1. **CSV** (default): Comma-separated values for spreadsheet import and manipulation
2. **Markdown** (`.md` extension or `--format md`): Rich formatted document with sections and tables

### 7.2 Output Filename Generation

**If destination not specified**:
- Extract base name from input file
- Append revision suffix: `_REVnnn` where nnn is incremented revision number
- Add format extension: `.csv` or `.md`
- Check directory for existing REVnnn files and increment to next available

**Example**:
- Input: `aircraft_electrical.kicad_sch`
- Output: `aircraft_electrical_REV001.csv`
- Next run: `aircraft_electrical_REV002.csv`

### 7.3 Builder Mode (Default) **[REVISED - 2025-10-20]**

**Purpose**: Clean, actionable wire list for harness construction.

**CSV Columns**:
- Wire Label (EAWMS format)
- From Component (component reference, e.g., "BT1", "SW1")
- From Pin (pin number, e.g., "1", "3")
- To Component (component reference, e.g., "SW1", "J1")
- To Pin (pin number, e.g., "2", "1")
- Wire Gauge (AWG size, e.g., "20 AWG")
- Wire Color
- Length (inches)
- Wire Type (specification, e.g., "M22759/16")
- Warnings (validation issues, if any)

**Note**: Junctions in the schematic are transparent in the output. Each wire shows the component pins it electrically connects, tracing through any junctions to find the actual components at both ends.

**Markdown Structure**:
- **Summary Section**:
  - Total wire count
  - Wire purchasing summary (total length needed by gauge/color combination)
- **Wire List Tables**:
  - Grouped by system code (L-circuits, P-circuits, etc.)
  - Sorted within each system by circuit number
- **Warnings/Notes Section**:
  - All validation warnings
  - Any assumptions made

### 7.4 Engineering Mode (`--engineering` flag)

**Purpose**: Detailed analysis for design review, validation, and documentation.

**Additional CSV Columns**:
- Calculated Min Gauge (e.g., "18.7 AWG")
- Current (amperes)
- Voltage Drop (volts)
- Voltage Drop (percentage)
- From Coordinates (FS/WL/BL)
- To Coordinates (FS/WL/BL)
- Calculated Length (before slack added)
- Component Load/Rating values

**Enhanced Markdown Structure**:

All builder mode sections, plus:

- **Component Validation Report**:
  - Table of all components with Load/Rating values
  - Component type identification
  - Coordinate listings
  - Missing data flagged

- **Detailed Calculations Section**:
  - Per-wire voltage drop analysis
  - Resistance calculations
  - Gauge selection rationale

- **Schematic Analysis**:
  - Total wire count
  - Wire segment statistics
  - Label coverage (% of wires labeled)
  - Junction analysis

- **Validation Results**:
  - All warnings and recommendations
  - Orphaned labels
  - Unlabeled wires
  - Connection validation results

- **Assumptions Documentation**:
  - Voltage drop percentage (5%)
  - Slack length (inches)
  - System voltage (volts)
  - Wire resistance values used
  - Ampacity tables referenced
  - Color mapping table
  - Label association threshold

### 7.5 Output Sorting

All outputs sorted by:
1. System code (alphabetically: G, L, P, R, etc.)
2. Circuit number (numerically within each system)
3. Segment letter (A, B, C... within each circuit)

---

## 8. Command-Line Interface

### 8.1 Basic Usage

```bash
python -m kicad2wireBOM input.kicad_sch output.csv
python -m kicad2wireBOM input.kicad_sch output.md
python -m kicad2wireBOM input.kicad_sch  # Auto-generates output_REV001.csv
```

### 8.2 Command-Line Arguments

**Required Arguments**:
- `source`: Path to KiCAD schematic file (.kicad_sch)

**Optional Arguments**:
- `dest`: Path to output file (if omitted, auto-generates with REVnnn suffix)
  - Extension determines format (.csv or .md)

### 8.3 Command-Line Flags

**Information Flags**:
- `--help`: Display usage information and exit
- `--version`: Display tool version and exit
- `--schematic-requirements`: Display documentation for schematic designers and exit

**Mode Flags**:
- `--permissive`: Enable permissive mode (use defaults for missing fields)
- `--engineering`: Enable engineering mode output (detailed calculations)

**Configuration Options**:
- `--system-voltage VOLTS`: System voltage for calculations (default: 12)
- `--slack-length INCHES`: Extra wire length per segment (default: 24)
- `--format {csv,md}`: Explicitly specify output format (overrides file extension)
- `--label-format {compact,dashes}`: Wire label format (default: compact)
  - `compact`: `L1A`, `P12B` (no separators)
  - `dashes`: `L-1-A`, `P-12-B` (dash separators)
- `--label-threshold MM`: Max distance for label-to-wire association (default: 10)
- `--config FILE`: Path to configuration file (overrides default .kicad2wireBOM.yaml search)

### 8.4 Usage Examples

```bash
# Basic BOM generation (builder mode, CSV)
python -m kicad2wireBOM schematic.kicad_sch wire_bom.csv

# Auto-generate filename with revision
python -m kicad2wireBOM schematic.kicad_sch

# 14V system with custom slack
python -m kicad2wireBOM --system-voltage 14 --slack-length 30 schematic.kicad_sch bom.csv

# Engineering mode markdown output
python -m kicad2wireBOM --engineering schematic.kicad_sch analysis.md

# Permissive mode for incomplete schematic
python -m kicad2wireBOM --permissive draft.kicad_sch draft_bom.csv

# Show what's needed in schematic
python -m kicad2wireBOM --schematic-requirements

# Use custom config file
python -m kicad2wireBOM --config my_project.yaml schematic.kicad_sch
```

### 8.5 Exit Codes

- `0`: Success - BOM generated successfully
- `1`: Error - Missing required data (strict mode), file I/O error, parse error

---

## 9. Data Sources and Reference Materials

### 9.1 Wire Resistance Values

**Source**: Aeroelectric Connection Chapter 5
**Example**: 10 AWG = 1.0 milliohm per foot (from ae__page61.txt)

**Implementation**:
- Extract and tabulate resistance values for standard AWG sizes
- Sizes: 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2 AWG
- Store in `reference_data.py` as lookup table
- Format: `{awg_size: resistance_per_foot}`

### 9.2 Ampacity Tables

**Source**: Aeroelectric Connection simplified ampacity guidance
**Basis**: Practical application of MIL-W-5088L principles for experimental aircraft

**Implementation**:
- Digitize Bob Nuckolls' current-carrying capacity recommendations per AWG size
- Account for bundling/harnessing effects per Aeroelectric guidance
- Store in `reference_data.py` as lookup table
- Format: `{awg_size: max_amperes}`

### 9.3 System Code to Wire Color Mapping

**Source**: Extract from `docs/ea_wire_marking_standard.md` and/or Aeroelectric Connection

**Implementation**:
- Internal lookup table mapping system letter codes to standard wire colors
- Store in `reference_data.py`
- Format: `{system_code: color_name}`

**Examples** (to be verified against references):
- `L` (Lighting) → White
- `P` (Power) → Red
- `G` (Ground) → Black
- `R` (Radio/Nav) → Gray or Shielded

### 9.4 System Codes

**Source**: `docs/ea_wire_marking_standard.md` (existing EAWMS documentation)

**Usage**:
- Validate system codes in labels
- Provide in `--schematic-requirements` output
- Map to wire colors

### 9.5 Voltage Drop Standards

**Value**: 5% maximum
- 0.6V for 12V system
- 0.7V for 14V system

**Source**: Common experimental aircraft practice per Aeroelectric Connection
**Justification**: Balance between wire weight and electrical performance

### 9.6 Test Validation Data

**Files**: `tests/fixtures/test_*_fixture.kicad_sch`

**Purpose**:
- Verify schematic parsing
- Label association testing
- Wire extraction validation
- Component data extraction
- Junction handling

---

## 10. Implementation Architecture

### 10.1 Module Structure **[REVISED - 2025-10-21]**

The `kicad2wireBOM/` package contains the following modules:

#### Current Modules

1. **`__main__.py`** - CLI entry point and orchestration
2. **`parser.py`** - S-expression parsing and schematic file reading
3. **`schematic.py`** - Schematic data model (wires, labels, components, junctions)
4. **`label_association.py`** - Label-to-wire proximity matching
5. **`symbol_library.py`** - Symbol library parsing for pin definitions
6. **`pin_calculator.py`** - Pin position calculation with rotation/mirroring
7. **`connectivity_graph.py`** - Graph data structures and component tracing
8. **`graph_builder.py`** - Build connectivity graph from schematic
9. **`wire_connections.py`** - Wire connection identification (2-point and multipoint)
10. **`bom_generator.py`** - **[NEW]** Unified BOM entry generation (combines multipoint and regular)
11. **`wire_calculator.py`** - Length, gauge, voltage drop calculations
12. **`wire_bom.py`** - WireBOM and WireConnection data models
13. **`reference_data.py`** - Wire resistance, ampacity, color mapping tables
14. **`output_csv.py`** - CSV output generation

**Note**: Module 10 (`bom_generator.py`) is new as of v2.6 to eliminate code duplication between CLI and integration tests.

### 10.2 Test Structure

**Test Directory**: `tests/`

**Test Files**:
- `test_parser.py`: S-expression parsing, schematic file reading
- `test_schematic.py`: Schematic data model, wire/label/component extraction
- `test_component.py`: Component model, LocLoad encoding parsing
- `test_label_association.py`: Label-to-wire proximity matching
- `test_wire_calculator.py`: Length, voltage drop, gauge calculations
- `test_validator.py`: All validation checks
- `test_output_csv.py`: CSV generation in both modes
- `test_output_markdown.py`: Markdown generation
- `test_integration.py`: End-to-end tests with complete schematics
- `test_cli.py`: Command-line interface, argument parsing

**Test Fixtures** (in `tests/fixtures/`):
- `test_01_fixture.kicad_sch`: Simple two-component circuit
- `test_02_fixture.kicad_sch`: Multi-segment circuit (battery → switch → lamp)
- `test_03_fixture.kicad_sch`: Junction example with multiple wires
- `test_04_missing_labels.kicad_sch`: Unlabeled wires (permissive mode test)
- `test_05_multiple_circuits.kicad_sch`: Multiple independent circuits
- Expected output files for comparison

**Test Strategy**:
- Unit tests for each module function
- Integration tests for complete workflows
- Fixture-based testing with known good inputs/outputs
- Validate calculations against hand-calculated examples
- Test both strict and permissive modes
- Test both builder and engineering output modes
- Test edge cases: missing labels, orphaned labels, duplicate IDs, etc.

### 10.3 Dependencies

**Required**:
- `sexpdata` or custom s-expression parser
- `pytest`: Testing framework
- `PyYAML`: Configuration file parsing

**Standard Library**:
- `argparse`: Command-line argument parsing
- `csv`: CSV file generation
- `pathlib`: File path handling
- `dataclasses`: Data model definitions
- `typing`: Type hints
- `re`: Regular expression parsing (label patterns, LocLoad encoding)
- `math`: Distance calculations

---

## 11. Special Considerations

### 11.1 Coordinate Systems

**Schematic Coordinates**: KiCAD uses millimeters, origin typically top-left

**Aircraft Coordinates**: Inches, FS/WL/BL from aircraft datum

**Important**: These are separate coordinate systems:
- Schematic coordinates used for label-to-wire association (proximity)
- Aircraft coordinates used for wire length calculations (Manhattan distance)

**No conversion needed** between the two systems - they serve different purposes.

### 11.2 Hierarchical Schematics

**Future Enhancement**: Support for KiCAD hierarchical sheets

**Current Approach**: Single flat schematic file

**When implementing hierarchical support**:
- Parse sheet instances
- Track wire connections across sheet boundaries
- Maintain global wire label uniqueness
- Calculate wire lengths considering sheet interconnections

**Note**: Defer hierarchical support to later development phase. Focus on flat schematics first.

### 11.3 Junction Handling

**KiCAD Junction**: Explicit graphical element showing wire connection point

**Purpose in BOM Tool**:
- Identifies where multiple wires physically meet
- Important for understanding topology
- May indicate terminal blocks, splice points, or bus bars

**Usage**:
- Record junction positions
- Associate wires that connect at junction
- Note in output if multiple wires share junction (informational)

**Not Used For**:
- Star topology inference (use component analysis instead)
- Net consolidation (we want individual wires, not consolidated nets)

### 11.4 Wire Label Variations

**Input Flexibility**: Accept various label formats in schematic
- Compact: `L1A`
- Dashes: `L-1-A`
- Padded: `L001A`
- Mixed: `L-001-A`

**Output Standardization**: Normalize to chosen format via `--label-format` flag
- Ensures consistent BOM output regardless of schematic label style

### 11.5 S-Expression Parsing Robustness

**Challenges**:
- KiCAD format may change between versions
- Nested structures of varying depth
- Optional elements (some components may lack certain properties)

**Approach**:
- Defensive parsing: Check for element existence before accessing
- Version detection: Read `(version ...)` element, warn if unexpected
- Graceful degradation: Skip unparseable elements, log warnings
- Test against multiple KiCAD versions (v8, v9)

---

## 12. Success Criteria

### Phase 1-5 (Core Features) ✅ COMPLETE

- ✅ Tool parses KiCAD `.kicad_sch` files successfully
- ✅ Wire segments extracted with correct start/end points
- ✅ Labels associated with wires based on proximity
- ✅ Component positions and LocLoad data extracted
- ✅ Circuit IDs parsed from labels correctly
- ✅ Wire labels follow EAWMS format (SYSTEM-CIRCUIT-SEGMENT)
- ✅ Wire gauge calculations are correct (validated against hand calculations)
- ✅ Wire length calculations use Manhattan distance + slack correctly
- ✅ Voltage drop calculations stay within 5% threshold
- ✅ 3+way multipoint connections working correctly
- ✅ Unified BOM generation (no code duplication)
- ✅ CSV output format working
- ✅ Code follows project standards (TDD, YAGNI, DRY)
- ✅ All 125 unit and integration tests pass
- ✅ Tool works with test fixtures from real KiCAD schematics

### Phase 6 (Validation & Error Handling) - IN PLANNING

See `docs/plans/validation_design.md` for detailed specification.

**Key Requirements**:
- [ ] Detect missing circuit ID labels (test_05A)
- [ ] Detect duplicate circuit IDs (test_05B)
- [ ] Handle non-circuit labels as notes (test_05C)
- [ ] Add `notes` field to WireConnection for non-circuit labels
- [ ] Add "Notes" column to CSV output
- [ ] Implement strict vs permissive modes
- [ ] Clear, actionable error messages
- [ ] Validation tests using test_05 variants

**Future Enhancements**:
- [ ] Markdown output format
- [ ] Engineering mode (detailed calculations)
- [ ] `--schematic-requirements` documentation output
- [ ] Auto-generated filenames with REVnnn format

---

## 13. Migration from Netlist-Based Design

**Previous Approach**: Archived in `docs/archive/`

**Key Differences**:
| Aspect | Old (Netlist) | New (Schematic) |
|--------|---------------|-----------------|
| Input File | `.net` XML | `.kicad_sch` s-expression |
| Parsing Library | `kinparse` | `sexpdata` or custom |
| Primary Entity | Net (electrical connectivity) | Wire Segment (physical wire) |
| Label Source | Net name field | Label elements in schematic |
| Wire Granularity | Lost (nets collapse wires) | Preserved (individual wires) |
| Multi-wire Nets | Cannot distinguish | Each wire is separate entity |

**What Stays the Same**:
- EAWMS wire marking standard
- LocLoad field encoding format
- Aircraft coordinate system (FS/WL/BL)
- Wire calculation algorithms (length, gauge, voltage drop)
- Reference data (resistance, ampacity, colors)
- Output formats (CSV, Markdown)
- CLI interface design
- Validation approach

---

## 14. Programmer Implementation Notes

### 14.1 Starting Point

**First Tasks**:
1. Set up project structure and dependencies
2. Write s-expression parser (or integrate `sexpdata` library)
3. Parse basic schematic elements (wire, label, symbol)
4. Create data models (WireSegment, Component, Label)

**Test-Driven Approach**:
- Start with smallest test fixture (test_01_fixture.kicad_sch)
- Write failing test for parsing wire segments
- Implement minimal parser to pass test
- Refactor and repeat

### 14.2 Critical Algorithms

**Label-to-Wire Association**:
- Point-to-line-segment distance calculation is geometrically tricky
- Test thoroughly with various label placements
- Consider edge cases: label at wire endpoint, label far from wire

**Component Pin Position Calculation**:
- Symbol rotation and mirroring affects pin positions
- KiCAD uses rotation angles in degrees
- May need transformation matrix for accurate pin positioning

**Coordinate Tolerance Matching**:
- Floating-point comparison requires epsilon tolerance
- Use consistent tolerance throughout (0.1mm suggested)

### 14.3 Common Pitfalls

**S-Expression Parsing**:
- Symbols like `(`, `)`, `"` need careful handling
- Deeply nested structures require recursive parsing
- Optional elements may be absent (check before accessing)

**Schematic Coordinates**:
- KiCAD coordinates are float values in mm
- Label positions may use different origin/scale than wires
- Always use same coordinate system for proximity calculations

**Wire Connectivity**:
- Wires may connect at endpoints or junctions
- Not all wires connect to component pins (may connect to other wires)
- Junction elements explicitly mark connection points

### 14.4 Testing Strategy

**Unit Tests**:
- Test each function in isolation
- Mock complex dependencies
- Use simple data structures for test inputs

**Integration Tests**:
- Use actual `.kicad_sch` test fixtures
- Verify complete workflow end-to-end
- Compare output against expected results

**Test Fixtures**:
- Start with simplest possible schematic (2 components, 1 wire)
- Gradually add complexity (multiple wires, junctions, labels)
- Include edge cases (missing data, orphaned labels, etc.)

### 14.5 Questions to Resolve During Implementation

**S-Expression Parser**:
- Use `sexpdata` library or write custom parser?
- How to handle KiCAD version differences in format?

**Pin Position Calculation**:
- Do we need exact pin positions or are component positions sufficient?
- How to handle rotated/mirrored symbols?

**Label Association**:
- What distance threshold is appropriate? (10mm suggested)
- How to handle ambiguous cases (label equidistant from multiple wires)?

**Junction Usage**:
- Should junctions affect BOM output? (informational note vs functional impact)

---

## 15. Acronyms and Terminology

See `docs/acronyms.md` for complete project acronyms and domain-specific terminology.

**Key Terms**:
- **FS**: Fuselage Station (longitudinal aircraft coordinate)
- **WL**: Waterline (vertical aircraft coordinate)
- **BL**: Buttline (lateral aircraft coordinate)
- **EAWMS**: Experimental Aircraft Wire Marking Standard
- **AWG**: American Wire Gauge
- **s-expression**: Symbolic expression (Lisp-style nested list format)

---

## 16. References

1. **MIL-W-5088L**: Military Specification - Wiring, Aerospace Vehicle
   Location: `docs/references/milspecs/MIL-STD-5088L.txt`

2. **Aeroelectric Connection**: Bob Nuckolls' practical guide to aircraft electrical systems
   Location: `docs/references/aeroelectric_connection/`
   Key chapters: Ch5 (grounding, wire sizing, voltage drop), Ch8 (wire marking)

3. **EA Wire Marking Standard**: Project-specific EAWMS documentation
   Location: `docs/ea_wire_marking_standard.md`

4. **KiCAD Documentation**: KiCAD v8/v9 schematic file format reference
   Test files: `tests/fixtures/test_*_fixture.kicad_sch`

5. **sexpdata Library**: Python library for parsing s-expressions
   PyPI: https://pypi.org/project/sexpdata/

---

## 17. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-15 | Claude (Architect) | Initial design (netlist-based) |
| 1.1 | 2025-10-17 | Claude (Architect) | Revised for net name parsing approach |
| 2.0 | 2025-10-18 | Claude (Architect) | Complete redesign for schematic-based parsing |
| 2.1 | 2025-10-19 | Claude (Architect) | Added Phase 4: Pin position calculation with rotation/mirroring, junction semantics clarification, connectivity graph algorithms |

---

**Next Steps**:
1. Tom reviews this schematic-based design
2. Create detailed implementation plan
3. Set up test fixtures with actual KiCAD schematics
4. Begin Phase 1 implementation (S-expression parsing foundation)
