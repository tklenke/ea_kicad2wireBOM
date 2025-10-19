# CRITICAL: Architecture Change - Netlist to Schematic Parsing

**Date**: 2025-10-18
**Architect**: Claude
**Status**: Design Complete, Awaiting Implementation

---

## Summary

The kicad2wireBOM project has undergone a **fundamental architectural redesign** based on the discovery that KiCAD netlists lose wire-level granularity needed for wire harness manufacturing.

**Previous Approach** (ABANDONED):
- Parse KiCAD netlist files (`.net` XML format)
- Extract nets (electrical connectivity)
- Infer wire segments from nets
- **FATAL FLAW**: Netlists collapse multiple physical wires into single nets

**New Approach** (CURRENT):
- Parse KiCAD schematic files (`.kicad_sch` s-expression format)
- Extract individual wire segments directly from schematic
- Associate labels with wires using spatial proximity
- Preserve wire-level granularity for BOM generation

---

## The Problem That Forced The Change

### Wire Harness Manufacturing Requirements

In a wire harness, **physical wires** are distinct from **electrical nets**:

```
Example: Two switches feeding one connector

Schematic shows:
  Wire labeled "P1A": SW1 pin 1 → TB1 pin 1
  Wire labeled "P2A": SW2 pin 1 → TB1 pin 1

Electrically: One net (all connected at TB1)
Physically: TWO wires that need:
  - Separate labels (P1A, P2A)
  - Individual BOM entries
  - Distinct lengths, gauges, colors
  - Different wire marking
```

### What Netlists Collapse

**KiCAD Netlist Output**:
```xml
<net code="1" name="/Power1">
  <node ref="SW1" pin="1"/>
  <node ref="SW2" pin="1"/>
  <node ref="TB1" pin="1"/>
</net>
```

**Wire-level information LOST**:
- No way to distinguish wire SW1→TB1 from wire SW2→TB1
- No labels for individual wire segments
- Cannot generate separate BOM entries

### What Schematics Preserve

**KiCAD Schematic Output**:
```lisp
(wire (pts (xy 125.73 73.66) (xy 144.78 73.66)) (uuid "..."))
(label "P1A" (at 138.43 73.66 0))

(wire (pts (xy 125.73 102.87) (xy 144.78 102.87)) (uuid "..."))
(label "P2A" (at 134.62 102.87 0))

(junction (at 144.78 86.36))
```

**Wire-level information PRESERVED**:
- Individual wire segments with UUIDs
- Labels positioned on specific wires
- Junction showing where wires meet
- Can generate accurate per-wire BOM

---

## What Changed

### Input Format
- **Old**: `.net` XML files (netlists)
- **New**: `.kicad_sch` s-expression files (schematics)

### Parsing Library
- **Old**: `kinparse` library
- **New**: `sexpdata` library (or custom s-expression parser)

### Primary Data Entity
- **Old**: Net (electrical connectivity graph)
- **New**: WireSegment (physical wire with endpoints)

### Label Source
- **Old**: Net name field in netlist
- **New**: Label elements positioned on wires in schematic

### Label Association
- **Old**: Direct (net name is the label)
- **New**: Proximity matching (find nearest wire to label)

### Multi-Wire Handling
- **Old**: Cannot distinguish (all wires collapsed into net)
- **New**: Each wire is separate entity with own label

---

## What Stayed The Same

**Good news**: Most of the design concepts transfer directly:

✓ EAWMS wire marking standard (SYSTEM-CIRCUIT-SEGMENT format)
✓ Footprint field encoding (`|(fs,wl,bl)<type><amps>`)
✓ Aircraft coordinate system (FS/WL/BL)
✓ Wire length calculation (Manhattan distance + slack)
✓ Wire gauge calculation (voltage drop + ampacity constraints)
✓ System code to color mapping
✓ Reference data (resistance, ampacity tables)
✓ Output formats (CSV and Markdown)
✓ CLI interface design (flags, arguments, auto-naming)
✓ Validation approach (strict vs permissive modes)
✓ Test-driven development methodology

---

## Documents Updated

### New Documents Created
- `docs/plans/kicad2wireBOM_design.md` v2.0 - Complete redesign
- `docs/plans/required_from_tom.md` - Updated for new approach
- `docs/plans/programmer_notes.md` - Implementation guidance
- `docs/plans/ARCHITECTURE_CHANGE.md` - This document

### Old Documents Archived
Moved to `docs/archive/`:
- `kicad2wireBOM_design.md` (v1.0, v1.1)
- `incremental_implementation_plan.md`
- `programmer_todo.md`
- `system_code_analysis.md`
- `keyword_extraction_from_657CZ.md`
- `architect_todo.md`

**DO NOT reference archived documents** - they describe the wrong architecture.

---

## Test Fixtures

**Good news**: Tom already created three test fixtures as KiCAD schematics!

- `tests/fixtures/test_01_fixture.kicad_sch` - Simple battery → lamp
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch
- `tests/fixtures/test_03_fixture.kicad_sch` - **Perfect junction example**

**test_03 fixture** shows exactly the problem we're solving:
- Two switches (SW1, SW2) feeding one connector (J1)
- Junction at (144.78, 86.36) where wires meet
- Labels "P1A" and "P2A" on separate wire segments
- Electrically one net, but physically two wires

This is **real data from Tom's KiCAD schematics** - excellent foundation for TDD.

---

## Implementation Path Forward

### Next Steps

1. **Tom reviews new design**
   - Read `docs/plans/kicad2wireBOM_design.md` v2.0
   - Check `docs/plans/required_from_tom.md` for open questions
   - Verify approach addresses wire granularity problem

2. **Tom answers open questions**
   - Label association distance threshold (10mm suggested)
   - S-expression parser library choice (sexpdata recommended)
   - Pin position calculation precision (simple suggested initially)
   - Hierarchical schematic support (defer to later phase suggested)

3. **Architect creates implementation plan** (if needed)
   - Break design into detailed work packages
   - Sequence tasks for TDD approach
   - OR defer to Programmer to create plan during implementation

4. **Switch to Programmer role**
   - Begin with s-expression parsing (Phase 1)
   - Use test_01_fixture.kicad_sch as first test case
   - Build up functionality with TDD

### Estimated Complexity

**Easier than netlist approach**:
- Simpler data model (wires vs nets)
- No complex inference needed (labels are explicit)
- Test fixtures already exist

**New challenges**:
- S-expression parsing (but simpler than XML)
- Label-to-wire proximity matching (geometric algorithm)
- Coordinate system handling (schematic vs aircraft coords)

**Overall**: Comparable complexity, but **correct architecture** for the problem.

---

## Risk Assessment

### Risks Mitigated
✓ Wire granularity problem solved (primary motivation)
✓ Real test fixtures available (de-risked parsing)
✓ Clear algorithm for label association (defined in design)
✓ No dependency on KiCAD netlist export quirks

### Remaining Risks
⚠ S-expression parsing complexity (mitigated by sexpdata library)
⚠ Label proximity matching edge cases (mitigated by test fixtures)
⚠ Pin position calculation if needed (start simple, enhance later)
⚠ KiCAD format changes between versions (test with v8 and v9)

### Risk Mitigation Strategy
- Start with simplest test fixture (test_01)
- Test-driven development ensures algorithm correctness
- Permissive mode allows graceful degradation
- Clear validation messages help users fix schematics

---

## Success Metrics

**Design is successful if**:
1. Tool correctly extracts individual wire segments from schematic
2. Labels associate with correct wires (validated with test fixtures)
3. Junction handling preserves wire granularity (test_03 passes)
4. BOM output shows separate entries for wires on same net
5. All three test fixtures produce correct BOM output

**Implementation is successful if**:
- All tests pass
- Code is maintainable (TDD, clean architecture)
- Tom can generate accurate wire BOMs for aircraft electrical systems
- Tool handles edge cases gracefully (validation, warnings)

---

## Lessons Learned

**Architect's Notes**:

1. **Validate assumptions early**: The netlist-based approach seemed correct until analyzing real KiCAD output revealed wire granularity loss.

2. **Real data is critical**: Having Tom's actual KiCAD schematics as test fixtures immediately validated the schematic-based approach.

3. **Pivot decisively**: When architecture is fundamentally wrong, archive and restart rather than patch. Clean slate better than incremental fixes.

4. **Preserve what works**: Even though input format changed dramatically, most design concepts (calculations, validation, output) transferred directly.

5. **Test fixtures drive design**: test_03_fixture.kicad_sch with its junction perfectly demonstrates the problem and validates the solution.

---

## Communication Plan

**For Programmer Role**:
- Read this document first (high-level context)
- Then read `programmer_notes.md` (implementation guidance)
- Then read full design spec (detailed algorithms)
- Reference `required_from_tom.md` for open questions

**For Tom**:
- This document explains the change and rationale
- `required_from_tom.md` lists decisions needed
- Design document is comprehensive reference

**For Future Sessions**:
- **DO NOT** reference archived documents
- **DO** read ARCHITECTURE_CHANGE.md for context
- **DO** use test fixtures to validate understanding

---

## Approval and Sign-off

**Architect**: Claude (Architect role)
**Date**: 2025-10-18
**Status**: Design complete, ready for Tom's review

**Awaiting**:
- [ ] Tom's review and approval
- [ ] Tom's answers to open questions
- [ ] Begin implementation

---

## Appendix: Quick Reference

### Key Documents (Read These)
- `docs/plans/kicad2wireBOM_design.md` v2.0 - Design spec
- `docs/plans/required_from_tom.md` - Open questions
- `docs/plans/programmer_notes.md` - Implementation guide
- `docs/plans/ARCHITECTURE_CHANGE.md` - This document

### Test Fixtures (Work With These)
- `tests/fixtures/test_01_fixture.kicad_sch`
- `tests/fixtures/test_02_fixture.kicad_sch`
- `tests/fixtures/test_03_fixture.kicad_sch`

### Archived Documents (Don't Read These)
- `docs/archive/*` - Old netlist-based designs

### Reference Materials (Same as Before)
- `docs/ea_wire_marking_standard.md` - EAWMS spec
- `docs/references/aeroelectric_connection/` - Wire tables
- `docs/references/milspecs/` - MIL standards
