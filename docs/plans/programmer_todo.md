# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-4 Complete - 110/110 tests passing ✅
**Last Updated**: 2025-10-20

---

## ⚠️ CRITICAL BUG - IMMEDIATE FIX REQUIRED

### Y-Axis Inversion Bug in Pin Position Calculation

**Discovered**: 2025-10-20 (Architect role investigation)

**Severity**: CRITICAL - Affects all components with non-zero Y pin offsets

**Root Cause**: KiCad uses inverted Y-axis coordinate system (graphics convention where +Y is DOWN), but our pin position calculation treats it as mathematical convention (+Y is UP).

**Bug Location**: `kicad2wireBOM/pin_calculator.py:62`

**Current (WRONG) Code:**
```python
abs_y = component.y + y_rot
```

**Should Be:**
```python
abs_y = component.y - y_rot  # Y-axis inverted in KiCad schematics
```

**Evidence:**

SW1 symbol defines pins with mathematical Y coordinates:
- Pin 1: offset (6.35, +2.54) - positive Y = "up" in symbol definition
- Pin 3: offset (6.35, -2.54) - negative Y = "down" in symbol definition

But on schematic, KiCad inverts Y-axis when placing:
- SW1 at (119.38, 76.2) with rotation 0
- Pin 1 should be at (125.73, **73.66**) - LOWER Y value = "up" on schematic
- Pin 3 should be at (125.73, **78.74**) - HIGHER Y value = "down" on schematic

Currently we calculate:
- Pin 1 at (125.73, 78.74) ❌ WRONG - this is actually pin 3's position
- Pin 3 at (125.73, 73.66) ❌ WRONG - this is actually pin 1's position

**Impact:**
- ❌ All switch pin numbers are swapped (pins 1 and 3)
- ❌ J1-2 position is wrong (should be at Y=88.90, not Y=83.82)
- ❌ test_03A output doesn't match expected (expected is CORRECT, current is WRONG)
- ❌ Any component with Y pin offsets will have wrong pin positions
- ✅ Components with Y=0 pin offsets work by accident (e.g., J1 pin 1, SW1/SW2 pin 2)

**Fix Tasks (TDD Approach):**

1. **Write failing test** - Create test that verifies pin positions match KiCad UI
   - Test SW1 pin 1 should be at (125.73, 73.66), not (125.73, 78.74)
   - Test J1 pin 2 should be at (148.59, 88.90), not (148.59, 83.82)
   - Test should currently FAIL

2. **Fix pin_calculator.py** - Apply Y-axis inversion
   - Change line 62: `abs_y = component.y - y_rot`
   - Add comment explaining KiCad's inverted Y-axis
   - Verify rotation matrix still correct with inverted Y

3. **Verify rotation handling** - Check if Y-inversion interacts with rotation
   - Test components at 90°, 180°, 270° rotations
   - Ensure Y-inversion applies AFTER rotation transform (current order should be correct)

4. **Verify mirroring handling** - Check if Y-mirroring needs adjustment
   - Review mirror_y logic in light of inverted coordinate system
   - May need to invert the inversion for Y-mirrored components

5. **Update or verify all existing tests**
   - Run full test suite after fix
   - Update expected values if needed
   - Verify test_03A now produces correct output matching expected

6. **Document coordinate system** - Add documentation
   - Add comment in pin_calculator.py explaining KiCad's coordinate system
   - Update design doc Section 4.1 with Y-axis inversion note

**Priority**: HIGHEST - This is a fundamental coordinate system bug affecting all multi-pin components

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
- Wire calculations (length, gauge, voltage drop)
- CSV output generation
- 110/110 tests passing (but wrong pin positions due to Y-axis bug)

**What's Broken** ⚠️:
- ❌ Pin position calculation - Y-axis inverted (see CRITICAL BUG above)
- ❌ All output has wrong pin numbers for components with non-zero Y pin offsets

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
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures and tracing
- `kicad2wireBOM/graph_builder.py` - Build graph from schematic
- `kicad2wireBOM/wire_connections.py` - Wire connection identification
- `kicad2wireBOM/wire_calculator.py` - Wire calculations
- `kicad2wireBOM/output_csv.py` - CSV output generation
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit ✅
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch
- `tests/fixtures/test_03A_fixture.kicad_sch` - Junction + crossing wires (output wrong due to Y-axis bug)

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
