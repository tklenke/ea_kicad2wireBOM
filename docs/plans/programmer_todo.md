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

### Phase 8: BOM Output Quality Improvements

**Objective**: Improve BOM usability with enhanced error messages, proper ordering, and correct component direction

**Status**: Ready for implementation

**Design**: See "Phase 8 Design" section below

**Sub-features**:
1. Enhanced validation error messages (include component connections)
2. BOM sorting (by system code, circuit ID, segment ID)
3. Component direction ordering (aircraft coordinate-based FROM/TO ordering)

**Tasks**:

[x] Task 8.1: Add connectivity graph parameter to SchematicValidator
- RED: Test SchematicValidator.__init__() accepts optional connectivity_graph parameter ✅
- GREEN: Add `connectivity_graph: Optional[ConnectivityGraph] = None` parameter to __init__ ✅
- REFACTOR: Clean up ✅
- COMMIT: "Add connectivity graph parameter to SchematicValidator"

[x] Task 8.2: Implement helper method to trace wire endpoints
- RED: Test `_format_wire_connections(wire)` returns formatted string with component info ✅
- Test cases: wire with both ends to components, one end to junction, both unknown ✅
- GREEN: Implement helper method that: ✅
  1. Gets nodes at wire start_point and end_point from graph
  2. Calls trace_to_component() for each endpoint
  3. Formats result as "Component1 (pin X) → Component2 (pin Y)"
  4. Handles edge cases (junction, unknown, power symbols)
- REFACTOR: Clean up ✅
- COMMIT: "Add wire endpoint tracing helper for error messages"

[x] Task 8.3: Update missing label error messages
- RED: Test that missing label errors include "Wire connects: ..." line ✅
- GREEN: Update `_check_wire_labels()` to call `_format_wire_connections()` and include in error message ✅
- REFACTOR: Clean up ✅
- COMMIT: "Include component connections in missing label errors"

[ ] Task 8.4: Update CLI to pass graph to SchematicValidator
- RED: Test CLI passes connectivity_graph to SchematicValidator (flat schematics)
- GREEN: Update __main__.py line ~193 to pass graph parameter
- REFACTOR: Clean up
- COMMIT: "Pass connectivity graph to flat schematic validator"

[ ] Task 8.5: Integration testing - enhanced error messages
- Run against test_06 fixture and verify error message includes component info
- Verify all existing tests still pass (176 tests)
- COMMIT: "Verify enhanced validation error messages working"

[ ] Task 8.6: Implement BOM sorting
- RED: Test that BOM entries are sorted by (system_code, circuit_num, segment_letter)
- Test case: Generate BOM with mixed order (G, L, P, A) and verify sorted output
- GREEN: Implement sorting in __main__.py before write_builder_csv()
  1. Parse circuit_id to extract system_code, circuit_num, segment_letter (use existing parse functions)
  2. Sort bom.wires using sort key: (system_code, int(circuit_num), segment_letter)
- REFACTOR: Clean up
- COMMIT: "Sort BOM by system code, circuit ID, segment ID"

[ ] Task 8.7: Implement component direction ordering by aircraft coordinates
- RED: Test `should_swap_components(comp1, comp2)` comparison function
- Test cases:
  - Different BL: abs(BL) largest first
  - Same BL, different FS: largest FS first
  - Same BL and FS, different WL: largest WL first
  - Equal on all: return False (keep current order)
  - Missing LocLoad: return False
- GREEN: Implement comparison function in __main__.py or new module
  1. Compare abs(comp1.bl) vs abs(comp2.bl) - return True if comp2 > comp1
  2. If BL equal, compare FS - return True if comp2.fs > comp1.fs
  3. If BL and FS equal, compare WL - return True if comp2.wl > comp1.wl
  4. Otherwise return False
- GREEN: Apply to each WireConnection before adding to BOM
  1. After creating wire_conn, check if should_swap_components(comp1, comp2)
  2. If True, swap from/to fields in wire_conn
- REFACTOR: Clean up
- COMMIT: "Order wire components by aircraft coordinates (BL, FS, WL)"

[ ] Task 8.8: Integration testing - BOM ordering
- Generate BOM from test fixtures and verify:
  - Wires sorted by system/circuit/segment
  - Components ordered by aircraft coordinates
- Verify all existing tests still pass (176 tests)
- COMMIT: "Verify BOM ordering working correctly"

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

## PHASE 8 DESIGN: BOM Output Quality Improvements

This phase includes three related improvements to BOM output quality and usability.

---

### 8A: Enhanced Validation Error Messages

#### Problem Statement

Current validation error messages show only wire UUIDs, making it difficult for users to locate problematic wires:

```
ERROR: Wire segment f8149f75-7b05-4795-8b9b-a0966b819075 has no valid circuit ID label
       Suggestion: Add circuit ID label to wire
```

Users must manually search the schematic for the UUID to find the wire.

#### Proposed Solution

Include component connection information in error messages:

```
ERROR: Wire segment f8149f75-7b05-4795-8b9b-a0966b819075 has no valid circuit ID label
       Wire connects: BT1 (pin 1) → FH1 (pin Val_A)
       Suggestion: Add circuit ID label to wire
```

This allows users to immediately identify which wire has the problem.

#### Technical Approach

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

#### Edge Cases

| Case | Output Format |
|------|---------------|
| Both ends to components | `BT1 (pin 1) → FH1 (pin 2)` |
| One end to junction | `BT1 (pin 1) → junction` |
| One end unknown | `BT1 (pin 1) → unknown` |
| Both ends unknown | `unknown → unknown` (or omit line) |
| Power symbol | `SW1 (pin 2) → GND` |
| Cross-sheet (hierarchical) | `SW1 (pin 1) → L2 (pin 1)` |

#### Design Decisions

**Q: Should we show component info for all validation errors?**
A: Yes, for errors where it's helpful:
- Missing label errors ✅ (primary use case)
- Multiple circuit IDs ✅ (helps identify wire)
- Duplicate circuit IDs - NO (error is about multiple wires, not one specific wire)

**Q: What if graph is None (backward compatibility)?**
A: Gracefully skip the connection line if graph not available. Existing error message still useful.

**Q: Performance impact?**
A: Minimal - only traces on validation errors (rare in well-formed schematics). Validation runs before BOM generation anyway.

#### Implementation Estimate

**Complexity**: EASY
**Estimated Time**: 1 hour
**Risk**: LOW (uses existing infrastructure, additive change)

---

### 8B: BOM Sorting by System/Circuit/Segment

#### Problem Statement

Current BOM output is unsorted - wires appear in the order they were processed (essentially random from user perspective). This makes the BOM hard to navigate and cross-reference with schematics.

Example of current unsorted output:
```csv
Wire Label,From Component,...
G11A,L3,...
G5A,L1,...
A9A,FH1,...
L2B,L2,...
L10A,L3,...
```

#### Proposed Solution

Sort BOM entries in a logical hierarchy that matches schematic organization:
1. **Primary**: System code (A, E, F, G, K, L, M, P, R, U, V, W)
2. **Secondary**: Circuit ID (numeric)
3. **Tertiary**: Segment ID (letter A, B, C, ...)

Example of properly sorted output:
```csv
Wire Label,From Component,...
A9A,FH1,...        # Avionics
G5A,L1,...         # Ground
G6A,L2,...
G7A,BT1,...
G8A,LRU1,...
G11A,L3,...
L2A,FH1,...        # Lighting
L2B,L2,...
L3A,FH1,...
L3B,L1,...
L10A,L3,...
P1A,BT1,...        # Power
```

#### Technical Approach

**Available Infrastructure**:
- WireSegment already has `system_code`, `circuit_num`, `segment_letter` parsed from circuit_id
- WireBOM has list of WireConnection objects
- Python's built-in `sorted()` function with tuple keys

**Implementation**:
1. Before calling `write_builder_csv()`, sort `bom.wires` in place
2. Create sort key function that extracts (system_code, circuit_num_int, segment_letter)
3. Use `bom.wires.sort(key=sort_key_func)`

#### Edge Cases

| Case | Handling |
|------|----------|
| Missing system_code | Use empty string (sorts first) |
| Missing circuit_num | Use 0 (sorts first) |
| Missing segment_letter | Use empty string (sorts first) |
| Non-numeric circuit_num | Use 0 or raise error during parsing (already validated) |

#### Design Decisions

**Q: Should we sort in CSV writer or in main()?**
A: In main(), before passing to writer. This keeps CSV writer as simple output-only function.

**Q: What about multipoint circuits with different segment letters?**
A: Each segment gets its own entry, sorts correctly (L3A before L3B).

**Q: Alphabetic or numeric sort for circuit_num?**
A: Numeric (1, 2, 10 not "1", "10", "2"). Parse as int for sorting.

#### Implementation Estimate

**Complexity**: EASY
**Estimated Time**: 30 minutes
**Risk**: VERY LOW (standard sorting operation)

---

### 8C: Component Direction Ordering by Aircraft Coordinates

#### Problem Statement

Current FROM/TO component ordering in BOM entries is arbitrary - it depends on wire tracing direction in the connectivity graph. This creates inconsistent wire directions that don't align with physical harness construction.

Example of current arbitrary ordering:
```csv
Wire Label,From Component,From Pin,To Component,To Pin
L2B,L2,1,SW1,1           # Component order arbitrary
L3B,SW2,1,L1,1           # Could be reversed
```

For wire harness construction, it's helpful to have a consistent direction based on aircraft coordinate system, typically starting from components furthest from centerline, moving aft to forward, top to bottom.

#### Proposed Solution

Order FROM/TO components using aircraft coordinate system priority:
1. **Primary**: Largest abs(BL) first - furthest laterally from centerline
2. **Secondary**: Largest FS first (if BL equal) - furthest aft
3. **Tertiary**: Largest WL first (if BL and FS equal) - topmost

This creates consistent directional flow in harness construction.

Example with coordinate-based ordering:
```csv
Wire Label,From Component,From Pin,To Component,To Pin
# L2: BL=10, FS=100, WL=25  →  SW1: BL=0, FS=50, WL=20
L2B,L2,1,SW1,1           # L2 first (abs(BL)=10 > abs(BL)=0)

# SW2: BL=0, FS=60, WL=20  →  L1: BL=-10, FS=100, WL=25
L3B,L1,1,SW2,1           # L1 first (abs(BL)=10 > abs(BL)=0)
```

#### Technical Approach

**Available Infrastructure**:
- Component class has `fs`, `wl`, `bl` attributes from LocLoad encoding
- BOM entries created in __main__.py with comp1 and comp2 available
- WireConnection dataclass has from/to fields that can be swapped

**Implementation**:
1. Create `should_swap_components(comp1, comp2) -> bool` comparison function
2. Apply after creating WireConnection but before adding to BOM
3. If True, swap from_component/from_pin with to_component/to_pin

**Comparison Algorithm**:
```python
def should_swap_components(comp1, comp2) -> bool:
    """Return True if comp1 and comp2 should be swapped (comp2 should be FROM)"""
    # Handle missing components or LocLoad
    if not comp1 or not comp2:
        return False
    if not hasattr(comp1, 'bl') or not hasattr(comp2, 'bl'):
        return False

    # Priority 1: abs(BL) - furthest from centerline first
    abs_bl1 = abs(comp1.bl)
    abs_bl2 = abs(comp2.bl)
    if abs_bl1 != abs_bl2:
        return abs_bl2 > abs_bl1  # Swap if comp2 further from centerline

    # Priority 2: FS - furthest aft first
    if comp1.fs != comp2.fs:
        return comp2.fs > comp1.fs  # Swap if comp2 further aft

    # Priority 3: WL - topmost first
    if comp1.wl != comp2.wl:
        return comp2.wl > comp1.wl  # Swap if comp2 higher

    # Equal on all coordinates - keep current order
    return False
```

#### Edge Cases

| Case | Handling |
|------|----------|
| Missing LocLoad on one component | Keep current order (don't swap) |
| Missing LocLoad on both | Keep current order |
| Equal on all coordinates | Keep current order |
| Power symbols (GND, +12V) | Likely missing LocLoad, keep current order |
| Cross-sheet hierarchical | Works if both components have LocLoad |

#### Design Decisions

**Q: Where should the swap happen?**
A: In __main__.py after creating WireConnection, before adding to BOM. Keeps logic in one place.

**Q: Should we swap in-place or create new WireConnection?**
A: Swap fields in existing WireConnection (more efficient, simpler code).

**Q: What if power symbols don't have LocLoad?**
A: Gracefully skip swapping (return False). Power symbols typically don't need coordinate-based ordering.

**Q: Should we add a --no-component-ordering flag?**
A: Not for v1. This is a reasonable default. Can add flag later if users request it.

#### Implementation Estimate

**Complexity**: MODERATE
**Estimated Time**: 1-2 hours (including edge case testing)
**Risk**: LOW (localized change, clear comparison logic)

---

## PHASE 8 SUMMARY

**Total Implementation Estimate**: 3-4 hours
**Total Complexity**: MODERATE (mainly due to 8C coordinate comparison)
**Overall Risk**: LOW (all additive changes, no algorithm modifications)

**Implementation Order**:
1. Tasks 8.1-8.5: Enhanced error messages (validation improvement)
2. Task 8.6: BOM sorting (simple, builds confidence)
3. Task 8.7-8.8: Component ordering (most complex, do last)

---

## NOTES

- All Phase 1-7 features are complete and tested
- System is ready for real-world usage
- Phase 8 is a usability enhancement (not blocking functionality)
