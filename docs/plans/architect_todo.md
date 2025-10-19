# Architect TODO: kicad2wireBOM

**Date**: 2025-10-19
**Status**: Phase 1-3 Complete, Phase 4 Planning Needed

---

## CURRENT STATUS

✅ **Migration Complete**: Schematic-based parsing working
- 69/69 tests passing
- Basic end-to-end processing functional
- test_01_fixture generates correct BOM

---

## DECISIONS NEEDED

### 1. Pin Position Calculation Strategy

**Context**: Wire endpoints need to match component pins. Simple approach (component center) works for 2-component circuits but won't scale.

**Options**:
- **Simple**: Use component center position only (current implementation)
- **Precise**: Calculate exact pin positions with rotation/mirroring
- **Hybrid**: Component position + pin numbers from schematic

**Decision Needed**: Which approach for Phase 4?

**Impact**: Affects wire-to-component matching algorithm complexity

---

### 2. Junction Handling Algorithm

**Context**: Phase 4 requires network tracing through junctions (test_03_fixture).

**Need**:
- Algorithm design for building connectivity graph
- Approach for tracing multi-segment wire paths
- Strategy for identifying wire start/end components

**Decision Needed**: Architect should design junction handling approach

**Reference**: `docs/plans/kicad2wireBOM_design.md` Section 4

---

### 3. Implementation Priority

**Next work identified**:
- [ ] Junction extraction and parsing
- [ ] Wire network tracing
- [ ] Component pin matching
- [ ] Validation and error handling
- [ ] Additional output formats

**Decision Needed**: What order should these be implemented?

**Recommendation**: Junction handling first (critical for test_03_fixture)

---

## INFORMATION NEEDED FROM TOM

### 1. Hierarchical Schematics

**Question**: Are your aircraft schematics flat or hierarchical (multiple sheets)?

**Impact**:
- Flat: Can proceed with current design
- Hierarchical: Need to design sheet interconnection handling

**Reference**: `required_from_tom.md` Line 329

---

### 2. Multi-Pin Components

**Question**: Do you have components with multiple wires to different pins?

**Examples**:
- Multi-pin connectors with different circuits
- Components where pin distinction matters

**Impact**: Determines if we need precise pin position calculation

**Reference**: `required_from_tom.md` Line 290

---

## NEXT SESSION TASKS

**For Architect Role**:

1. Review Phase 4 requirements in design doc
2. Design junction handling algorithm
3. Decide on pin matching strategy
4. Create detailed Phase 4 implementation plan
5. Update programmer_todo.md with specific tasks

**For Tom**:

1. Answer hierarchical schematic question
2. Answer multi-pin component question
3. Review design doc if not done yet (`docs/plans/kicad2wireBOM_design.md`)

---

## NOTES

- Programmer has completed all work that can be done without architectural decisions
- Current implementation is solid foundation but needs connectivity tracing to be fully functional
- Test fixtures exist and are ready for integration testing once Phase 4 complete
