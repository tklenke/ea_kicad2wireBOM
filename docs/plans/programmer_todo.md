# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-4 Complete, Tasks 1-7 (3+Way Connections) Complete - 122/122 tests passing ✅, Task 8 (Unified BOM Generation Refactoring) Pending
**Last Updated**: 2025-10-21

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

### Task 3: Identify Common Pin ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_identify_common_pin_in_3way()`
  - test_03A P4A/P4B: expect J1-pin2 as common pin ✅
  - test_04 grounds: expect BT1-pin2 as common pin ✅
- [x] Implement `identify_common_pin()` with SEGMENT-LEVEL algorithm
  - Implemented in `connectivity_graph.py:450`
  - Algorithm correctly implements fragment counting and segment tracing
  - Segments traced from each pin, stopping at junctions (3+ fragments) or group pins
  - Identifies the ONE pin whose segment has no circuit_id labels
- [x] Run tests, verify common pin identification
  - All 115 tests passing ✅
  - test_03A: J1-pin2 correctly identified ✅
  - test_04: BT1-pin2 correctly identified ✅

### Task 4: Validate 3+Way Labeling ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_validate_3way_connection_correct_labels()` - passes validation ✓
- [x] Write test: `test_validate_3way_connection_too_many_labels()` - fails validation ✓
- [x] Write test: `test_validate_3way_connection_too_few_labels()` - fails validation ✓
- [x] Implement: `validate_multipoint_connection()` in `connectivity_graph.py`
  - Checks: label_count == (N - 1) ✓
  - Checks: exactly one common pin identified ✓
  - Supports strict (error) and permissive (warning) modes ✓
- [x] Run tests, verify validation - All 118 tests passing ✓

### Task 5: Generate BOM Entries for 3+Way Connections ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_generate_bom_for_3way_connection()`
  - test_03A: P4A: SW2-2 → J1-2, P4B: SW1-2 → J1-2 ✓
  - test_04: G1A: L1-1 → BT1-2, G2A: L2-1 → BT1-2, G3A: L3-1 → BT1-2 ✓
- [x] Implement: `generate_multipoint_bom_entries()` in `wire_connections.py`
  - For each labeled segment in group, generates: labeled-pin → common-pin ✓
  - Uses segment-level tracing to find labels ✓
- [x] Run tests, verify BOM output - All 120 tests passing ✓

### Task 6: Integration Test with test_03A ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_03A_fixture_multipoint_integration()`
  - Parses test_03A fixture ✓
  - Generates complete BOM (multipoint + regular) ✓
  - Verifies all 5 entries: P1A, P2A, P3A, P4A, P4B ✓
  - P4A/P4B correctly generated from 3-way connection ✓
- [x] All assertions pass ✓

### Task 7: Integration Test with test_04 ✅ COMPLETE (2025-10-21)
- [x] Write test: `test_04_fixture_multipoint_integration()`
  - Parses test_04 fixture ✓
  - Generates complete BOM (multipoint + regular) ✓
  - Verifies all 7 entries: G1A, G2A, G3A, L1A, L2A, L3A, L4A ✓
  - G1A/G2A/G3A correctly generated from 4-way ground connection ✓
- [x] All assertions pass ✓

**Success Criteria**:
- All existing tests still pass (111/111)
- New 3+way connection tests pass
- test_03A output matches expected (P4A/P4B correct)
- test_04 output correct for 4-way ground connection

### Task 8: Unified BOM Generation Refactoring 🔧 PENDING (2025-10-21)

**Problem**: Multipoint connection logic exists and passes integration tests, but CLI (`__main__.py`) doesn't use it. This creates a gap where tests pass but CSV output is incorrect for 3+way connections.

**Root Cause**: Code duplication between CLI and integration tests. The integration tests implement the correct logic (detect multipoint + generate entries + skip multipoint labels in regular processing), but `__main__.py` only does regular 2-point processing.

**Architectural Decision**: Create unified `bom_generator.py` module with `generate_bom_entries()` function to eliminate duplication and ensure CLI uses same code path as tests. See design doc Section 4.5.

**Implementation Tasks** (TDD approach):

#### Subtask 8.1: Create bom_generator.py module 📋 PENDING
- [ ] Create new file: `kicad2wireBOM/bom_generator.py`
- [ ] Add module header comments (ABOUTME)
- [ ] Import required types: `WireSegment`, `ConnectivityGraph`, `identify_wire_connections`, `generate_multipoint_bom_entries`
- [ ] Define function signature:
  ```python
  def generate_bom_entries(
      wires: list[WireSegment],
      graph: ConnectivityGraph
  ) -> list[dict[str, str]]:
  ```

#### Subtask 8.2: Write unit tests for generate_bom_entries() 📋 PENDING
- [ ] Create test: `test_generate_bom_entries_with_2point_connections()`
  - Uses test_01 or test_02 fixture (no multipoint)
  - Verifies regular 2-point entries generated correctly
  - Expected: Each labeled wire produces one entry
- [ ] Create test: `test_generate_bom_entries_with_3way_connection()`
  - Uses test_03A fixture
  - Verifies multipoint entries (P4A, P4B) AND regular entries (P1A, P2A, P3A)
  - Expected: 5 total entries
- [ ] Create test: `test_generate_bom_entries_with_4way_connection()`
  - Uses test_04 fixture
  - Verifies 4-way ground (G1A, G2A, G3A) AND power circuits (L1A, L2A, L3A, L4A)
  - Expected: 7 total entries
- [ ] Run tests - should FAIL (no implementation yet)

#### Subtask 8.3: Implement generate_bom_entries() 📋 PENDING
- [ ] Implement algorithm from design doc Section 4.5:
  1. Store wires in graph.wires dict (for multipoint processing)
  2. Call `graph.detect_multipoint_connections()` to find N ≥ 3 pin groups
  3. For each multipoint group, call `generate_multipoint_bom_entries()`
  4. Track which circuit_ids are used by multipoint (set of labels)
  5. For remaining wires (not in multipoint_labels):
     - Call `identify_wire_connections()` for 2-point tracing
     - Generate entry dict if both endpoints found
  6. Return combined list (multipoint + regular entries)
- [ ] Run tests - should PASS
- [ ] Verify all 122 existing tests still pass

#### Subtask 8.4: Refactor integration tests to use new function 📋 PENDING
- [ ] Update `test_03A_fixture_multipoint_integration()`:
  - Remove duplicated logic (lines 49-91)
  - Replace with single call: `bom_entries = generate_bom_entries(wires, graph)`
  - Keep assertions unchanged
- [ ] Update `test_04_fixture_multipoint_integration()`:
  - Remove duplicated logic (lines 152-189)
  - Replace with single call: `bom_entries = generate_bom_entries(wires, graph)`
  - Keep assertions unchanged
- [ ] Run integration tests - should PASS (output unchanged)
- [ ] Verify all 122+ tests still pass

#### Subtask 8.5: Update CLI to use new function 📋 PENDING
- [ ] Update `__main__.py`:
  - Import `generate_bom_entries` from `bom_generator`
  - Replace lines 136-165 (individual wire processing loop) with:
    ```python
    # Generate BOM entries (handles both multipoint and regular)
    bom_entries = generate_bom_entries(wires, graph)

    # For each entry, calculate wire properties
    for entry in bom_entries:
        circuit_id = entry['circuit_id']
        from_component = entry['from_component']
        from_pin = entry['from_pin']
        to_component = entry['to_component']
        to_pin = entry['to_pin']

        # [Existing wire calculation logic continues...]
    ```
  - Keep all wire calculation logic (length, gauge, color) unchanged
- [ ] Commit changes with message about refactoring

#### Subtask 8.6: Verify CLI output correctness 📋 PENDING
- [ ] Generate CSV for test_03A: `python -m kicad2wireBOM tests/fixtures/test_03A_fixture.kicad_sch /tmp/test_03A_out.csv`
- [ ] Compare output to expected: `diff /tmp/test_03A_out.csv docs/input/test_03A_out_expected.csv`
  - Should match (except gauge discrepancy noted by Tom)
  - P4A: SW2,2 → J1,2 ✓
  - P4B: SW1,2 → J1,2 ✓
- [ ] Generate CSV for test_04: `python -m kicad2wireBOM tests/fixtures/test_04_fixture.kicad_sch /tmp/test_04_out.csv`
- [ ] Compare output to expected: `diff /tmp/test_04_out.csv docs/input/test_04_out_expected.csv`
  - Should match
  - G1A: L1,1 → BT1,2 ✓
  - G2A: L2,1 → BT1,2 ✓
  - G3A: L3,1 → BT1,2 ✓
- [ ] All tests pass: `pytest -v`
- [ ] Commit with message about verified CLI output

**Success Criteria**:
- New `bom_generator.py` module created ✓
- Unit tests for `generate_bom_entries()` pass ✓
- Integration tests refactored and still pass ✓
- CLI refactored to use new function ✓
- CLI CSV output matches expected files for test_03A and test_04 ✓
- All tests pass (122+) ✓
- No code duplication between CLI and tests ✓

**Design Reference**: See `docs/plans/kicad2wireBOM_design.md` Section 4.5

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
