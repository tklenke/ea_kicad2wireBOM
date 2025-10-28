# Engineering Report Enhancement - Markdown Tables

**Version**: 1.0
**Status**: Design Phase
**Date**: 2025-10-28
**Architect**: Claude

---

## 1. Overview

Enhance the engineering report from plain text to Markdown format with comprehensive tables for wire BOM, component BOM, and purchasing summaries.

### 1.1 Motivation

The current engineering_report.txt provides only high-level statistics. Builders need:
- Complete wire BOM in readable table format
- Complete component BOM in readable table format
- Purchasing summaries for wire procurement (by gauge + type)
- Purchasing summaries for component procurement (by value + datasheet)

### 1.2 Key Changes

1. **File format**: Change from `.txt` to `.md` (Markdown)
2. **Wire BOM Table**: Full wire details in Markdown table format
3. **Component BOM Table**: Full component details in Markdown table format
4. **Wire Purchasing Summary**: Total wire length grouped by gauge and type
5. **Component Purchasing Summary**: Component count grouped by value and datasheet

---

## 2. Requirements

### 2.1 Functional Requirements

**FR-1**: Generate Markdown (.md) file instead of plain text (.txt)
**FR-2**: Include Wire BOM table with all wire connection details
**FR-3**: Include Component BOM table with all component details
**FR-4**: Include Wire Purchasing Summary table (gauge, type, total length)
**FR-5**: Include Component Purchasing Summary table (value, datasheet, quantity)
**FR-6**: Include Wire Engineering Analysis table (voltage drop, ampacity, utilization, power loss)
**FR-7**: Preserve existing project information and summary statistics sections
**FR-8**: Tables must be valid Markdown with aligned columns

### 2.2 Non-Functional Requirements

**NFR-1**: Markdown must render correctly in GitHub, VS Code, and standard viewers
**NFR-2**: Tables should be human-readable in raw text format
**NFR-3**: File size should remain reasonable for large projects (100+ wires)

---

## 3. File Structure

### 3.1 Report Sections (in order)

```markdown
# Engineering Report
kicad2wireBOM Wire Harness Analysis

---

## Project Information
- **Project**: [title from schematic]
- **Revision**: [rev from schematic]
- **Issue Date**: [date from schematic]
- **Company**: [company from schematic]

---

## Overall Summary
- **Total Components**: 10
- **Total Wires**: 10
- **Total Wire Length**: 748.0 inches (62.3 feet)

---

## Wire Purchasing Summary
Total wire length needed by gauge and type for procurement.

| Wire Gauge | Wire Type   | Total Length (in) | Total Length (ft) |
|------------|-------------|------------------:|------------------:|
| 12 AWG     | M22759/16   |           384.0   |           32.0    |
| 18 AWG     | M22759/16   |           364.0   |           30.3    |
| **Total**  |             |       **748.0**   |       **62.3**    |

---

## Component Purchasing Summary
Component counts by value and datasheet for procurement.

| Value         | Datasheet   | Quantity | Example Refs       |
|---------------|-------------|----------|-------------------|
| Battery_Cell  | ~           | 1        | BT1               |
| Desc          | S700-1-2    | 2        | SW1, SW2          |
| Desc          |             | 1        | FH1               |
| ~             |             | 3        | L1, L2, L3        |
| **Total**     |             | **10**   |                   |

---

## Wire Engineering Analysis
Electrical calculations for voltage drop, ampacity utilization, and power loss.

| Wire Label | Current (A) | Gauge | Length (in) | Voltage Drop (V) | Vdrop % | Ampacity (A) | Utilization % | Resistance (Ω) | Power Loss (W) |
|------------|------------:|-------|------------:|-----------------:|--------:|-------------:|--------------:|---------------:|---------------:|
| G1A        | 10.0        | 18    | 33.0        | 0.22             | 1.5%    | 16           | 62.5%         | 0.0069         | 0.69           |
| G2A        | 10.0        | 18    | 134.0       | 0.88             | 6.3%    | 16           | 62.5%         | 0.0279         | 2.79           |
| L1A        | 10.0        | 18    | 37.0        | 0.24             | 1.7%    | 16           | 62.5%         | 0.0077         | 0.77           |
| L1B        | 10.0        | 18    | 31.0        | 0.20             | 1.4%    | 16           | 62.5%         | 0.0065         | 0.65           |
| L2A        | 14.0        | 12    | 39.0        | 0.14             | 1.0%    | 25           | 56.0%         | 0.0010         | 0.20           |
| P1A        | 40.0        | 12    | 43.0        | 0.22             | 1.6%    | 25           | **160%** ⚠️   | 0.0014         | 2.24           |
| **Total**  |             |       | **748.0**   | **3.02**         |         |              |               |                | **12.5**       |

**Summary**:
- **Total Power Loss**: 12.5 W (heat dissipated in wire harness)
- **Worst Voltage Drop**: G2A at 6.3% (exceeds 5% limit ⚠️)
- **Safety Warnings**: 1 wire exceeds ampacity rating (P1A at 160%)

**Notes**:
- Voltage drop % based on 14V system (12V nominal + charging)
- Utilization > 100% indicates wire undersized for circuit current
- Power loss calculated as I² × R for each wire segment

---

## Wire BOM
Complete wire bill of materials with all connections.

| Wire Label | From Component | From Pin | To Component | To Pin | Gauge | Color | Length (in) | Type      | Notes | Warnings |
|------------|----------------|----------|--------------|--------|-------|-------|-------------|-----------|-------|----------|
| G1A        | GND1           | 1        | L1           | 1      | 18    | Black | 33.0        | M22759/16 |       |          |
| G2A        | L2             | 2        | GND1         | 1      | 18    | Black | 134.0       | M22759/16 |       |          |
| ...        | ...            | ...      | ...          | ...    | ...   | ...   | ...         | ...       | ...   | ...      |

---

## Component BOM
Complete component bill of materials with electrical specifications.

| Reference | Value        | Description  | Datasheet | Type | Amps | FS   | WL   | BL    |
|-----------|--------------|--------------|-----------|------|------|------|------|-------|
| BT1       | Battery_Cell | Single-cell  | ~         | S    | 40.0 | 0.0  | 0.0  | 0.0   |
| FH1       | Desc         |              |           | R    | 20.0 | 5.0  | 10.0 | -4.0  |
| ...       | ...          | ...          | ...       | ...  | ...  | ...  | ...  | ...   |

---

## Component Summary by Type
Component count grouped by reference prefix.

- **Batteries (BT)**: 1
- **Switches (SW)**: 2
- **Lights (L)**: 3
- **Power Symbols (GND)**: 3

---

## Wire Summary by System
Wire count grouped by system code.

- **Ground (G)**: 4
- **Lighting (L)**: 5
- **Power (P)**: 1

---

*Generated by kicad2wireBOM*
```

---

## 4. Table Specifications

### 4.1 Wire BOM Table

**Columns** (11 total):
1. Wire Label - Circuit ID (e.g., "L1A")
2. From Component - Source component ref
3. From Pin - Source pin number
4. To Component - Destination component ref
5. To Pin - Destination pin number
6. Gauge - AWG wire size (e.g., "18")
7. Color - Wire color
8. Length (in) - Wire length in inches
9. Type - Wire type (e.g., "M22759/16")
10. Notes - Additional notes
11. Warnings - Warning messages

**Sorting**: By wire label (circuit ID) ascending

**Alignment**:
- Text columns: left-aligned
- Numeric columns (Length): right-aligned

### 4.2 Component BOM Table

**Columns** (9 total):
1. Reference - Component ref designator
2. Value - Component value field
3. Description - Component description
4. Datasheet - Datasheet URL or filename
5. Type - Component type (L/R/S)
6. Amps - Load/Rating/Source current
7. FS - Fuselage Station coordinate
8. WL - Water Line coordinate
9. BL - Butt Line coordinate

**Sorting**: By reference ascending

**Alignment**:
- Text columns: left-aligned
- Numeric columns (Amps, FS, WL, BL): right-aligned

### 4.3 Wire Purchasing Summary Table

**Columns** (4 total):
1. Wire Gauge - AWG size (e.g., "12 AWG")
2. Wire Type - Type designation (e.g., "M22759/16")
3. Total Length (in) - Sum of all wire lengths in inches
4. Total Length (ft) - Sum converted to feet (inches / 12)

**Grouping**: Group by (wire_gauge, wire_type), sum lengths
**Sorting**: By wire gauge ascending (numerically), then wire type
**Totals Row**: Add final row with totals across all gauges

**Calculation**:
```python
from collections import defaultdict

# Group wires by (gauge, type)
wire_groups = defaultdict(float)  # key: (gauge, type), value: total_length_inches

for wire in wires:
    key = (wire.wire_gauge, wire.wire_type)
    wire_groups[key] += wire.length

# Sort by gauge (numeric), then type
sorted_groups = sorted(wire_groups.items(),
                       key=lambda x: (int(x[0][0]), x[0][1]))

# Calculate totals
total_inches = sum(wire_groups.values())
total_feet = total_inches / 12.0
```

### 4.4 Wire Engineering Analysis Table

**Columns** (10 total):
1. Wire Label - Circuit ID (e.g., "L1A")
2. Current (A) - Circuit current (from circuit grouping)
3. Gauge - AWG wire size
4. Length (in) - Wire length in inches
5. Voltage Drop (V) - Calculated voltage drop
6. Vdrop % - Voltage drop as percentage of system voltage
7. Ampacity (A) - Maximum current rating for this gauge
8. Utilization % - (Current / Ampacity) × 100 - **CRITICAL SAFETY METRIC**
9. Resistance (Ω) - Total wire resistance (ohms)
10. Power Loss (W) - Power dissipated as heat (I² × R)

**Sorting**: By wire label (circuit ID) ascending

**Alignment**:
- Wire Label: left-aligned
- All numeric columns: right-aligned

**Calculations**:
```python
from kicad2wireBOM.reference_data import WIRE_RESISTANCE, WIRE_AMPACITY, DEFAULT_CONFIG
from kicad2wireBOM.wire_calculator import calculate_voltage_drop, group_wires_by_circuit, determine_circuit_current

# For each wire, calculate engineering data
system_voltage = DEFAULT_CONFIG['system_voltage']  # e.g., 14V

for wire in wires:
    # Get circuit current (group wires by circuit ID, sum loads)
    circuit_id = extract_circuit_id(wire.wire_label)  # e.g., "L1" from "L1A"
    circuit_current = circuit_currents[circuit_id]  # Pre-calculated

    # Voltage drop (already have function)
    vdrop_volts = calculate_voltage_drop(circuit_current, wire.wire_gauge, wire.length)
    vdrop_percent = (vdrop_volts / system_voltage) * 100.0

    # Ampacity utilization
    ampacity = WIRE_AMPACITY[wire.wire_gauge]
    utilization_percent = (circuit_current / ampacity) * 100.0

    # Resistance
    resistance_per_foot = WIRE_RESISTANCE[wire.wire_gauge]
    length_feet = wire.length / 12.0
    total_resistance = resistance_per_foot * length_feet

    # Power loss (I² × R)
    power_loss_watts = (circuit_current ** 2) * total_resistance
```

**Summary Calculations**:
```python
# Total power loss
total_power_loss = sum(power_loss for each wire)

# Worst voltage drop
worst_vdrop = max(vdrop_percent for each wire)
worst_vdrop_label = wire.wire_label with max vdrop_percent

# Safety warnings
overloaded_wires = [wire for wire in wires if utilization_percent > 100]
high_vdrop_wires = [wire for wire in wires if vdrop_percent > 5.0]
```

**Summary Section** (after table):
```markdown
**Summary**:
- **Total Power Loss**: 12.5 W (heat dissipated in wire harness)
- **Worst Voltage Drop**: G2A at 6.3% (exceeds 5% limit ⚠️)
- **Safety Warnings**: 1 wire exceeds ampacity rating (P1A at 160%)

**Notes**:
- Voltage drop % based on 14V system (12V nominal + charging)
- Utilization > 100% indicates wire undersized for circuit current
- Power loss calculated as I² × R for each wire segment
```

### 4.5 Component Purchasing Summary Table

**Columns** (4 total):
1. Value - Component value field
2. Datasheet - Datasheet URL or filename
3. Quantity - Count of components with this value+datasheet combination
4. Example Refs - Comma-separated list of component refs (max 3-5 examples)

**Grouping**: Group by (value, datasheet), count components
**Sorting**: By value, then datasheet
**Totals Row**: Add final row with total component count

**Calculation**:
```python
from collections import defaultdict

# Group components by (value, datasheet)
comp_groups = defaultdict(list)  # key: (value, datasheet), value: list of refs

for comp in components:
    key = (comp.value, comp.datasheet)
    comp_groups[key].append(comp.ref)

# Sort by value, then datasheet
sorted_groups = sorted(comp_groups.items(),
                       key=lambda x: (x[0][0], x[0][1]))

# Format example refs (limit to first 3-5)
for (value, datasheet), refs in sorted_groups:
    example_refs = ', '.join(sorted(refs)[:5])
    if len(refs) > 5:
        example_refs += f', ... ({len(refs)} total)'
```

---

## 5. Implementation Changes

### 5.1 Module Changes

**File**: `kicad2wireBOM/output_engineering_report.py`

**Changes**:
1. Rename function: `write_engineering_report()` (keep same signature for compatibility)
2. Change file extension in output_path from `.txt` to `.md`
3. Rewrite content generation to use Markdown format
4. Add `_format_markdown_table()` utility for table formatting
5. Add `_generate_wire_purchasing_summary()` helper function
6. Add `_generate_component_purchasing_summary()` helper function
7. Add `_calculate_circuit_currents()` helper function - group wires by circuit, determine current
8. Add `_generate_wire_engineering_analysis()` helper function - electrical calculations table
9. Add `_generate_engineering_summary()` helper function - safety warnings and totals
10. Add `_generate_wire_bom_table()` helper function
11. Add `_generate_component_bom_table()` helper function

### 5.2 CLI Changes

**File**: `kicad2wireBOM/__main__.py`

**Line 425** - Update filename:
```python
# OLD
write_engineering_report(components, bom.wires, str(output_dir / 'engineering_report.txt'), title_block)

# NEW
write_engineering_report(components, bom.wires, str(output_dir / 'engineering_report.md'), title_block)
```

### 5.3 HTML Index Changes

**File**: `kicad2wireBOM/output_html_index.py`

Update engineering report link to point to `.md` file:
```python
# OLD
<li><a href="engineering_report.txt">Engineering Report</a> - Technical analysis</li>

# NEW
<li><a href="engineering_report.md">Engineering Report</a> - Technical analysis</li>
```

### 5.4 Test Changes

**File**: `tests/test_output_engineering_report.py`

1. Update all test file paths from `.txt` to `.md`
2. Update assertions to check for Markdown format (headers with `#`, tables with `|`)
3. Add new tests for table formatting
4. Add new tests for purchasing summaries
5. Add new tests for wire engineering analysis calculations
6. Add new tests for engineering summary warnings

---

## 6. Markdown Table Formatting

### 6.1 Table Alignment Syntax

```markdown
| Left    | Center  | Right   |
|---------|:-------:|--------:|
| Text    | Text    | 123.45  |
```

- Default (left): `|---------|`
- Center: `|:-------:|`
- Right: `|--------:|`

### 6.2 Formatting Helper Function

```python
def _format_markdown_table(headers: List[str],
                           rows: List[List[str]],
                           alignments: List[str] = None) -> List[str]:
    """
    Format data as Markdown table.

    Args:
        headers: Column headers
        rows: Data rows (each row is list of cell values)
        alignments: List of 'left', 'center', 'right' for each column
                   Default: all left-aligned

    Returns:
        List of formatted table lines
    """
    if alignments is None:
        alignments = ['left'] * len(headers)

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    lines = []

    # Header row
    header_cells = [headers[i].ljust(col_widths[i]) for i in range(len(headers))]
    lines.append('| ' + ' | '.join(header_cells) + ' |')

    # Separator row with alignment
    sep_cells = []
    for i, align in enumerate(alignments):
        width = col_widths[i]
        if align == 'center':
            sep_cells.append(':' + '-' * (width - 2) + ':')
        elif align == 'right':
            sep_cells.append('-' * (width - 1) + ':')
        else:  # left
            sep_cells.append('-' * width)
    lines.append('| ' + ' | '.join(sep_cells) + ' |')

    # Data rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if alignments[i] == 'right':
                cells.append(cell_str.rjust(col_widths[i]))
            elif alignments[i] == 'center':
                cells.append(cell_str.center(col_widths[i]))
            else:
                cells.append(cell_str.ljust(col_widths[i]))
        lines.append('| ' + ' | '.join(cells) + ' |')

    return lines
```

---

## 7. Backward Compatibility

**Breaking Changes**:
- Output file extension changes from `.txt` to `.md`
- File content format changes from plain text to Markdown

**Migration**:
- Users relying on `.txt` extension will need to update references
- Markdown is still readable as plain text
- Most systems (GitHub, VS Code, browsers with extensions) render Markdown automatically

---

## 8. Testing Strategy

### 8.1 Unit Tests

1. Test Markdown header formatting
2. Test `_format_markdown_table()` with various alignments
3. Test Wire BOM table generation with sample data
4. Test Component BOM table generation with sample data
5. Test Wire Purchasing Summary calculation and formatting
6. Test Component Purchasing Summary calculation and formatting
7. Test Wire Engineering Analysis calculations (voltage drop, utilization, power loss)
8. Test Engineering Summary warnings (overload, high vdrop)
9. Test table alignment (left, center, right)
10. Test empty lists (no wires, no components)
11. Test special characters in values (commas, pipes, etc.)

### 8.2 Integration Tests

1. Generate engineering report from test_07 fixture
2. Verify `.md` file created
3. Verify all sections present
4. Verify tables render correctly in Markdown viewer
5. Verify Wire Engineering Analysis calculations are accurate
6. Verify safety warnings detected properly

---

## 9. Acceptance Criteria

Feature complete when:

1. ✅ Engineering report generated as `.md` file (not `.txt`)
2. ✅ Wire BOM table includes all wire details
3. ✅ Component BOM table includes all component details
4. ✅ Wire Purchasing Summary groups by gauge+type, sums lengths
5. ✅ Component Purchasing Summary groups by value+datasheet, counts components
6. ✅ Wire Engineering Analysis table calculates voltage drop, ampacity utilization, power loss
7. ✅ Engineering Summary identifies safety warnings (overload >100%, high vdrop >5%)
8. ✅ Tables use proper Markdown syntax with alignment
9. ✅ Tables render correctly in GitHub and VS Code
10. ✅ All existing tests updated and passing
11. ✅ New tests for table generation and calculations passing
12. ✅ HTML index updated to link to `.md` file

---

## 10. Example Output

See Section 3.1 for complete example of enhanced engineering report.

---

## 11. Future Enhancements

Deferred for later:
- HTML table output option (in addition to Markdown)
- Excel/XLSX export with formatted tables
- PDF generation with professional styling
- Charts/graphs for wire gauge distribution
- Cost estimation in purchasing summaries
