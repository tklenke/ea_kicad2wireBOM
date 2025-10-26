# Architect TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-10 Complete** - Production-ready wire BOM generation tool with routing diagrams
✅ **224/224 tests passing**

**Design Documents**:
- `kicad2wireBOM_design.md` v3.2 - Main design specification
- `wire_routing_diagrams_design.md` - Routing diagrams (Phase 10 complete)
- `ea_wire_marking_standard.md` - Wire marking standard (maintained)

**Core Capabilities**:
- Flat and hierarchical schematics
- Circuit-based wire gauge calculation
- N-way multipoint connections
- Comprehensive validation framework
- SVG routing diagrams (optimized for 8.5×11 portrait printing)

---

## PHASE 11: COMPREHENSIVE OUTPUT GENERATION

**Status**: Design complete, ready for implementation

**Deliverables**:
- [x] Design unified output directory structure
- [x] Design component BOM CSV format and content
- [x] Design engineering report markdown structure
- [x] Design HTML index page layout and features
- [x] Design system diagram renaming (*_routing.svg → *_System.svg)
- [x] Design component wiring diagrams (*_Component.svg)
- [x] Update kicad2wireBOM_design.md with new outputs (v3.3)
- [x] Create implementation tasks in programmer_todo.md
- [ ] Review implementation when complete
- [ ] Update opportunities_for_improvement.md if new OFIs identified

**Design Summary**:
- All outputs consolidated into single directory per run (7+ files)
- Directory name matches source schematic basename
- Always generate all outputs (removed `--routing-diagrams` flag)
- Capture stdout/stderr to files while teeing to console
- HTML index provides user-friendly entry point with links and summary
- Engineering report combines wire + component data with calculations
- Component BOM enables procurement and build planning
- System diagrams show all wiring for each system code (renamed *_System.svg)
- Component diagrams show first-hop connections for each component (*_Component.svg)

**New Output Files**:
- `<basename>.html` - HTML index with embedded console logs
- `component_bom.csv` - Component data with reference, value, description, datasheet, coordinates, electrical properties
- `engineering_report.md` - Comprehensive engineering documentation
- `<component>_Component.svg` - Per-component wiring diagrams (first-hop connections)

**Modified Output Files**:
- `<system>_System.svg` - Renamed from `<system>_routing.svg` for clarity

**New Modules**:
- `output_manager.py` - Directory management and stream capture
- `output_component_bom.py` - Component BOM generation
- `output_engineering_report.py` - Engineering report generation
- `output_html_index.py` - HTML index generation

**Files Modified**:
- `kicad2wireBOM_design.md` - Sections 2.2, 7.2, 7.6-7.8, 9.1-9.4, 11.1
- `programmer_todo.md` - Phase 11 implementation tasks (11.1-11.10)
- `component.py` - Add datasheet field (implementation task)

---

## FUTURE OPTIONS

See `docs/notes/opportunities_for_improvement.md` for detailed feature ideas.

**Potential Next Phases**:
- 3D wire routing visualization (add WL dimension to diagrams)
- Interactive HTML diagrams with zoom/pan
- Wire harness weight calculation for W&B
- Multiple netlist processing (entire KiCad project at once)
- Temperature derating for hot environments
