# Architect TODO: kicad2wireBOM

**Date**: 2025-10-25
**Status**: All Planned Architecture Complete ✅

---

## CURRENT STATUS

✅ **All Core Architecture Implemented**: 176/176 tests passing

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v3.0
**Validation Design**: `docs/plans/validation_design.md`
**Hierarchical Validation**: `docs/plans/hierarchical_validation_design.md`

---

## COMPLETED ARCHITECTURAL WORK

### Phase 1-6.5: Core Wire BOM Generation ✅
- Schematic parsing architecture (S-expressions)
- Pin position calculation with transforms
- Connectivity graph design (unified, spanning all sheets)
- 2-point and N-way multipoint connection algorithms
- Unified BOM generation with notes aggregation
- Validation framework (missing labels, duplicates, non-circuit labels)
- LocLoad custom field migration
- CLI design with strict/permissive modes

### Phase 7: Hierarchical Schematic Support ✅
**Design Location**: Section 8 of `kicad2wireBOM_design.md` v3.0

**Key Architectural Decisions**:
1. **Unified Connectivity Graph** - Single graph spanning all sheets (not per-sheet graphs)
2. **Recursive Parser** - Parse root sheet, then recursively parse sub-sheets
3. **Circuit Label Resolution** - Follows electrical connectivity, not label names
4. **Component References** - Resolved from hierarchical instance paths
5. **New node types**: `sheet_pin`, `hierarchical_label` for cross-sheet connections
6. **Global Power Nets** - GND, +12V, etc. automatically connected across all sheets

### Phase 7.6: Hierarchical Validation ✅
**Design Location**: `docs/plans/hierarchical_validation_design.md`

**Key Architectural Decision**:
- **Connectivity-Aware Duplicate Detection**: Only flag duplicate circuit IDs on electrically UNCONNECTED wires as errors
- Circuit labels are descriptive, not authoritative - connectivity graph determines electrical connectivity
- Pipe notation parsing (L3B|L10A) for cross-sheet multipoint connections

### Phase 8: Enhanced Validation Error Messages 🚧 IN PROGRESS

**Status**: Design complete, awaiting Programmer implementation
**Design Location**: `docs/plans/programmer_todo.md` - Phase 8 Design section
**Date**: 2025-10-25

**Problem**: Validation errors show only wire UUIDs, making it hard for users to locate problematic wires in KiCad

**Architectural Decision**:
- **Leverage existing connectivity graph** to trace wire endpoints to component pins
- **Enhance error messages** with human-readable connection info: "Wire connects: BT1 (pin 1) → FH1 (pin Val_A)"
- **Consistent validator interface**: Both SchematicValidator and HierarchicalValidator receive connectivity_graph parameter
- **Graceful degradation**: If graph unavailable, fall back to existing error format

**Key Design Points**:
1. Uses existing `trace_to_component()` infrastructure (no new algorithms needed)
2. Additive change - doesn't break existing functionality
3. Handles edge cases (junctions, power symbols, unknown endpoints)
4. Low performance impact (only runs on validation errors)

**Implementation Tasks**: 5 tasks documented in `programmer_todo.md`

---

## ARCHITECTURAL QUESTIONS

### Resolved ✅
- **Hierarchical Schematics**: Designed and implemented 2-level hierarchical support (main + sub-sheets)
- **Cross-Sheet Wire Tracing**: Resolved via unified connectivity graph with sheet_pin and hierarchical_label nodes
- **Duplicate Circuit IDs Across Sheets**: Resolved via connectivity-aware validation

### Open Questions
**Tom's Schematic Structure**: Are your aircraft schematics:
- Flat (single sheet): ✅ Supported
- 2-level hierarchical (main + sub-sheets): ✅ Supported
- Multi-level nested (sub-sheets within sub-sheets): ⚠️ Not yet supported
- Sheet instances (same sub-sheet used multiple times): ⚠️ Not yet supported

---

## NEXT PHASE OPTIONS

The tool is production-ready. Future architectural work could include:

### 1. CLI Enhancements
- Markdown output format
- Engineering mode (detailed calculations shown)
- Verbose/quiet flags
- JSON output for programmatic integration

### 2. Wire Calculation Improvements
- Actual voltage drop calculation (beyond defaults)
- Temperature derating for hot zones
- Bundle derating for wire harnesses
- Custom wire resistance/ampacity tables

### 3. Production Features
- REVnnn automatic filename versioning
- `--schematic-requirements` output mode
- BOM revision comparison (REV001 vs REV002)
- Project configuration file support (`.kicad2wireBOM.yaml`)

### 4. Advanced Hierarchical Support
- Multi-level nested hierarchies (sub-sheets within sub-sheets)
- Sheet instances (same sub-sheet instantiated multiple times)
- Hierarchical path tracking in BOM output

### 5. Integration Features
- KiCad plugin architecture design
- GUI interface design (desktop or web)
- Component database auto-population
- 3D wire routing visualization

**All potential features documented in**: `docs/notes/opportunities_for_improvement.md`

---

## NOTES

- All core functionality is complete and tested
- System is ready for real-world usage on flat and 2-level hierarchical schematics
- No outstanding architectural decisions required for current feature set
- Future work should be driven by actual usage requirements

**No active architectural tasks at this time - awaiting Tom's direction for next phase.**
