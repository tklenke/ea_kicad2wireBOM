# Architect TODO: kicad2wireBOM

**Date**: 2025-10-21
**Status**: Phase 5B - Unified BOM Generation Refactoring Ready for Programmer

---

## CURRENT STATUS

✅ **Phases 1-5 Complete**: 122/122 tests passing
- Schematic parsing, connectivity graph, junction handling all working
- 3+way multipoint connection logic implemented and tested

🔧 **Current Issue**: CLI doesn't use multipoint logic - CSV output incorrect
- Integration tests pass but CLI produces wrong output
- Need unified BOM generation to fix gap between tests and production

**Next Step**: Programmer implements Task 8 (unified BOM generation refactoring)

---

## ACTIVE ARCHITECTURAL DECISIONS

### 3+Way Connections ✅

**Decision**: Implement multi-point connections (N ≥ 3 pins) using (N-1) labeling convention

**Labeling Convention**:
- N pins → expect (N-1) circuit ID labels
- Unlabeled segments form backbone
- Pin NOT reached by labeled segment = common endpoint
- Each labeled wire: labeled-pin → common-pin

**Common Pin Algorithm**: Use SEGMENT-level analysis
- Trace segments from each pin through connections (transparent) to junctions (stop points)
- Pin whose segment has NO labels = common pin

**Reference**: Design doc Section 4.4

---

### Unified BOM Generation ✅

**Decision**: Create `bom_generator.py` module with `generate_bom_entries()` function

**Problem**: Multipoint logic passes tests but CLI doesn't use it (code duplication gap)

**Solution**:
- Single function handles both multipoint and regular 2-point connections
- CLI and tests use identical code path
- Eliminates duplication, ensures correctness

**Reference**: Design doc Section 4.5, programmer_todo.md Task 8

---

## OPEN QUESTIONS

**Hierarchical Schematics**: Are your aircraft schematics flat or hierarchical?
- Flat: Current design handles this
- Hierarchical: Need sheet interconnection design (future work)

---

## DESIGN DOCUMENTS

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v2.6

**Key Sections**:
- Section 4.4: 3+way connections
- Section 4.5: Unified BOM generation
- Section 10.1: Module structure

---

## ARCHIVED DECISIONS

<details>
<summary>Expand to see earlier architectural decisions (Phases 1-4)</summary>

### 1. Pin Position Calculation Strategy ✅
**Decision**: Precise calculation with rotation matrices and mirroring
**Reference**: Design doc Section 4.1

### 2. Junction Handling Algorithm ✅
**Decision**: Graph-based approach with explicit junction elements only
**Reference**: Design doc Sections 3.5, 4.2, 4.3

### 3. BOM Output Format ✅
**Decision**: Junctions are transparent in BOM output
**Reference**: Design doc Sections 4.3, 7.3

### 4. Wire Endpoint Tracing ✅
**Decision**: Extend trace_to_component() to handle wire_endpoint nodes
**Reference**: Design doc Section 4.3

</details>
