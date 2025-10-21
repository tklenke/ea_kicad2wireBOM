# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-4 Complete - 111/111 tests passing ✅
**Last Updated**: 2025-10-20

---

## ✅ RECENT BUG FIXES

### Y-Axis Inversion Bug in Pin Position Calculation - FIXED (2025-10-20)

**Discovered**: 2025-10-20 (Architect role investigation)
**Fixed**: 2025-10-20 (Programmer role - TDD approach)

**Severity**: CRITICAL - Affected all components with non-zero Y pin offsets

**Root Cause**: KiCad uses inverted Y-axis coordinate system (graphics convention where +Y is DOWN), but our pin position calculation was treating it as mathematical convention (+Y is UP).

**Bug Location**: `kicad2wireBOM/pin_calculator.py:62`

**Fix Applied:**
```python
# Before (WRONG):
abs_y = component.y + y_rot

# After (CORRECT):
abs_y = component.y - y_rot  # Y-axis inverted in KiCad (graphics convention: +Y is DOWN)
```

**Testing:**
- Added `test_calculate_pin_position_y_axis_inversion()` test verifying actual KiCad fixture data
- Updated 4 existing tests to reflect correct Y-axis coordinate system
- All 111 tests passing ✅

**Verification:**
- SW1 pin 1 now correctly at (125.73, 73.66) ✅
- J1 pin 2 now correctly at (148.59, 88.90) ✅
- All rotation angles (90°, 180°, 270°) work correctly ✅
- Y-mirroring works correctly with inverted coordinate system ✅

---

## COMPLETED WORK

### ✅ Connector Component Tracing Bug FIXED (2025-10-20)

**Bug**: Connector components (like J1) were being skipped in favor of components reachable through longer wire paths.

**Root Cause**: `trace_to_component()` was iterating through wires and returning the FIRST component found. When a junction had multiple wires, it would find components through wire_endpoints before checking for direct component_pin connections.

**Solution**: Implemented two-pass tracing algorithm:
1. FIRST PASS: Check all connected wires for direct component_pin connections
2. SECOND PASS: If no direct connection, recurse through junctions/wire_endpoints

**Testing**:
- Added `test_trace_to_component_prioritizes_direct_component_pin()` test
- All 110 tests passing ✅
- J1 connector now correctly recognized as endpoint

**Current Output** (`test_03A_fixture.kicad_sch`):
```csv
P2A: SW2-3 → J1-1  ✅ (J1 recognized!)
P1A: J1-1 → SW1-3  ✅ (J1 recognized!)
```

### ✅ Wire Endpoint Tracing Implementation (2025-10-20)

The `trace_to_component()` method now correctly handles all node types with proper prioritization:
- `component_pin` nodes → returns component immediately ✅
- `junction` nodes → checks direct pins first, then traces recursively ✅
- `wire_endpoint` nodes → checks direct pins first, then traces recursively ✅

---

## CURRENT STATUS

**What's Working** ✅:
- Schematic parsing (wire segments, labels, components, junctions)
- Label-to-wire association
- Connectivity graph building
- Junction element tracing (schematic dots)
- Wire_endpoint tracing
- Pin position calculation with Y-axis inversion fix
- Wire calculations (length, gauge, voltage drop)
- CSV output generation
- 111/111 tests passing ✅

**New Feature Needed** 🔧:
- 3+Way connection detection and validation (see below)

**Command Line**:
```bash
# Run tests
pytest -v

# Generate BOM
python -m kicad2wireBOM tests/fixtures/test_03A_fixture.kicad_sch output.csv
```

---

## NEXT IMPLEMENTATION: 3+Way Connections

**Architectural Decision**: See kicad2wireBOM_design.md Section 4.4

**Requirement**: Implement detection and validation of 3+way connections (N ≥ 3 component pins connected through junctions).

**Key Concept**:
- N pins connected → expect (N-1) labels
- Unlabeled pin is the common endpoint (terminal block, ground bus, etc.)
- Each labeled wire traces to the common unlabeled pin

**Implementation Tasks** (TDD approach):

### Task 1: Detect 3+Way Connections ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_detect_3way_connection_with_3_pins()` using test_03A fixture (P4A/P4B case)
  - Fixture: `tests/fixtures/test_03A_fixture.kicad_sch`
  - Expected: Detect 3-pin group {SW1-pin2, SW2-pin2, J1-pin2}
- [x] Write test: `test_detect_4way_connection()` using test_04 fixture (G1A/G2A/G3A case)
  - Fixture: `tests/fixtures/test_04_fixture.kicad_sch`
  - Expected: Detect 4-pin group {L1-pin1, L2-pin1, L3-pin1, BT1-pin2}
- [x] Implement: Add method `detect_multipoint_connections(graph: ConnectivityGraph) -> list[set[ComponentPin]]`
  - Implemented in `kicad2wireBOM/connectivity_graph.py`
  - Uses BFS graph traversal to find all connected component pin groups
  - Returns groups where N ≥ 3
- [x] Run tests, verify detection works
  - All 113 tests passing ✅

### Task 2: Count Labels in 3+Way Connections ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_count_labels_in_3way_connection()`
  - test_03A P4A/P4B: expect 2 labels for 3 pins ✅
  - test_04 grounds: expect 3 labels for 4 pins ✅
- [x] Implement: Add method `count_labels_in_group(group: set[ComponentPin], graph: ConnectivityGraph) -> int`
  - Implemented in `kicad2wireBOM/connectivity_graph.py`
  - Uses BFS to traverse all wires in connected component
  - Counts unique circuit ID labels found
- [x] Run tests, verify label counting
  - All 114 tests passing ✅

### Task 3: Identify Common Pin
- [ ] Write test: `test_identify_common_pin_in_3way()`
  - test_03A P4A/P4B: expect J1-pin2 as common pin
  - test_04 grounds: expect BT1-pin2 as common pin
- [ ] Implement: Add method `identify_common_pin(group: set[ComponentPin], graph: ConnectivityGraph) -> ComponentPin`
  - For each pin in group, check if it's reached by a labeled segment
  - The pin NOT reached by labeled segments is the common pin
  - Return common pin or None if ambiguous
- [ ] Run tests, verify common pin identification

### Task 4: Validate 3+Way Labeling
- [ ] Write test: `test_validate_3way_connection_correct_labels()` - should pass without errors
- [ ] Write test: `test_validate_3way_connection_too_many_labels()` - should error/warn
- [ ] Write test: `test_validate_3way_connection_too_few_labels()` - should error/warn
- [ ] Implement: Add validation in `wire_connections.py` or new `multipoint_validator.py`
  - Check: label_count == (N - 1)
  - Check: exactly one common pin identified
  - Strict mode: raise errors
  - Permissive mode: log warnings
- [ ] Run tests, verify validation

### Task 5: Generate BOM Entries for 3+Way Connections
- [ ] Write test: `test_generate_bom_for_3way_connection()`
  - test_03A: expect P4A: SW2-pin2 → J1-pin2, P4B: SW1-pin2 → J1-pin2
  - test_04: expect G1A: L1-pin1 → BT1-pin2, etc.
- [ ] Modify: Update `identify_wire_connections()` or create new function for 3+way handling
  - For each labeled segment in 3+way group, generate entry: labeled-pin → common-pin
- [ ] Run tests, verify BOM output matches expected

### Task 6: Integration Test with test_03A
- [ ] Write test: `test_03A_fixture_complete_bom_with_3way()`
  - Parse test_03A fixture
  - Generate complete BOM
  - Compare against `docs/input/test_03A_out_expected.csv`
  - All 5 wires should match expected output
- [ ] Fix any issues until test passes

### Task 7: Integration Test with test_04
- [ ] Create expected output file: `docs/input/test_04_out_expected.csv`
  - Document expected BOM for 4-way ground connection + power circuits
- [ ] Write test: `test_04_fixture_complete_bom_with_4way()`
  - Parse test_04 fixture
  - Generate complete BOM
  - Compare against expected output
- [ ] Fix any issues until test passes

**Success Criteria**:
- All existing tests still pass (111/111)
- New 3+way connection tests pass
- test_03A output matches expected (P4A/P4B correct)
- test_04 output correct for 4-way ground connection

---

## FUTURE WORK

### Phase 5+: Enhancements (Not Blocking)

**Validation & Error Handling**:
- [ ] Warnings for unlabeled wires
- [ ] Orphaned label detection
- [ ] Duplicate circuit ID detection
- [ ] Better error messages

**CLI Polish**:
- [ ] Validation mode (check without generating BOM)
- [ ] Verbose/debug output option
- [ ] Configuration file loading

**Optional Features**:
- [ ] Markdown output format
- [ ] Engineering mode output
- [ ] Hierarchical schematic support

---

## KEY FILES

### Implementation
- `kicad2wireBOM/parser.py` - Schematic parsing
- `kicad2wireBOM/schematic.py` - Data models (WireSegment, Label, Component, Junction)
- `kicad2wireBOM/label_association.py` - Label-to-wire matching
- `kicad2wireBOM/symbol_library.py` - Symbol library parsing
- `kicad2wireBOM/pin_calculator.py` - Pin position calculation
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures and tracing
- `kicad2wireBOM/graph_builder.py` - Build graph from schematic
- `kicad2wireBOM/wire_connections.py` - Wire connection identification
- `kicad2wireBOM/wire_calculator.py` - Wire calculations
- `kicad2wireBOM/output_csv.py` - CSV output generation
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit ✅
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch ✅
- `tests/fixtures/test_03A_fixture.kicad_sch` - Junction + crossing wires + 3-way connection (P4A/P4B) ✅
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection (G1A/G2A/G3A) + power circuits **[NEW - 2025-10-21]**

---

## DEVELOPMENT WORKFLOW

### TDD Cycle (ALWAYS FOLLOW)
1. **RED**: Write failing test
2. **Verify**: Run test, confirm it fails correctly
3. **GREEN**: Write minimal code to pass test
4. **Verify**: Run test, confirm it passes
5. **REFACTOR**: Clean up while keeping tests green
6. **COMMIT**: Commit with updated todo

### Pre-Commit Checklist
1. Update this programmer_todo.md with completed tasks
2. Run full test suite (`pytest -v`)
3. Include updated programmer_todo.md in commit

### Circle K Protocol
If you encounter design inconsistencies, architectural ambiguities, or blockers:
1. Say "Strange things are afoot at the Circle K"
2. Explain the issue clearly
3. Suggest options or ask for guidance
4. Wait for architectural decision

---

## DESIGN REFERENCE

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.2

**Key Sections**:
- Section 3.5: Junction semantics (explicit junctions only)
- Section 4.1: Pin position calculation algorithm
- Section 4.2: Connectivity graph data structures
- Section 4.3: Wire-to-component matching (junction transparency)
- Section 7.3: CSV output format

**Archived Docs** (DO NOT USE):
- `docs/archive/` - Old netlist-based design (wrong architecture)
