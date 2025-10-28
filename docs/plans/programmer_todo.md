# Programmer TODO: kicad2wireBOM

**Last Updated**: 2025-10-28

---

## CURRENT STATUS

✅ **Phase 1-13 Complete** - All features implemented and tested
✅ **306/306 tests passing**

**Key Modules**:
- `parser.py`, `schematic.py`, `hierarchical_schematic.py` - Parsing
- `connectivity_graph.py`, `graph_builder.py` - Graph construction
- `wire_connections.py`, `bom_generator.py` - BOM generation
- `wire_calculator.py`, `reference_data.py` - Wire calculations
- `diagram_generator.py` - System, component, and star routing diagrams
- `output_csv.py`, `output_component_bom.py`, `output_engineering_report.py` - Output generation
- `output_html_index.py`, `output_manager.py` - HTML and directory management
- `validator.py` - Schematic validation (strict and permissive modes)
- `__main__.py` - CLI

---

## CURRENT WORK: Phase 14 - Engineering Report Enhancement

**Design Document**: `docs/plans/engineering_report_enhancement.md`

### Phase 14.1: Markdown Table Formatting Utility

- [x] **Task 14.1.1**: Implement `_format_markdown_table()` helper function
  - Accept headers, rows, and alignment specifications
  - Calculate column widths based on content
  - Generate Markdown table with proper alignment syntax
  - TEST: Write `test_format_markdown_table()` with:
    - Left, center, right alignment
    - Various column widths
    - Special characters in cells
  - ✅ 4/4 tests passing

### Phase 14.2: Wire Purchasing Summary

- [x] **Task 14.2.1**: Implement `_generate_wire_purchasing_summary()` function
  - Group wires by (gauge, type) tuple
  - Sum total wire length for each group
  - Calculate length in inches and feet
  - Sort by gauge (numeric), then type
  - Add totals row
  - Return formatted Markdown table lines
  - TEST: Write `test_wire_purchasing_summary()` with:
    - Multiple gauges and types
    - Verify grouping and summation
    - Verify totals row
  - ✅ 3/3 tests passing

### Phase 14.3: Component Purchasing Summary

- [x] **Task 14.3.1**: Implement `_generate_component_purchasing_summary()` function
  - Group components by (value, datasheet) tuple
  - Count components in each group
  - Collect example refs (first 3-5)
  - Sort by value, then datasheet
  - Add totals row
  - Return formatted Markdown table lines
  - TEST: Write `test_component_purchasing_summary()` with:
    - Multiple value/datasheet combinations
    - Verify grouping and counting
    - Verify example refs formatting
    - Verify totals row
  - ✅ 3/3 tests passing

### Phase 14.4: Wire Engineering Analysis

- [x] **Task 14.4.1**: Implement `_calculate_circuit_currents()` helper function
  - Group wires by circuit ID using `group_wires_by_circuit()` from wire_calculator
  - For each circuit group, call `determine_circuit_current()` from wire_calculator
  - Return dict mapping circuit_id (e.g., "L1") to current in amps
  - Handle -99 sentinel for missing data
  - TEST: Write `test_calculate_circuit_currents()` with sample wires
  - ✅ 2/2 tests passing

- [x] **Task 14.4.2**: Implement `_generate_wire_engineering_analysis()` function
  - Import WIRE_RESISTANCE, WIRE_AMPACITY, DEFAULT_CONFIG from reference_data
  - For each wire:
    - Extract circuit_id from wire_label (e.g., "L1" from "L1A")
    - Get circuit current from circuit_currents dict
    - Calculate voltage drop using `calculate_voltage_drop()`
    - Calculate vdrop % = (vdrop / system_voltage) × 100
    - Get ampacity from WIRE_AMPACITY[gauge]
    - Calculate utilization % = (current / ampacity) × 100
    - Calculate resistance = resistance_per_foot × (length / 12)
    - Calculate power loss = current² × resistance
  - Format as Markdown table (all numeric columns right-aligned)
  - Add totals row (sum: length, voltage drop, power loss)
  - TEST: Write `test_wire_engineering_analysis()` with:
    - Sample wires with known circuit currents
    - Verify voltage drop calculations
    - Verify utilization percentages
    - Verify power loss calculations
    - Verify totals row
  - ✅ 2/2 tests passing

- [x] **Task 14.4.3**: Implement `_generate_engineering_summary()` function
  - Calculate total power loss (sum all wire power losses)
  - Find worst voltage drop (max vdrop %)
  - Identify overloaded wires (utilization > 100%)
  - Identify high vdrop wires (vdrop > 5%)
  - Format summary section with warnings
  - TEST: Write `test_engineering_summary()` with:
    - Wires with utilization > 100%
    - Wires with vdrop > 5%
    - Verify warnings generated
  - ✅ 2/2 tests passing

### Phase 14.5: Wire BOM Table

- [x] **Task 14.5.1**: Implement `_generate_wire_bom_table()` function
  - Extract all wire fields into table rows
  - Format each field as string
  - Use `_format_markdown_table()` with proper alignments
  - Right-align length column
  - Sort by wire label
  - TEST: Write `test_wire_bom_table()` with sample wire data
  - ✅ 2/2 tests passing

### Phase 14.6: Component BOM Table

- [ ] **Task 14.6.1**: Implement `_generate_component_bom_table()` function
  - Extract all component fields into table rows
  - Format coordinates and electrical specs
  - Use `_format_markdown_table()` with proper alignments
  - Right-align numeric columns (Amps, FS, WL, BL)
  - Sort by reference
  - TEST: Write `test_component_bom_table()` with sample component data

### Phase 14.7: Main Report Generation

- [ ] **Task 14.7.1**: Rewrite `write_engineering_report()` for Markdown output
  - Change to Markdown header format (# and ##)
  - Add all sections in order:
    1. Header with title
    2. Project Information (if available)
    3. Overall Summary (with total wire length)
    4. Wire Purchasing Summary table
    5. Component Purchasing Summary table
    6. Wire Engineering Analysis table with summary
    7. Wire BOM table
    8. Component BOM table
    9. Component Summary by Type (existing)
    10. Wire Summary by System (existing)
  - Calculate circuit currents before generating tables
  - Use helper functions for all tables
  - Write to `.md` file
  - TEST: Write `test_write_engineering_report_markdown()` to verify full report

### Phase 14.8: Integration Updates

- [ ] **Task 14.8.1**: Update CLI to use `.md` extension
  - Change `__main__.py` line 425: `engineering_report.txt` → `engineering_report.md`
  - Pass components list to `write_engineering_report()` for circuit current calculations
  - TEST: Run integration test, verify `.md` file created

- [ ] **Task 14.8.2**: Update HTML index to link to `.md` file
  - Change `output_html_index.py`: link from `engineering_report.txt` → `engineering_report.md`
  - TEST: Verify HTML index links correctly

### Phase 14.9: Test Updates

- [ ] **Task 14.9.1**: Update existing engineering report tests
  - Change all test file paths from `.txt` to `.md`
  - Update assertions for Markdown format:
    - Check for `#` headers instead of `===` separators
    - Check for table syntax with `|` characters
  - Verify all existing tests pass

- [ ] **Task 14.9.2**: Add integration test for Phase 14
  - Generate engineering report from test_07 fixture
  - Verify all sections present
  - Verify tables are valid Markdown
  - Verify purchasing summaries have correct calculations
  - Verify wire engineering analysis calculations accurate
  - Verify safety warnings detected (if any in fixture)

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
