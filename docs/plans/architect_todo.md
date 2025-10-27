# Architect TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-12 Complete** - Production-ready wire BOM generation tool
✅ **265/265 tests passing**
🔨 **Phase 13 In Progress** - Routing diagram enhancements v2.0

**Design Documents**:
- `kicad2wireBOM_design.md` v3.5 - Main design specification
- `ea_wire_marking_standard.md` - Wire marking standard
- `routing_diagram_enhancements_v2.md` - Phase 13 routing diagram improvements

**Core Capabilities**:
- Flat and hierarchical schematics
- Circuit-based wire gauge calculation
- N-way multipoint connections with power symbol support
- Comprehensive validation framework
- 3D SVG routing diagrams (optimized for 8.5×11 printing)
- Unified output directory with multiple formats
- Component BOM, engineering report, HTML index

---

## CURRENT WORK

### Phase 13: Routing Diagram Enhancements v2.0

**Status**: [~] Design Complete, Implementation Pending
**Design Document**: `docs/plans/routing_diagram_enhancements_v2.md`
**Programmer Tasks**: `docs/plans/programmer_todo.md` - Phase 13

**Enhancements**:
1. ✅ Landscape orientation (11×8.5 instead of 8.5×11 portrait)
2. ✅ Centered origin placement (FS=0, BL=0 at center below title)
3. ✅ Reversed FS axis (aircraft points UP - nose at bottom, tail at top)
4. ✅ Reversed non-linear BL scaling (expand centerline, compress wingtips)
5. ✅ Configurable wire stroke width (via reference_data.py)
6. ✅ Circuit labels grouped under components with stroke-1 boxes

**Deliverables**:
- [x] Design document created
- [x] Programmer tasks documented in programmer_todo.md
- [ ] Implementation (programmer work)
- [ ] Testing (programmer work)
- [ ] Visual validation

---

## FUTURE OPTIONS

See `docs/notes/opportunities_for_improvement.md` for detailed feature ideas
