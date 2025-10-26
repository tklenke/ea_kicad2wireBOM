# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-11 Complete** - All features implemented and tested
✅ **250/250 tests passing**

**Implemented Features**:
- Flat and hierarchical schematic parsing
- Circuit-based wire gauge calculation
- N-way multipoint connection detection
- Validation framework (strict/permissive modes)
- SVG routing diagrams (system and component) with print optimization
- Unified output directory structure with multiple formats
- Component BOM with electrical characteristics (Type, Amps)
- Engineering report with statistics and breakdowns
- HTML index with navigation to all outputs
- Console output capture (stdout/stderr)

**Key Modules**:
- `parser.py`, `schematic.py`, `hierarchical_schematic.py` - Parsing
- `connectivity_graph.py`, `graph_builder.py` - Graph construction
- `wire_connections.py`, `bom_generator.py` - BOM generation
- `wire_calculator.py`, `reference_data.py` - Wire calculations
- `diagram_generator.py` - System and component routing diagrams
- `output_csv.py` - Wire BOM CSV output
- `output_component_bom.py` - Component BOM CSV output (Phase 11)
- `output_engineering_report.py` - Engineering report text output (Phase 11)
- `output_html_index.py` - HTML index page (Phase 11)
- `output_manager.py` - Directory management and console capture (Phase 11)
- `__main__.py` - CLI

---

## WORKFLOW REMINDERS

**TDD Cycle**:
1. RED: Write failing test
2. VERIFY: Confirm it fails correctly
3. GREEN: Write minimal code to pass
4. VERIFY: Confirm it passes
5. REFACTOR: Clean up while keeping tests green
6. COMMIT: Commit with updated todo

**Pre-Commit Checklist**:
1. Update this programmer_todo.md
2. Run full test suite (`pytest -v`)
3. Include updated todo in commit

---

## PHASE 12: 3D DIAGRAM PROJECTION

**Status**: Ready to implement

### Overview
Add 3D visualization to system and component diagrams using elongated orthographic projection. Shows all three aircraft axes (FS, WL, BL) on 2D printed output.

### Design Changes

**3D Projection Formula**:
```
screen_x = FS + (WL × wl_scale) × cos(angle)
screen_y = BL + (WL × wl_scale) × sin(angle)
```

**Default Parameters**:
- `wl_scale` = 3.0 (makes WL 3x more visible)
- `angle` = 30° (projection angle)
- Both configurable

**3D Manhattan Routing** (BL → FS → WL):
From outer component (C1) to inner component (C2):
1. Start: (FS1, WL1, BL1)
2. BL move: (FS1, WL1, BL2) - stay horizontal at C1's WL
3. FS move: (FS2, WL1, BL2) - still horizontal at C1's WL
4. WL move: (FS2, WL2, BL2) - vertical drop/rise at C2's location
5. End: (FS2, WL2, BL2)

### Implementation Tasks

**Phase 12.1: Add 3D Projection Constants** [~]
- [ ] Add to reference_data.py:
  - `DEFAULT_WL_SCALE = 3.0`
  - `DEFAULT_PROJECTION_ANGLE = 30` (degrees)
- [ ] Add projection helper functions to diagram_generator.py:
  - `project_3d_to_2d(fs, wl, bl, wl_scale, angle)` → (screen_x, screen_y)
  - Takes aircraft coords, returns screen coords
  - Use math.radians() for angle conversion

**Phase 12.2: Update DiagramComponent for 3D** [~]
- [ ] Modify DiagramComponent dataclass in diagram_generator.py
  - Add `wl: float` field
  - Update all instantiations to include WL coordinate
- [ ] Update component position calculations to use 3D projection
  - Replace all (fs, bl) pairs with project_3d_to_2d(fs, wl, bl)

**Phase 12.3: Update DiagramWireSegment for 3D Routing** [~]
- [ ] Modify `manhattan_path` property for 4-segment routing:
  - Returns 5 points instead of 3
  - Point 1: (FS1, WL1, BL1) - start at C1
  - Point 2: (FS1, WL1, BL2) - BL move, horizontal
  - Point 3: (FS2, WL1, BL2) - FS move, still horizontal
  - Point 4: (FS2, WL2, BL2) - WL move, vertical
  - Point 5: (FS2, WL2, BL2) - end at C2 (same as point 4)
  - Each point projected with project_3d_to_2d()
- [ ] Update wire path rendering to handle 4-segment paths

**Phase 12.4: Update Diagram Rendering Functions** [~]
- [ ] Update render_system_diagram() for 3D:
  - Pass WL coordinates when creating DiagramComponent objects
  - Use 3D projection for all component positions
  - Use 3D projection for axis labels and grid (if any)
  - Update auto-scaling to account for WL projection offset
- [ ] Update render_component_diagram() for 3D (same changes)
- [ ] Verify non-linear BL compression still works with 3D projection

**Phase 12.5: Update Tests for 3D** [~]
- [ ] Update diagram generator tests:
  - Test 3D projection formula (known coordinates → expected screen coords)
  - Test 4-segment Manhattan routing path generation
  - Verify C1 at (0,0,0) and C2 at (0,10,0) projects correctly
- [ ] Update integration tests for new diagram appearance
- [ ] Visual inspection: Generate sample diagrams and verify 3D effect

**Phase 12.6: Configuration (Optional Future)** [~]
- [ ] Consider adding CLI flags (deferred to later):
  - `--wl-scale FACTOR` - Override default WL scale factor
  - `--projection-angle DEGREES` - Override projection angle
  - For now, use hardcoded defaults

---

## PHASE 11: UNIFIED OUTPUT DIRECTORY ✅

**Status**: COMPLETE - 2025-10-26

### Summary
Successfully implemented unified output directory structure with comprehensive output set. All outputs now consolidated into single directory named after source file.

### Output Structure Implemented
```
<source_basename>/
├── wire_bom.csv              # Wire BOM for builders
├── component_bom.csv          # Component BOM with Type, Amps, coordinates
├── engineering_report.txt     # Statistics and breakdowns
├── index.html                 # HTML navigation page
├── L_System.svg              # System diagrams (per system code)
├── P_System.svg
├── CB1_Component.svg         # Component diagrams (per component)
├── SW1_Component.svg
├── stdout.txt                # Console output log
└── stderr.txt                # Error output log
```

### CLI Changes
- `dest` argument now specifies output parent directory (not CSV file)
- Removed `--routing-diagrams` flag (always generate all outputs)
- `-f/--force` flag deletes and recreates directory
- All outputs generated automatically

### Modules Added
- `output_manager.py` - Directory creation and console capture
- `output_component_bom.py` - Component BOM CSV with Type (L/R/S) and Amps
- `output_engineering_report.py` - Engineering report with statistics
- `output_html_index.py` - HTML index page with links

### Testing
- 60 new tests added
- 250/250 tests passing
- Comprehensive integration test verifies all outputs

---

## WORKFLOW REMINDERS

(unchanged from above)
