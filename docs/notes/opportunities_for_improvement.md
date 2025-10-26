# Opportunities for Improvement (OFI)

This document tracks potential improvements to the ea_tools project that are not currently prioritized but may be valuable in the future.

## Wire Marking Standard

### Practical Implementation Tools

**Source:** Aeroelectric Connection Chapter 8, lines 1021-1024

**Description:** Bob Nuckolls recommends using Digi-Key rolls of narrow tape with digits 0-9 for marking wires. This is a practical, proven method used in experimental aircraft.

**Opportunity:**
- Research and document specific Digi-Key part numbers for wire marking tape
- Evaluate alternative wire marking products (heat-shrink sleeves, label makers, etc.)
- Create a recommended tooling list for wire marking implementation
- Consider cost/durability tradeoffs between different marking methods

**Priority:** Low - Current standard is complete without specific product recommendations

**Status:** Deferred

---

## kicad2wireBOM Features

### Optional Custom Net Fields (Circuit_ID and System_Code)

**Source:** kicad2wireBOM design discussion - removed via YAGNI principle

**Description:** Allow users to override parsed circuit ID and system code by adding custom fields directly to nets in KiCad schematic.

**Opportunity:**
- Add support for `Circuit_ID` custom field on nets to explicitly set circuit number (overrides parsing from net name)
- Add support for `System_Code` custom field on nets to explicitly set system letter (overrides parsing from net name)
- Useful when net naming conventions don't align with EAWMS requirements
- Provides explicit control for edge cases

**Example Use Case:**
- Net named "INSTRUMENT_PANEL_LIGHTS" could have Circuit_ID="105" and System_Code="L"
- Avoids need to rename net to "Net-L105" format

**Priority:** Low - Net name parsing should handle most cases

**Status:** Deferred - Removed from v1.0 design per YAGNI

---

### Project Configuration File Support

**Source:** kicad2wireBOM design discussion - removed via YAGNI principle

**Description:** Support project-specific configuration files (`.kicad2wireBOM.yaml` or `.kicad2wireBOM.json`) for persistent settings and customizations.

**Opportunity:**
- Custom wire resistance tables (for non-standard wire types)
- Custom ampacity tables (for different wire specs or temperature ratings)
- Custom color mappings (project-specific color schemes)
- Default system voltage (for 14V, 24V, or 28V systems)
- Default slack length (project-specific routing preferences)
- Per-project defaults reduce need for CLI flags on every run

**Configuration File Search Order:**
1. Path specified by `--config` flag
2. Current working directory
3. Same directory as input netlist file
4. User home directory

**Example YAML Structure:**
```yaml
system_voltage: 14  # volts
slack_length: 30    # inches
wire_resistance:
  22: 0.016
  20: 0.010
  # ...
system_colors:
  L: White
  P: Red
  # ...
```

**Priority:** Medium - Would improve user experience for repeated runs, but CLI flags sufficient for v1

**Status:** Deferred - CLI-only interface for v1.0, add config file support in future release

---

### Wire Specification Overrides

**Source:** kicad2wireBOM design specification Section 12

**Description:** Allow users to override calculated wire gauge, color, and type directly in the schematic for specific wires.

**Opportunity:**
- Add optional fields to footprint encoding: `WIRE_GAUGE`, `WIRE_COLOR`, `WIRE_TYPE`
- Parser validates overrides against calculated minimums (warn if undersized)
- Useful for design constraints:
  - Matching existing harness wire gauge
  - Project-specific color schemes
  - Special wire type requirements (shielded, high-temp, etc.)
- Tool calculates minimum safe values, user can override to larger if needed

**Example Use Case:**
- Calculated minimum is 20 AWG, but builder wants 18 AWG throughout for consistency
- Specific circuit requires shielded wire (WIRE_TYPE override)
- Color scheme differs from standard (WIRE_COLOR override)

**Priority:** Medium - Would add flexibility, but not essential for v1

**Status:** Deferred

---

### GUI Interface

**Source:** kicad2wireBOM design specification Section 12

**Description:** Graphical user interface for non-CLI users.

**Opportunity:**
- Desktop application or web interface
- Visual netlist validation
- Interactive error correction
- Preview output before generation
- Settings management

**Priority:** Low - CLI sufficient for target users (experimental aircraft builders)

**Status:** Deferred

---

### KiCad Plugin Integration

**Source:** kicad2wireBOM design specification Section 12

**Description:** Direct integration with KiCad schematic editor as a plugin.

**Opportunity:**
- Generate wire BOM directly from KiCad menu
- Real-time validation as schematic is edited
- Auto-populate component fields
- Highlight components with missing data
- Integrated with KiCad's BOM generation workflow

**Priority:** Medium - Would significantly improve user experience

**Status:** Deferred - Requires understanding KiCad plugin API

---

### Interactive Mode for Missing Data

**Source:** kicad2wireBOM design specification Section 12

**Description:** Prompt user interactively for missing fields during processing.

**Opportunity:**
- When missing FS/WL/BL coordinates, prompt user to enter values
- When missing Load/Rating, prompt for value
- Save entered values back to schematic (if possible)
- Allows processing incomplete schematics without returning to KiCad

**Priority:** Low - Permissive mode + schematic editing is cleaner workflow

**Status:** Deferred

---

### BOM Revision Comparison

**Source:** kicad2wireBOM design specification Section 12

**Description:** Compare two wire BOM revisions and highlight changes.

**Opportunity:**
- Compare REV001 vs REV002
- Show added/removed/modified wires
- Highlight gauge changes, length changes, routing changes
- Generate change report for documentation
- Useful for tracking design evolution and build updates

**Priority:** Medium - Very useful for iterative design

**Status:** Deferred

---

### Component Database Auto-Population

**Source:** kicad2wireBOM design specification Section 12

**Description:** Look up component electrical characteristics from part number database.

**Opportunity:**
- Maintain database of common components (radios, lights, instruments)
- Auto-populate Load/Rating values from part number
- Reduce manual data entry in schematic
- Ensure consistent/accurate load values

**Priority:** Low - Manual entry is reliable and transparent

**Status:** Deferred

---

### 3D Wire Routing Visualization

**Source:** kicad2wireBOM design specification Section 12

**Description:** Visualize wire routing in 3D aircraft model.

**Status:** Partially Implemented - 2D diagrams complete ✅, 3D deferred

**2D Implementation (Phase 10 ✅)**:
- SVG diagrams with FS×BL top-down view
- Manhattan routing visualization
- Component positions plotted
- Print-optimized for 8.5×11 paper
- See "Wire Routing Diagrams" in COMPLETED section below

**Remaining 3D Opportunity**:
- Import aircraft 3D model (STEP, STL)
- Add WL (vertical) dimension to visualization
- Render isometric or interactive 3D view
- Interactive routing review and adjustment

**Priority:** Low - 2D diagrams meet current needs

---

### Wire Cost Estimation

**Source:** kicad2wireBOM design specification Section 12

**Description:** Calculate estimated wire costs from supplier pricing data.

**Opportunity:**
- Maintain price database for wire by gauge/type/color
- Calculate total material cost from purchasing summary
- Compare cost of different wire gauge choices
- Generate procurement budget estimates

**Priority:** Low - Nice to have, not critical

**Status:** Deferred

---

### Harness Weight Calculation

**Source:** kicad2wireBOM design specification Section 12

**Description:** Estimate total wire harness weight for weight & balance calculations.

**Opportunity:**
- Weight-per-foot database for each wire gauge/type
- Calculate total harness weight from wire list
- Include connector and terminal weights
- Feed into aircraft W&B spreadsheet
- Important for experimental aircraft certification

**Priority:** Medium - Weight is critical for aircraft, but can be calculated separately

**Status:** Deferred

---

### PCB Coordinate Integration

**Source:** kicad2wireBOM design specification Section 12

**Description:** Use actual PCB component placement coordinates when available.

**Opportunity:**
- Import KiCad PCB file in addition to netlist
- Use real component placement for boards/panels
- More accurate wire lengths for panel wiring
- Mix PCB coords (for board-mounted) with aircraft coords (for distributed components)

**Priority:** Low - Most EA wiring is point-to-point, not PCB-based

**Status:** Deferred

---

### Multiple Netlist Processing

**Source:** kicad2wireBOM design specification Section 12

**Description:** Process entire KiCad project (multiple schematics) at once.

**Opportunity:**
- Process all schematic sheets in hierarchical design
- Generate single unified wire BOM
- Detect cross-sheet connections
- Handle complex multi-sheet aircraft electrical systems

**Priority:** Medium - Useful for large projects, but v1 can process sheets individually

**Status:** Deferred

---

### Export to Additional Formats

**Source:** kicad2wireBOM design specification Section 12

**Description:** Export wire BOM to additional file formats beyond CSV and Markdown.

**Opportunity:**
- Excel/XLSX with formatting, formulas, charts
- PDF for printable build documentation
- CAD formats (DXF, STEP) for 3D routing visualization
- JSON/XML for programmatic integration
- HTML for web-based viewing

**Priority:** Low - CSV and Markdown cover most needs

**Status:** Deferred

---

### Temperature Derating

**Source:** kicad2wireBOM design specification Section 12

**Description:** Adjust wire ampacity calculations based on ambient temperature.

**Opportunity:**
- Account for high-temperature environments (engine compartment, near exhaust)
- Apply derating factors from MIL-W-5088L or Aeroelectric Connection
- Temperature zones in schematic (add temp field to components)
- More conservative gauge selection for hot areas

**Priority:** Low - Standard ampacity tables are already conservative for bundled wires

**Status:** Deferred

---

---

## COMPLETED / IMPLEMENTED

### Wire Routing Diagrams ✅ IMPLEMENTED (Phase 10)

**Status**: ✅ COMPLETE (2025-10-26)

**Implementation**: SVG routing diagrams showing 2D top-down view (FS×BL) with Manhattan routing, optimized for 8.5×11 portrait printing. Includes professional titles with expanded system names, non-linear BL compression for wingtip lights, and print-optimized styling.

**Module**: `kicad2wireBOM/diagram_generator.py`
**CLI**: `--routing-diagrams [OUTPUT_DIR]`
**Documentation**: `docs/plans/wire_routing_diagrams_design.md`

**Originally Deferred Features Now Implemented**:
- One diagram per system code ✅
- Auto-scaling with fixed-width layout ✅
- Component positions and labels ✅
- Wire segment labels ✅
- Professional titles with system name mapping ✅

**Still Deferred** (from original OFI):
- 3D visualization with WL dimension
- Interactive HTML with zoom/pan
- Color coding by gauge/current
- Export to PDF or PNG
- Component symbols (different shapes by type)

See design document for complete feature list.

---

## Template for New OFIs

When adding new opportunities, use this template:

### [Short Title]

**Source:** [Where this idea came from]

**Description:** [What is the opportunity]

**Opportunity:**
- [Specific actionable items]

**Priority:** [High/Medium/Low]

**Status:** [New/Under Review/Deferred/Completed]