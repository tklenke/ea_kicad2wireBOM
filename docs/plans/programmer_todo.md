# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-4 Complete - 108/108 tests passing
**Last Updated**: 2025-10-20

---

## ⚠️ CURRENT BLOCKER - REQUIRES IMMEDIATE FIX

### Wire Endpoint Tracing Not Implemented

**Status**: 108/108 tests passing BUT test_03A BOM output is incomplete

**Problem**: The `trace_to_component()` method in `connectivity_graph.py:138-196` does not handle `wire_endpoint` nodes. It only handles:
- `component_pin` nodes → returns component
- `junction` nodes → traces recursively through connected wires
- `wire_endpoint` nodes → **returns None (BUG)**

**Impact**: Labeled wire segments often connect to unlabeled wire segments at `wire_endpoint` nodes. When tracing stops at these nodes, we get incomplete connections:

```csv
Current Output (WRONG):
P2A,SW2,3,,,         # Missing: should show connection to J1-1
P3A,,,,,             # Missing: should show SW1-3 to SW2-3
P1A,,,SW1,3,         # Missing: should show J1-1 connection

Expected Output:
P2A,J1,1,SW2,3,...
P3A,SW1,3,SW2,3,...
P1A,J1,1,SW1,3,...
```

**Architectural Decision** (from Architect, 2025-10-20): **Extend tracing through wire_endpoints**

This is NOT an architecture change - it's completing the existing architecture.

**Fix Required**: Add third case to `connectivity_graph.py:trace_to_component()` after line 163:

```python
# If this node is a wire_endpoint, trace through connected wires
if node.node_type == 'wire_endpoint':
    # Use same recursive pattern as junction case above
    for wire_uuid in node.connected_wire_uuids:
        # Skip the wire we came from
        if wire_uuid == exclude_wire_uuid:
            continue

        # Get the wire's endpoints
        wire = self.wires[wire_uuid]
        start_key = (round(wire.start_point[0], 2), round(wire.start_point[1], 2))
        end_key = (round(wire.end_point[0], 2), round(wire.end_point[1], 2))

        start_node = self.nodes[start_key]
        end_node = self.nodes[end_key]

        # Find which end is NOT this wire_endpoint node
        node_key = (round(node.position[0], 2), round(node.position[1], 2))

        if start_key == node_key:
            result = self.trace_to_component(end_node, exclude_wire_uuid=wire_uuid)
        elif end_key == node_key:
            result = self.trace_to_component(start_node, exclude_wire_uuid=wire_uuid)
        else:
            continue

        # If we found a component, return it
        if result is not None:
            return result

# No component found (this line already exists at line 196)
return None
```

**TDD Approach**:
1. Write failing test showing current bug (wire_endpoint doesn't trace through)
2. Add wire_endpoint case to trace_to_component()
3. Verify test passes
4. Run full test suite (should still be 108 passing, now with correct BOM output)
5. Manually verify test_03A output CSV shows complete connections

**File to modify**: `kicad2wireBOM/connectivity_graph.py`

**Reference**: See `architect_todo.md` "Junction Transparency Implementation Gap" section for full analysis

---

## CURRENT STATUS

**What's Working** ✅:
- Schematic parsing (wire segments, labels, components, junctions)
- Label-to-wire association
- Pin position calculation with rotation/mirroring
- Connectivity graph building
- Junction tracing (partially - missing wire_endpoint case)
- Wire calculations (length, gauge, voltage drop)
- CSV output generation
- 108/108 tests passing

**What's Broken** ⚠️:
- BOM output incomplete for wires with unlabeled segments (see blocker above)

**Command Line**:
```bash
# Run tests
pytest -v

# Generate BOM (currently produces incomplete output for test_03A)
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
