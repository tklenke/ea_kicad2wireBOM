# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 7 COMPLETE - All Planned Features Implemented ✅
**Last Updated**: 2025-10-25

---

## CURRENT STATUS

✅ **Phase 1-7.6 COMPLETE**: 176/176 tests passing

**All Core Features Implemented**:
- Flat and hierarchical schematic parsing
- Pin position calculation with transforms
- Connectivity graph building (wires, junctions, components, cross-sheet)
- 2-point and N-way multipoint connections
- Unified BOM generation with notes aggregation
- Validation framework (connectivity-aware duplicate detection)
- CLI with strict/permissive modes
- CSV output

**The tool is production-ready for generating wire BOMs from KiCad schematics.**

---

## CURRENT TASKS

### Phase 8: Enhanced Validation Error Messages

**Objective**: Include component connection information in validation error messages

**Status**: Ready for implementation

**Design**: See "Phase 8 Design" section below

**Tasks**:

[ ] Task 8.1: Add connectivity graph parameter to SchematicValidator
- RED: Test SchematicValidator.__init__() accepts optional connectivity_graph parameter
- GREEN: Add `connectivity_graph: Optional[ConnectivityGraph] = None` parameter to __init__
- REFACTOR: Clean up
- COMMIT: "Add connectivity graph parameter to SchematicValidator"

[ ] Task 8.2: Implement helper method to trace wire endpoints
- RED: Test `_format_wire_connections(wire)` returns formatted string with component info
- Test cases: wire with both ends to components, one end to junction, both unknown
- GREEN: Implement helper method that:
  1. Gets nodes at wire start_point and end_point from graph
  2. Calls trace_to_component() for each endpoint
  3. Formats result as "Component1 (pin X) → Component2 (pin Y)"
  4. Handles edge cases (junction, unknown, power symbols)
- REFACTOR: Clean up
- COMMIT: "Add wire endpoint tracing helper for error messages"

[ ] Task 8.3: Update missing label error messages
- RED: Test that missing label errors include "Wire connects: ..." line
- GREEN: Update `_check_wire_labels()` to call `_format_wire_connections()` and include in error message
- REFACTOR: Clean up
- COMMIT: "Include component connections in missing label errors"

[ ] Task 8.4: Update CLI to pass graph to SchematicValidator
- RED: Test CLI passes connectivity_graph to SchematicValidator (flat schematics)
- GREEN: Update __main__.py line ~193 to pass graph parameter
- REFACTOR: Clean up
- COMMIT: "Pass connectivity graph to flat schematic validator"

[ ] Task 8.5: Integration testing
- Run against test_06 fixture and verify error message includes component info
- Verify all existing tests still pass (176 tests)
- COMMIT: "Verify enhanced validation error messages working"

---

## KEY REFERENCES

**Design Documents**:
- `docs/plans/kicad2wireBOM_design.md` v3.0 - Complete design specification
- `docs/plans/hierarchical_validation_design.md` - Validation design
- `docs/ea_wire_marking_standard.md` - Wire marking standard (EAWMS)
- `docs/acronyms.md` - Domain terminology

**Test Fixtures**:
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way connection
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection
- `tests/fixtures/test_05*.kicad_sch` - Validation test cases
- `tests/fixtures/test_06_*.kicad_sch` - Hierarchical schematic (main + 2 sub-sheets)

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

## FUTURE PHASES (Awaiting Architectural Direction)

**Potential Next Features** (see `docs/notes/opportunities_for_improvement.md`):

1. **CLI Enhancements**: Markdown output, engineering mode, verbose/quiet flags
2. **Wire Calculations**: Actual length/gauge/voltage drop (currently using defaults)
3. **Production Features**: REVnnn filenames, --schematic-requirements output
4. **Multi-level Hierarchy**: Nested sub-sheets (currently supports 2 levels)
5. **Sheet Instances**: Same sub-sheet instantiated multiple times
6. **Configuration Files**: `.kicad2wireBOM.yaml` for project defaults
7. **GUI Interface**: Desktop or web interface
8. **KiCad Plugin**: Direct integration with KiCad schematic editor

**No active programming tasks at this time.**

---

## PHASE 8 DESIGN: Enhanced Validation Error Messages

### Problem Statement

Current validation error messages show only wire UUIDs, making it difficult for users to locate problematic wires:

```
ERROR: Wire segment f8149f75-7b05-4795-8b9b-a0966b819075 has no valid circuit ID label
       Suggestion: Add circuit ID label to wire
```

Users must manually search the schematic for the UUID to find the wire.

### Proposed Solution

Include component connection information in error messages:

```
ERROR: Wire segment f8149f75-7b05-4795-8b9b-a0966b819075 has no valid circuit ID label
       Wire connects: BT1 (pin 1) → FH1 (pin Val_A)
       Suggestion: Add circuit ID label to wire
```

This allows users to immediately identify which wire has the problem.

### Technical Approach

**Available Infrastructure**:
- Connectivity graph is built before validation runs (both flat and hierarchical)
- `trace_to_component()` method exists in ConnectivityGraph
- Wire endpoints (start_point, end_point) available in WireSegment
- HierarchicalValidator already receives connectivity graph

**Implementation**:
1. Pass connectivity_graph to SchematicValidator (make it consistent with HierarchicalValidator)
2. Add `_format_wire_connections(wire)` helper method to validator
3. Use `trace_to_component()` to find components at each wire endpoint
4. Format as readable string with component references and pin numbers

### Edge Cases

| Case | Output Format |
|------|---------------|
| Both ends to components | `BT1 (pin 1) → FH1 (pin 2)` |
| One end to junction | `BT1 (pin 1) → junction` |
| One end unknown | `BT1 (pin 1) → unknown` |
| Both ends unknown | `unknown → unknown` (or omit line) |
| Power symbol | `SW1 (pin 2) → GND` |
| Cross-sheet (hierarchical) | `SW1 (pin 1) → L2 (pin 1)` |

### Design Decisions

**Q: Should we show component info for all validation errors?**
A: Yes, for errors where it's helpful:
- Missing label errors ✅ (primary use case)
- Multiple circuit IDs ✅ (helps identify wire)
- Duplicate circuit IDs - NO (error is about multiple wires, not one specific wire)

**Q: What if graph is None (backward compatibility)?**
A: Gracefully skip the connection line if graph not available. Existing error message still useful.

**Q: Performance impact?**
A: Minimal - only traces on validation errors (rare in well-formed schematics). Validation runs before BOM generation anyway.

### Implementation Estimate

**Complexity**: EASY
**Estimated Time**: 1-2 hours for experienced developer
**Risk**: LOW (uses existing infrastructure, additive change)

---

## NOTES

- All Phase 1-7 features are complete and tested
- System is ready for real-world usage
- Phase 8 is a usability enhancement (not blocking functionality)
