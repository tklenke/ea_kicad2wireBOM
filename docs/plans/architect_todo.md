# Architect TODO: kicad2wireBOM

**Date**: 2025-10-19
**Status**: Phase 1-3 Complete, Phase 4 Design Complete

---

## CURRENT STATUS

✅ **Migration Complete**: Schematic-based parsing working
- 69/69 tests passing
- Basic end-to-end processing functional
- test_01_fixture generates correct BOM

✅ **Phase 4 Design Complete**: Pin calculation and junction handling designed
- Pin position calculation algorithm with rotation/mirroring
- Junction semantics clarified (explicit junctions only)
- Connectivity graph data structures defined
- Design documented in kicad2wireBOM_design.md v2.1

---

## DECISIONS MADE

### 1. Pin Position Calculation Strategy ✅

**Decision**: Use **precise** calculation with rotation matrices and mirroring

**Rationale**:
- Tom confirmed multi-pin components with rotation/mirroring in real schematics
- Precise calculation ensures correct pin matching
- Algorithm is straightforward 2D geometry (not overly complex)

**Implementation**:
- Parse symbol library pin definitions
- Apply mirror transform → rotation matrix → translation
- See design doc Section 4.1 for complete algorithm

**Status**: ✅ Complete - Ready for Programmer

---

### 2. Junction Handling Algorithm ✅

**Decision**: Use **graph-based approach** with explicit junction elements only

**Rationale**:
- KiCad uses explicit `(junction ...)` elements to indicate electrical connections
- Wires can cross in 2D without connecting (like PCB layers)
- test_03A_fixture proves this: P3A crosses P2A with NO connection

**Critical Rule**:
- **Junction present** at (x,y) → wires ARE connected
- **Junction absent** at (x,y) → wires crossing are NOT connected

**Implementation**:
- NetworkNode and ConnectivityGraph classes
- Build graph from junctions, pins, and wires
- See design doc Sections 3.5, 4.2, 4.3 for complete algorithms

**Status**: ✅ Complete - Ready for Programmer

---

### 3. Implementation Priority ✅

**Decision**: Implement in phases:

**Phase 4A**: Pin Position Calculation
- Parse symbol library pin definitions
- Implement rotation/mirror transforms
- Calculate absolute pin positions
- Unit tests for rotation edge cases

**Phase 4B**: Graph Data Structures
- Implement NetworkNode and ConnectivityGraph
- Graph building and node connection methods
- Unit tests for graph operations

**Phase 4C**: Graph Building Integration
- Integrate pin calculation
- Parse junctions
- Build complete connectivity graph
- Integration tests with all fixtures

**Phase 4D**: BOM Integration
- Wire-to-component matching
- Junction handling in output
- Update BOM generation
- All fixtures producing correct output

**Status**: ✅ Complete - Ready for Programmer

---

## INFORMATION NEEDED FROM TOM

### 1. Hierarchical Schematics ⚠️ Still Open

**Question**: Are your aircraft schematics flat or hierarchical (multiple sheets)?

**Impact**:
- Flat: Can proceed with current design (recommended for Phase 4)
- Hierarchical: Need to design sheet interconnection handling (defer to Phase 5)

**Recommendation**: Start with flat schematics, add hierarchical support later if needed

**Reference**: `required_from_tom.md` Line 329

---

### 2. Multi-Pin Components ✅ Answered

**Answer**: YES - Multi-pin components exist and they DO get rotated and mirrored

**Impact**: Precise pin position calculation is REQUIRED (designed in Section 4.1)

**Status**: ✅ Resolved - Algorithm designed

---

### 3. Junction Patterns ✅ Answered

**Answer**: Test fixture test_03A created showing:
- Junctions where wires connect (P1A + P2A at junction)
- Crossings with NO junction (P3A crosses P2A, not connected)

**Impact**: Explicit junction elements are the ONLY indicator of electrical connection

**Status**: ✅ Resolved - Algorithm designed in Sections 3.5, 4.2

---

## DELIVERABLES COMPLETED

✅ **kicad2wireBOM_design.md v2.1**
- Section 3.5: Junction semantics and parsing
- Section 4.1: Pin position calculation with rotation/mirroring
- Section 4.2: Connectivity graph data structures
- Section 4.3: Wire-to-component matching
- Section 4.4: Circuit identification (updated numbering)

✅ **architect_todo.md** (this file)
- Documented all decisions
- Marked questions as resolved
- Updated status to "Phase 4 Design Complete"

✅ **Test Fixture Analysis**
- test_03A_fixture analyzed
- Junction semantics validated
- Crossing behavior confirmed

---

## READY FOR PROGRAMMER

**Phase 4 implementation can begin**:
1. Design specification complete (kicad2wireBOM_design.md v2.1)
2. All architectural decisions made
3. Algorithm pseudocode provided
4. Test fixtures available for TDD
5. Implementation phases defined

**Recommended workflow**:
1. Programmer reads updated design document
2. Switch to Programmer role
3. Begin Phase 4A (pin position calculation)
4. Follow TDD approach with test fixtures

---

## ISSUES FROM PROGRAMMER (2025-10-20) - ✅ RESOLVED

### BOM Output Semantics Need Clarification ✅

**Problem**: Phase 4 implementation complete (105/105 tests passing), but BOM output from test_03A_fixture reveals semantic ambiguity.

**Resolution (2025-10-20)**:

**Decision**: Junctions are **transparent** in BOM output. Each wire shows component-to-component connections by tracing through junctions.

**Rationale**: In experimental aircraft, schematic junctions represent electrical connection points but must become physical components (terminal blocks, connectors, splice blocks) in the build. Wire-to-wire splicing is not acceptable for reliability and maintainability.

**BOM Output Format** - Split component and pin into separate columns:
- **Old**: `Wire Label,From,To,...` where From/To = "SW1-3" or "JUNCTION-uuid" or "UNKNOWN"
- **New**: `Wire Label,From Component,From Pin,To Component,To Pin,...` where components are traced through junctions

**Expected Output for test_03A**:
```csv
Wire Label,From Component,From Pin,To Component,To Pin,...
P1A,J1,1,SW1,3,...
P2A,J1,1,SW2,3,...
P3A,SW1,3,SW2,3,...
P4A,SW2,2,J1,1,...
P4B,SW1,3,J1,1,...
```

**Design Documents Updated**:
- `kicad2wireBOM_design.md` v2.1 - Section 4.3 (junction tracing algorithm) and Section 7.3 (output format)
- Design revision history added documenting this change

**Next Step**: Programmer implements junction tracing and updated CSV output format

---

## ARCHIVE PENDING

- [ ] Move ARCHITECTURE_CHANGE.md to docs/archive/
  - Migration complete
  - Document served its purpose
  - Awaiting Tom's approval to archive
