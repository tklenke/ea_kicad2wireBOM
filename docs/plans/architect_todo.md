# Architect TODO: kicad2wireBOM

**Date**: 2025-10-22
**Status**: Phase 1-6 Complete - Major Milestone Achieved ✅

---

## CURRENT STATUS

✅ **All Planned Features Complete**: 150/150 tests passing
- Schematic parsing, connectivity graph, junction handling all working
- 3+way multipoint connection logic implemented and tested
- Unified BOM generation created and integrated into CLI
- Validation & error handling with notes aggregation complete
- CSV output correctly includes multipoint entries and notes field
- CLI supports both strict and permissive modes

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.6
**Validation Design**: `docs/plans/validation_design.md`

---

## KEY ARCHITECTURAL DECISIONS (All Implemented)

All major architectural decisions have been implemented and validated:

1. **3+Way Connections** (Section 4.4): Multi-point connections using (N-1) labeling convention
2. **Unified BOM Generation** (Section 4.5): Single `bom_generator.py` module handles all connection types
3. **Pin Position Calculation** (Section 4.1): Precise calculation with rotation matrices and mirroring
4. **Junction Handling** (Sections 3.5, 4.2, 4.3): Graph-based approach with explicit junction elements
5. **Wire Endpoint Tracing** (Section 4.3): Recursive tracing through wire_endpoint nodes
6. **Notes Aggregation** (Section 4.5): BFS traversal collects notes from all wire fragments in a circuit
7. **Validation Framework**: Missing labels, duplicate labels, non-circuit label handling

---

## OPEN QUESTIONS

**Hierarchical Schematics**: Are your aircraft schematics flat or hierarchical?
- Flat: Current design handles this ✅
- Hierarchical: Would need sheet interconnection design (future work)

---

## PHASE 6.5: LocLoad Custom Field Migration

**Status**: [~] In Progress - Handed off to Programmer

**Objective**: Replace Footprint field overloading with dedicated `LocLoad` custom field.

**Decision**: Use custom field named `LocLoad` with format `(FS,WL,BL){S|L|R|G}<value>` (removed leading `|`)
- Types: S=Source, L=Load, R=Rating, G=Ground
- Value required for S, L, R types; optional for G type

**Tasks**:
- [x] Evaluate field name options (chose `LocLoad`)
- [x] Define format specification: `(FS,WL,BL){S|L|R|G}<value>`
- [x] Removed `|` prefix, added `G` type for ground points
- [x] Removed backwards compatibility requirement (clean break)
- [x] Create implementation tasks for Programmer
- [x] Tom updating all test fixtures
- [x] Programmer implementing parser changes

**NOTE FROM PROGRAMMER (2025-10-23)**: Task 1 in programmer_todo.md says "Add `locload` field to Component class" but this is not needed. The Component class stores parsed values (fs, wl, bl, load, rating, source), not the raw field string. This pattern was the same with Footprint - we never stored the raw string. Migration is complete and all 150 tests pass without adding a locload field. Architect should remove Task 1 from programmer_todo.md as it's unnecessary.

---

## PHASE 7: Hierarchical Schematic Support (UNRESOLVED - ON HOLD)

**Status**: Design phase - Awaiting LocLoad migration completion

**Scope**: Single-level hierarchy (main sheet → N sub-sheets)

**Current Understanding**:

### Test Fixture Analysis (test_06)
- **Main sheet** (`test_06_fixture.kicad_sch`): Battery, fuse holder, switches
- **Sub-sheet** (`test_06_lighting.kicad_sch`): Lamps
- **Hierarchical connections**: `TAIL_LT`, `TIP_LT`, `GND` pins connect sheets
- **Cross-sheet wires**: Labels `L2B` and `L3B` appear on BOTH sheets

### Key Architectural Challenges

1. **Sheet Interconnection**:
   - Hierarchical sheet symbols define boundaries
   - Sheet pins (on parent) connect to hierarchical labels (on child)
   - These create implicit electrical connections not visible as wire segments

2. **Cross-Sheet Wire Tracing**:
   - Wire labeled "L2B" exists on main sheet AND sub-sheet
   - Must trace through hierarchical pin/label to connect fragments
   - Example path: Main wire → Sheet pin "TIP_LT" → Hierarchical label "TIP_LT" → Sub-sheet wire

3. **Component Reference Resolution**:
   - Sub-sheets have different UUID paths in instances
   - Reference designators unique across all sheets (L1, L2 on sub-sheet)
   - LocLoad coordinates are in aircraft coordinate system (global)

4. **Global Net Names**:
   - Power symbols (GND, +12V) create global nets
   - All GND symbols connect electrically regardless of sheet
   - LocLoad field now used for ground point locations

### Design Approach (Option B - Unified BOM)
- Trace wires across sheet boundaries
- Merge fragments from multiple sheets into single circuit
- Generate electrically accurate BOM

### Open Questions

1. **Sheet Parsing Strategy**:
   - Parse all sheets into single flat data structure?
   - Maintain sheet hierarchy in data model?
   - How to handle sheet file references?

2. **Pin Mapping Algorithm**:
   - How to map sheet pins to hierarchical labels?
   - String matching by name?
   - What if names don't match?

3. **Connectivity Graph**:
   - Build single unified graph across all sheets?
   - Or separate graphs with cross-sheet edges?
   - How to represent hierarchical connections?

4. **Circuit Identification**:
   - Does circuit label need to appear on every sheet?
   - Or can it propagate through hierarchical connections?
   - Example: "L2B" on main sheet, unlabeled wire on sub-sheet connected via "TIP_LT"

5. **BOM Output Format**:
   - Show which sheet(s) each wire segment is on?
   - Or just unified circuit with total length?
   - Useful for assembly instructions?

### Next Steps (After LocLoad Migration)
1. Analyze test_06 fixtures in detail to understand expected behavior
2. Design sheet parsing and interconnection data structures
3. Design cross-sheet wire tracing algorithm
4. Create detailed implementation plan for Programmer
5. Define additional test cases for hierarchical scenarios

**References**:
- Test fixtures: `tests/fixtures/test_06_fixture.kicad_sch`, `test_06_lighting.kicad_sch`
- Tom's use case: Main sheet = power distribution, Sub-sheets = Avionics, Lighting, Engine systems

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
