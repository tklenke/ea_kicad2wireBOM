# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-4 Complete - 109/109 tests passing ✅
**Last Updated**: 2025-10-20

---

## ⚠️ CURRENT BLOCKER: J1 Connector Component Not Being Recognized

**Issue Identified**: 2025-10-20

The BOM output is incorrectly tracing through J1 (connector component) instead of treating it as an endpoint.

**Current Output** (`docs/input/test_03A_out_current.csv`):
```csv
P2A,SW2,3,SW1,3,... ❌ (shows SW2↔SW1, skipping J1)
P1A,SW2,3,SW1,3,... ❌ (shows SW2↔SW1, skipping J1)
```

**Expected Output** (`docs/input/test_03A_out_expected.csv`):
```csv
P2A,SW2,1,J1,1,...  ✅ (shows SW2↔J1 connection)
P1A,SW1,1,J1,1,...  ✅ (shows SW1↔J1 connection)
P3A,SW1,3,SW2,3,... ✅ (direct SW1↔SW2 connection)
```

**Root Cause**: J1 is a `Conn_01x02` connector component (2-pin connector). It should be treated as a component endpoint, but the current implementation is either:
1. Not adding J1's pins to the connectivity graph as `component_pin` nodes, OR
2. Not parsing J1 component at all (missing footprint encoding?)

**Architecture Clarification** (design doc updated):
- **Junction ELEMENTS** (schematic dots) → TRANSPARENT, trace through them
- **Connector COMPONENTS** (J1, J2, TB1) → ENDPOINTS, stop at their pins

**Next Steps**:
1. Verify J1 component is being parsed from schematic
2. Check if J1's footprint has proper encoding `|(fs,wl,bl)Rvalue`
3. Verify J1's pins are being added to connectivity graph as `component_pin` nodes
4. Add/fix test to ensure connector components are treated as endpoints

---

## COMPLETED WORK

### ✅ Wire Endpoint Tracing Implementation (2025-10-20)

The `trace_to_component()` method now correctly handles `wire_endpoint` nodes. All node types supported:
- `component_pin` nodes → returns component ✅
- `junction` nodes → traces recursively through connected wires ✅
- `wire_endpoint` nodes → traces recursively through connected wires ✅

---

## CURRENT STATUS

**What's Working** ✅:
- Schematic parsing (wire segments, labels, components, junctions)
- Label-to-wire association
- Pin position calculation with rotation/mirroring
- Connectivity graph building
- Junction element tracing (schematic dots)
- Wire_endpoint tracing
- Wire calculations (length, gauge, voltage drop)
- CSV output generation
- 109/109 tests passing (but output doesn't match expected)

**What's Broken** ⚠️:
- J1 connector component not recognized as endpoint (see CURRENT BLOCKER above)

**Command Line**:
```bash
# Run tests
pytest -v

# Generate BOM
python -m kicad2wireBOM tests/fixtures/test_03A_fixture.kicad_sch output.csv
```

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
- `kicad2wireBOM/connectivity_graph.py` - **⚠️ NEEDS FIX** - Graph data structures and tracing
- `kicad2wireBOM/graph_builder.py` - Build graph from schematic
- `kicad2wireBOM/wire_connections.py` - Wire connection identification
- `kicad2wireBOM/wire_calculator.py` - Wire calculations
- `kicad2wireBOM/output_csv.py` - CSV output generation
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit ✅
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch
- `tests/fixtures/test_03A_fixture.kicad_sch` - Junction + crossing wires **⚠️ OUTPUT INCOMPLETE**

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
