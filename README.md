# kicad2wireBOM

A wire Bill of Materials (BOM) generator for experimental aircraft electrical systems. Converts KiCad schematic files to comprehensive wire BOMs with automated gauge calculation, wire routing diagrams, and engineering analysis.

## Project Overview

**kicad2wireBOM** automates the tedious and error-prone task of creating wire harness BOMs from electrical schematics. Designed specifically for experimental aircraft builders, it parses KiCad schematic files at the wire segment level (not the net level), preserving the physical wire granularity required for accurate harness construction and regulatory compliance.

### Who Is This For?

Experimental aircraft builders who:
- Use KiCad for electrical system design
- Need accurate wire harness BOMs for construction
- Want automated wire gauge calculations and voltage drop analysis
- Need visual routing diagrams for harness installation

### What Problem Does It Solve?

Traditional EDA tools work with **electrical nets** (consolidated connectivity), but wire harness builders need **individual wire segments**. Two wires connecting to the same terminal are electrically one net, but they're physically two distinct wires requiring separate labels, lengths, gauges, and BOM entries.

kicad2wireBOM extracts wire segments directly from KiCad schematics before net consolidation, preserving the physical installation reality.

### Key Features

- **Wire-Level Parsing**: Extracts individual wire segments with their labels, not consolidated nets
- **Automated Gauge Calculation**: Circuit-based wire sizing using ampacity and voltage drop constraints
- **Length Calculation**: Manhattan distance using aircraft coordinates (FS/WL/BL)
- **Visual Routing Diagrams**: SVG system and component diagrams for build planning
- **Hierarchical Schematics**: Multi-sheet designs with cross-sheet wire tracing
- **3+Way Connections**: Proper handling of multipoint connections (common grounds, distribution points)
- **Engineering Analysis**: Voltage drop, ampacity utilization, power loss calculations
- **Component BOM**: Extracted component data with electrical specifications
- **Validation Framework**: Strict and permissive modes with clear error messages

## Standards & References

This tool implements industry-standard wire marking and electrical design practices:

- **[EAWMS](docs/ea_wire_marking_standard.md)** - Experimental Aircraft Wire Marking Standard (project-specific)
- **[Design Specification](docs/plans/kicad2wireBOM_design.md)** - Complete technical design (v3.7)
- **MIL-W-5088L** - Military Specification: Wiring, Aerospace Vehicle (Appendix B circuit codes)
- **MIL-STD-681E** - Identification Coding and Application of Hookup and Lead Wire
- **FAA AC 43.13-1B** - Acceptable Methods, Techniques, and Practices (Chapter 11: Electrical Systems)
- **Aeroelectric Connection** - Bob Nuckolls' practical guide to aircraft electrical systems

## Installation & Requirements

**Python Requirements**: Python 3.8 or higher

**Dependencies**: Listed in `requirements.txt`

**Installation**:

```bash
# Clone the repository
git clone https://github.com/yourusername/ea_tools.git
cd ea_tools

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m kicad2wireBOM --help
```

## Quick Start

Generate a complete wire BOM from your KiCad schematic:

```bash
# Basic usage - creates ./myproject/ with all outputs
python -m kicad2wireBOM myproject.kicad_sch

# Open the HTML index to view results
open myproject/myproject.html
```

**Output files generated**:
- HTML index page with links to all outputs
- Wire BOM (CSV)
- Component BOM (CSV)
- Engineering report (Markdown)
- SVG system routing diagrams (one per system)
- SVG component wiring diagrams (one per component, with Manhattan routing)
- SVG component star diagrams (one per component, radial layout)
- Console logs (stdout.txt, stderr.txt)

## Command Line Options

### Basic Syntax

```bash
python -m kicad2wireBOM [OPTIONS] SOURCE [DEST]
```

### Arguments

**SOURCE** (required)
Path to KiCad schematic file (`.kicad_sch`). Can be a hierarchical schematic with sub-sheets.

**DEST** (optional)
Parent directory for output. Defaults to current directory. Output files are created in `DEST/<basename>/` subdirectory.

### Options

#### Mode Flags

**`--permissive`**
Enable permissive mode. Uses defaults for missing data and continues processing with warnings. Default is strict mode, which aborts on validation errors.

Use permissive mode for:
- Incomplete schematics during iterative design
- Draft BOMs with missing data
- Preliminary analysis

Use strict mode (default) for:
- Final BOMs for construction
- FAA documentation
- Production harnesses

**`--3d`**
Generate 3D routing diagrams with WL (vertical) axis projection using elongated orthographic projection. Default is 2D diagrams showing only FS (fore/aft) and BL (left/right) axes.

#### Configuration Options

**`-f, --force`**
Force overwrite of existing output directory without prompting. Use with caution - deletes entire output directory.

**`--system-voltage VOLTS`**
System voltage for voltage drop calculations. Default: 14V (12V nominal + alternator charging). Common values:
- 14V: Single-engine piston aircraft (typical)
- 28V: Twin-engine or turbine aircraft

**`--slack-length INCHES`**
Extra wire length added to each segment for routing slack, strain relief, and termination. Default: 24 inches. Recommendations:
- 24": Standard for most installations
- 30-36": Long wire runs or complex routing
- 12-18": Short runs in tight spaces

**`--label-threshold MM`**
Maximum distance (millimeters) for associating labels with wire segments in the schematic. Default: 10mm. Increase if labels are far from wires; decrease to avoid misassociation.

### Usage Examples

```bash
# Basic BOM generation - creates ./aircraft/ with all outputs
python -m kicad2wireBOM aircraft.kicad_sch

# Specify output parent directory - creates /builds/aircraft/
python -m kicad2wireBOM aircraft.kicad_sch /builds/

# 28V system with custom slack for twin-engine aircraft
python -m kicad2wireBOM --system-voltage 28 --slack-length 30 aircraft.kicad_sch

# Permissive mode for incomplete schematic during design
python -m kicad2wireBOM --permissive draft.kicad_sch

# Force overwrite existing output (no prompt)
python -m kicad2wireBOM -f aircraft.kicad_sch

# Generate 3D diagrams showing vertical wire routing
python -m kicad2wireBOM --3d aircraft.kicad_sch

# Combination: 28V system, 3D diagrams, permissive mode
python -m kicad2wireBOM --system-voltage 28 --3d --permissive aircraft.kicad_sch
```

## Output Files

All outputs are generated in a dedicated directory: `<dest>/<basename>/`

### HTML Index (`<basename>.html`)

User-friendly entry point to all outputs with:
- Summary statistics (wire count, component count, systems)
- Links to all generated files
- Embedded console logs (stdout, stderr)
- Validation status
- Generation timestamp

**Use**: Open in web browser for quick overview and easy navigation to other files.

### Wire BOM (`wire_bom.csv`)

Complete wire harness BOM in CSV format with columns:
- **Wire Label**: EAWMS format (e.g., L-105-A)
- **From Component**: Source component reference (e.g., CB1)
- **From Pin**: Source pin number
- **To Component**: Destination component reference (e.g., SW1)
- **To Pin**: Destination pin number
- **Gauge**: Wire gauge in AWG (e.g., 20 AWG)
- **Color**: Wire insulation color per system code
- **Length**: Wire length in inches (Manhattan distance + slack)
- **Type**: Wire specification (e.g., M22759/16)
- **Notes**: Additional labels or comments from schematic
- **Warnings**: Validation warnings specific to this wire

**Use**: Primary document for harness construction. Import to spreadsheet for procurement, printing, or build tracking.

### Component BOM (`component_bom.csv`)

Complete component list with extracted schematic data:
- **Reference**: Component reference designator (e.g., CB1, SW2)
- **Value**: Component value (e.g., 10A Circuit Breaker)
- **Description**: Component description from schematic
- **Datasheet**: Datasheet URL or filename
- **Type**: Electrical role (Load, Rating, Source, Ground)
- **Amps**: Load current or rating capacity
- **FS, WL, BL**: Aircraft coordinates (Fuselage Station, Waterline, Buttline)

**Use**: Component procurement, installation planning, inventory management.

### Engineering Report (`engineering_report.md`)

Comprehensive Markdown document with:

1. **Project Information**: Schematic filename, generation date, system voltage
2. **Summary Statistics**: Wire counts by system, component counts by type, total wire length
3. **Wire Engineering Analysis Table**: Per-wire voltage drop, ampacity utilization, resistance, power loss with safety warnings
4. **Engineering Summary**: Worst-case voltage drop, highest ampacity utilization, safety flags (overload, excessive drop)
5. **Wire BOM Table**: Complete wire list with all details
6. **Component BOM Table**: Complete component list with specifications
7. **Wire Purchasing Summary**: Total length needed grouped by gauge+type for procurement
8. **Component Purchasing Summary**: Component counts grouped by value+datasheet

**Use**: Design review, safety validation, FAA documentation, engineering records, procurement planning.

### System Routing Diagrams (`<system>_System.svg`)

One SVG per system code (e.g., `L_System.svg` for Lighting, `P_System.svg` for Power) showing:
- All components in the system plotted by aircraft coordinates
- All wire segments with Manhattan routing (BL → FS → WL)
- Component and wire labels
- Professional title with expanded system name (e.g., "L - Lighting System")
- Print-optimized for 8.5×11 paper (portrait or landscape)

**2D Mode** (default): Shows FS (fore/aft) and BL (left/right) axes only - top-down view of aircraft.

**3D Mode** (`--3d` flag): Adds WL (vertical) axis using elongated orthographic projection - shows vertical wire routing through aircraft structure.

**Use**: Build planning, wire routing visualization, understanding system-wide connections, printed reference during harness construction.

### Component Wiring Diagrams (`<component>_Component.svg`)

One SVG per component (e.g., `SW1_Component.svg`, `LIGHT1_Component.svg`) showing:
- The component and its first-hop neighbors (direct connections)
- Wire segments connecting component to neighbors with Manhattan routing
- Component and wire labels
- Same 2D/3D projection modes as system diagrams

**Use**: Component installation reference with spatial layout, troubleshooting individual components, installation planning.

### Component Star Diagrams (`<component>_Star.svg`)

One SVG per component (e.g., `SW1_Star.svg`, `LIGHT1_Star.svg`) showing first-hop connections in radial/polar layout:
- **Center circle**: The component with reference, value, and description
- **Outer circles**: All directly connected components arranged in a ring
- **Connection lines**: Labeled with circuit IDs
- **Auto-sized circles**: Based on text content with wrapping for readability
- Portrait orientation optimized for printing

**Key Difference from Component Wiring Diagrams**: Star diagrams use a simplified radial layout (like spokes on a wheel) rather than Manhattan routing. No aircraft coordinates - just logical connectivity.

**Why Use Star Diagrams**: When schematics and routing diagrams become crowded with many components and wires, star diagrams provide clear, uncluttered wiring instructions. Each component's connections are shown in isolation without the visual complexity of the full system.

**Use Cases**:
- **Build instructions**: "What wires do I connect to SW1?" - instantly clear in star diagram
- **Crowded schematics**: When system diagram has 20+ components, star diagram isolates one component's connections
- **Troubleshooting**: Quickly verify all connections to a specific component without tracing through complex routing
- **Quality control**: Check off each connection during harness assembly

**Example**: `SW1_Star.svg` shows SW1 in center circle with CB1, LIGHT1, and LIGHT2 in outer circles, with lines labeled L1A, L1B, L2A connecting them.

### Console Logs

**`stdout.txt`**: Captured console output (info messages, progress, summaries)
**`stderr.txt`**: Captured error output (validation errors, warnings)

Both files are also embedded in the HTML index for easy review.

**Use**: Debugging, validation review, understanding what the tool did.

## Schematic Requirements

To generate an accurate wire BOM, your KiCad schematic must follow specific conventions. This section provides everything you need to prepare your schematic correctly.

### Required Component Custom Field: `LocLoad`

Every component that connects to wires must have a **LocLoad** custom field encoding its physical location and electrical characteristics.

#### Format

```
(FS,WL,BL)<TYPE><VALUE>
```

- **FS, WL, BL**: Aircraft coordinates in inches (decimals allowed, negatives for left side)
  - **FS** (Fuselage Station): Longitudinal position from datum (+forward, -aft)
  - **WL** (Waterline): Vertical position from datum (+up, -down)
  - **BL** (Buttline): Lateral position from centerline (+right, -left)
- **TYPE**: Single letter indicating electrical role
  - **L**: Load - component consumes power (lights, radios, motors)
  - **R**: Rating - pass-through device capacity (switches, breakers, connectors, fuses)
  - **S**: Source - power source (battery, alternator, generator)
  - **G**: Ground - ground connection point (value optional)
- **VALUE**: Numeric amperage (amps drawn for loads, amps capacity for ratings/sources)

#### Examples

```
(200.0,35.5,10.0)L2.5
  → Landing light at FS=200", WL=35.5", BL=10", drawing 2.5A

(150.0,30.0,0.0)R20
  → Landing light switch at FS=150", WL=30", BL=0" (centerline), rated 20A

(10,0,0)S40
  → Battery at FS=10", WL=0", BL=0", 40A capacity

(0,10,0)G
  → Ground point at FS=0", WL=10", BL=0" (no amperage needed)

(160.0,38.0,-10.5)L15
  → Nav radio at FS=160", WL=38", BL=-10.5" (left side), drawing 15A
```

#### How to Add LocLoad Field in KiCad

1. Select component in schematic
2. Press `E` (Edit Symbol Fields) or right-click → Properties
3. Click "Add Field"
4. Field Name: `LocLoad`
5. Field Value: Enter the formatted string (e.g., `(200,35,10)L2.5`)
6. Set "Show" checkbox if you want it visible on schematic
7. Click OK

#### Determining Component Type

**Load (L)**: Component consumes electrical power
- Lights, landing lights, position lights, panel lights
- Avionics (radios, transponders, GPS, autopilots)
- Instruments (flight instruments, engine monitors)
- Motors (flaps, trim, pumps)

**Rating (R)**: Pass-through device with current capacity limit
- Switches
- Circuit breakers
- Fuses
- Connectors
- Terminal blocks
- Relays/contactors (use rated contact current)

**Source (S)**: Provides electrical power
- Battery
- Alternator
- Generator
- External power connector

**Ground (G)**: Ground connection point
- Ground bus
- Ground lugs
- Airframe ground points
- Battery negative terminal (when used as ground reference)

### Required Wire Labels

Every wire segment in your schematic must have a label in **EAWMS (Experimental Aircraft Wire Marking Standard)** format.

#### Label Format

```
<SYSTEM><CIRCUIT><SEGMENT>
```

- **SYSTEM**: Single letter system code (see table below)
- **CIRCUIT**: Numeric circuit identifier (1-999, or 001-999 with leading zeros)
- **SEGMENT**: Single letter segment identifier (A, B, C, ...)

#### System Codes

Common system codes for experimental aircraft (per MIL-W-5088L Appendix B):

| Code | System | Example Circuits |
|------|--------|------------------|
| **A** | Avionics | GPS, autopilot, EFIS |
| **E** | Engine Instrument | EGT, CHT, oil pressure, tach |
| **F** | Flight Instrument | Airspeed, altimeter, VSI |
| **G** | Ground | Ground return paths |
| **K** | Engine Control | Magneto switches, starter |
| **L** | Lighting | Landing lights, nav lights, strobes, panel lights |
| **M** | Miscellaneous (Electrical) | Cigarette lighter, USB ports |
| **P** | DC Power | Main bus, battery, alternator distribution |
| **R** | Radio | COM, NAV radios, transponder |
| **U** | Miscellaneous (Electronic) | Antenna feeds, common leads |
| **V** | AC Power | AC alternator (rare in piston singles) |
| **W** | Warning | Annunciators, warning lights, stall warning |

See [ea_wire_marking_standard.md](docs/ea_wire_marking_standard.md) for complete system code list and usage guidance.

#### Segment Identifiers

When a circuit runs through multiple components, each physical wire segment gets a unique letter:

**Example**: Landing light circuit from bus → breaker → switch → light → ground

- **L105A**: Bus to circuit breaker
- **L105B**: Circuit breaker to switch
- **L105C**: Switch to landing light
- **L105D**: Landing light to ground

#### Label Examples

```
L1A          → Lighting system, circuit 1, segment A (compact format)
L-1-A        → Same (with dashes for readability)
P012B        → Power system, circuit 12, segment B
G1A          → Ground system, circuit 1, segment A
R5C          → Radio system, circuit 5, segment C
```

Both compact (`L1A`) and dashed (`L-1-A`) formats are accepted. Output format can be controlled via CLI flag (future feature).

#### How to Add Wire Labels in KiCad

1. Click "Label" tool or press `L`
2. Type wire label (e.g., `L1A`)
3. Place label near wire segment it identifies
4. Label must be within 10mm of wire (default threshold, configurable via `--label-threshold`)

**Important**: Place labels directly on wire segments, not on components or junctions.

### Circuit Grouping and Wire Gauge Calculation

All wire segments with the same circuit ID (e.g., L1A, L1B, L1C) are treated as **one circuit** for wire gauge calculation.

The tool:
1. Groups all wires by circuit ID
2. Sums all load currents in the circuit
3. Calculates wire gauge based on circuit total current
4. Applies the same gauge to ALL wires in the circuit

**Example**: Landing light circuit
- L105A (bus to breaker): No load on breaker, but carries 2.5A to the light downstream
- L105B (breaker to switch): No load on switch, but carries 2.5A to the light downstream
- L105C (switch to light): Connects to 2.5A load
- L105D (light to ground): Ground return carrying 2.5A

Result: All four wires (L105A, L105B, L105C, L105D) sized for 2.5A circuit current.

**Schematic Designer Control**: You control wire sizing by assigning circuit IDs. If two wires share a circuit ID, they'll have the same gauge. If they need different gauges, use different circuit IDs.

### 3+Way Connections (Multipoint Labeling)

When 3 or more component pins connect together (common grounds, distribution points), use the **(N-1) labeling rule**:

- **N pins** in the connection → **(N-1) labels** required
- Label the wire segments from branch pins toward the common pin
- Leave the common pin unlabeled

The tool automatically identifies the unlabeled pin as the common endpoint.

#### Example: 3-Way Ground Connection

```
Light1 ────G1A──── (junction) ────unlabeled──── BT1 (battery negative)
                       │
Light2 ────G2A─────────┘
```

- 3 pins: Light1, Light2, BT1
- 2 labels: G1A (Light1 side), G2A (Light2 side)
- Unlabeled: BT1 battery negative (common ground point)

BOM Output:
- G1A: Light1 → BT1
- G2A: Light2 → BT1

#### Example: 4-Way Power Distribution

```
FH1 ────unlabeled──── (J1) ────P5A──── CB1
                        │
                     P5B──── CB2
                        │
                     P5C──── CB3
```

- 4 pins: FH1 (fuse holder), CB1, CB2, CB3 (breakers)
- 3 labels: P5A, P5B, P5C
- Unlabeled: FH1 (common power source)

BOM Output:
- P5A: FH1 → CB1
- P5B: FH1 → CB2
- P5C: FH1 → CB3

### Hierarchical Schematics

kicad2wireBOM supports hierarchical designs (main sheet + sub-sheets):

- Main sheet: Power distribution, battery, alternator
- Sub-sheets: Lighting, Avionics, Engine, etc.

#### Requirements

1. **Hierarchical Sheet Symbols** on main sheet with sheet pins
2. **Hierarchical Labels** on sub-sheets matching sheet pin names
3. **Consistent component references** across all sheets (KiCad ensures this)

#### Cross-Sheet Circuits

Wire labels can change across sheet boundaries. The tool traces electrical connectivity through hierarchical pins/labels to identify which wires belong to the same circuit.

**Example**: Main sheet has L2A, lighting sub-sheet has L2B. If they're electrically connected through a hierarchical pin/label, the tool knows they're the same circuit L2 and sizes them together.

### Validation and Common Errors

kicad2wireBOM validates your schematic and reports clear, actionable errors. Understanding common validation issues helps you prepare compliant schematics.

#### Missing LocLoad Field

**Error**: `Component SW1 missing LocLoad field`

**Fix**: Add LocLoad custom field to component with format `(FS,WL,BL)<TYPE><VALUE>`

**Permissive Mode**: Uses default coordinates (-9, -9, -9) and 0A with warning.

#### Invalid LocLoad Format

**Error**: `Component SW1 has invalid LocLoad format: '200,35,10L2.5'`

**Fix**: LocLoad must start with parentheses: `(200,35,10)L2.5`

#### Missing Wire Label

**Error**: `Wire segment {uuid} has no circuit ID label`

**Fix**: Add label to wire in EAWMS format (e.g., L1A, P12B)

**Permissive Mode**: Generates fallback label (UNK1A, UNK2A, ...) with warning.

#### Duplicate Wire Labels

**Error**: `Duplicate circuit ID 'L1A' found on multiple wire segments`

**Fix**: Each wire must have unique label. Use different segment letters (L1A, L1B, L1C, ...).

**Permissive Mode**: Appends suffix (L1A, L1A-2, L1A-3) with warning.

#### Orphaned Labels

**Warning**: `Label 'L1A' at position (x, y) is not close to any wire segment`

**Fix**: Move label closer to wire (within 10mm default threshold) or check wire routing.

**Note**: This is always a warning, not an error (both modes).

#### 3+Way Connection Label Count Mismatch

**Error**: `3+way connection with 4 pins requires exactly 3 labels, found 2`

**Fix**: Add missing label to unlabeled branch wire, or remove extra label if one exists.

**Permissive Mode**: Warns and attempts best-effort tracing.

#### Unable to Determine Circuit Current

**Warning**: `Cannot determine circuit current for L5 - missing load/source data`

**Fix**: Add LocLoad field to at least one component in circuit L5 with load (L type) or source (S type).

**Result**: Wire gauge set to -99 with warning in BOM. You must manually specify gauge.

### Complete Schematic Checklist

Before running kicad2wireBOM, verify:

- [ ] Every component has LocLoad custom field
- [ ] LocLoad format is correct: `(FS,WL,BL)<TYPE><VALUE>`
- [ ] Component types (L/R/S/G) are correct for their role
- [ ] Amperage values are realistic and accurate
- [ ] Every wire segment has a label
- [ ] Wire labels follow EAWMS format: `<SYSTEM><CIRCUIT><SEGMENT>`
- [ ] No duplicate wire labels (each label unique)
- [ ] Labels are close to their wire segments (within 10mm)
- [ ] 3+way connections use (N-1) labeling rule
- [ ] Circuit IDs are consistent for wires that should share the same gauge
- [ ] Hierarchical pins/labels match between main and sub-sheets

## Error Handling & Validation

kicad2wireBOM includes a comprehensive validation framework with two operating modes:

### Validation Modes

#### Strict Mode (Default)

Aborts processing on validation errors. Ensures complete, validated schematics.

**Use for**:
- Final BOMs for construction
- FAA documentation
- Production harnesses

**Behavior**:
- Missing required data → Error and exit
- Invalid format → Error and exit
- Duplicate labels → Error and exit
- 3+way label mismatch → Error and exit

#### Permissive Mode (`--permissive` flag)

Continues processing with warnings and defaults for missing data.

**Use for**:
- Incomplete schematics during design iteration
- Draft BOMs with missing data
- Preliminary analysis

**Behavior**:
- Missing LocLoad → Default to (-9, -9, -9) and 0A with warning
- Missing label → Generate fallback (UNK1A, UNK2A, ...) with warning
- Duplicate labels → Append suffix (L1A, L1A-2, ...) with warning
- 3+way label mismatch → Warn and attempt best-effort tracing

### Error Messages

All errors include:
- Specific component reference or wire ID
- Clear description of the issue
- Suggested fix (when applicable)
- Schematic location (coordinates) for easy correction

**Example Error Messages**:

```
Error: Component SW1 missing LocLoad field
  → Add LocLoad custom field with format (FS,WL,BL)<TYPE><VALUE>

Error: Wire segment {uuid} has no circuit ID label
  → Add label to wire in schematic (e.g., L1A, P12B)

Error: Duplicate circuit ID 'L1A' found on multiple wire segments
  → Each wire must have unique label. Check segment letters.

Warning: Label 'L1A' at position (125.5, 67.3) is not close to any wire segment
  → Move label closer to wire or check wire routing
```

### Validation Checks

The tool performs these validation checks:

1. **Component Field Validation**
   - LocLoad field exists
   - LocLoad format valid
   - Coordinates are numeric
   - Type is L, R, S, or G
   - Amperage is numeric (when required)

2. **Wire Label Validation**
   - Every wire has a label
   - Labels match EAWMS format
   - No duplicate labels
   - Labels are within threshold distance of wires

3. **Connection Validation**
   - Wires connect to component pins (or trace through junctions to pins)
   - 3+way connections have (N-1) labels
   - Can identify common pin in multipoint connections

4. **Electrical Validation**
   - Can determine circuit current (at least one load or source in circuit)
   - Wire gauge meets ampacity constraint
   - Voltage drop within 5% limit
   - No overloaded wires (ampacity utilization ≤ 100%)

Validation results are shown in:
- Console output (stdout/stderr)
- HTML index (validation section)
- Engineering report (warnings and safety flags)
- Wire BOM (warnings column)

## Project Status

**Version**: 3.7 (Engineering Report Enhancement)
**Status**: Production-ready
**Test Coverage**: 326/326 tests passing
**Phases Complete**: 1-14 ✅

### Core Capabilities

- ✅ Wire BOM generation with circuit-based gauge calculation
- ✅ Hierarchical schematic support (main + sub-sheets)
- ✅ Validation framework (strict/permissive modes)
- ✅ SVG routing diagrams (system and component views, 2D/3D)
- ✅ Engineering report with Markdown tables and electrical analysis
- ✅ Component BOM generation
- ✅ HTML index with embedded console logs
- ✅ Unified output directory structure
- ✅ 3+way multipoint connection handling

### Documentation

- Complete design specification: [docs/plans/kicad2wireBOM_design.md](docs/plans/kicad2wireBOM_design.md)
- Wire marking standard: [docs/ea_wire_marking_standard.md](docs/ea_wire_marking_standard.md)
- Acronyms and terminology: [docs/acronyms.md](docs/acronyms.md)

## License

See [LICENSE](LICENSE) file for license details.
