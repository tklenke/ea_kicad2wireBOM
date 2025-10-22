# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 6 Revision - Notes Aggregation Bug Fix 🚧
**Last Updated**: 2025-10-22

---

## CURRENT STATUS

✅ **Phase 1-5 Complete** (Core features)
⚠️ **Phase 6 Needs Revision** (Validation & Error Handling):
- 146/146 tests passing but test_05C output is incorrect
- ✅ Notes field infrastructure implemented
- ✅ CSV output includes Notes column
- ✅ Validator module with all validation checks implemented
- ✅ Integration tests for test_05A/B/C fixtures all passing
- ✅ CLI --permissive flag working
- ⚠️ **BUG FOUND**: Notes not aggregated across wire fragments (test_05C)

**Issue Identified by Architect**:
- test_05C fixture has "10AWG" label on vertical wire fragment (BT1-2 → junction)
- Circuit ID "G4A" label is on horizontal wire fragment (junction → GB1-1)
- Expected: G4A BOM entry should have notes="10AWG"
- Actual: G4A BOM entry has notes="" (empty)
- Root cause: Notes only collected from fragment with circuit ID, not all fragments forming circuit

**Status**: Architectural design revised. Ready for implementation.
**Next Task**: Implement notes aggregation across wire fragments in bom_generator.py

---

## PHASE 6 REVISION: NOTES AGGREGATION

**Architectural Decision**: Notes must be aggregated from ALL wire fragments forming a circuit, not just the fragment with the circuit ID label.

**Design References**:
- `docs/plans/validation_design.md` - Section 7: Integration Points (bom_generator.py)
- `docs/plans/kicad2wireBOM_design.md` - Section 3.4: Label Extraction and Association
- `docs/plans/kicad2wireBOM_design.md` - Section 4.5: Notes Aggregation Algorithm

### Task: Implement Notes Aggregation in bom_generator.py

**Objective**: Modify `bom_generator.py` to collect notes from all wire fragments forming a circuit.

**Current Behavior** (line 75 in bom_generator.py):
```python
notes_str = ' '.join(wire.notes) if wire.notes else ''
```
This only uses notes from the single wire fragment with the circuit_id.

**Required Behavior**:
- Traverse connectivity graph to find ALL wire fragments between from_conn and to_conn
- Collect notes from each fragment's notes list
- Deduplicate (avoid same note appearing multiple times)
- Concatenate with space separator

**Implementation Steps**:

1. [ ] **Write helper function**: `collect_circuit_notes(graph, circuit_id, from_conn, to_conn)`
   - Takes connectivity graph and endpoint connections
   - Uses BFS/DFS to traverse from from_pos to to_pos
   - Collects notes from all wire segments in path
   - Returns deduplicated, space-separated string

2. [ ] **Write unit tests** for `collect_circuit_notes()`:
   - Test case: Single fragment with notes
   - Test case: Multiple fragments, notes on one fragment
   - Test case: Multiple fragments, notes on multiple fragments
   - Test case: Duplicate notes (verify deduplication)
   - Test case: No notes (empty string)

3. [ ] **Update `generate_bom_entries()`** to use new helper:
   - Replace `' '.join(wire.notes)` with call to `collect_circuit_notes()`
   - Pass graph, circuit_id, from_conn, to_conn

4. [ ] **Verify test_05C output**:
   - Run CLI on test_05C_fixture.kicad_sch
   - Verify G4A entry has notes="10AWG"
   - Verify L2A entry has notes="24AWG"

5. [ ] **Run full test suite**: Ensure no regressions (146/146 tests should still pass)

6. [ ] **Update expected output file**: `docs/input/test_05C_out_expected.csv` if needed

7. [ ] **Commit with updated programmer_todo.md**

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

**Key Implemented Sections**:
- Section 4.1: Pin position calculation with rotation/mirroring
- Section 4.2-4.3: Connectivity graph and wire-to-component matching
- Section 4.4: 3+way multipoint connections
- Section 4.5: Unified BOM generation
- Section 10.1: Module structure

---

## KEY FILES

### Implementation Modules
- `kicad2wireBOM/parser.py` - S-expression parsing
- `kicad2wireBOM/schematic.py` - Data models
- `kicad2wireBOM/symbol_library.py` - Symbol library parsing
- `kicad2wireBOM/pin_calculator.py` - Pin position calculation
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures
- `kicad2wireBOM/wire_connections.py` - Connection identification (multipoint)
- `kicad2wireBOM/bom_generator.py` - Unified BOM entry generation ✅
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way connection (P4A/P4B)
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection (G1A/G2A/G3A)

---

## COMPLETED WORK ARCHIVE

<details>
<summary>Phases 1-5: Expand to see completed implementation history</summary>

### Phase 5: Unified BOM Generation ✅ (2025-10-22)
- Created `kicad2wireBOM/bom_generator.py` with `generate_bom_entries()` function
- Added 3 unit tests in `tests/test_bom_generator.py`
- Refactored integration tests (eliminated ~80 lines of duplicated code)
- Updated CLI to use unified function (~50 lines removed)
- Verified multipoint entries in CSV output (P4A, P4B, G1A, G2A, G3A)
- **Result**: 125/125 tests passing

### Phase 4: 3+Way Multipoint Connections ✅ (2025-10-21)
- Task 1-7: Detect, validate, and generate BOM entries for N≥3 pin connections
- Implemented (N-1) labeling convention
- Common pin identification using segment-level analysis
- Integration tests with test_03A and test_04
- **Result**: 122/122 tests passing

### Phase 3: Bug Fixes ✅ (2025-10-20)
- Y-Axis Inversion: Fixed pin position calculation for KiCad coordinate system
- Connector Component Tracing: Two-pass algorithm for direct connections
- Wire Endpoint Tracing: Extended trace_to_component() for wire_endpoint nodes

### Phases 1-2: Foundation ✅
- S-expression parser using sexpdata library
- Schematic data models (WireSegment, Component, Junction)
- Symbol library parsing and pin position calculation
- Connectivity graph building
- Basic 2-point wire connection identification

</details>

---

## POTENTIAL FUTURE WORK

See `docs/notes/opportunities_for_improvement.md` for enhancement ideas:
- Validation & error handling improvements
- CLI polish (validation mode, verbose output, markdown format)
- Optional features (engineering mode, hierarchical schematics)
- Wire specification overrides, configuration files
