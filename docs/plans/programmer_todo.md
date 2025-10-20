# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Architecture**: Schematic-based parsing (NOT netlist-based)
**Approach**: Test-Driven Development (TDD)
**Status**: Phase 1-4 Complete - Full connectivity graph with pin-level wire connections

**Last Updated**: 2025-10-20

---

## IMPLEMENTATION STATUS

### ✅ COMPLETED (Phases 0-3)

**Phase 0: Project Setup**
- [x] Package structure created
- [x] Dependencies installed (sexpdata, pytest)
- [x] Test fixtures verified

**Phase 1: S-Expression Parsing Foundation**
- [x] Parse schematic files using sexpdata
- [x] Extract wire elements
- [x] Extract label elements
- [x] Extract symbol (component) elements
- [x] Parse wire elements to WireSegment objects
- [x] Parse label elements to Label objects
- [x] Parse symbol elements to Component objects
- [x] Parse footprint encoding

**Phase 2: Data Model Creation**
- [x] WireSegment dataclass created
- [x] Label dataclass created
- [x] Component dataclass (reused from previous work)

**Phase 3: Label-to-Wire Association**
- [x] Point-to-segment distance calculation
- [x] Circuit ID pattern validation
- [x] Circuit ID parsing
- [x] Proximity-based label association

**Current Status**: Basic end-to-end processing works!
```bash
python -m kicad2wireBOM tests/fixtures/test_01_fixture.kicad_sch output.csv
```
Generates correct wire BOM with labeled wires.

**Test Results**: 105/105 tests passing ✅

---

## 🚧 IN PROGRESS / TODO

### Phase 4: Pin Matching and Junction Handling

**Status**: ✅ Architectural design complete (see kicad2wireBOM_design.md v2.1)

**Current Limitation**: The CLI uses a simplified heuristic (connects first 2 components for all wires). This works for test_01_fixture but fails for multi-pin components and junction-based networks.

**Architectural Decisions Made**:
- Pin calculation: **Precise** with rotation/mirroring (Section 4.1)
- Junction handling: **Graph-based** with explicit junctions only (Sections 3.5, 4.2)
- Implementation: 4 sub-phases (4A → 4B → 4C → 4D)

---

#### Phase 4A: Pin Position Calculation ✅ COMPLETE

**Goal**: Calculate exact pin positions accounting for component rotation and mirroring

**Tasks**:
- [x] Parse symbol library definitions from schematic `(lib_symbols ...)` section
- [x] Extract pin definitions: position, number, angle, length
- [x] Create `PinDefinition` dataclass
- [x] Create `SymbolLibrary` class to cache pin definitions by lib_id
- [x] Implement pin position calculation algorithm:
  - [x] Apply mirror transform (if component.mirror_x or mirror_y)
  - [x] Apply 2D rotation matrix (component.rotation)
  - [x] Translate to component absolute position
- [x] Create `ComponentPin` dataclass with absolute position
- [x] Add tests for pin calculation:
  - [x] Component at 0° rotation
  - [x] Component at 90° rotation
  - [x] Component at 180° rotation
  - [x] Component at 270° rotation
  - [x] Component with X-axis mirror
  - [x] Component with Y-axis mirror
  - [x] Complex transform (mirror + rotation)

**Reference**: Design doc Section 4.1

**Test Fixtures**:
- test_03A_fixture.kicad_sch (multi-pin switches with rotations)

**Implementation**:
- `kicad2wireBOM/symbol_library.py` - Symbol library parsing
- `kicad2wireBOM/pin_calculator.py` - Pin position calculation
- `tests/test_symbol_library.py` - 5 tests
- `tests/test_pin_calculator.py` - 7 tests
- Commit: 09ce5b3, 3f1f8c8

---

#### Phase 4B: Graph Data Structures ✅ COMPLETE

**Goal**: Implement connectivity graph for network tracing

**Tasks**:
- [x] Create `NetworkNode` dataclass:
  - [x] Fields: position, node_type, component_ref, pin_number, junction_uuid
  - [x] Connected wire UUIDs set
- [x] Create `ConnectivityGraph` class:
  - [x] Nodes dictionary (keyed by rounded position)
  - [x] Wires dictionary (keyed by UUID)
  - [x] Junctions dictionary (keyed by UUID)
  - [x] Component pins dictionary (keyed by "REF-PIN")
- [x] Implement graph methods:
  - [x] `get_or_create_node(position, node_type)`
  - [x] `add_wire(wire)` - creates nodes at endpoints
  - [x] `add_junction(junction)` - marks node as junction type
  - [x] `add_component_pin(pin)` - marks node as component_pin type
  - [x] `get_connected_nodes(wire_uuid)` - returns start/end nodes
  - [x] `get_node_at_position(position, tolerance)` - finds nearby node
- [x] Add tests for graph operations:
  - [x] Node creation and retrieval
  - [x] Wire addition and endpoint matching
  - [x] Junction node creation
  - [x] Pin node creation
  - [x] Position matching with tolerance (0.01mm)
  - [x] Multiple wires at junction
  - [x] Wire connects to existing node

**Reference**: Design doc Section 4.2

**Key Insight**: Round positions to 0.01mm precision for dictionary keys (handles float matching)

**Implementation**:
- `kicad2wireBOM/connectivity_graph.py` - NetworkNode and ConnectivityGraph classes
- `tests/test_connectivity_graph.py` - 12 tests
- Commit: 67baa4c

---

#### Phase 4C: Graph Building Integration ✅ COMPLETE

**Goal**: Build complete connectivity graph from schematic

**Tasks**:
- [x] Update Junction dataclass (add uuid, diameter, color)
- [x] Parse junction elements from schematic
- [x] Parse component lib_id, position, and rotation from schematic
- [x] Implement graph building workflow:
  1. [x] Parse symbol libraries and cache pin definitions
  2. [x] Calculate all component pin positions
  3. [x] Add all junctions to graph
  4. [x] Add all component pins to graph
  5. [x] Add all wires to graph (matches to existing nodes)
- [x] Add integration tests:
  - [x] test_01_fixture: Simple 2-component graph
  - [x] test_03A_fixture: Graph with junction + crossing wires
  - [x] Pins connect to wires correctly
  - [x] Junctions connect multiple wires

**Critical Rule**: Only connect wires through **explicit junction elements**
- Junction present at (x,y) → wires ARE connected
- Junction absent at (x,y) → wires crossing are NOT connected

**Reference**: Design doc Sections 3.5, 4.2

**Implementation**:
- `kicad2wireBOM/graph_builder.py` - build_connectivity_graph() function
- `tests/test_graph_building.py` - 5 integration tests
- Commit: 17e97b0, [next commit]

---

#### Phase 4D: Wire-to-Component Matching and BOM Integration ✅ COMPLETE

**Goal**: Use connectivity graph for accurate wire matching in BOM output

**Tasks**:
- [x] Implement `identify_wire_connections(wire, graph)`:
  - [x] Get start and end nodes from graph
  - [x] Convert node to reference string:
    - component_pin → "SW1-1"
    - junction → "JUNCTION-{uuid}"
    - wire_endpoint → "UNKNOWN"
- [x] Update WireSegment dataclass:
  - [x] Add start_connection field
  - [x] Add end_connection field
- [x] Update CLI to use graph connections:
  - [x] Build connectivity graph after parsing
  - [x] Identify wire connections using graph
  - [x] Use connection info in BOM output
  - [x] Handle junction and unknown connections

**Reference**: Design doc Section 4.3

**Implementation**:
- `kicad2wireBOM/wire_connections.py` - identify_wire_connections() function
- Updated `kicad2wireBOM/__main__.py` - CLI uses graph for connections
- Updated `kicad2wireBOM/schematic.py` - WireSegment has connection fields
- `tests/test_wire_connections.py` - 5 tests
- Commit: [next commit]

**BOM Output Example** (test_01_fixture):
```
Wire Label | From    | To              | ...
P1A        | SW1-1   | JUNCTION-51609a | ...
P2A        | SW2-3   | JUNCTION-51609a | ...
(unlabeled)| JUNCTION-51609a | J1-1   | ...
```

---

### Phase 5: Enhanced Wire Calculations

Current wire calculator reused from previous work - already functional!

**Potential Enhancements** (optional, not blocking):
- [ ] Add validation warnings for wires without labels (permissive mode)
- [ ] Add validation for orphaned labels
- [ ] Add duplicate circuit ID detection
- [ ] Improve current determination algorithm

### Phase 6: Output Generation

**Current Status**: CSV output works for basic cases

**TODO**:
- [ ] Test CSV output with complex multi-wire circuits
- [ ] Implement Markdown output (optional)
- [ ] Add engineering mode output (optional, can defer)

### Phase 7: CLI Polish

**Current Status**: Basic CLI works, tested

**TODO**:
- [ ] Add better error messages
- [ ] Add validation mode (check schematic without generating BOM)
- [ ] Add verbose/debug output option
- [ ] Configuration file loading (optional, can defer)

### Phase 8: Integration Testing

**TODO**:
- [ ] Create integration test for test_01_fixture
- [ ] Create integration test for test_02_fixture
- [ ] **CRITICAL**: Create integration test for test_03_fixture (junction test)
- [ ] Add edge case tests

---

## NEXT SESSION RECOMMENDATIONS

### ⭐ IMMEDIATE PRIORITY: Phase 4 Implementation

**Start with Phase 4A: Pin Position Calculation**
1. Read design doc Section 4.1 completely
2. Study test_03A_fixture symbol definitions
3. Write first failing test: parse symbol library for pin definitions
4. Implement symbol library parser (TDD approach)
5. Write test for 0° rotation pin calculation
6. Implement pin calculation algorithm
7. Add tests for 90°, 180°, 270° rotations
8. Add tests for mirroring

**Then Phase 4B: Graph Data Structures**
1. Create NetworkNode and ConnectivityGraph classes
2. TDD: Write tests for each graph method
3. Implement graph building methods
4. Test with mock data

**Then Phase 4C: Integration**
1. Parse junctions from schematic
2. Integrate pin calculation into schematic parsing
3. Build full connectivity graph
4. Test with all three fixtures

**Then Phase 4D: BOM Integration**
1. Implement wire connection identification
2. Update BOM output to show pin-level connections
3. Integration tests with expected output

### After Phase 4: Future Work

**Medium Priority (Robustness)**
- Validation and error handling
- Warnings for unlabeled wires
- Orphaned label detection
- Circuit ID uniqueness validation

**Low Priority (Nice to Have)**
- Markdown output format
- Engineering mode output
- Configuration file support
- Hierarchical schematic support

---

## KEY FILES

### Implementation (Existing)
- `kicad2wireBOM/parser.py` - Schematic parsing (✅ complete for basic features)
- `kicad2wireBOM/schematic.py` - Data models (✅ complete, needs Phase 4 updates)
- `kicad2wireBOM/label_association.py` - Label matching (✅ complete)
- `kicad2wireBOM/component.py` - Component model (✅ reused, needs Phase 4 updates)
- `kicad2wireBOM/wire_calculator.py` - Calculations (✅ reused)
- `kicad2wireBOM/__main__.py` - CLI (✅ basic version working, needs Phase 4 updates)

### Implementation (Phase 4 - To Create)
- `kicad2wireBOM/pin_calculator.py` - Pin position calculation (Phase 4A)
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures and algorithms (Phase 4B)
- `kicad2wireBOM/symbol_library.py` - Symbol definition parsing and caching (Phase 4A)

### Tests (Existing)
- `tests/test_parser_schematic.py` - Parser tests (8 tests ✅)
- `tests/test_schematic.py` - Data model tests (4 tests ✅)
- `tests/test_label_association.py` - Label matching tests (11 tests ✅)
- All other test files - Reused from previous work (46 tests ✅)

### Tests (Phase 4 - To Create)
- `tests/test_pin_calculator.py` - Pin calculation tests (Phase 4A)
- `tests/test_connectivity_graph.py` - Graph data structure tests (Phase 4B)
- `tests/test_symbol_library.py` - Symbol library parsing tests (Phase 4A)
- `tests/test_junction_handling.py` - Junction semantics tests (Phase 4C)
- `tests/test_integration_phase4.py` - End-to-end tests with all fixtures (Phase 4D)

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit ✅ WORKING
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch (untested)
- `tests/fixtures/test_03_fixture.kicad_sch` - Junction example (HIGH PRIORITY)
- `tests/fixtures/test_03A_fixture.kicad_sch` - ✨ NEW: Junction + crossing wires (validates semantics)

---

## MIGRATION NOTES

This implementation was completed using a **hybrid migration approach**:

**Kept from netlist-based work:**
- Component dataclass and all tests
- Wire calculator functions (length, gauge, voltage drop)
- Reference data tables
- Wire BOM data structures
- CSV output generation
- 50 existing tests

**Replaced with schematic-based:**
- Parser (now uses sexpdata, not kinparse)
- Removed Circuit abstraction (netlist-specific)
- Added WireSegment and Label models
- Added label-to-wire proximity matching
- Updated CLI orchestration

**Result**: 80% code reuse, 20% new schematic-specific code. All 69 tests passing.

---

## DEVELOPMENT WORKFLOW

### TDD Cycle (ALWAYS FOLLOW)
1. **RED**: Write failing test
2. **Verify**: Run test, confirm it fails correctly
3. **GREEN**: Write minimal code to pass test
4. **Verify**: Run test, confirm it passes
5. **REFACTOR**: Clean up while keeping tests green
6. **COMMIT**: Commit the change with updated todo

### Pre-Commit Checklist
Before EVERY commit:
1. Update this programmer_todo.md with completed tasks
2. Mark tasks `[x]` Complete when done
3. Run full test suite (`pytest -v`)
4. Include updated programmer_todo.md in commit

### Circle K Protocol
If you encounter:
- Design inconsistencies
- Architectural ambiguities
- Blockers requiring decisions

**THEN**:
1. Say "Strange things are afoot at the Circle K"
2. Explain the issue clearly
3. Suggest options or ask for guidance
4. Wait for architectural decision

---

## ARCHIVED DOCUMENTS

**Moved to `docs/archive/`**:
- Old netlist-based design documents
- Previous implementation plans
- `programmer_notes.md` (archived after Phase 1-3 completion)

**DO NOT** reference archived documents - they describe the wrong architecture.

---

## SUCCESS METRICS

**Minimum Viable Product** (Current status):
- [x] Parse .kicad_sch files
- [x] Extract wire segments
- [x] Associate labels with wires
- [x] Calculate wire lengths and gauges
- [x] Generate CSV output
- [x] Handle test_01_fixture correctly ✅

**Full Feature Set** (TODO):
- [ ] Handle junctions correctly (test_03_fixture)
- [ ] Trace multi-segment wire paths
- [ ] Match wire endpoints to component pins
- [ ] Handle all three test fixtures
- [ ] Validation and error messages
- [ ] Complete test coverage

**Production Ready** (Future):
- [ ] Hierarchical schematic support
- [ ] Configuration file support
- [ ] Multiple output formats
- [ ] Comprehensive error handling
- [ ] User documentation

---

**Next Programmer Session**: Start with junction extraction and network tracing (Phase 4)
