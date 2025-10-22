# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Task 8 (Unified BOM Generation Refactoring) - Ready to Implement
**Last Updated**: 2025-10-21

---

## CURRENT STATUS

**Working** ✅:
- 122/122 tests passing
- Schematic parsing, connectivity graph, multipoint detection all implemented
- Integration tests verify multipoint logic works correctly

**Problem** ❌:
- CLI doesn't use multipoint logic - CSV output incorrect for 3+way connections
- Code duplication between CLI and integration tests

**Next Task**: Implement unified BOM generation (Task 8 below)

---

## ACTIVE TASK: Unified BOM Generation Refactoring

### Task 8: Create unified bom_generator.py module 🔧 PENDING

**Problem**: Multipoint logic exists and passes tests, but CLI doesn't use it.

**Solution**: Create `bom_generator.py` with `generate_bom_entries()` function that both CLI and tests use.

**Design Reference**: `docs/plans/kicad2wireBOM_design.md` Section 4.5

---

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

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.6

**Key Sections**:
- Section 4.4: 3+way connections (multipoint)
- Section 4.5: Unified BOM generation **[CRITICAL FOR TASK 8]**
- Section 10.1: Module structure

---

## KEY FILES

### Implementation
- `kicad2wireBOM/parser.py` - Schematic parsing
- `kicad2wireBOM/schematic.py` - Data models
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures and tracing
- `kicad2wireBOM/wire_connections.py` - Connection identification (2-point and multipoint)
- `kicad2wireBOM/bom_generator.py` - **[NEW - TO BE CREATED]** Unified BOM entry generation
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way connection (P4A/P4B)
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection (G1A/G2A/G3A)

---

## COMPLETED WORK ARCHIVE

<details>
<summary>Phase 1-5: Expand to see completed tasks and bug fixes</summary>

### Tasks 1-7: 3+Way Connections ✅ COMPLETE (2025-10-21)
- Task 1: Detect 3+Way Connections ✅
- Task 2: Count Labels in 3+Way Connections ✅
- Task 3: Identify Common Pin ✅
- Task 4: Validate 3+Way Labeling ✅
- Task 5: Generate BOM Entries for 3+Way Connections ✅
- Task 6: Integration Test with test_03A ✅
- Task 7: Integration Test with test_04 ✅

**Result**: 122/122 tests passing, multipoint logic fully implemented

### Bug Fixes ✅
- Y-Axis Inversion Bug (2025-10-20): Fixed pin position calculation for KiCad coordinate system
- Connector Component Tracing Bug (2025-10-20): Implemented two-pass algorithm to prioritize direct connections
- Wire Endpoint Tracing (2025-10-20): Extended trace_to_component() for wire_endpoint nodes

</details>

---

## FUTURE WORK

### Phase 6+: Enhancements (Not Blocking)
- Validation & error handling improvements
- CLI polish (validation mode, verbose output)
- Optional features (Markdown output, engineering mode, hierarchical schematics)
