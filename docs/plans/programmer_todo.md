# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-12 Complete** - All features implemented and tested
✅ **265/265 tests passing** (includes post-Phase 12 enhancements)

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
- All tests passing after Phase 12 (up from 250 to 260)
- Comprehensive test coverage for projection formula, routing, and rendering

### Commits
- Phase 12.1: Add 3D projection constants and helper function
- Phase 12.2: Add WL coordinate to DiagramComponent dataclass
- Phase 12.3: Update DiagramWireSegment for 4-segment 3D routing
- Phase 12.4: Update rendering functions for 3D projection
- Bug fix: Fix negative SVG coordinates bug in 3D projection

### Bug Fix: Negative SVG Coordinates
**Issue**: Polyline points with negative values causing lines to go off SVG page.

**Root Cause**: Bounds were calculated on raw FS/BL coordinates, but 3D projection adds WL offsets. When WL was negative or large, projected coordinates fell outside calculated bounds, resulting in negative SVG coordinates.

**Solution**:
- Updated `calculate_bounds()` to project all 3D components to 2D screen coordinates first
- Calculate bounds on projected coordinates instead of raw 3D coordinates
- Updated `SystemDiagram` dataclass to track both projected bounds (for SVG rendering) and original bounds (for legend display)
- Added 4 new fields to SystemDiagram: `fs_min_original`, `fs_max_original`, `bl_min_original`, `bl_max_original`

**Result**: All tests passing after fix. No negative coordinates possible in SVG output.

---

## POST-PHASE 12 ENHANCEMENTS ✅

**Status**: COMPLETE - 2025-10-26

### Summary
Completed several quality-of-life and usability enhancements including validation improvements, title block support, and 2D diagram mode.

### Enhancements Implemented

**1. Missing LocLoad Validation** (5 tests added):
- Fixed silent failure when components missing LocLoad encoding
- Added `_check_component_locload()` to validator.py
- Respects strict/permissive mode (error vs warning)
- Updated __main__.py to track and pass missing LocLoad components to validator

**2. Error-Resilient Index.html** (manual testing):
- Create index.html before sys.exit(1) on validation errors
- Ensures users can access stdout.txt and stderr.txt even when processing fails
- Applied to both validation error handler and general exception handler

**3. Title Block Support** (2 tests added):
- Added `parse_title_block()` to parser.py to extract title, date, rev, company from schematics
- Updated all output functions to accept and display title_block:
  - CSV headers (wire_bom.csv and component_bom.csv) include project info as comment lines
  - Engineering report includes PROJECT INFORMATION section
  - HTML index includes Project Information section
  - SVG diagrams include project title line (title, rev, date)

**4. Component Info in Component Diagrams** (manual testing):
- Updated generate_svg() to accept component_value and component_desc parameters
- Component diagrams now show "{CompRef}: {Value} - {Description}" in title
- Example: "CB1: 30A - Circuit Breaker"

**5. 2D Diagram Mode** (manual testing):
- Added `--2d` command line argument to enable 2D diagrams (FS/BL only)
- Default remains 3D projection with WL axis
- Updated generate_svg() to skip 3D projection when use_2d=True
- Recalculates bounds for 2D mode using FS/BL coordinates directly
- All wire paths, labels, and component positions use simple FS/BL mapping in 2D mode

### Testing
- 5 new tests added (missing LocLoad validation, title_block parsing)
- 265/265 tests passing (up from 260)
- Manual testing confirmed all enhancements working correctly

### Files Modified
- `validator.py` - Added missing LocLoad validation
- `parser.py` - Added parse_title_block() function
- `__main__.py` - Track missing LocLoad, create index.html on errors, parse title_block, add --2d flag
- `diagram_generator.py` - Add title_block and component info to SVGs, implement 2D mode
- `output_csv.py` - Add title_block comment headers to wire BOM
- `output_component_bom.py` - Add title_block comment headers to component BOM
- `output_engineering_report.py` - Add PROJECT INFORMATION section
- `output_html_index.py` - Add Project Information section
- `reference_data.py` - Updated DEFAULT_WL_SCALE from 3.0 to 1.5

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
