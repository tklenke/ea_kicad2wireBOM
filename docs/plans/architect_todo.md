# Architect TODO: kicad2wireBOM

**Date**: 2025-10-20
**Status**: Phase 4 Complete - Implementation has minor bug requiring fix

---

## CURRENT STATUS

✅ **Phase 1-4 Complete**: Schematic-based parsing fully functional
- 108/108 tests passing
- Pin position calculation with rotation/mirroring working
- Connectivity graph building working
- Junction transparency implemented

⚠️ **Known Issue**: BOM output incomplete due to wire_endpoint tracing bug
- See programmer_todo.md for details and fix
- This is an implementation bug, not an architecture problem
- Architecture is sound, just needs one missing case added to trace_to_component()

---

## ARCHITECTURAL DECISIONS

### 1. Pin Position Calculation Strategy ✅

**Decision**: Use **precise** calculation with rotation matrices and mirroring

**Rationale**: Real schematics have multi-pin components with rotation/mirroring. Precise calculation ensures correct pin matching using straightforward 2D geometry.

**Reference**: Design doc Section 4.1

---

### 2. Junction Handling Algorithm ✅

**Decision**: Use **graph-based approach** with explicit junction elements only

**Rationale**: KiCad uses explicit `(junction ...)` elements to indicate electrical connections. Wires can cross in 2D without connecting.

**Critical Rule**:
- **Junction present** at (x,y) → wires ARE connected
- **Junction absent** at (x,y) → wires crossing are NOT connected

**Reference**: Design doc Sections 3.5, 4.2, 4.3

---

### 3. BOM Output Format ✅

**Decision**: Junctions are **transparent** in BOM output

**Rationale**: In experimental aircraft, schematic junctions represent electrical connection points but must become physical components (terminal blocks, connectors, splice blocks) in the build. Wire-to-wire splicing is not acceptable for reliability and maintainability.

**Output Format**:
```csv
Wire Label,From Component,From Pin,To Component,To Pin,...
P1A,J1,1,SW1,3,...
P2A,J1,1,SW2,3,...
P3A,SW1,3,SW2,3,...
```

Each wire shows component-to-component connections by tracing through junctions.

**Reference**: Design doc Sections 4.3, 7.3

---

### 4. Wire Endpoint Tracing ✅

**Decision**: Extend `trace_to_component()` to handle `wire_endpoint` nodes using same recursive pattern as junctions

**Rationale**: Labeled wire segments often connect to unlabeled wire segments at wire_endpoint nodes. Current architecture is sound - we just need to add the missing case to the existing recursive graph traversal.

**Status**: Architectural decision complete - design added to Section 4.3 of kicad2wireBOM_design.md. Implementation is Programmer's responsibility (see programmer_todo.md "CURRENT BLOCKER").

**Reference**: See programmer_todo.md "CURRENT BLOCKER" section for implementation details

---

## OPEN QUESTIONS

### Hierarchical Schematics

**Question**: Are your aircraft schematics flat or hierarchical (multiple sheets)?

**Impact**:
- Flat: Current design handles this (no changes needed)
- Hierarchical: Need to design sheet interconnection handling (future Phase 5)

**Recommendation**: Current implementation assumes flat schematics. Add hierarchical support later if needed.

---

## DESIGN DOCUMENTS

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.2

**Key Sections**:
- Section 3.5: Junction semantics and parsing
- Section 4.1: Pin position calculation with rotation/mirroring
- Section 4.2: Connectivity graph data structures
- Section 4.3: Wire-to-component matching (junction transparency)
- Section 7.3: CSV output format

---

## TASKS

### Immediate
- [ ] Programmer fixes wire_endpoint tracing bug (see programmer_todo.md)

### Future (When Needed)
- [ ] Design hierarchical schematic support (if Tom's schematics use multiple sheets)
- [ ] Design validation and error handling strategy
- [ ] Consider multi-format output options (Markdown, engineering mode)

### Housekeeping
- [ ] Move ARCHITECTURE_CHANGE.md to docs/archive/ (awaiting Tom's approval)
