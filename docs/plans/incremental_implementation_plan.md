# kicad2wireBOM: Incremental Implementation Plan

## Overview

This plan uses a **thin vertical slice** approach instead of horizontal layers. We build end-to-end functionality incrementally, validating against real KiCad netlists at each step.

**Philosophy:**
- Start with minimal spike to prove KiCad data extraction works
- Add one feature at a time
- Test against real netlists after each increment
- TDD: Write test first, implement minimal code, verify, commit
- Each test fixture drives the next set of features

---

## Phase 0: Initial Spike (Validate Foundation)

**Goal:** Prove we can extract data from KiCad netlists with footprint encoding

**Test Fixture:** `tests/fixtures/test_01_minimal_two_component.net`

**Tasks:**
1. Set up project structure:
   - `kicad2wireBOM/` package directory
   - `tests/` directory
   - Install kinparse dependency
   - Basic pytest configuration

2. Write minimal netlist parser:
   - Parse netlist with kinparse
   - Extract net code (for circuit_id)
   - Extract net name (for documentation)
   - Extract component references
   - Extract footprint field (full string including encoding)

3. Parse footprint encoding:
   - Regex to extract: `|(fs,wl,bl)<L|R><amps>`
   - Parse coordinates (FS, WL, BL)
   - Parse type letter (L or R)
   - Parse amperage value

4. Print extracted data to console

**Success Criteria:**
- Can parse KiCad netlist ✓
- Can extract net codes ✓
- Can extract footprint encoding ✓
- Can parse coordinates and load/rating ✓

**Modules Started:**
- `parser.py` - Basic netlist parsing
- `component.py` - Component data structure (simple dataclass)

**Commit:** "Initial spike: Parse KiCad netlist and extract footprint data"

---

## Phase 1: Test Fixture 01 - Minimal Two-Component Circuit

**Fixture:** `tests/fixtures/test_01_minimal_two_component.net`
- J1 (connector) → SW1 (switch)
- Single net (Net-P12)
- Simplest possible circuit

**Features to Implement:**
1. ✅ Parse netlist (from spike)
2. ✅ Extract component data (from spike)
3. **NEW: Wire length calculation**
   - Manhattan distance formula
   - Add slack (24")
4. **NEW: Wire gauge calculation**
   - Reference data: wire resistance and ampacity tables (stub with hardcoded values for now)
   - Voltage drop calculation (5% max)
   - Select minimum AWG size
5. **NEW: System code detection**
   - Implement basic algorithm (ref prefix matching)
   - Start with simple patterns: "LIGHT" → "L", "BAT" → "P"
6. **NEW: Wire label generation**
   - Format: `{system_code}-{circuit_id}-{segment_letter}`
   - Example: `P-12-A`
7. **NEW: Simple CSV output**
   - Headers: Wire Label, From, To, Wire Gauge, Length, Wire Type
   - One row per wire segment

**Test Strategy:**
- Unit tests for each calculation function
- Integration test: Parse fixture → Generate CSV → Verify output

**Success Criteria:**
- Produces valid CSV with one wire entry
- Wire length = Manhattan distance + 24"
- Wire gauge meets voltage drop constraint
- Wire label follows EAWMS format

**Commit:** "Complete test fixture 01: Basic two-component circuit with CSV output"

---

## Phase 2: Test Fixture 02 - Simple Load Circuit

**Fixture:** `tests/fixtures/test_02_simple_load.net`
- J1 (source) → SW1 (switch) → LIGHT1 (load)
- Net-L105
- Tests: Wire segmentation (A, B segments), load calculations

**Features to Add:**
1. **Wire segmentation**
   - Multi-component circuit creates multiple segments
   - Segment labeling: A, B, C...
   - Signal flow ordering (source → passthrough → load)
2. **Load vs Rating logic**
   - Identify load components (has Load value)
   - Identify passthrough components (has Rating value)
   - Use load current for wire gauge calculation
3. **Enhanced system code detection**
   - Add "LIGHT", "LAMP", "LED" → "L"
   - Parse net name prefix for system code hint

**Test Strategy:**
- Verify two wire segments created (J1→SW1, SW1→LIGHT1)
- Verify segment labels (L-105-A, L-105-B)
- Verify load current used for gauge calculation

**Success Criteria:**
- CSV output has two rows (two segments)
- Segments labeled A and B correctly
- Both segments use load current for gauge calculation

**Commit:** "Complete test fixture 02: Multi-segment circuit with load calculation"

---

## Phase 3: Test Fixture 03 - Multi-Node Star Topology

**Fixture:** `tests/fixtures/test_03_multi_node_star.net`
- J1 (hub) → SW1, SW2, SW3 (spokes)
- Single net connecting 4 components
- Tests: Star topology detection, hub identification

**Features to Add:**
1. **Multi-node detection**
   - Identify nets with 3+ components
2. **Hub identification**
   - Implement hub priority algorithm
   - Tier 1: BUS, BUSS, BAT, GND
   - Tier 2: FUSE, CB, PANEL
   - Tier 3: J/CONN with Rating ≥ 20A
   - Tier 4: Highest rating, closest to origin
3. **Star topology wire creation**
   - Create segments: hub → spoke1, hub → spoke2, hub → spoke3
   - Segment ordering by distance from hub

**Test Strategy:**
- Verify 3 segments created (hub to each spoke)
- Verify correct hub identified
- Verify segment labeling (A, B, C)

**Success Criteria:**
- CSV has 3 rows (one per spoke)
- Hub correctly identified as J1
- All segments originate from hub

**Commit:** "Complete test fixture 03: Multi-node star topology"

---

## Phase 4: Test Fixture 06 - Missing Data (Permissive Mode)

**Fixture:** `tests/fixtures/test_06_missing_data.net`
- Components with missing footprint encodings
- Tests: Permissive mode, default values, warnings

**Features to Add:**
1. **Strict mode validation**
   - Error on missing FS/WL/BL
   - Error on missing Load/Rating
   - Abort processing with helpful error messages
2. **Permissive mode**
   - CLI flag: `--permissive`
   - Default missing coordinates to (-9, -9, -9)
   - Default missing Load/Rating to 0A
   - Generate warnings but continue processing
3. **Warning system**
   - Collect warnings during processing
   - Include in CSV output (Warnings column)
   - Log to console

**Test Strategy:**
- Test strict mode: Verify errors and abort
- Test permissive mode: Verify defaults and warnings
- Verify warning messages in output

**Success Criteria:**
- Strict mode fails with clear error messages
- Permissive mode produces BOM with warnings
- Missing coords default to (-9, -9, -9)

**Commit:** "Complete test fixture 06: Strict and permissive modes with validation"

---

## Phase 5: Test Fixture 07 - Negative Coordinates

**Fixture:** `tests/fixtures/test_07_negative_coords.net`
- Components with negative BL (left side of aircraft)
- Tests: Negative coordinate handling

**Features to Add:**
1. **Negative coordinate support**
   - Verify parser handles negative values
   - Manhattan distance with absolute values
2. **Coordinate validation**
   - Ensure coordinates are valid floats
   - No additional logic needed (Manhattan distance already uses abs())

**Test Strategy:**
- Parse negative coordinates correctly
- Calculate correct wire lengths with negative BL

**Success Criteria:**
- Negative coordinates parse correctly
- Wire lengths calculated correctly (absolute differences)

**Commit:** "Complete test fixture 07: Negative coordinate handling"

---

## Phase 6: Test Fixture 05 - Multiple Independent Circuits

**Fixture:** `tests/fixtures/test_05_multiple_circuits.net`
- 3 separate circuits (Lighting, Radio, Ground)
- Multiple system codes (L, R, G)
- Tests: System code parsing, BOM grouping/sorting

**Features to Add:**
1. **Enhanced system code detection**
   - Expand component type patterns:
     - "RADIO", "NAV", "COM", "XPNDR" → "R"
     - "GPS", "EFIS", "EMS", "AHRS" → "A"
     - "FUEL", "OIL", "CHT", "EGT" → "E"
   - Net name analysis:
     - "GND", "GROUND", "RTN", "RETURN" → "G"
     - "PWR", "POWER", "BUS" → "P"
   - Pass-through component analysis (parse ref for keywords)
   - Fallback to "U" (Unknown/Miscellaneous)
2. **Reference data extraction**
   - Extract complete wire resistance table
   - Extract complete ampacity table
   - Extract complete system color mapping
   - Implement in `reference_data.py`
3. **Wire color assignment**
   - Map system code → color
   - Add Wire Color column to CSV
4. **Output sorting**
   - Sort by: system code, circuit number, segment letter
   - Group by system in output

**Test Strategy:**
- Verify all system codes detected correctly
- Verify wire colors assigned
- Verify output sorted correctly

**Success Criteria:**
- All system codes (L, R, G) detected correctly
- Wire colors assigned per system
- CSV output sorted by system/circuit/segment

**Commit:** "Complete test fixture 05: Multiple circuits with system detection and colors"

---

## Phase 7: Test Fixture 08 - Realistic Complex System

**Fixture:** `tests/fixtures/test_08_realistic_system.net`
- 10-15 components, 8-12 circuits
- Full aircraft electrical panel subset
- Tests: End-to-end integration

**Features to Add:**
1. **CLI interface basics**
   - Argument parsing (source, dest)
   - Basic flags (--help, --permissive)
2. **Auto-generate output filename**
   - REVnnn format
   - Increment revision number
3. **Engineering mode output**
   - Additional columns: calculated gauge, voltage drop, coordinates
   - CLI flag: `--engineering`
4. **Markdown output format**
   - Summary section (total wires, purchasing summary)
   - Wire list tables grouped by system
   - Warnings section
   - CLI flag: `--format md` or `.md` extension

**Test Strategy:**
- Full end-to-end test with realistic netlist
- Verify all features work together
- Test both CSV and Markdown output
- Test builder and engineering modes

**Success Criteria:**
- Processes realistic netlist successfully
- Produces accurate, complete BOM
- Both output formats work
- Both output modes work
- CLI interface functional

**Commit:** "Complete test fixture 08: Realistic system with full CLI and output formats"

---

## Phase 8: Remaining Features and Polish

After all test fixtures pass, complete remaining functionality:

### 8.1 Validation Enhancements
- **Rating vs Load validation**
  - Check load doesn't exceed ratings in circuit path
  - Generate warnings
- **Gauge progression validation**
  - Warn if downstream wire heavier than upstream
- **Component validation report** (engineering mode)
  - Table of all components with coordinates and ratings

### 8.2 CLI Completion
- **Remaining flags:**
  - `--version`
  - `--schematic-requirements` (output documentation)
  - `--system-voltage` (default 12V)
  - `--slack-length` (default 24")
  - `--format {csv,md}`
- **Exit codes:**
  - 0 = success
  - 1 = error
- **Error messages:**
  - Helpful, actionable messages
  - Component references included
  - Suggestions for correction

### 8.3 Output Enhancements
- **Purchasing summary** (Markdown only)
  - Total length needed per gauge/color combination
  - Grouped for bulk ordering
- **Engineering mode additions:**
  - Detailed calculations section
  - Circuit analysis (power budget per system)
  - Assumptions documentation
  - Voltage drop analysis table
- **Net name and net type in notes**
  - Capture from KiCad netlist
  - Include in appropriate output field

### 8.4 Documentation
- **README.md:**
  - Installation instructions
  - Usage examples
  - Quick start guide
- **Schematic requirements documentation:**
  - Generate with `--schematic-requirements`
  - Complete field descriptions
  - Examples
  - Encoding format reference

### 8.5 Module Organization
Review and refactor into clean modules:
- `parser.py` - Netlist parsing
- `component.py` - Component data model
- `circuit.py` - Circuit analysis and segmentation
- `wire_calculator.py` - Length, gauge, color calculations
- `wire_bom.py` - BOM data structures
- `validator.py` - Validation logic
- `reference_data.py` - Wire tables, color maps, system patterns
- `output_csv.py` - CSV generation
- `output_markdown.py` - Markdown generation
- `__main__.py` - CLI entry point

---

## Testing Strategy

### Test Levels
1. **Unit tests:** Individual functions (calculations, parsing, etc.)
2. **Integration tests:** Module interactions
3. **Fixture tests:** End-to-end with real netlists
4. **Regression tests:** Ensure changes don't break existing functionality

### Test Coverage Goals
- All calculation functions: 100%
- Parser functions: 100%
- CLI argument handling: 100%
- Integration tests: All test fixtures passing

### Test Execution
```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_parser.py -v

# Run with coverage
pytest --cov=kicad2wireBOM --cov-report=term-missing
```

---

## Implementation Principles

### TDD Cycle (Every Feature)
1. **RED:** Write failing test first
2. **GREEN:** Write minimal code to pass test
3. **REFACTOR:** Clean up while keeping tests green
4. **COMMIT:** Commit with descriptive message

### Incremental Progress
- Each phase builds on previous
- Always have working code (tests pass)
- Commit after each passing test
- No "big bang" integration at end

### Code Quality
- Follow CLAUDE.md standards
- ABOUTME comments in every file
- Type hints on all functions
- Docstrings on public functions
- No temporal names ("new", "old", "improved")
- YAGNI: Only implement what's needed now
- DRY: Refactor duplication after tests pass

---

## Success Criteria

The implementation is complete when:

- ✅ All 5 test fixtures pass
- ✅ All unit tests pass
- ✅ CSV output (builder and engineering modes)
- ✅ Markdown output (builder and engineering modes)
- ✅ CLI fully functional with all flags
- ✅ Validation works (strict and permissive modes)
- ✅ System code detection working
- ✅ Wire calculations correct (length, gauge, color)
- ✅ Code follows CLAUDE.md standards
- ✅ Documentation complete (README, --schematic-requirements)
- ✅ Ready for real-world use

---

## Estimated Timeline (Solo Developer)

- **Phase 0 (Spike):** 2-3 hours
- **Phase 1 (Fixture 01):** 4-6 hours
- **Phase 2 (Fixture 02):** 3-4 hours
- **Phase 3 (Fixture 03):** 3-4 hours
- **Phase 4 (Fixture 06):** 3-4 hours
- **Phase 5 (Fixture 07):** 1-2 hours
- **Phase 6 (Fixture 05):** 4-6 hours
- **Phase 7 (Fixture 08):** 4-6 hours
- **Phase 8 (Remaining):** 8-12 hours

**Total:** ~30-45 hours (4-6 days of focused work)

---

## Next Step

Ready to start **Phase 0: Initial Spike**?

Switch to Programmer role and begin with minimal netlist parser to validate KiCad data extraction.
