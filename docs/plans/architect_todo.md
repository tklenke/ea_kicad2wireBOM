# Architect TODO: kicad2wireBOM

**Date**: 2025-10-23
**Status**: Phase 1-6.5 Complete - Major Milestone Achieved ✅

---

## CURRENT STATUS

✅ **All Planned Features Complete**: 150/150 tests passing
- Schematic parsing, connectivity graph, junction handling all working
- 3+way multipoint connection logic implemented and tested
- Unified BOM generation created and integrated into CLI
- Validation & error handling with notes aggregation complete
- CSV output correctly includes multipoint entries and notes field
- CLI supports both strict and permissive modes
- LocLoad custom field migration complete

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.7
**Validation Design**: `docs/plans/validation_design.md`

---

## KEY ARCHITECTURAL DECISIONS (All Implemented)

All major architectural decisions have been implemented and validated:

1. **LocLoad Custom Field** (Section 2.2): Dedicated custom field for component location and electrical data
2. **3+Way Connections** (Section 4.4): Multi-point connections using (N-1) labeling convention
3. **Unified BOM Generation** (Section 4.5): Single `bom_generator.py` module handles all connection types
4. **Pin Position Calculation** (Section 4.1): Precise calculation with rotation matrices and mirroring
5. **Junction Handling** (Sections 3.5, 4.2, 4.3): Graph-based approach with explicit junction elements
6. **Wire Endpoint Tracing** (Section 4.3): Recursive tracing through wire_endpoint nodes
7. **Notes Aggregation** (Section 4.5): BFS traversal collects notes from all wire fragments in a circuit
8. **Validation Framework**: Missing labels, duplicate labels, non-circuit label handling

---

## OPEN QUESTIONS

**Hierarchical Schematics**: Are your aircraft schematics flat or hierarchical?
- Flat: Current design handles this ✅
- Hierarchical: Would need sheet interconnection design (future work)

---


## PHASE 7: Hierarchical Schematic Support ✅ COMPLETE

**Status**: ✅ Design complete AND Programmer todos created
**Design Location**: Section 8 of `kicad2wireBOM_design.md` v3.0
**Programmer Todos**: `docs/plans/programmer_todo.md` Phase 7 section
**Date Completed**: 2025-01-24 (design), 2025-10-24 (todos)

**Summary**:

Comprehensive design specification completed for hierarchical schematic support. Covers:

### Architecture Decisions

✅ **Unified Connectivity Graph** - Single graph spanning all sheets (not per-sheet graphs)
- Added node types: `sheet_pin`, `hierarchical_label`
- Cross-sheet edges explicit in graph
- Existing trace algorithms work unchanged

✅ **Recursive Parser** - Parse root sheet, then recursively parse sub-sheets
- HierarchicalSchematic container with root_sheet + sub_sheets dict
- SheetConnection dataclass maps pin/label pairs
- GlobalNet dataclass for power symbols (GND, +12V, etc.)

✅ **Circuit Label Resolution** - Follows electrical connectivity, not label names
- Circuit identity spans sheets
- Labels "L2A" (main) and "L2B" (lighting) part of same circuit
- Trace connectivity through graph to collect all labels

✅ **Component References** - Resolved from hierarchical instance paths
- Reference designators unique across all sheets
- Parser extracts correct reference from instance path

### Implementation Phases

Detailed 5-phase implementation plan created:
1. **Phase 7.1**: Parser enhancement (recursive sheet parsing)
2. **Phase 7.2**: Graph builder enhancement (unified graph)
3. **Phase 7.3**: Wire tracing update (cross-sheet tracing)
4. **Phase 7.4**: BOM generation update (multi-sheet circuits)
5. **Phase 7.5**: CLI update (hierarchical input)

### Test Strategy

Test fixture test_06 analyzed:
- Main sheet with battery, fuses, switches
- Lighting sub-sheet with lamps (L1, L2, L3)
- Avionics sub-sheet with LRU
- Expected circuits: L2A, L3A (multipoint), A9A, P1A, G7A, etc.

### Documentation Updates

- Section 8 (NEW): Complete hierarchical design (8.1-8.14)
- Section 3.1: Parser updates for recursive parsing
- Section 4: Enhanced connectivity graph
- Section 10: New hierarchical_schematic.py module
- Section 12.2: Updated with Phase 7 status

**Deliverables Completed**:
- ✅ Complete design specification in Section 8 of kicad2wireBOM_design.md
- ✅ Detailed programmer implementation tasks in programmer_todo.md
- ✅ 50+ explicit, actionable tasks broken down by phase (7.1 through 7.5)
- ✅ TDD guidance for each task (RED-GREEN-REFACTOR-COMMIT)
- ✅ Test coverage requirements specified
- ✅ Expected outcomes documented

**Next Action**: Programmer to implement Phase 7.1-7.5 following todos in programmer_todo.md

---

## PHASE 7.6: Hierarchical Validation - Connectivity-Aware Duplicate Detection ✅ COMPLETE

**Status**: ✅ Design complete AND Programmer todos created
**Design Location**: `docs/plans/hierarchical_validation_design.md` (NEW)
**Programmer Todos**: `docs/plans/programmer_todo.md` Phase 7.6 section
**Date Completed**: 2025-10-25

**Summary**:

Comprehensive architectural design for connectivity-aware validation in hierarchical schematics. Fixes incorrect validation errors where duplicate circuit IDs appear on electrically connected wires across sheet boundaries.

### Problem Identified

Current validator flags test_06 with errors:
- `ERROR: Duplicate circuit ID 'L2B' found on 2 wire segments`
- `ERROR: Duplicate circuit ID 'A9A' found on 2 wire segments`

These are FALSE POSITIVES - L2B and A9A appear on multiple sheets but are electrically connected through hierarchical pins/labels, making them VALID.

### Architectural Solution

**Key Insight**: Circuit labels are descriptive, not authoritative. The connectivity graph determines electrical connectivity.

**Validation Rule Change**:
- **Old**: Flag any duplicate circuit ID as error
- **New**: Only flag duplicate IDs on electrically UNCONNECTED wires as error

### Design Components

✅ **Pipe Notation Parsing** - Parse `"L3B|L10A"` as multiple circuit IDs on one wire
- Indicates cross-sheet multipoint connection
- Each ID validated independently

✅ **HierarchicalValidator Class** - New validator with connectivity awareness
- Receives connectivity graph as parameter
- Groups wires by circuit ID
- Checks electrical connectivity using BFS graph traversal
- Errors only on true duplicates (unconnected wires)

✅ **BFS Connectivity Algorithm** - Determines if wire segments are connected
- Traverses connectivity graph from wire endpoint nodes
- Returns set of all reachable nodes
- Checks if all wire segments in same connected component

✅ **Enhanced Error Messages** - Include sheet context
- Shows which sheets contain the duplicate
- Distinguishes between connected (valid) and unconnected (error) duplicates

✅ **Backward Compatibility** - All flat schematic validation unchanged
- Single-sheet schematics work as before
- No impact on test_01 through test_05C

### Implementation Phases

Detailed 5-phase implementation plan created:
1. **Phase 7.6.1**: Pipe notation label parsing
2. **Phase 7.6.2**: Connectivity-aware duplicate detection
3. **Phase 7.6.3**: Enhanced ValidationError with sheet context
4. **Phase 7.6.4**: CLI integration
5. **Phase 7.6.5**: Integration testing

### Test Strategy

**Success Criteria**:
- test_06 passes validation in both strict and permissive modes
- L2B and A9A duplicates recognized as valid (electrically connected)
- True duplicates (unconnected wires with same ID) still caught
- All existing tests (test_01-test_05C) continue to pass

**Deliverables Completed**:
- ✅ Complete design specification in `hierarchical_validation_design.md`
- ✅ Detailed programmer implementation tasks in `programmer_todo.md` Phase 7.6
- ✅ 15+ explicit, actionable tasks broken down by component
- ✅ TDD guidance for each task (RED-GREEN-REFACTOR-COMMIT)
- ✅ Integration test requirements specified
- ✅ Expected outcomes documented

**Next Action**: Programmer to implement Phase 7.6.1-7.6.5 following todos in programmer_todo.md

---

## NEXT PHASE OPTIONS

The tool is now production-ready for basic wire BOM generation. Future enhancements could include:

1. **CLI Enhancements**: Markdown output, engineering mode, verbose/quiet flags
2. **Wire Calculations**: Actual length/gauge/voltage drop (currently using defaults)
3. **Production Features**: REVnnn filenames, --schematic-requirements output
4. **Advanced Features**: See `docs/notes/opportunities_for_improvement.md`

**Current Priority**: LocLoad migration (Phase 6.5), then Hierarchical Schematics (Phase 7)

---

## NOTES

- All core functionality is complete and tested
- System is ready for real-world usage
- No outstanding architectural tasks
- Future work should be driven by actual usage requirements
