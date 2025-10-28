# Architect TODO: kicad2wireBOM

**Last Updated**: 2025-10-28

---

## CURRENT STATUS

✅ **Phase 1-13 Complete** - Production-ready wire BOM generation tool
✅ **306/306 tests passing**

**Design Documents**:
- `kicad2wireBOM_design.md` v3.6 - Main design specification
- `ea_wire_marking_standard.md` - Wire marking standard

**Core Capabilities**:
- Flat and hierarchical schematics
- Circuit-based wire gauge calculation
- N-way multipoint connections with power symbol support
- Comprehensive validation framework (strict and permissive modes)
- 3D SVG routing diagrams with optional 2D mode
- System routing diagrams (one per system code)
- Component wiring diagrams (first-hop connections per component)
- Component star diagrams (radial/polar logical connectivity view)
- Landscape orientation with centered origin, aircraft-pointing-up
- Reversed non-linear BL scaling (expanded centerline, compressed wingtips)
- Circuit labels grouped under components
- Unified output directory with multiple formats
- Component BOM, engineering report, HTML index

---

## FUTURE OPTIONS

See `docs/notes/opportunities_for_improvement.md` for detailed feature ideas.

---

## CURRENT WORK

### Phase 14: Engineering Report Enhancement - Markdown Tables

**Status**: [~] Design Complete, Implementation Pending
**Design Document**: `docs/plans/engineering_report_enhancement.md`
**Programmer Tasks**: `docs/plans/programmer_todo.md` - Phase 14

**Enhancements**:
1. Change output format from `.txt` to `.md` (Markdown)
2. Add Wire BOM table (complete wire details in Markdown table)
3. Add Component BOM table (complete component details in Markdown table)
4. Add Wire Purchasing Summary table (total length by gauge + type)
5. Add Component Purchasing Summary table (component count by value + datasheet)
6. Preserve existing project info and summary statistics
7. Properly aligned Markdown tables

**Deliverables**:
- [x] Design document created (engineering_report_enhancement.md)
- [x] Programmer tasks documented in programmer_todo.md (8 phases, 11 tasks)
- [ ] Implementation (programmer work)
- [ ] Testing (programmer work)

---

## FUTURE OPTIONS

See `docs/notes/opportunities_for_improvement.md` for detailed feature ideas.
