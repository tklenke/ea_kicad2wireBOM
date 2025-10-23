# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 1-6 Complete - Major Milestone Achieved ✅
**Last Updated**: 2025-10-22

---

## CURRENT STATUS

✅ **All Planned Features Complete**: 150/150 tests passing

**Implemented Features**:
- ✅ Schematic parsing (S-expressions, symbol libraries)
- ✅ Pin position calculation (rotation, mirroring, transforms)
- ✅ Connectivity graph building (wires, junctions, components)
- ✅ 2-point wire connections
- ✅ 3+way multipoint connections with (N-1) labeling
- ✅ Unified BOM generation
- ✅ Notes field infrastructure
- ✅ Notes aggregation across wire fragments
- ✅ Validator module (missing labels, duplicates, non-circuit labels)
- ✅ CLI with --permissive flag
- ✅ CSV output with all fields

**Status**: All implementation tasks complete. Ready for next phase or code review.

---

## PHASE 6.5: LocLoad Custom Field Migration ✅

**Status**: Complete (2025-10-23)
**Result**: All 150 tests passing

**Objective**: Replace Footprint field parsing with new custom `LocLoad` field for component location and electrical data.

**Background**:
- Previously overloaded KiCad's `Footprint` field with format: `|(FS,WL,BL){S|L|R}<value>`
- New approach: Use custom field `LocLoad` with cleaner format: `(FS,WL,BL){S|L|R|G}<value>`
- Tom updated all test fixtures to use the new field
- This provides cleaner separation from KiCad built-in fields

**Format Change**:
- **Old**: `|(0,0,0)S40` in Footprint field
- **New**: `(0,0,0)S40` in LocLoad custom field
- Removed leading `|` character from format
- Added `G` type for ground points: `(0,0,10)G` (no value required for ground)

**Implementation Tasks**:

### Task 1: Update Component Data Model
- [x] ~~Add `locload` field to Component class~~ (NOT NEEDED - Component stores parsed values, not raw field string)
- Note: Component class already stores parsed values (fs, wl, bl, load, rating, source). No changes needed.

### Task 2: Update Parser
- [x] Modified `parser.py` to extract `LocLoad` property from component symbols
- [x] Parse format: `(FS,WL,BL){S|L|R|G}<value>` (note: no leading `|`)
  - Types: S=Source, L=Load, R=Rating, G=Ground
  - Value required for S, L, R types
  - Value optional/not required for G type (ground points)
- [x] Removed all Footprint field parsing - LocLoad is the ONLY source going forward
- [x] Renamed `parse_footprint_encoding()` to `parse_locload_encoding()`

### Task 3: Write Tests
- [x] Test parsing LocLoad field (existing tests validate with test_01-05 fixtures)
- [x] Test format parsing without leading `|` (covered by existing tests)
- [x] Test G type (ground) - parser supports, awaiting test_06 fixture integration
- [x] Verified all 150 existing tests pass after Tom updated fixtures

### Task 4: Update All Parsers
- [x] Reviewed all code that reads encoding fields
- [x] Updated to ONLY read LocLoad field (no fallback)
- [x] Removed Footprint field parsing completely
- [x] Updated comments in `__main__.py` from "footprint encoding" to "LocLoad encoding"

### Task 5: Verify Integration
- [x] Run full test suite (150/150 passing)
- [ ] Test with test_06 fixtures once they have LocLoad fields (deferred - fixtures don't have components yet)
- [x] Verified CLI output is unchanged

**Commits**:
- `8ff0da8`: Migrate test fixtures from Footprint to LocLoad custom field
- `1189d5f`: Migrate parser from Footprint to LocLoad field

**Expected Outcome**: ✅ Parser reads component data ONLY from LocLoad field. Footprint field parsing completely removed.

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
- Section 4.5: Unified BOM generation with notes aggregation
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
- `kicad2wireBOM/bom_generator.py` - Unified BOM entry generation with notes aggregation
- `kicad2wireBOM/validator.py` - Validation framework
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way connection (P4A/P4B)
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection (G1A/G2A/G3A)
- `tests/fixtures/test_05_fixture.kicad_sch` - Validation baseline
- `tests/fixtures/test_05A_fixture.kicad_sch` - Missing labels
- `tests/fixtures/test_05B_fixture.kicad_sch` - Duplicate labels
- `tests/fixtures/test_05C_fixture.kicad_sch` - Non-circuit labels

---

## NEXT STEPS

**Status**: Awaiting Tom's direction on next priorities

No outstanding implementation tasks. Future work depends on:
- Real-world usage feedback
- New feature requests
- Performance optimization needs
- Additional validation requirements

See `docs/notes/opportunities_for_improvement.md` for potential future enhancements.
