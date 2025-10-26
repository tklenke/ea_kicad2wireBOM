# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-26

---

## CURRENT STATUS

✅ **Phase 1-10 Complete** - All features implemented and tested
✅ **224/224 tests passing**

**Implemented Features**:
- Flat and hierarchical schematic parsing
- Circuit-based wire gauge calculation
- N-way multipoint connection detection
- Validation framework (strict/permissive modes)
- SVG routing diagrams with print optimization
- CSV and Markdown output formats

**Key Modules**:
- `parser.py`, `schematic.py`, `hierarchical_schematic.py` - Parsing
- `connectivity_graph.py`, `graph_builder.py` - Graph construction
- `wire_connections.py`, `bom_generator.py` - BOM generation
- `wire_calculator.py`, `reference_data.py` - Wire calculations
- `diagram_generator.py` - Routing diagrams (Phase 10)
- `output_csv.py` - Output formatting
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

## PHASE 11: UNIFIED OUTPUT DIRECTORY

**Status**: Ready to implement

### Overview
Consolidate all output files into a single directory for each run. Generate comprehensive output set including HTML index, component BOM, and engineering report.

### Design Changes

**New Output Structure**:
- Source: `/path/to/myproject.kicad_sch`
- If `dest` not provided: Creates `./myproject/` in current working directory
- If `dest=/output/dir/`: Creates `/output/dir/myproject/` directory
- All outputs go into this directory:
  - `myproject.html` - HTML index with links, stdout/stderr, and summary
  - `wire_bom.csv` - Wire BOM for builders
  - `component_bom.csv` - Component BOM with all extracted data
  - `engineering_report.md` - Comprehensive engineering report
  - `stdout.txt` - Captured console output (also tee to console)
  - `stderr.txt` - Captured error output (also tee to console)
  - `L_System.svg`, `P_System.svg`, etc. - System diagrams (one per system)
  - `LIGHT1_Component.svg`, `SW1_Component.svg`, etc. - Component diagrams (one per component)

**CLI Changes**:
- Remove `--routing-diagrams` flag (always generate all outputs)
- Change `dest` positional argument semantics:
  - Old: "Output CSV file (optional)"
  - New: "Output directory (optional, defaults to current directory)"
- Keep `-f/--force` flag: Delete and recreate entire output directory if exists
- Always generate routing diagrams (no longer optional)

### Implementation Tasks

**Phase 11.1: Output Directory Management** [~]
- [ ] Create `output_manager.py` module with directory creation logic
- [ ] Implement `create_output_directory(source_path, dest_dir, force)` function
  - Extracts base name from source (e.g., "myproject.kicad_sch" → "myproject")
  - Creates directory: `<dest_dir>/<basename>/`
  - If force=True: Delete existing directory first using `shutil.rmtree()`
  - If force=False and directory exists: Prompt user for confirmation
  - Returns Path object to output directory
- [ ] Write tests for output directory creation logic

**Phase 11.2: stdout/stderr Capture** [~]
- [ ] Create `TeeWriter` class in `output_manager.py`
  - Implements `write()`, `flush()` methods
  - Writes to both file and original stream (console)
  - Used as context manager to temporarily replace sys.stdout/sys.stderr
- [ ] Implement `capture_output(output_dir)` context manager
  - Opens `stdout.txt` and `stderr.txt` in output directory
  - Replaces sys.stdout and sys.stderr with TeeWriter instances
  - Restores original streams on exit
- [ ] Write tests for TeeWriter class

**Phase 11.3: Update __main__.py CLI** [~]
- [ ] Update argparse configuration:
  - Change `dest` help text to "Output directory (optional, defaults to current directory)"
  - Remove `--routing-diagrams` argument
  - Update help descriptions
- [ ] Refactor main() to use output_manager:
  - Call `create_output_directory()` at start
  - Wrap processing in `capture_output()` context manager
  - Update `write_builder_csv()` call to use output_dir / 'wire_bom.csv'
  - Always call `generate_routing_diagrams()` with output_dir
- [ ] Update existing tests to work with new directory structure

**Phase 11.4: Update diagram_generator.py** [~]
- [ ] Rename system diagram files: `<system>_routing.svg` → `<system>_System.svg`
  - Update output filename in `render_system_diagram()`
  - Update all references in comments and function names
- [ ] Add `generate_component_diagrams()` function
  - Takes: wire_connections, components_dict, output_dir
  - For each unique component reference:
    - Extract all wire connections where component appears (from or to)
    - Build set of first-hop neighbor components
    - For power symbols (GND, +12V): treat all instances as one logical component
    - Create DiagramWireSegment objects for wires to/from this component
    - Render component diagram SVG
- [ ] Add `render_component_diagram()` function
  - Similar to render_system_diagram but centered on single component
  - Title: "<component_ref> - Component Wiring"
  - Shows component + all first-hop neighbors
  - Auto-scale to fit components (may be smaller than system diagrams)
- [ ] Update `generate_routing_diagrams()` to call both system and component generation
- [ ] Update tests for renamed files and new component diagrams

**Phase 11.5: Integration Testing** [~]
- [ ] Create end-to-end test with fixture schematic
- [ ] Verify all expected files created in output directory:
  - HTML index, wire BOM, component BOM, engineering report
  - stdout.txt and stderr.txt
  - System diagrams (*_System.svg) - one per system code
  - Component diagrams (*_Component.svg) - one per component
- [ ] Verify stdout.txt and stderr.txt contain expected content
- [ ] Verify console output still appears (tee behavior)
- [ ] Verify HTML index links to all generated files (relative paths work)
- [ ] Test force flag (directory deletion and recreation)
- [ ] Test without force flag (user prompt)

**Phase 11.6: Component BOM Generation** [~]
- [ ] Add `datasheet` field to Component dataclass in component.py
- [ ] Update parse_symbol_element() in parser.py to extract Datasheet property
- [ ] Create output_component_bom.py module
- [ ] Implement write_component_csv() function
  - CSV columns: Reference, Value, Description, Datasheet, FS, WL, BL, Type, Amps
  - Type column: "Load", "Rating", "Source", or "Ground" based on component properties
  - Amps column: load/rating/source value (or blank for Ground)
  - Sort by reference designator (natural sort: CB1, CB2, CB10 not CB1, CB10, CB2)
- [ ] Write tests for component BOM generation

**Phase 11.7: Engineering Report Generation** [~]
- [ ] Create output_engineering_report.py module
- [ ] Implement write_engineering_report() function with sections:
  - Header: Project name, timestamp, tool version, source file
  - Summary: Total wires, total components, system counts, validation status
  - Validation Results: Errors and warnings with details
  - Wire BOM: Grouped by system code, formatted markdown tables
  - Component BOM: Formatted markdown table with all fields
  - Wire Calculations: Voltage drops, gauge selection rationale per circuit
  - Purchasing Summary: Total wire length needed by gauge and color
  - Configuration: System voltage, slack length, label threshold used
- [ ] Write tests for engineering report generation

**Phase 11.8: HTML Index Generation** [~]
- [ ] Create output_html_index.py module
- [ ] Implement write_html_index() function with:
  - Minimal CSS styling (just clean and functional)
  - Project title (extracted from source filename)
  - Generation metadata: timestamp, kicad2wireBOM version
  - Summary statistics: total wires, total components, systems processed
  - Validation section: warnings/errors highlighted (if any)
  - File links section: relative links to all output files
  - Console output section: stdout and stderr as `<pre><code>` blocks
  - All paths relative (works when directory is moved)
- [ ] Write tests for HTML index generation

**Phase 11.9: Integration and Testing** [~]
- [ ] Update main() in __main__.py to generate all new outputs:
  - Call write_component_csv()
  - Call write_engineering_report()
  - Call write_html_index() (must be last, reads stdout.txt/stderr.txt)
- [ ] Update end-to-end tests to verify all 7+ output files created
- [ ] Verify file contents are correct and complete
- [ ] Test with hierarchical and flat schematics
- [ ] Test with validation errors/warnings

**Phase 11.10: Documentation Updates** [~]
- [ ] Update kicad2wireBOM_design.md Section 7 (Output Formats)
- [ ] Update kicad2wireBOM_design.md Section 9 (CLI)
- [ ] Update kicad2wireBOM_design.md Section 11.1 (add new modules)
- [ ] Update README or usage documentation if exists
- [ ] Mark Phase 11 complete in architect_todo.md

---

## WORKFLOW REMINDERS

(unchanged from above)
