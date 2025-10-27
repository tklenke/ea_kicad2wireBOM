# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-12 Complete** - All features implemented and tested
✅ **265/265 tests passing**

**Key Modules**:
- `parser.py`, `schematic.py`, `hierarchical_schematic.py` - Parsing
- `connectivity_graph.py`, `graph_builder.py` - Graph construction
- `wire_connections.py`, `bom_generator.py` - BOM generation
- `wire_calculator.py`, `reference_data.py` - Wire calculations
- `diagram_generator.py` - System and component routing diagrams
- `output_csv.py`, `output_component_bom.py`, `output_engineering_report.py` - Output generation
- `output_html_index.py`, `output_manager.py` - HTML and directory management
- `__main__.py` - CLI

---

## CURRENT WORK: Phase 13 - Routing Diagram Enhancements v2.0

**Design Document**: `docs/plans/routing_diagram_enhancements_v2.md`

### Phase 13.1: Configuration Setup

- [x] **Task 13.1.1**: Add diagram configuration to `reference_data.py`
  - Add `DIAGRAM_CONFIG` dict with layout constants (svg_width, svg_height, margins, etc.)
  - Add BL scaling parameters: `BL_CENTER_EXPANSION = 3.0`, `BL_TIP_COMPRESSION = 10.0`, `BL_CENTER_THRESHOLD = 30.0`
  - Add `WIRE_STROKE_WIDTH = 3.0` (make configurable)
  - TEST: Verify constants importable and have correct types

- [x] **Task 13.1.2**: Update imports in `diagram_generator.py`
  - Import `DIAGRAM_CONFIG` from reference_data
  - Replace hardcoded constants (FIXED_WIDTH, FIXED_HEIGHT, MARGIN, etc.) with config values
  - Replace hardcoded wire stroke width with `DIAGRAM_CONFIG['wire_stroke_width']`
  - TEST: Run existing tests, verify no regressions

### Phase 13.2: Coordinate System Changes

- [x] **Task 13.2.1**: Implement `scale_bl_nonlinear_v2()` function
  - Create new function in `diagram_generator.py` alongside existing `scale_bl_nonlinear()`
  - Piecewise scaling: BL < 30" → expand by center_expansion factor
  - BL > 30" → compress logarithmically
  - Parameters from reference_data.py
  - TEST: Write `test_scale_bl_nonlinear_v2()` with test cases:
    - BL=0 → 0
    - BL=10 → 30 (3x expansion)
    - BL=30 → 90 (threshold)
    - BL=200 → ~130 (heavy compression)
    - BL=-10 → -30 (sign preserved)

- [x] **Task 13.2.2**: Create new `transform_to_svg_v2()` function
  - Accept `origin_svg_x, origin_svg_y` parameters instead of bounds
  - Call `scale_bl_nonlinear_v2()` for BL scaling
  - Map BL to horizontal offset from center: `svg_x = origin_svg_x + (bl_scaled * scale_x)`
  - Map FS to vertical with inversion (FS+ goes up): `svg_y = origin_svg_y - (fs * scale_y)`
  - TEST: Write `test_transform_to_svg_v2()` with test cases:
    - FS=0, BL=0 → origin position
    - FS=+50, BL=0 → above origin (lower svg_y)
    - FS=-50, BL=0 → below origin (higher svg_y)
    - FS=0, BL=+20 → right of origin
    - FS=0, BL=-20 → left of origin

- [ ] **Task 13.2.3**: Update `generate_svg()` for landscape layout
  - Change dimensions to landscape (1100×700 from DIAGRAM_CONFIG)
  - Calculate origin position: `origin_svg_x = svg_width/2`, `origin_svg_y = title_height + origin_offset_y`
  - Update all coordinate transformation calls to use `transform_to_svg_v2()`
  - Update wire segment rendering loop
  - Update component marker rendering loop
  - Update component label rendering loop
  - Update wire label rendering loop
  - TEST: Generate diagram from test_01 fixture, verify landscape, verify origin centered

### Phase 13.3: Scaling Calculations

- [ ] **Task 13.3.1**: Update scale calculation for reversed BL scaling
  - Apply `scale_bl_nonlinear_v2()` to all BL values to get scaled range
  - Calculate `bl_scaled_min` and `bl_scaled_max` from scaled values
  - Calculate scale_x to fit `bl_scaled_max - bl_scaled_min` in available width
  - Calculate scale_y to fit FS range in available height
  - TEST: Write `test_scale_calculation_v2()` to verify scale factors reasonable

- [ ] **Task 13.3.2**: Update `calculate_bounds()` for v2 scaling
  - Option A: Create `calculate_bounds_v2()` that uses `scale_bl_nonlinear_v2()`
  - Option B: Add parameter to `calculate_bounds()` to select scaling function
  - Return scaled bounds for layout calculations
  - TEST: Verify bounds calculation with new scaling

### Phase 13.4: Circuit Labels Under Components

- [ ] **Task 13.4.1**: Build component-to-circuits mapping in `generate_svg()`
  - Before rendering, create `component_circuits: Dict[str, List[str]]`
  - Loop through `diagram.wire_segments`
  - Add `segment.label` to lists for both `comp1.ref` and `comp2.ref`
  - Sort and deduplicate each component's circuit list
  - TEST: Write `test_build_component_circuits_map()` to verify mapping correct

- [ ] **Task 13.4.2**: Implement circuit label box rendering
  - After component labels section, add new section `<g id="component-circuits">`
  - For each component with circuits:
    - Format label text as comma-separated: `", ".join(circuit_labels)`
    - Estimate text width: `text_width = len(label_text) * 7 + 10` (approximate)
    - Set text height: `text_height = 16`
    - Calculate box position below component marker
    - Render white background rect with navy stroke-1
    - Render centered text inside box
  - TEST: Generate diagram, verify circuit labels appear with boxes

- [ ] **Task 13.4.3**: Handle circuit label box collisions
  - Track rendered box positions
  - Before rendering each box, check for overlaps
  - If overlap detected, offset box downward by text_height + 4
  - Continue until no overlap
  - TEST: Create test with multiple components at similar positions, verify boxes don't overlap

### Phase 13.5: Testing and Validation

- [ ] **Task 13.5.1**: Update existing integration tests
  - Run all existing diagram tests
  - Update assertions for new layout (landscape dimensions, origin position)
  - Verify all tests pass

- [ ] **Task 13.5.2**: Add new integration tests for v2 features
  - Test: `test_diagram_landscape_orientation()` - verify width > height
  - Test: `test_diagram_origin_centered()` - verify FS=0,BL=0 at expected position
  - Test: `test_diagram_fs_axis_inverted()` - verify FS+ renders above FS-
  - Test: `test_diagram_bl_expansion_at_center()` - verify centerline spacing
  - Test: `test_circuit_labels_under_components()` - verify boxes and labels render

- [ ] **Task 13.5.3**: Visual validation
  - Generate diagrams from test_01, test_03A, test_07 fixtures
  - Open in browser
  - Verify aircraft points UP (nose at bottom, tail at top)
  - Verify origin (FS=0, BL=0) centered below title
  - Verify BL expansion at centerline, compression at tips
  - Verify circuit labels grouped under components with stroke boxes
  - Verify wire stroke width from config
  - Print on 11×8.5 landscape, verify legibility

### Phase 13.6: Component Star Diagrams (NEW)

**See design document Section 11 for detailed specification**

- [ ] **Task 13.6.1**: Implement star layout algorithm
  - Add `calculate_star_layout()` function to `diagram_generator.py`
  - Input: center component, list of neighbor components, radius (default 250px)
  - Calculate polar coordinates: angle = 360° / N for each neighbor
  - Return dict mapping component ref to (x, y) SVG coordinates
  - TEST: Write `test_calculate_star_layout()` with:
    - 1 neighbor → 0° position
    - 2 neighbors → 0°, 180° positions
    - 4 neighbors → 0°, 90°, 180°, 270° positions
    - Verify even angular distribution

- [ ] **Task 13.6.2**: Implement circle sizing logic
  - Add `calculate_circle_radius()` function to `diagram_generator.py`
  - Input: list of text strings (ref, value, desc), font size
  - Estimate text width and height
  - Return radius that fits text (min 40px, max 80px)
  - Add `wrap_text()` helper for long descriptions
  - TEST: Write `test_calculate_circle_radius()` with:
    - Short text → minimum radius (40px)
    - Long text → larger radius (up to 80px)
    - Very long text → max radius + wrapping

- [ ] **Task 13.6.3**: Create star diagram data structures
  - Add `StarDiagramComponent` dataclass (ref, value, desc, x, y, radius)
  - Add `StarDiagramWire` dataclass (circuit_id, from_ref, to_ref)
  - Add `ComponentStarDiagram` dataclass (center, neighbors, wires)
  - Add `build_component_star_diagram()` function
  - TEST: Write `test_build_component_star_diagram()` to verify data structure creation

- [ ] **Task 13.6.4**: Implement star SVG generation
  - Add `generate_star_svg()` function to `diagram_generator.py`
  - Portrait layout (750×950 px)
  - Title block with component ref, value, description
  - Render order: background → wires → wire labels → circles → circle text
  - Center circle: lightblue fill, navy stroke, 3px width
  - Outer circles: white fill, blue stroke, 2px width
  - Wire labels: positioned at midpoint of each line
  - Circle text: multi-line, centered, wrapped if needed
  - TEST: Write `test_generate_star_svg()` - generate test diagram, verify SVG structure

- [ ] **Task 13.6.5**: Integrate star diagrams into main generation
  - Add `generate_component_star_diagrams()` function
  - Loop through all components
  - Skip power symbols (GND, +12V, etc.)
  - For each component: find neighbors, build star diagram, generate SVG
  - File naming: `{comp_ref}_Star.svg`
  - Call from `generate_routing_diagrams()` after system and component diagrams
  - TEST: Run on test_07 fixture, verify star diagrams generated for all non-power components

- [ ] **Task 13.6.6**: Handle edge cases and polish
  - Components with 1 neighbor: still show as star (center + 1 outer)
  - Components with 20+ neighbors: use smaller circles or warning message
  - Long component descriptions: wrap text inside circles
  - Empty value or description: skip that line in circle
  - TEST: Create test cases for:
    - Single neighbor component
    - Many neighbor component (10+)
    - Long text wrapping
    - Missing component data

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
