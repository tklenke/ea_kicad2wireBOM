# Architect TODO: kicad2wireBOM

**Date**: 2025-10-21
**Status**: Phase 4 Complete - New Feature: 3+Way Connections

---

## CURRENT STATUS

✅ **Phase 1-4 Complete**: Schematic-based parsing fully functional
- 111/111 tests passing
- Pin position calculation with rotation/mirroring working (Y-axis inversion fixed)
- Connectivity graph building working
- Junction transparency implemented
- Wire_endpoint tracing working
- Connector component tracing prioritization working

🔧 **Phase 5: 3+Way Connections** - Architecture Complete, Ready for Implementation
- Architecture defined in kicad2wireBOM_design.md Section 4.4
- Implementation tasks documented in programmer_todo.md
- Test fixtures available: test_03A (3-way), test_04 (4-way)

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

**Status**: ✅ Complete - Implemented and tested (2025-10-20)

**Reference**: Design doc Section 4.3

---

### 5. 3+Way Connections ✅

**Decision**: Implement detection and validation of multi-point connections (N ≥ 3 component pins) using labeling convention

**Labeling Convention**: For N pins connected through junctions:
- Expect exactly (N-1) circuit ID labels
- Unlabeled segments form backbone (junction-to-junction, junction-to-common-pin)
- The pin NOT reached by any labeled segment is the common endpoint
- Each labeled wire generates one BOM entry: labeled-pin → common-pin

**Rationale**:
- Matches physical reality of aircraft wiring (multiple grounds to battery, multiple feeds from distribution point)
- Labeling convention is intuitive and unambiguous
- Unlabeled pin clearly identifies the common endpoint (terminal block, ground bus, etc.)
- Scales naturally to any N ≥ 3

**Examples**:
- 3-way (test_03A P4A/P4B): SW1-pin2, SW2-pin2 → J1-pin2 (terminal block)
- 4-way (test_04 grounds): L1/L2/L3 → BT1-pin2 (battery negative)

**Status**: Architecture complete (2025-10-21) - Ready for Programmer implementation

**Reference**: Design doc Section 4.4, programmer_todo.md "NEXT IMPLEMENTATION"

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

### Completed ✅
- [x] Clarify junction terminology in design doc (junction elements vs connector components)
- [x] Investigate test_03A output mismatch - identified Y-axis inversion bug (2025-10-20)
- [x] Y-axis inversion bug fixed by Programmer (2025-10-20)
- [x] Connector component tracing prioritization bug fixed (2025-10-20)
- [x] Design 3+way connection architecture (2025-10-21)
- [x] Move ARCHITECTURE_CHANGE.md to docs/archive/

### Immediate - Ready for Programmer
- [ ] Implement 3+way connection detection and validation (see programmer_todo.md)
- [ ] Create test_04 expected output file for validation

### Future (When Needed)
- [ ] Design hierarchical schematic support (if Tom's schematics use multiple sheets)
- [ ] Design validation and error handling strategy beyond 3+way connections
- [ ] Consider multi-format output options (Markdown, engineering mode)
