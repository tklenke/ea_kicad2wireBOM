# Work Package 09: Markdown Output

## Overview

**Module:** `kicad2wireBOM/output_markdown.py`

**Purpose:** Generate formatted Markdown documents from WireBOM.

**Dependencies:** wire_bom.py, component.py

**Estimated Effort:** 8-10 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 9: output_markdown.py"

**Key Functions:**
- `write_builder_markdown(bom, output_path)`
- `write_engineering_markdown(bom, output_path, components, config)`
- Helper functions for table formatting

---

## Key Tasks

### Task 9.1: Implement format_markdown_table Helper (1 hour)

**Purpose:** Generate markdown table string from headers and rows.

**Tests:**
- Generate valid markdown table
- Handle empty rows
- Align columns correctly
- Escape pipe characters in content

**Example Output:**
```markdown
| Wire Label | From | To |
|------------|------|-----|
| L-105-A    | J1-1 | SW1-2 |
```

### Task 9.2: Implement write_builder_markdown (3 hours)

**Sections:**
1. **Title and Summary**
   - Total wire count
   - Date generated
2. **Wire Purchasing Summary**
   - Table: Gauge | Color | Total Length
   - Sorted by gauge
3. **Wire List by System**
   - Group by system code
   - Table for each system
   - Sort by circuit number
4. **Warnings/Notes**
   - List all warnings
   - Multi-node topology notes

**Tests:**
- All sections present
- Tables formatted correctly
- Wires grouped by system
- Warnings listed

### Task 9.3: Implement write_engineering_markdown (4 hours)

**Additional Sections:**
1. **Component Validation Report**
   - Table: Ref | Type | FS | WL | BL | Load/Rating | Issues
2. **Detailed Calculations**
   - Per-wire voltage drop analysis
   - Resistance calculations shown
3. **Circuit Analysis**
   - Power budget per system
   - Total current per system code
4. **Validation Results**
   - All warnings categorized
   - Rating vs load checks
   - Gauge progression issues
5. **Assumptions Documentation**
   - Voltage drop threshold (5%)
   - Slack length (24")
   - System voltage (12V)
   - Wire resistance table
   - Ampacity table
   - Color mapping table

**Tests:**
- All sections present
- Tables formatted correctly
- Calculations shown clearly
- Reference data documented

### Task 9.4: Implement Helper Functions (1 hour)

**Functions:**
- `format_component_table(components)` - Component list as table
- `format_wire_summary(summary_dict)` - Purchasing summary table
- `format_validation_warnings(warnings)` - Group and format warnings

---

## Testing Checklist

- [ ] Markdown tables well-formed
- [ ] Builder mode creates readable report
- [ ] Engineering mode includes all sections
- [ ] Wires grouped by system correctly
- [ ] Purchasing summary calculates totals
- [ ] Reference data tables included in engineering mode
- [ ] Generated markdown renders correctly
- [ ] All tests pass

---

## Integration Notes

**Depends on:** wire_bom.py, component.py

**Used by:** CLI

---

## Estimated Timeline

~9 hours total

---

## Completion Criteria

- Both markdown modes work
- Generated markdown is well-formatted and readable
- All required sections present
- Module exports match interface contract
