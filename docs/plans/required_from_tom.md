# Items Required from Tom

This document tracks items that need Tom's input, decisions, or action before implementation can proceed.

**Status Codes:**
- `[ ]` - Not started
- `[~]` - In progress
- `[x]` - Complete

---

## Review and Feedback

### Design Document Review

**Files to review:**
- `docs/plans/kicad2wireBOM_design.md` - Complete design specification
- `docs/plans/implementation/README.md` - Implementation plan overview
- `docs/plans/implementation/00_overview_and_contracts.md` - Module interface contracts
- `docs/plans/implementation/01_reference_data.md` through `10_cli_and_integration.md` - Individual work packages

**Action:** `[~]` In progress - Claude reviewing documents one by one

**Format:** Use `@@TOM:` or `@@Tom:` markers for questions/corrections

**Example:**
```markdown
The system uses default wire type M22759/16.
@@TOM: Should we also support M22759/32 as an option?
```

**When complete:** Let Claude know so comments can be extracted and addressed

---

## Test Fixtures / Example Netlists

### KiCad Netlist Fixtures with Footprint Encoding **[REVISED - 2025-10-17]**

We need actual KiCad v9 netlists with footprint-encoded component data for testing.

**CRITICAL REQUIREMENT:** All net names MUST follow the pattern `/[SYSTEM][CIRCUIT][SEGMENT]`
- Example: `/L1A` = Lighting system, circuit 1, segment A
- Example: `/P12B` = Power system, circuit 12, segment B
- Example: `/G1A` = Ground system, circuit 1, segment A

**Naming Convention:** `test_<complexity>_<description>.net`

**Required Fixtures:**

#### 1. Minimal Two-Component Circuit
**Filename:** `tests/fixtures/test_01_minimal_two_component.net`

**Status:** `[~]` Needs revision - Old version exists, needs SD-defined net names

**Description:** Simplest possible circuit - connector to switch

**Components:**
- J1: Connector at (100.0, 25.0, 0.0), rated 15A
  - Footprint: `Connector:Conn_01x02|(100.0,25.0,0.0)R15`
- SW1: Switch at (150.0, 30.0, 0.0), rated 20A
  - Footprint: `Button_Switch_THT:SW_PUSH_6mm|(150.0,30.0,0.0)R20`

**Nets:** **[REVISED]**
- `/P1A`: Connects J1 pin 1 to SW1 pin 1 (Power system, circuit 1, segment A)

**Purpose:** Basic parser validation, simplest case, net name parsing

---

#### 2. Simple Load Circuit (Multi-Segment with Shielded Wire)
**Filename:** `tests/fixtures/test_02_simple_load.net`

**Status:** `[x]` Complete - Using `docs/input/input_01_simple_lamp.net`

**Description:** Complete battery → switch → lamp circuit with ground return and shielded wire

**Components:**
- BT1: Battery at (10, 0, 0), "B" type, 40A rating
  - Footprint: `|(10,0,0)B40`
- SW1: Switch "Landing Light" at (100.0, 25.0, 0.0), rated 20A
  - Footprint: `|(100.0,25.0,0.0)R20`
- L1: Lamp at (20, 0, 0), drawing 3.5A
  - Footprint: `|(20,0,0)L3.5`

**Nets:**
- `/L1A` (class "Default"): BT1(+) to SW1 (Lighting system, circuit 1, segment A)
- `/L1B` (class "Shielded,Default"): SW1 to L1 (Lighting system, circuit 1, segment B) **[SHIELDED]**
- `/G1A` (class "Default"): L1 to BT1(-) (Ground return)

**Purpose:**
- Multi-segment circuits (A, B segments)
- Load calculations (3.5A lamp load)
- Shielded wire handling (net class parsing)
- Ground return circuit
- System code validation (L vs G)

**Special:** Tests net class "Shielded" → should set wire type to "M22759/16 (Shielded)"

---

#### 3. Multi-Node Circuit Warning Test **[REVISED - 2025-10-17]**
**Filename:** `tests/fixtures/test_03_multi_node_warning.net`

**Status:** `[ ]` Not created

**Description:** Net with 3+ components to trigger multi-node warning

**Components:**
- J1: Hub connector at (100.0, 25.0, 0.0), rated 30A
- SW1: Spoke 1 at (150.0, 25.0, 0.0), rated 10A
- SW2: Spoke 2 at (100.0, 50.0, 0.0), rated 10A

**Nets:** **[REVISED]**
- `/P1A`: Connects J1, SW1, and SW2 (3 components - should trigger warning)

**Purpose:** Test multi-node net validation warning (3+ components on single net)
**Expected Warning:** "Net /P1A connects 3 components. Consider splitting into separate nets with different segment letters."

---

#### 4. System Code Validation Test **[NEW - 2025-10-17]**
**Filename:** `tests/fixtures/test_04_system_code_validation.net`

**Status:** `[ ]` Not created

**Description:** Net with mismatched system code to test validation warning

**Components:**
- J1: Connector at (50.0, 20.0, 0.0), rated 30A
  - Footprint: `Connector:Conn_01x02|(50.0,20.0,0.0)R30`
- RADIO1: Radio at (120.0, 30.0, 0.0), drawing 8A
  - Value: "Garmin GTR 20"
  - Footprint: `LRU:LRU_2x|(120.0,30.0,0.0)L8`

**Nets:**
- `/L1A`: Connects J1 to RADIO1 (Net marked as Lighting but component is Radio)

**Purpose:** Test system code validation - parsed "L" vs inferred "R"
**Expected Warning:** "Net /L1A system code 'L' (Lighting) doesn't match component analysis. Components suggest 'R' (Radio)."

---

#### 5. Multiple Independent Circuits
**Filename:** `tests/fixtures/test_05_multiple_circuits.net`

**Status:** `[ ]` Not created

**Description:** Multiple separate circuits with different system codes

**Components:**
- J1: Main connector (source) at (50.0, 20.0, 0.0), rated 30A
- LIGHT1: Landing light at (200.0, 40.0, 15.0), 5A load
- LIGHT2: Nav light at (180.0, 35.0, -15.0), 2A load
- RADIO1: Radio at (120.0, 30.0, -5.0), 8A load
- GND_BUS: Ground bus at (60.0, 15.0, 0.0)

**Nets:** **[REVISED - SD defines system codes]**
- `/L1A`: Landing light circuit (J1→LIGHT1)
- `/L2A`: Nav light circuit (J1→LIGHT2)
- `/R1A`: Radio circuit (J1→RADIO1)
- `/G1A`: Ground return (LIGHT1→GND_BUS)
- `/G2A`: Ground return (LIGHT2→GND_BUS)
- `/G3A`: Ground return (RADIO1→GND_BUS)

**Purpose:** Test multiple systems (L, R, G), system code parsing from net names, BOM grouping/sorting by system

---

#### 6. Missing/Incomplete Data (Permissive Mode Test)
**Filename:** `tests/fixtures/test_06_missing_data.net`

**Status:** `[ ]` Not created

**Description:** Components with missing footprint encodings AND bad net name

**Components:**
- J1: Has encoding - `Connector:Conn_01x02|(100.0,25.0,0.0)R15`
- SW1: Missing encoding - `Button_Switch_THT:SW_PUSH_6mm` (no `|` data)
- LIGHT1: Missing encoding - `LED_THT:LED_D5.0mm`

**Nets:** **[REVISED - include bad net name test]**
- `Net-(J1-Pin_1)`: Auto-generated KiCad net name (doesn't follow `/[SYSTEM][CIRCUIT][SEGMENT]` pattern)

**Purpose:** Test permissive mode (defaults, warnings), strict mode (errors), net name format validation, fallback label generation

---

#### 7. Negative Coordinates
**Filename:** `tests/fixtures/test_07_negative_coords.net`

**Status:** `[ ]` Not created

**Description:** Components with negative BL (left side of aircraft)

**Components:**
- J1: Centerline at (100.0, 25.0, 0.0), rated 30A
- LIGHT_L: Left wing light at (200.0, 35.0, -50.0), 2.5A load (negative BL)
- LIGHT_R: Right wing light at (200.0, 35.0, 50.0), 2.5A load (positive BL)

**Nets:** **[REVISED]**
- `/L1A`: J1→LIGHT_L
- `/L2A`: J1→LIGHT_R

**Purpose:** Test negative coordinate handling (BL=-50.0), symmetrical left/right wire calculations

---

#### 8. Realistic Complex System
**Filename:** `tests/fixtures/test_08_realistic_system.net`

**Status:** `[ ]` Not created

**Description:** Full aircraft electrical panel subset (10-15 components, 8-12 circuits)

**Suggested Components:**
- BAT1: Main battery
- ALT1: Alternator
- MSTR_SW: Master switch
- Multiple circuit breakers (CB1, CB2, CB3...)
- Multiple loads (lights, avionics, instruments)
- Ground bus
- Various wire lengths (short and long runs)
- Mix of system codes (P, L, R, G, E, K, M)

**Nets:** **[REVISED - must follow naming pattern]**
- All nets must use `/[SYSTEM][CIRCUIT][SEGMENT]` format
- Example: `/P1A`, `/P1B`, `/L1A`, `/R1A`, `/G1A`, etc.
- Multi-segment circuits split into separate nets: `/L1A`, `/L1B`, `/L1C`

**Purpose:** Integration testing, realistic calculations, end-to-end validation, label format options (compact vs dashes)

---

## Reference Data Extraction

### Wire Resistance Values

**Status:** `[ ]` Not extracted

**Source:** `docs/references/aeroelectric_connection/` - Chapter 5

**Task:** Extract resistance values (ohms per foot) for AWG sizes 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22

**Note:** Can be done by programmer during implementation (Task 1.1 in reference_data package), but having it ready would speed things up.

---

### Wire Ampacity Values

**Status:** `[ ]` Not extracted

**Source:** `docs/references/aeroelectric_connection/` - Bob Nuckolls' bundled wire ampacity tables

**Task:** Extract max current ratings (amps) for AWG sizes 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22

**Note:** Use **bundled wire** values (conservative), not free-air values

---

### System Code Color Mapping

**Status:** `[x]` Complete

**Source:** `docs/ea_wire_marking_standard.md` - Section 3 now includes standard wire color mappings by system code

**Task:** Create complete mapping of system letter codes → wire colors

**Example format:**
```
L (Lighting) → White
P (Power) → Red
G (Ground) → Black
R (Radio/Nav) → Gray
A (Avionics) → Blue
... etc
```

**Note:** Can be done by programmer, but having it verified by Tom ensures correctness

---

## Design Decisions Needed

### Default Wire Type

**Status:** `[x]` Decided: M22759/16

**Decision:** Use M22759/16 as the default wire specification (most common aircraft wire)

**Confirmed:** M22759/16 is the standard default, can be overridden via configuration if needed

---

### Default System Voltage

**Status:** `[x]` Decided: 12V (configurable via CLI)

**Confirmed:** 12V default is fine, users can override with `--system-voltage` flag

---

### Slack Length Default

**Status:** `[x]` Decided: 24 inches (configurable via CLI)

**Confirmed:** 24" (12" per end) is reasonable default

---

### Voltage Drop Percentage

**Status:** `[x]` Decided: 5% global default (configurable via CLI)

**Decision:** Voltage drop percentage will be a global configuration setting, not per-circuit

**Confirmed:** Single global value (default 5%) can be overridden with `--max-voltage-drop` flag

---

## KiCad Schematic Templates

### Reusable Component Template

**Status:** `[ ]` Optional but helpful

**Description:** A KiCad schematic template with pre-configured footprint encoding examples that Tom can copy/paste

**Would include:**
- Example connector with footprint: `Connector:Conn_01x02|(100.0,25.0,0.0)R15`
- Example switch with footprint: `Button_Switch_THT:SW_PUSH_6mm|(150.0,30.0,0.0)R20`
- Example load with footprint: `LED_THT:LED_D5.0mm|(200.0,35.0,10.0)L2.5`
- Instructions in schematic notes field

**Benefit:** Speeds up creating test fixtures and real schematics

---

## Architectural Analysis

### System Code Detection Analysis

**Status:** `[x]` Complete

**Deliverables:**
- `docs/plans/system_code_analysis.md` - Preliminary analysis of component categorization
- `docs/plans/keyword_extraction_from_657CZ.md` - Comprehensive keyword extraction from real 657CZ schematic

**Summary:**
- Analyzed all 163 components from 657CZ schematic
- Categorized components into 6 system codes (L, P, R, E, K, M)
- Extracted comprehensive keyword lists for detection
- Identified 74 LRU (avionics) components requiring Garmin-specific keywords
- Documented critical gaps in programmer's current implementation
- Ready-to-implement keyword lists provided for programmer

---

## Documentation Clarifications

### Anything Unclear in Plans?

**Status:** `[x]` Complete - No @@TOM flags remain in design documents

**Action:** Review documents and mark any:
- Unclear explanations
- Missing information
- Technical questions
- Implementation concerns
- Timeline concerns

**Result:** All @@TOM flags resolved

---

## Design Revisions

### Design Revision 1.1 - Net Name Parsing (2025-10-17)

**Status:** `[x]` Complete

**Decision:** SD embeds wire marking codes directly in net names (e.g., `/L1A`, `/P12B`, `/G1A`)

**Rationale:**
- Analysis of `docs/input/input_01_simple_lamp.net` revealed SD names nets with complete system/circuit/segment codes
- More reliable and deterministic than inferring from components
- Simpler implementation path
- Puts semantic control with SD (where it belongs)

**Design Changes:**
- **Section 2.3**: Rewritten for net name parsing as primary, component analysis as validation
- **Section 3.4**: Wire labels extracted from net names (not generated from inferred data)
- **Section 4.2**: Added 4 new validation checks (net format, duplicate labels, multi-node, system code validation)
- **Section 6**: Added `--label-format` CLI flag (compact/dashes)

**Documents Updated:**
- `docs/plans/kicad2wireBOM_design.md` - Design Revision History + `[REVISED]` markers
- `docs/plans/programmer_todo.md` - Revised Phase 1, 4, 6, 6.5 tasks with revision notices
- `claude/roles/architect.md` - Added `[REVISED]` methodology
- `claude/roles/programmer.md` - Added Circle K protocol for design inconsistencies

**Impact on Programmer:**
- Simpler primary path (parse vs infer)
- Component analysis still needed for validation quality checks
- Phase 6.5 comprehensive keywords still valuable for catching SD mistakes
- No work wasted - all analysis repurposed for validation

---

## Next Steps

1. **Tom reviews revised documents** - Check `[REVISED]` sections for any concerns
2. **Tom creates test fixtures** - Generate KiCad netlists with net names following `/[SYSTEM][CIRCUIT][SEGMENT]` pattern
3. **Begin implementation** - Switch to Programmer role and start with Phase 0

---

## Notes

- This document will be updated as items are completed or new needs identified
- Check boxes `[x]` indicate completion
- Add new items to appropriate sections as they come up
- Use `@@TOM:` markers in this document too if you have questions about what's needed
- **Watch for `[REVISED - YYYY-MM-DD]` markers** in design docs to track changes
