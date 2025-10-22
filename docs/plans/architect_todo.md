# Architect TODO: kicad2wireBOM

**Date**: 2025-10-22
**Status**: Phase 1-5 Complete - Core Features Implemented ✅

---

## CURRENT STATUS

✅ **All Core Features Complete**: 125/125 tests passing
- Schematic parsing, connectivity graph, junction handling all working
- 3+way multipoint connection logic implemented and tested
- Unified BOM generation created and integrated into CLI
- CSV output correctly includes multipoint entries

**Next Step**: Phase 6 Validation & Error Handling - Design Complete, Ready for Implementation

---

## KEY ARCHITECTURAL DECISIONS (Implemented)

All major architectural decisions have been implemented and validated:

1. **3+Way Connections** (Section 4.4): Multi-point connections using (N-1) labeling convention
2. **Unified BOM Generation** (Section 4.5): Single `bom_generator.py` module handles all connection types
3. **Pin Position Calculation** (Section 4.1): Precise calculation with rotation matrices and mirroring
4. **Junction Handling** (Sections 3.5, 4.2, 4.3): Graph-based approach with explicit junction elements
5. **Wire Endpoint Tracing** (Section 4.3): Recursive tracing through wire_endpoint nodes

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.6

---

## OPEN QUESTIONS

**Hierarchical Schematics**: Are your aircraft schematics flat or hierarchical?
- Flat: Current design handles this ✅
- Hierarchical: Would need sheet interconnection design (future work)

---

## PHASE 6: VALIDATION & ERROR HANDLING

**Status**: Design Complete ✅ - Ready for Programmer

**Design Document**: `docs/plans/validation_design.md`

**Objective**: Detect and report schematic errors with clear, actionable messages

**Key Features**:
1. **Missing Labels Detection** (test_05A): Detect when no circuit IDs present
2. **Duplicate Label Detection** (test_05B): Find duplicate circuit IDs across wires
3. **Non-Circuit Label Handling** (test_05C): Move invalid labels to notes field
4. **Strict vs Permissive Modes**: Error/abort vs warn/continue
5. **Notes Field**: Add notes column for non-circuit labels (24AWG, SHIELDED, etc.)

**Test Fixtures Ready**:
- test_05_fixture.kicad_sch (correct baseline)
- test_05A_fixture.kicad_sch (all labels missing)
- test_05B_fixture.kicad_sch (duplicate G3A, missing G4A)
- test_05C_fixture.kicad_sch (non-circuit labels 24AWG, 10AWG)

**Architectural Decisions Made**:
- Add `notes: str` field to WireConnection data model
- Create new `validator.py` module with SchematicValidator class
- Add "Notes" column to CSV output (after Wire Type, before Warnings)
- Non-circuit labels concatenated with spaces in notes field
- Label classification: regex pattern `^[A-Z]-?\d+-?[A-Z]$` for circuit IDs

**Ready for Programmer**: All design decisions documented, test cases identified

---

## FUTURE PHASES (Not Yet Planned)

**Phase 7 Options**:
1. **CLI Enhancements**: Markdown output, engineering mode, verbose/quiet flags
2. **Wire Calculations**: Actual length/gauge/voltage drop (currently using defaults)
3. **Production Features**: REVnnn filenames, --schematic-requirements output
4. **Hierarchical Schematics**: Multi-sheet support (if needed by Tom)
5. **Advanced Features**: See `docs/notes/opportunities_for_improvement.md`
