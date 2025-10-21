# Architect TODO: kicad2wireBOM

**Date**: 2025-10-21
**Status**: Phase 5 Architecture Complete - Unified BOM Generation Refactoring

---

## CURRENT STATUS

✅ **Phase 1-4 Complete**: Schematic-based parsing fully functional
- 122/122 tests passing
- Pin position calculation with rotation/mirroring working (Y-axis inversion fixed)
- Connectivity graph building working
- Junction transparency implemented
- Wire_endpoint tracing working
- Connector component tracing prioritization working

✅ **Phase 5: 3+Way Connections** - Implementation Complete BUT CLI Integration Missing
- Multipoint detection, validation, and BOM generation implemented ✅
- Integration tests passing (122/122) ✅
- **PROBLEM DISCOVERED**: CLI doesn't use multipoint logic - CSV output incorrect ❌
- **GAP**: Tests pass but production code doesn't match tested code path

🔧 **Phase 5B: Unified BOM Generation Refactoring** - Architecture Complete, Ready for Programmer
- Architecture defined in kicad2wireBOM_design.md Section 4.5
- Implementation tasks documented in programmer_todo.md Task 8
- Creates new `bom_generator.py` module to eliminate code duplication
- Will fix CLI to produce correct CSV output for 3+way connections

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

### 6. Common Pin Identification Algorithm (3+Way Connections) ✅

**Decision**: Use **SEGMENT-level analysis** to identify the common pin

**Key Terminology**:
- **Fragment**: A single KiCad wire element (what the parser sees as a "wire")
- **Connection**: A point where exactly 2 fragments meet
- **Junction**: A point where 3+ fragments meet (KiCad junction element)
- **Segment**: The chain of fragments between a pin and a junction (or between two pins)

**Algorithm Definition**: A pin is "reached by a labeled segment" if the SEGMENT (chain of fragments) from that pin to the junction contains at least one labeled fragment.

**Precise Algorithm**:

For each pin in the N-pin group:
1. **Trace the segment** from the pin toward the junction/backbone:
   - Start at pin position
   - Follow connected fragments through "connections" (2-fragment points)
   - Stop when reaching a "junction" (3+ fragment point) or another group pin
2. **Check for labels**: If ANY fragment in this segment has a circuit ID label → pin IS reached by labeled segment
3. **Identify common pin**: The ONE pin whose segment has NO labels is the common pin

**Example (test_03A P4A/P4B)**:

6 fragments → 3 connections + 1 junction → 3 segments:
- **Segment 1**: SW1-pin2 → Junction (fragments: 10, 9) - has label P4B ✓
- **Segment 2**: SW2-pin2 → Junction (fragment: 11) - has label P4A ✓
- **Segment 3**: J1-pin2 → Junction (fragments: 6, 2, 13) - NO labels ✓

**Common pin: J1-pin2** (terminal block)

**Rationale**:
- Works at the correct conceptual level (segments, not fragments)
- Connections are transparent (we trace through them)
- Junctions are stopping points (segment boundaries)
- Labels on any fragment in the segment mark that pin's branch

**Implementation Notes**:
1. Build fragment adjacency at each position
2. Count fragments per position to identify connections (2) vs junctions (3+)
3. From each pin, trace through fragments:
   - Follow through connections (2-fragment points)
   - Stop at junctions (3+ fragment points) or other group pins
   - Track if any fragment in the path has a circuit_id label
4. Return the pin whose segment has no labels

**Status**: Architectural decision complete (2025-10-21) - Ready for Programmer implementation

**Reference**: Design doc Section 4.4, programmer_todo.md Task 3

---

### 7. Unified BOM Generation ✅

**Decision**: Create dedicated `bom_generator.py` module with unified `generate_bom_entries()` function

**Problem Discovered**: The multipoint connection logic (Tasks 1-7 in programmer_todo.md) was implemented and tested, BUT the CLI (`__main__.py`) doesn't use it. This creates a dangerous gap:
- Integration tests pass (122/122) ✓
- Multipoint logic exists and works ✓
- CLI CSV output is WRONG for 3+way connections ✗

**Root Cause**: Code duplication. Integration tests implement the correct pattern (detect multipoint → generate multipoint entries → skip those labels in regular processing → combine results), but the CLI only does regular 2-point processing.

**Rationale**:
- **Single Source of Truth**: Both CLI and tests must use identical code path
- **DRY Principle**: Eliminate duplication between `__main__.py` and integration tests
- **Correctness**: Tests passing should guarantee CLI works correctly
- **Maintainability**: Future changes only need to be made in one place

**Design Details**:

**New Module**: `kicad2wireBOM/bom_generator.py`

**Function**: `generate_bom_entries(wires: list[WireSegment], graph: ConnectivityGraph) -> list[dict]`

**Algorithm**:
1. Store wires in graph for multipoint processing
2. Detect multipoint groups (N ≥ 3 pins)
3. Generate multipoint BOM entries
4. Track multipoint circuit IDs
5. Generate regular 2-point entries (excluding multipoint labels)
6. Return combined list

**Benefits**:
- CLI will produce correct CSV output for 3+way connections
- Integration tests verify same code path as production
- Future multipoint enhancements automatically work in CLI
- Eliminates tech debt from code duplication

**Status**: Architecture complete (2025-10-21) - Ready for Programmer implementation

**Reference**: Design doc Section 4.5, programmer_todo.md Task 8

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

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.6

**Key Sections**:
- Section 3.5: Junction semantics and parsing
- Section 4.1: Pin position calculation with rotation/mirroring
- Section 4.2: Connectivity graph data structures
- Section 4.3: Wire-to-component matching (junction transparency)
- Section 4.4: 3+way connections (multipoint)
- Section 4.5: Unified BOM generation **[NEW - 2025-10-21]**
- Section 7.3: CSV output format
- Section 10.1: Module structure (includes bom_generator.py)

---

## TASKS

### Completed ✅
- [x] Clarify junction terminology in design doc (junction elements vs connector components)
- [x] Investigate test_03A output mismatch - identified Y-axis inversion bug (2025-10-20)
- [x] Y-axis inversion bug fixed by Programmer (2025-10-20)
- [x] Connector component tracing prioritization bug fixed (2025-10-20)
- [x] Design 3+way connection architecture (2025-10-21)
- [x] Move ARCHITECTURE_CHANGE.md to docs/archive/
- [x] Clarify "common pin identification" algorithm for 3+way connections (2025-10-21)
- [x] **Investigate CSV output discrepancies for test_03A and test_04 (2025-10-21)**
- [x] **Design unified BOM generation refactoring (2025-10-21)**
  - Identified gap between integration tests and CLI
  - Designed bom_generator.py module
  - Documented in design doc Section 4.5
  - Created implementation plan in programmer_todo.md Task 8

### Future (When Needed)
- [ ] Design hierarchical schematic support (if Tom's schematics use multiple sheets)
- [ ] Design validation and error handling strategy beyond 3+way connections
- [ ] Consider multi-format output options (Markdown, engineering mode)
