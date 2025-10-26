# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-12 Complete** - All features implemented and tested
✅ **260/260 tests passing**

**Implemented Features**:
- Flat and hierarchical schematic parsing
- Circuit-based wire gauge calculation
- N-way multipoint connection detection
- Validation framework (strict/permissive modes)
- SVG routing diagrams (system and component) with 3D projection
- 3D elongated orthographic projection showing all three axes (FS, WL, BL)
- 4-segment 3D Manhattan routing (BL→FS→WL order)
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

## PHASE 12: 3D DIAGRAM PROJECTION ✅

**Status**: COMPLETE - 2025-10-26

### Summary
Successfully implemented 3D elongated orthographic projection for all routing diagrams. All three aircraft axes (FS, WL, BL) now visible on 2D printed output using angled projection.

### Implemented Features

**3D Projection System**:
- Added DEFAULT_WL_SCALE = 3.0 (makes WL axis 3x more visible)
- Added DEFAULT_PROJECTION_ANGLE = 30° (projection angle)
- Implemented project_3d_to_2d() function with formula:
  - screen_x = FS + (WL × wl_scale) × cos(angle)
  - screen_y = BL + (WL × wl_scale) × sin(angle)

**3D Data Structures**:
- Updated DiagramComponent with wl field (FS, WL, BL coordinates)
- Updated DiagramWireSegment.manhattan_path to return 5 3D points
- 4-segment Manhattan routing (BL → FS → WL order):
  1. Start at C1: (FS1, WL1, BL1)
  2. BL move: (FS1, WL1, BL2)
  3. FS move: (FS2, WL1, BL2)
  4. WL move: (FS2, WL2, BL2)
  5. End at C2: (FS2, WL2, BL2)

**3D Rendering**:
- Updated generate_svg() to project all 3D coordinates to 2D
- Projects wire paths, labels, component markers, and component labels
- Non-linear BL compression still works with 3D projection
- calculate_wire_label_position() updated for 5-point 3D paths

**Testing**:
- Added 10 new tests for 3D projection functionality
- Updated all existing diagram tests for 3D format
- 260/260 tests passing (up from 250)
- Comprehensive test coverage for projection formula, routing, and rendering

### Commits
- Phase 12.1: Add 3D projection constants and helper function
- Phase 12.2: Add WL coordinate to DiagramComponent dataclass
- Phase 12.3: Update DiagramWireSegment for 4-segment 3D routing
- Phase 12.4: Update rendering functions for 3D projection

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
