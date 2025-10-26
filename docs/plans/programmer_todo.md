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
Consolidate all output files into a single directory for each run. Remove `--routing-diagrams` flag since all outputs are always generated.

### Design Changes

**New Output Structure**:
- Source: `/path/to/myproject.kicad_sch`
- If `dest` not provided: Creates `./myproject/` in current working directory
- If `dest=/output/dir/`: Creates `/output/dir/myproject/` directory
- All outputs go into this directory:
  - `wire_bom.csv` - Main wire BOM
  - `stdout.txt` - Captured console output (also tee to console)
  - `stderr.txt` - Captured error output (also tee to console)
  - `L_routing.svg`, `P_routing.svg`, etc. - Routing diagrams (one per system)

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
- [ ] Remove output_dir parameter validation (caller handles directory creation)
- [ ] Simplify `generate_routing_diagrams()` - assumes output_dir exists and is writable
- [ ] Update tests if needed

**Phase 11.5: Integration Testing** [~]
- [ ] Create end-to-end test with fixture schematic
- [ ] Verify all expected files created in output directory
- [ ] Verify stdout.txt and stderr.txt contain expected content
- [ ] Verify console output still appears (tee behavior)
- [ ] Test force flag (directory deletion and recreation)
- [ ] Test without force flag (user prompt)

**Phase 11.6: Documentation Updates** [~]
- [ ] Update kicad2wireBOM_design.md Section 7 (Output Formats)
- [ ] Update kicad2wireBOM_design.md Section 9 (CLI)
- [ ] Update README or usage documentation if exists
- [ ] Mark Phase 11 complete in architect_todo.md

---

## WORKFLOW REMINDERS

(unchanged from above)
