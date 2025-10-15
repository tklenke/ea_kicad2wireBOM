# kicad2wireBOM: Design Specification

## Document Overview

**Purpose**: Comprehensive design specification for kicad2wireBOM tool - a wire Bill of Materials generator for experimental aircraft electrical systems.

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Design Complete - Ready for Implementation Planning

---

## 1. Overview and Goals

### 1.1 Purpose

Generate comprehensive wire Bills of Materials (BOMs) from KiCad schematic netlists for experimental aircraft electrical systems. The tool automates wire specification by combining schematic connectivity data with physical installation details (aircraft coordinates, component loads/ratings) to calculate appropriate wire gauges, estimate lengths, assign colors per standards, and produce builder-ready documentation.

### 1.2 Key Innovation

Rather than requiring manual wire specification, the tool leverages custom fields added to KiCad schematics (component locations in aircraft coordinates, electrical loads/ratings, optional wire specifications) to automatically calculate:

- **Wire lengths** using Manhattan distance between fuselage station/waterline/buttline coordinates
- **Minimum wire gauge** based on current load, wire length, and voltage drop constraints (5% max)
- **Wire colors** per system code following experimental aircraft standards
- **EAWMS-compliant wire labels** (SYSTEM-CIRCUIT-SEGMENT format)

### 1.3 Target Users

Experimental aircraft builders using KiCad for electrical system design who need accurate wire harness BOMs for construction and regulatory compliance.

### 1.4 Core Philosophy

**Automate what can be calculated, validate what can be checked, warn about uncertainties, but always produce usable output.**

Default to strict validation (encourage complete schematics) with permissive mode available for iterative design work.

---

## 2. Input Requirements

### 2.1 Primary Input

KiCad netlist file (`.net` or `.xml` format, v9+) exported from schematic.

### 2.2 Required Custom Fields on Components

All components in the schematic must have:

- **FS** (Fuselage Station): Aircraft longitudinal coordinate in inches from datum
- **WL** (Waterline): Vertical coordinate in inches from datum
- **BL** (Buttline): Lateral coordinate in inches from centerline (positive right, negative left)
- **Load** OR **Rating**: Current in amperes
  - **Load**: For consuming devices (lights, avionics, motors) - current drawn
  - **Rating**: For pass-through devices (connectors, switches, breakers) - maximum current capacity

### 2.3 Optional Custom Fields on Components

- **Wire_Type**: Wire specification (e.g., M22759/16, M22759/32) - if omitted, uses system default
- **Wire_Color**: Override auto-assigned color based on system code
- **Wire_Gauge**: Explicit wire gauge specification (e.g., "20 AWG") - tool validates against calculated minimum
- **Connector_Type**: Type/style of connector for documentation purposes

### 2.4 Optional Custom Fields on Nets

- **Circuit_ID**: Explicit EAWMS circuit number (overrides parsing from net name)
- **System_Code**: Explicit system letter (overrides parsing from net name)

### 2.5 Net Naming Convention

If Circuit_ID field not present on net:

- **Preferred format**: `Net-L105` (system letter + circuit number)
- Parser attempts to extract system code and circuit number from various formats
- Falls back to error if unable to parse and no Circuit_ID field present

### 2.6 Field Export Verification

**IMPORTANT**: Implementation plan must include experimental validation of which custom fields KiCad reliably exports to netlist format. This may vary by KiCad version and export settings.

Test with actual KiCad schematics to verify field names and formats that appear in exported netlist.

### 2.7 Optional Configuration File

Projects may include `.kicad2wireBOM.yaml` or `.kicad2wireBOM.json` configuration file for project-specific defaults:

- Custom wire resistance tables
- Custom color mappings
- Default system voltage
- Default slack length
- Custom ampacity tables

Configuration file is optional; tool works with built-in defaults and command-line options.

---

## 3. Calculation Logic

### 3.1 Wire Length Calculation

**Method**: Manhattan distance (sum of absolute differences in each axis) between component FS/WL/BL coordinates.

**Formula**:
```
Length = |FS₁ - FS₂| + |WL₁ - WL₂| + |BL₁ - BL₂| + slack
```

**Slack Allowance**:
- Default: 24 inches (12" per end for termination/routing flexibility)
- Configurable via command-line parameter `--slack-length`
- Documented in output and `--schematic-requirements`

**Rationale**:
- Manhattan distance is conservative (accounts for rectilinear routing through aircraft structure)
- More realistic than straight-line distance for actual wire runs
- Slack ensures adequate wire for termination, strain relief, and routing adjustments

**Multi-node Nets**:
For nets connecting 3+ components:
- Detect topology from spatial coordinates (star vs daisy-chain)
- Calculate segments between adjacent nodes
- Warn user that routing assumptions were made
- Log informational message during processing

### 3.2 Wire Gauge Calculation

**Basis**: Aeroelectric Connection (Bob Nuckolls) ampacity tables and voltage drop guidelines.

**Primary Constraint**: Maximum 5% voltage drop at system voltage
- Default system voltage: 12V (configurable via `--system-voltage`)
- 5% of 12V = 0.6V max drop
- 5% of 14V = 0.7V max drop

**Calculation Method**:

1. Calculate voltage drop: `Vdrop = Current × Resistance_per_foot × Length`
2. Determine minimum gauge where `Vdrop ≤ 0.05 × Vsystem`
3. Use wire resistance values from Aeroelectric Connection reference materials
4. Verify gauge also meets current-carrying capacity (ampacity) per Aeroelectric Connection tables
5. Select minimum gauge that satisfies both constraints

**Result**:
- Minimum required gauge (e.g., "18.7 AWG calculated")
- Round up to next standard AWG size (e.g., 18 AWG selected)
- Document both calculated and selected values in engineering mode

### 3.3 Wire Color Assignment

**Method**: Auto-assign based on system code using standard mapping from EAWMS/Aeroelectric Connection documentation.

**Override**: Component/net `Wire_Color` field takes precedence over auto-assignment.

**Fallback**: If system code unmapped, flag warning and assign default color (white or user-specified in config).

**Color Mapping Source**: Extract from `docs/ea_wire_marking_standard.md` and/or Aeroelectric Connection reference materials.

### 3.4 Wire Label Generation (EAWMS Format)

**Format**: `SYSTEM-CIRCUIT-SEGMENT`

**Example**: `L-105-A`
- `L` = Lighting system
- `105` = Circuit 105
- `A` = First segment

**Component Extraction**:
- **System Code**: Letter extracted from net name or `System_Code` field
- **Circuit Number**: Numeric portion extracted from net name or `Circuit_ID` field
- **Segment Letter**: Sequential A, B, C... ordered by signal flow from source to load

**Multi-segment Circuits**:
For circuits with multiple physical wire runs:
- First segment: `-A`
- Second segment: `-B`
- And so on...

---

## 4. Validation and Error Handling

### 4.1 Operating Modes

**Strict Mode** (default):
- Error and abort on missing required fields (FS/WL/BL, Load/Rating)
- Ensures complete, validated schematics
- Recommended for final BOMs

**Permissive Mode** (`--permissive` flag):
- Use defaults with warnings for missing data
- Missing coordinates: Default to origin (0, 0, 0) with warning
- Missing Load/Rating: Default to 0A with warning
- Continue processing and generate BOM with warning annotations
- Useful for iterative design and draft BOMs

### 4.2 Validation Checks

#### 4.2.1 Required Field Validation

**In Strict Mode**:
- All components must have FS, WL, BL coordinates
- All components must have Load OR Rating value (not both, not neither)
- Error message identifies specific components missing data
- Abort processing with exit code 1

**In Permissive Mode**:
- Log warnings for missing fields
- Apply defaults
- Continue processing

#### 4.2.2 Wire Gauge Validation

If `Wire_Gauge` specified in schematic:
- Verify it meets or exceeds calculated minimum gauge
- **Action**: Warn if undersized, note in output warnings column
- Do not block BOM generation

#### 4.2.3 Rating vs Load Validation

- Trace circuit path from source through switches/breakers to load
- Verify no component rating is exceeded by downstream loads
- **Action**: Warn if load exceeds any rating in path
- Example: 15A load through 10A switch → Warning

#### 4.2.4 Wire Gauge Progression Validation

- Check that wire gauge doesn't inappropriately decrease along circuit path
- **Action**: Warn if downstream wire is heavier gauge than upstream
- This usually indicates a design error (heavier wire feeding lighter wire)

#### 4.2.5 Multi-node Net Detection

- Identify nets connecting 3+ components
- **Action**: Log informational message during processing
- Note in output that routing topology was inferred from coordinates
- Recommend designer review for accuracy

#### 4.2.6 Source/Load Identification

Attempt to identify signal flow using:
- Component type (J-designators, BAT prefix = sources)
- System knowledge (power system flows from battery/alternator)
- Load vs Rating fields

**Action**:
- If ambiguous, warn user
- Make best guess based on available information
- Continue processing
- Document assumption in engineering mode output

### 4.3 Error Output

All warnings and errors include:
- Component reference designator
- Net name
- Specific issue description
- Suggested correction (when applicable)

Format enables easy schematic correction by designer.

---

## 5. Output Formats and Modes

### 5.1 Output Formats

Two primary output formats:

1. **CSV** (default): Comma-separated values for spreadsheet import and manipulation
2. **Markdown** (`.md` extension or `--format md`): Rich formatted document with sections and tables

### 5.2 Output Filename Generation

**If destination not specified**:
- Extract base name from input file
- Append revision suffix: `_REVnnn` where nnn is incremented revision number
- Add format extension: `.csv` or `.md`
- Check directory for existing REVnnn files and increment to next available

**Example**:
- Input: `aircraft_electrical.net`
- Output: `aircraft_electrical_REV001.csv`
- Next run: `aircraft_electrical_REV002.csv`

### 5.3 Builder Mode (Default)

**Purpose**: Clean, actionable wire list for harness construction.

**CSV Columns**:
- Wire Label (EAWMS format)
- From (component-pin reference, e.g., "J1-1")
- To (component-pin reference, e.g., "SW1-2")
- Wire Gauge (AWG size, e.g., "20 AWG")
- Wire Color
- Length (inches)
- Wire Type (specification, e.g., "M22759/16")
- Warnings (validation issues, if any)

**Markdown Structure**:
- **Summary Section**:
  - Total wire count
  - Wire purchasing summary (total length needed by gauge/color combination)
- **Wire List Tables**:
  - Grouped by system code (L-circuits, P-circuits, etc.)
  - Sorted within each system by circuit number
- **Warnings/Notes Section**:
  - All validation warnings
  - Multi-node topology notes
  - Any assumptions made

### 5.4 Engineering Mode (`--engineering` flag)

**Purpose**: Detailed analysis for design review, validation, and documentation.

**Additional CSV Columns**:
- Calculated Min Gauge (e.g., "18.7 AWG")
- Current (amperes)
- Voltage Drop (volts)
- Voltage Drop (percentage)
- From Coordinates (FS/WL/BL)
- To Coordinates (FS/WL/BL)
- Calculated Length (before slack added)
- Component Load/Rating values

**Enhanced Markdown Structure**:

All builder mode sections, plus:

- **Component Validation Report**:
  - Table of all components with Load/Rating values
  - Component type identification
  - Coordinate listings
  - Missing data flagged

- **Detailed Calculations Section**:
  - Per-wire voltage drop analysis
  - Resistance calculations
  - Gauge selection rationale

- **Circuit Analysis**:
  - Power budget per system
  - Total current per system code
  - Circuit path traces

- **Validation Results**:
  - All warnings and recommendations
  - Rating vs load checks
  - Gauge progression analysis

- **Assumptions Documentation**:
  - Voltage drop percentage (5%)
  - Slack length (inches)
  - System voltage (volts)
  - Wire resistance values used
  - Ampacity tables referenced
  - Color mapping table
  - Multi-node topology assumptions

### 5.5 Output Sorting

All outputs sorted by:
1. System code (alphabetically: G, L, P, R, etc.)
2. Circuit number (numerically within each system)
3. Segment letter (A, B, C... within each circuit)

---

## 6. Command-Line Interface

### 6.1 Basic Usage

```bash
python -m kicad2wireBOM input.net output.csv
python -m kicad2wireBOM input.net output.md
python -m kicad2wireBOM input.net  # Auto-generates output_REV001.csv
```

### 6.2 Command-Line Arguments

**Required Arguments**:
- `source`: Path to KiCad netlist file (.net or .xml)

**Optional Arguments**:
- `dest`: Path to output file (if omitted, auto-generates with REVnnn suffix)
  - Extension determines format (.csv or .md)

### 6.3 Command-Line Flags

**Information Flags**:
- `--help`: Display usage information and exit
- `--version`: Display tool version and exit
- `--schematic-requirements`: Display documentation for schematic designers and exit

**Mode Flags**:
- `--permissive`: Enable permissive mode (use defaults for missing fields)
- `--engineering`: Enable engineering mode output (detailed calculations)

**Configuration Options**:
- `--system-voltage VOLTS`: System voltage for calculations (default: 12)
- `--slack-length INCHES`: Extra wire length per segment (default: 24)
- `--format {csv,md}`: Explicitly specify output format (overrides file extension)
- `--config FILE`: Path to configuration file (overrides default .kicad2wireBOM.yaml search)

### 6.4 Usage Examples

```bash
# Basic BOM generation (builder mode, CSV)
python -m kicad2wireBOM schematic.net wire_bom.csv

# Auto-generate filename with revision
python -m kicad2wireBOM schematic.net

# 14V system with custom slack
python -m kicad2wireBOM --system-voltage 14 --slack-length 30 schematic.net bom.csv

# Engineering mode markdown output
python -m kicad2wireBOM --engineering schematic.net analysis.md

# Permissive mode for incomplete schematic
python -m kicad2wireBOM --permissive draft.net draft_bom.csv

# Show what's needed in schematic
python -m kicad2wireBOM --schematic-requirements

# Use custom config file
python -m kicad2wireBOM --config my_project.yaml schematic.net
```

### 6.5 Exit Codes

- `0`: Success - BOM generated successfully
- `1`: Error - Missing required data (strict mode), file I/O error, parse error

---

## 7. Data Sources and Reference Materials

### 7.1 Wire Resistance Values

**Source**: Aeroelectric Connection Chapter 5
**Example**: 10 AWG = 1.0 milliohm per foot (from ae__page61.txt)

**Implementation**:
- Extract and tabulate resistance values for standard AWG sizes
- Sizes: 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2 AWG
- Store in `reference_data.py` as lookup table
- Format: `{awg_size: resistance_per_foot}`

**Task**: Implementation plan must include task to digitize resistance table from Aeroelectric Connection reference files.

### 7.2 Ampacity Tables

**Source**: Aeroelectric Connection simplified ampacity guidance
**Basis**: Practical application of MIL-W-5088L principles for experimental aircraft

**Implementation**:
- Digitize Bob Nuckolls' current-carrying capacity recommendations per AWG size
- Account for bundling/harnessing effects per Aeroelectric guidance
- Store in `reference_data.py` as lookup table
- Format: `{awg_size: max_amperes}`

**Task**: Implementation plan must include task to extract and validate ampacity values from Aeroelectric Connection.

### 7.3 System Code to Wire Color Mapping

**Source**: Extract from `docs/ea_wire_marking_standard.md` and/or Aeroelectric Connection

**Implementation**:
- Internal lookup table mapping system letter codes to standard wire colors
- Store in `reference_data.py`
- Format: `{system_code: color_name}`

**Examples** (to be verified against references):
- `L` (Lighting) → White
- `P` (Power) → Red
- `G` (Ground) → Black
- `R` (Radio/Nav) → Gray or Shielded
- [Additional mappings from standards]

**Task**: Implementation plan must include task to extract complete color mapping from EAWMS documentation.

### 7.4 System Codes

**Source**: `docs/ea_wire_marking_standard.md` (existing EAWMS documentation)

**Usage**:
- Validate system codes in net names
- Provide in `--schematic-requirements` output
- Map to wire colors

### 7.5 Voltage Drop Standards

**Value**: 5% maximum
- 0.6V for 12V system
- 0.7V for 14V system

**Source**: Common experimental aircraft practice per Aeroelectric Connection
**Justification**: Balance between wire weight and electrical performance

### 7.6 Test Validation Data

**File**: `data/example.xml`
**Description**: KiCad demo netlist from Sallen-Key filter circuit (from KiCad 9 documentation)

**Purpose**:
- Verify netlist parsing compatibility
- Field extraction testing
- Basic functionality validation

**Note**: NOT an EA schematic - does not contain custom fields. Tests must validate format compatibility only, not EA-specific logic.

**Additional Test Fixtures Needed**:
- Simple two-component EA circuit with full custom fields
- Multi-node circuit with 3+ components
- Circuit with missing fields (for permissive mode testing)
- Complex realistic EA electrical system

---

## 8. Implementation Architecture

### 8.1 Module Structure

The `kicad2wireBOM/` package contains 11 modules:

#### Module 1: `__main__.py` - CLI Entry Point

**Purpose**: Command-line interface and orchestration

**Functions**:
- `main()`: Entry point
  - Parse command-line arguments (argparse)
  - Handle special commands (--help, --version, --schematic-requirements)
  - Load optional configuration file
  - Auto-generate output filename if not provided
  - Determine output format from extension or --format flag
  - Orchestrate: parse → analyze → calculate → validate → output
  - Error handling and exit codes (0=success, 1=error)

- `generate_output_filename(input_path, format, output_dir)`:
  - Parse input filename
  - Find existing REVnnn files in directory
  - Increment to next revision number
  - Return new filename

- `load_config(config_path)`:
  - Search for `.kicad2wireBOM.yaml` or specified config file
  - Parse and validate configuration
  - Merge with defaults and CLI options (CLI takes precedence)

**Argument Parser**:
- Positional: `source`, `dest` (optional)
- Flags: `--help`, `--version`, `--schematic-requirements`, `--permissive`, `--engineering`
- Options: `--system-voltage`, `--slack-length`, `--format`, `--config`

---

#### Module 2: `parser.py` - Netlist Parsing

**Purpose**: Parse KiCad netlist and extract data

**Functions**:

- `parse_netlist_file(file_path)`:
  - Use kinparse library to parse KiCad netlist
  - Return raw parsed netlist object
  - Handle file not found, parse errors
  - Raise descriptive exceptions

- `extract_components(parsed_netlist)`:
  - Extract component list from parsed netlist
  - Parse custom fields: FS, WL, BL, Load, Rating, Wire_Type, Wire_Color, Wire_Gauge, Connector_Type
  - Create Component objects
  - Return list of Component objects
  - Handle missing/malformed fields gracefully (return None for missing)

- `extract_nets(parsed_netlist)`:
  - Extract net list with node connections
  - Parse optional net fields: Circuit_ID, System_Code
  - Return structured net data (name, code, nodes with ref/pin)
  - Return list of dicts: `{'name': str, 'code': str, 'nodes': [{'ref': str, 'pin': str}], 'circuit_id': str|None, 'system_code': str|None}`

- `parse_custom_field(component, field_name, field_type)`:
  - Helper to extract and type-convert custom fields
  - Handle various field name variations KiCad might use
  - Return typed value or None if field not present
  - Handle common format variations (e.g., "20 AWG" vs "20AWG" vs "20")

**Important Note**: Implementation plan must include experimental validation step to determine which field formats KiCad reliably exports. Test with actual KiCad v9 schematics.

---

#### Module 3: `component.py` - Component Data Model

**Purpose**: Component representation and type identification

**Classes**:

**Component** (dataclass):
  - **Required fields**:
    - `ref`: Reference designator (e.g., "J1", "SW2", "BAT1")
    - `fs`: Fuselage station (float, inches)
    - `wl`: Waterline (float, inches)
    - `bl`: Buttline (float, inches)

  - **Load/Rating** (mutually exclusive):
    - `load`: Current drawn (float, amps) - for consuming devices
    - `rating`: Current capacity (float, amps) - for pass-through devices

  - **Optional fields**:
    - `wire_type`: Wire specification string (e.g., "M22759/16")
    - `wire_color`: Override color string
    - `wire_gauge`: Specified gauge string (e.g., "20 AWG")
    - `connector_type`: Connector style/type string

  - **Derived properties**:
    - `coordinates` → tuple (fs, wl, bl)
    - `is_source` → bool (based on ref prefix, component type)
    - `is_load` → bool (has load value)
    - `is_passthrough` → bool (has rating value)
    - `component_role` → enum/string ("source", "load", "passthrough")

**Functions**:

- `identify_component_type(ref)`:
  - Determine if source, load, or passthrough based on reference designator
  - Sources: J (connectors), BAT (batteries), GEN (generators/alternators)
  - Passthrough: SW (switches), CB (circuit breakers), RELAY, FUSE
  - Loads: All others (LIGHT, RADIO, DISPLAY, MOTOR, etc.)
  - Return component role

- `validate_component(component, permissive)`:
  - Check required fields present (FS, WL, BL)
  - Verify load XOR rating (exactly one, not both, not neither)
  - Return list of validation errors/warnings
  - In permissive mode, generate warnings instead of errors

---

#### Module 4: `circuit.py` - Circuit Analysis

**Purpose**: Convert nets to circuits and analyze topology

**Classes**:

**Circuit**:
  - `net_name`: Original net name from KiCad
  - `system_code`: Extracted/specified system letter (e.g., "L")
  - `circuit_id`: Extracted/specified circuit number (e.g., "105")
  - `nodes`: List of (component, pin) tuples
  - `topology`: Topology type string ("simple", "star", "daisy")
  - `signal_flow`: Ordered list of nodes from source to load
  - `segments`: List of wire segments for this circuit

**Functions**:

- `build_circuits(nets, components)`:
  - Convert net dicts into Circuit objects
  - Link net nodes to Component objects by reference
  - Extract/parse system code and circuit ID
  - Return list of Circuit objects

- `detect_multi_node_topology(circuit)`:
  - Identify circuits with 3+ nodes
  - Analyze spatial coordinates to infer routing topology
  - Determine star (central hub) vs daisy-chain based on coordinate clustering
  - Return topology type string
  - Generate informational message for logging

- `determine_signal_flow(circuit, components)`:
  - Identify source component using:
    - `component.is_source` property
    - Reference prefix heuristics
    - System knowledge (power flows from battery/alternator)
  - Order nodes from source → intermediates → load
  - Return ordered node list
  - Generate warning if source ambiguous, make best guess

- `trace_circuit_path(circuit)`:
  - Follow circuit from source through switches/breakers to load
  - Build ordered list of components with roles
  - Return path as ordered list of (component, role) tuples
  - Used for rating validation and gauge progression checks

- `create_wire_segments(circuit)`:
  - Based on topology and signal flow, create wire segments
  - For simple 2-node: one segment
  - For multi-node: segments between adjacent ordered nodes
  - Assign segment letters (A, B, C...)
  - Return list of segment definitions

---

#### Module 5: `wire_calculator.py` - Wire Calculations

**Purpose**: Calculate wire specifications

**Functions**:

- `calculate_length(component1, component2, slack)`:
  - Manhattan distance formula: `|FS₁-FS₂| + |WL₁-WL₂| + |BL₁-BL₂|`
  - Add slack inches
  - Return total length in inches

- `calculate_voltage_drop(current, awg_size, length)`:
  - Lookup resistance per foot for AWG size (from reference_data)
  - Calculate: `Vdrop = current × resistance_per_foot × (length / 12)`
  - Return voltage drop in volts

- `determine_min_gauge(current, length, system_voltage, slack)`:
  - Calculate total length (with slack)
  - For each AWG size (from largest to smallest):
    - Calculate voltage drop
    - Check if Vdrop ≤ 5% of system_voltage
    - Check if current ≤ ampacity for this AWG
    - If both satisfied, return this AWG size
  - Return smallest AWG that meets both constraints
  - Also return calculated voltage drop and percentage

- `assign_wire_color(system_code, color_override=None)`:
  - If color_override provided, return it
  - Lookup system_code in SYSTEM_COLOR_MAP (from reference_data)
  - If not found, log warning and return default color (white)
  - Return color string

- `generate_wire_label(net_name, circuit_id, system_code, segment_letter)`:
  - If circuit_id provided, use it; otherwise parse from net_name
  - If system_code provided, use it; otherwise parse from net_name
  - Parse patterns like "Net-L105", "LANDING_LIGHT_L105", etc.
  - Format as: `{system_code}-{circuit_id}-{segment_letter}`
  - Example: "L-105-A"
  - Raise error if unable to parse and no overrides provided

- `round_to_standard_awg(calculated_gauge)`:
  - Given calculated minimum gauge (e.g., 18.7)
  - Round up to next standard AWG size from STANDARD_AWG_SIZES
  - Return standard AWG size
  - Example: 18.7 → 18 AWG

---

#### Module 6: `wire_bom.py` - Wire BOM Data Model

**Purpose**: Data structures for wire BOM

**Classes**:

**WireConnection** (dataclass):
  - **Core fields**:
    - `wire_label`: EAWMS format label (e.g., "L-105-A")
    - `from_ref`: Source component-pin (e.g., "J1-1")
    - `to_ref`: Destination component-pin (e.g., "SW1-2")
    - `wire_gauge`: Selected AWG size (e.g., "20 AWG")
    - `wire_color`: Assigned color
    - `length`: Total length in inches
    - `wire_type`: Wire specification (e.g., "M22759/16")

  - **Engineering fields** (for engineering mode):
    - `calculated_min_gauge`: Calculated minimum (e.g., "19.2 AWG")
    - `voltage_drop_volts`: Calculated drop in volts
    - `voltage_drop_percent`: Calculated drop as percentage
    - `current`: Circuit current in amps
    - `from_coords`: Tuple (FS, WL, BL)
    - `to_coords`: Tuple (FS, WL, BL)
    - `calculated_length`: Length before slack added

  - **Validation**:
    - `warnings`: List of warning strings

**WireBOM**:
  - `wires`: List of WireConnection objects
  - `config`: Dict of configuration used (system voltage, slack, etc.)
  - `components`: List of Component objects (for engineering mode reporting)

  - **Methods**:
    - `add_wire(wire)`: Append wire to list
    - `sort_by_system_code()`: Sort wires by system, circuit, segment
    - `get_wire_summary()`: Return purchasing summary dict {(gauge, color): total_length}
    - `get_validation_summary()`: Return all warnings/errors collected

---

#### Module 7: `output_csv.py` - CSV Output

**Purpose**: Generate CSV files

**Functions**:

- `write_builder_csv(bom, output_path)`:
  - Open CSV file for writing
  - Write header row with builder columns
  - For each wire in bom.wires:
    - Write row with: Wire Label, From, To, Wire Gauge, Wire Color, Length, Wire Type, Warnings
  - Close file

- `write_engineering_csv(bom, output_path)`:
  - Open CSV file for writing
  - Write header row with all columns (builder + engineering)
  - For each wire in bom.wires:
    - Write row with all fields including calculated values, coordinates, etc.
  - Close file

**Implementation**: Uses Python `csv.DictWriter` with appropriate fieldnames per mode.

**Column Order**:
- Builder: Label, From, To, Gauge, Color, Length, Type, Warnings
- Engineering: All builder columns + Min Gauge, Current, Vdrop (V), Vdrop (%), From Coords, To Coords, Calc Length, Component Load/Rating

---

#### Module 8: `output_markdown.py` - Markdown Output

**Purpose**: Generate formatted Markdown documents

**Functions**:

- `write_builder_markdown(bom, output_path)`:
  - Open markdown file for writing
  - Write title and summary section:
    - Total wire count
    - Wire purchasing summary table (gauge/color → total length)
  - Write wire list section:
    - Group by system code
    - Markdown table for each system
    - Sort by circuit number within system
  - Write warnings section:
    - List all warnings from bom
    - Note multi-node topology assumptions
  - Close file

- `write_engineering_markdown(bom, output_path, components, config)`:
  - Write all builder sections
  - Add component validation report:
    - Table of all components with coordinates, load/rating
    - Flag missing data
  - Add detailed calculations section:
    - Per-wire voltage drop analysis
    - Resistance calculations
    - Gauge selection rationale
  - Add circuit analysis section:
    - Power budget per system (total current per system code)
    - Circuit path traces
  - Add validation results section:
    - All warnings categorized
    - Rating vs load checks
    - Gauge progression analysis
  - Add assumptions documentation section:
    - Voltage drop % threshold
    - Slack length used
    - System voltage
    - Wire resistance values (reference table)
    - Ampacity table
    - Color mapping table
  - Close file

**Helper Functions**:
- `format_markdown_table(headers, rows)`: Generate markdown table string
- `format_component_table(components)`: Format component list as table
- `format_wire_summary(summary_dict)`: Format purchasing summary as table
- `format_validation_warnings(warnings)`: Group and format warnings

---

#### Module 9: `reference_data.py` - Reference Tables

**Purpose**: Store reference data and constants

**Data Structures**:

- **WIRE_RESISTANCE**: Dict `{awg: ohms_per_foot}`
  - Source: Extracted from Aeroelectric Connection Ch5
  - Example: `{10: 0.001, 12: 0.0016, 14: 0.0025, 16: 0.004, 18: 0.0064, 20: 0.010, 22: 0.016}`
  - Task: Digitize complete table from reference materials

- **WIRE_AMPACITY**: Dict `{awg: max_amps}`
  - Source: Aeroelectric Connection simplified ampacity tables
  - Example: `{22: 5, 20: 7.5, 18: 10, 16: 13, 14: 17, 12: 23, 10: 33, 8: 46}`
  - Task: Extract from Aeroelectric Connection

- **SYSTEM_COLOR_MAP**: Dict `{system_code: color_name}`
  - Source: Extracted from EAWMS/Aeroelectric Connection
  - Example: `{'L': 'White', 'P': 'Red', 'G': 'Black', 'R': 'Gray', ...}`
  - Task: Extract complete mapping from ea_wire_marking_standard.md

- **STANDARD_AWG_SIZES**: List `[22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]`
  - Common AWG sizes for aircraft wiring

- **DEFAULT_CONFIG**: Dict with default values
  - `system_voltage`: 12 (volts)
  - `slack_length`: 24 (inches)
  - `voltage_drop_percent`: 0.05 (5%)
  - `permissive_mode`: False
  - `engineering_mode`: False

**Functions**:
- `load_custom_resistance_table(config_dict)`: Override WIRE_RESISTANCE from config
- `load_custom_ampacity_table(config_dict)`: Override WIRE_AMPACITY from config
- `load_custom_color_map(config_dict)`: Override SYSTEM_COLOR_MAP from config

---

#### Module 10: `validator.py` - Validation Logic

**Purpose**: Validation checks and warning generation

**Classes**:

**ValidationResult**:
  - `component_ref`: Component reference or net name
  - `net_name`: Net name (if applicable)
  - `severity`: "error" or "warning"
  - `message`: Description of issue
  - `suggestion`: Recommended correction (optional)

**Functions**:

- `validate_required_fields(components, permissive_mode)`:
  - For each component:
    - Check FS, WL, BL present (not None)
    - Check Load OR Rating present (XOR)
  - In strict mode: Return errors for missing fields
  - In permissive mode: Return warnings for missing fields
  - Return list of ValidationResult objects

- `validate_wire_gauge(wire, calculated_min_gauge)`:
  - If wire.wire_gauge specified:
    - Parse AWG size from string
    - Compare to calculated_min_gauge
    - If specified < calculated: Create warning
  - Return ValidationResult or None

- `validate_rating_vs_load(circuit_path)`:
  - Trace path from source to load
  - For each passthrough component (has rating):
    - Check that downstream load ≤ rating
    - If exceeded: Create warning with details
  - Return list of ValidationResult objects

- `validate_gauge_progression(circuit_path, wire_segments)`:
  - For each adjacent pair of wire segments in path:
    - Compare AWG sizes
    - If downstream wire is heavier than upstream: Create warning
    - (Lower AWG number = heavier wire, e.g., 16 AWG > 20 AWG)
  - Return list of ValidationResult objects

- `collect_all_warnings(bom, circuits, components, permissive)`:
  - Run all validation checks
  - Collect ValidationResult objects
  - Attach relevant warnings to wire objects
  - Return summary of all issues

---

#### Module 11: `schematic_help.py` - Requirements Documentation

**Purpose**: Generate `--schematic-requirements` output

**Functions**:

- `print_schematic_requirements(config)`:
  - Print formatted documentation to stdout
  - Sections:

    1. **Required Custom Fields**:
       - FS, WL, BL: Descriptions, units, examples
       - Load/Rating: Explanation of difference, when to use each

    2. **Optional Custom Fields**:
       - Wire_Type, Wire_Color, Wire_Gauge, Circuit_ID, System_Code, Connector_Type
       - Purpose and format for each

    3. **Net Naming Convention**:
       - Preferred format: `Net-L105`
       - Alternative formats accepted
       - Examples: `Net-L105`, `Net-P12`, `Net-R200`

    4. **System Codes**:
       - Table of system codes with descriptions
       - Extracted from EAWMS documentation
       - Example: L=Lighting, P=Power, G=Ground, R=Radio, etc.

    5. **Wire Color Mapping**:
       - Table showing system code → color assignments
       - Note that colors can be overridden per component/net

    6. **Connector Types**:
       - List of valid/recommended connector type values
       - Examples: D-Sub, Molex, Deutsch, etc.

    7. **Load vs Rating Explanation**:
       - Load: Current drawn by device (lights, radios, motors)
       - Rating: Current capacity of device (switches, breakers, connectors)
       - Examples of each type

    8. **Tool Assumptions**:
       - Voltage drop threshold: 5% (configurable)
       - Slack length: 24" (configurable)
       - System voltage: 12V (configurable)
       - Length calculation method: Manhattan distance
       - Wire resistance/ampacity sources

    9. **Complete Example**:
       - Show sample KiCad component with all fields filled out
       - Annotated to explain each field

    10. **Field Export Verification**:
        - Reminder to verify KiCad exports custom fields to netlist
        - Suggest testing with example schematic
        - Note that field names may need adjustment based on KiCad version

**Implementation**: Uses data from `reference_data.py` and `config` to populate tables and examples.

---

### 8.2 Test Structure

**Test Directory**: `tests/`

**Test Files**:
- `test_parser.py`: Netlist parsing, field extraction
- `test_component.py`: Component model, validation, type identification
- `test_circuit.py`: Circuit analysis, topology detection, signal flow
- `test_wire_calculator.py`: Length, voltage drop, gauge calculations
- `test_wire_bom.py`: Wire BOM data model
- `test_output_csv.py`: CSV generation in both modes
- `test_output_markdown.py`: Markdown generation
- `test_validator.py`: All validation checks
- `test_integration.py`: End-to-end tests with complete netlists
- `test_cli.py`: Command-line interface, argument parsing, file generation

**Test Fixtures** (in `tests/fixtures/`):
- `example.xml`: KiCad demo (format compatibility only)
- `simple_two_component.net`: Minimal EA circuit with full fields
- `multi_node_circuit.net`: 3+ component circuit for topology testing
- `missing_fields.net`: Components with missing data (permissive mode testing)
- `realistic_ea_system.net`: Complete aircraft electrical system for integration testing
- `invalid_net_names.net`: Test net name parsing edge cases
- Expected output files for comparison

**Test Strategy**:
- Unit tests for each module function
- Integration tests for complete workflows
- Fixture-based testing with known good inputs/outputs
- Validate calculations against hand-calculated examples
- Test both strict and permissive modes
- Test both builder and engineering output modes
- Test edge cases: missing fields, multi-node, ambiguous flow, etc.

**Important**: Tests must be written against `data/example.xml` to verify KiCad netlist format compatibility, even though it lacks EA-specific fields.

---

### 8.3 Dependencies

**Required**:
- `kinparse`: KiCad netlist parsing library
- `pytest`: Testing framework
- `PyYAML` or `json`: Configuration file parsing (YAML recommended for readability)

**Standard Library**:
- `argparse`: Command-line argument parsing
- `csv`: CSV file generation
- `pathlib`: File path handling
- `dataclasses`: Data model definitions
- `typing`: Type hints
- `re`: Regular expression parsing (net names, field formats)
- `glob`: File pattern matching (for REVnnn detection)

---

## 9. Special Considerations

### 9.1 Ground/Return Path Handling

**Requirement**: All circuits must have explicit return wires specified in schematic.

**Rationale**:
- No assumptions about airframe return paths
- Composite airplanes require discrete ground wires
- Even metal airplanes benefit from explicit ground wire sizing and documentation
- Ensures proper voltage drop calculations for complete circuit

**Implementation**:
- Tool treats ground nets like any other net
- Calculate wire gauge for ground returns same as power wires
- GND/ground system code may map to specific color (black)

**Validation**:
- No special handling needed
- If designer omits ground in schematic, BOM will be incomplete (as it should be)

### 9.2 Multi-Node Net Topology Detection

**Challenge**: When a net connects 3+ components, determine physical wire routing.

**Approach**:
1. Analyze component coordinates (FS/WL/BL)
2. Detect topology type:
   - **Star**: Components cluster around one central point (hub)
   - **Daisy-chain**: Components form linear sequence
3. For star: Create segments from hub to each spoke
4. For daisy-chain: Create segments between adjacent components in spatial order
5. Log informational message that topology was inferred
6. Note in output for designer review

**Important**: Tool makes best guess but notes assumption. Designer should verify routing makes sense.

### 9.3 Component Type Heuristics

**Source Identification**:
- Reference prefix: J, BAT, GEN, ALT → source
- Component type: Connectors, batteries, generators/alternators
- System knowledge: Power system sources are batteries/alternators

**Load Identification**:
- Has `Load` field populated → load
- Reference prefix: LIGHT, RADIO, DISPLAY, MOTOR, PUMP → load

**Passthrough Identification**:
- Has `Rating` field populated → passthrough
- Reference prefix: SW, CB, RELAY, FUSE → passthrough

**Ambiguity Handling**:
- If cannot determine: Warn, make best guess based on available information
- Prefer field data (Load/Rating) over heuristics
- Document assumption in engineering mode

### 9.4 AWG Size Standardization

**Standard Sizes**: 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2 AWG

**Rounding**: Always round UP to next standard size when calculated minimum is between sizes.

**Example**:
- Calculated minimum: 18.7 AWG
- Selected size: 18 AWG (next standard size that meets requirement)

**Special Cases**:
- If calculated minimum is smaller than 22 AWG: Use 22 AWG (smallest standard size)
- If calculated minimum is larger than 2 AWG: Flag warning, may need parallel wires or bus bar

### 9.5 Configuration File Format

**File Name**: `.kicad2wireBOM.yaml` (or `.json`)

**Search Locations** (in order):
1. Path specified by `--config` flag
2. Current working directory
3. Same directory as input netlist file
4. User home directory

**Example YAML Structure**:
```yaml
# kicad2wireBOM Configuration File

system_voltage: 14  # volts (override default 12V)
slack_length: 30    # inches (override default 24")

# Custom wire resistance table (ohms per foot)
wire_resistance:
  22: 0.016
  20: 0.010
  18: 0.0064
  # ... etc

# Custom ampacity table (max amps)
wire_ampacity:
  22: 5
  20: 7.5
  18: 10
  # ... etc

# Custom system code to color mapping
system_colors:
  L: White
  P: Red
  G: Black
  R: Shielded Gray
  # ... etc

# Default output mode
permissive_mode: false
engineering_mode: false
```

**Validation**: Tool validates config file structure and data types, warns on invalid entries.

---

## 10. Implementation Approach

### 10.1 Development Methodology

**Test-Driven Development (TDD)**:
- Write failing test first (RED)
- Write minimal code to pass test (GREEN)
- Refactor while keeping tests green (REFACTOR)
- Commit after each passing test

**YAGNI (You Aren't Gonna Need It)**:
- Only implement features needed now
- Don't add speculative features
- Keep code simple and focused

**DRY (Don't Repeat Yourself)**:
- Refactor duplication AFTER tests pass
- Extract common patterns into functions
- Maintain clean, maintainable code

### 10.2 Implementation Phases

The implementation plan document will break this design into concrete tasks following this sequence:

**Phase 1: Foundation**
- Project setup, dependencies
- Netlist parsing with kinparse
- Component data model
- Basic tests

**Phase 2: Core Calculations**
- Wire length calculation (Manhattan distance)
- Voltage drop and gauge calculation
- Reference data extraction from Aeroelectric Connection
- Wire color assignment
- EAWMS label generation

**Phase 3: Circuit Analysis**
- Net to circuit conversion
- Topology detection
- Signal flow determination
- Wire segment creation

**Phase 4: Validation**
- Required field validation
- Wire gauge validation
- Rating vs load validation
- Gauge progression validation
- Permissive mode handling

**Phase 5: Output Generation**
- CSV output (builder and engineering modes)
- Markdown output (both modes)
- Output filename generation with revisions

**Phase 6: CLI and Integration**
- Command-line interface
- Configuration file loading
- Schematic requirements documentation
- End-to-end integration tests

**Phase 7: Documentation and Polish**
- User documentation
- Code comments
- Example schematics
- Final testing

### 10.3 Critical Tasks

**KiCad Field Export Validation**:
- MUST create test KiCad schematic with custom fields
- Export netlist and verify fields appear in parsed data
- Determine exact field name formats KiCad uses
- May need to adjust parser based on findings
- Document findings in implementation plan

**Reference Data Extraction**:
- Digitize wire resistance table from Aeroelectric Connection
- Digitize ampacity table from Aeroelectric Connection
- Extract system code color mapping from EAWMS documentation
- Validate values against multiple sources
- Document sources for each data point

**Test Fixture Creation**:
- Create realistic EA electrical system test schematic in KiCad
- Export as netlist fixture
- Use for integration testing
- Include various scenarios: simple, multi-node, edge cases

---

## 11. Success Criteria

The design is considered successfully implemented when:

- ✅ All unit tests pass
- ✅ Integration tests pass with realistic EA system fixtures
- ✅ Tool processes KiCad netlists and produces valid CSV/Markdown output
- ✅ Wire labels follow EAWMS format (SYSTEM-CIRCUIT-SEGMENT)
- ✅ Wire gauge calculations are correct (validated against hand calculations)
- ✅ Wire length calculations use Manhattan distance + slack correctly
- ✅ Voltage drop calculations stay within 5% threshold
- ✅ Both builder and engineering modes produce correct output
- ✅ Strict and permissive modes work as specified
- ✅ `--schematic-requirements` provides complete documentation
- ✅ Auto-generated filenames use REVnnn format correctly
- ✅ Configuration file loading works
- ✅ Multi-node topology detection and signal flow work reasonably
- ✅ All validation checks produce appropriate warnings
- ✅ Code follows project standards (TDD, YAGNI, DRY)
- ✅ Documentation is complete and accurate

---

## 12. Future Enhancements (Out of Scope)

These features are NOT part of this design but may be considered later:

1. **GUI Interface**: Graphical tool for non-CLI users
2. **KiCad Plugin**: Direct integration with KiCad schematic editor
3. **Interactive Mode**: Prompt user for missing fields during processing
4. **BOM Comparison**: Compare revisions, highlight changes
5. **Auto-populate from Database**: Look up component loads from part number database
6. **3D Visualization**: Show wire routing in 3D aircraft model
7. **Cost Estimation**: Calculate wire costs from supplier pricing
8. **Weight Calculation**: Estimate harness weight for W&B
9. **Length from PCB Coordinates**: Use actual component placement if available
10. **Multiple Netlist Support**: Process entire KiCad project at once
11. **Export to Other Formats**: Excel, PDF, CAD formats
12. **Temperature Derating**: Adjust ampacity for high-temperature environments

---

## 13. Acronyms and Terminology

**Acronyms**:
- **AWG**: American Wire Gauge - wire sizing standard
- **BL**: Buttline - lateral aircraft coordinate (inches from centerline)
- **BOM**: Bill of Materials
- **EAWMS**: Experimental Aircraft Wire Marking Standard
- **FS**: Fuselage Station - longitudinal aircraft coordinate (inches from datum)
- **TDD**: Test-Driven Development
- **WL**: Waterline - vertical aircraft coordinate (inches from datum)
- **YAGNI**: You Aren't Gonna Need It

**Terminology**:
- **Ampacity**: Current-carrying capacity of a wire
- **Load**: Current drawn by a consuming device
- **Manhattan Distance**: Sum of absolute differences in each axis (taxicab metric)
- **Net**: Electrical connection in a schematic
- **Netlist**: File describing all connections in a schematic
- **Node**: Connection point (component pin) in a net
- **Rating**: Maximum current capacity of a pass-through device
- **Segment**: Individual physical wire run within a circuit
- **Signal Flow**: Direction of electrical current from source to load
- **System Code**: Single-letter identifier for circuit function (L, P, R, etc.)
- **Topology**: Physical routing arrangement (star, daisy-chain, etc.)

---

## 14. References

1. **MIL-W-5088L**: Military Specification - Wiring, Aerospace Vehicle
   Location: `docs/references/milspecs/MIL-STD-5088L.txt`

2. **Aeroelectric Connection**: Bob Nuckolls' practical guide to aircraft electrical systems
   Location: `docs/references/aeroelectric_connection/`
   Key chapters: Ch5 (grounding, wire sizing, voltage drop), Ch8 (wire marking)

3. **EA Wire Marking Standard**: Project-specific EAWMS documentation
   Location: `docs/ea_wire_marking_standard.md`

4. **KiCad Documentation**: KiCad v9 netlist format reference
   Test file: `data/example.xml`

5. **kinparse Library**: Python library for parsing KiCad netlists
   PyPI: https://pypi.org/project/kinparse/

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-15 | Claude (Architect) | Initial design specification based on requirements discussion with Tom |

---

**Next Steps**:
1. Review and approve this design document
2. Create detailed implementation plan based on this design
3. Begin Phase 1 implementation (Foundation)
