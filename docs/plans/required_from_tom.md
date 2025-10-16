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

**Action:** `[ ]` Review all documents and add inline comments

**Format:** Use `@@TOM:` or `@@Tom:` markers for questions/corrections

**Example:**
```markdown
The tool calculates wire gauge using 5% voltage drop.
@@TOM: Should this be configurable per-circuit or just globally?
```

**When complete:** Let Claude know so comments can be extracted and addressed

---

## Test Fixtures / Example Netlists

### KiCad Netlist Fixtures with Footprint Encoding

We need actual KiCad v9 netlists with footprint-encoded component data for testing.

**Naming Convention:** `test_<complexity>_<description>.net`

**Required Fixtures:**

#### 1. Minimal Two-Component Circuit
**Filename:** `tests/fixtures/test_01_minimal_two_component.net`

**Status:** `[ ]` Not created

**Description:** Simplest possible circuit - connector to switch

**Components:**
- J1: Connector at (100.0, 25.0, 0.0), rated 15A
  - Footprint: `Connector:Conn_01x02|(100.0,25.0,0.0)R15`
- SW1: Switch at (150.0, 30.0, 0.0), rated 20A
  - Footprint: `Button_Switch_THT:SW_PUSH_6mm|(150.0,30.0,0.0)R20`

**Nets:**
- Net-P12: Connects J1 pin 1 to SW1 pin 1

**Purpose:** Basic parser validation, simplest case

---

#### 2. Simple Load Circuit
**Filename:** `tests/fixtures/test_02_simple_load.net`

**Status:** `[ ]` Not created

**Description:** Complete circuit from source through switch to load

**Components:**
- J1: Connector (source) at (50.0, 20.0, 0.0), rated 30A
  - Footprint: `Connector:Conn_01x02|(50.0,20.0,0.0)R30`
- SW1: Switch at (100.0, 25.0, 0.0), rated 20A
  - Footprint: `Button_Switch_THT:SW_PUSH_6mm|(100.0,25.0,0.0)R20`
- LIGHT1: LED (load) at (200.0, 35.0, 10.0), drawing 2.5A
  - Footprint: `LED_THT:LED_D5.0mm|(200.0,35.0,10.0)L2.5`

**Nets:**
- Net-L105: Connects J1→SW1 (segment A), SW1→LIGHT1 (segment B)

**Purpose:** Test wire segmentation (A, B), load calculations, label generation

---

#### 3. Multi-Node Circuit (Star Topology)
**Filename:** `tests/fixtures/test_03_multi_node_star.net`

**Status:** `[ ]` Not created

**Description:** One net connecting 4 components in star arrangement (hub + 3 spokes)

**Components:**
- J1: Hub connector at (100.0, 25.0, 0.0), rated 30A
- SW1: Spoke 1 at (150.0, 25.0, 0.0), rated 10A
- SW2: Spoke 2 at (100.0, 50.0, 0.0), rated 10A
- SW3: Spoke 3 at (50.0, 25.0, 0.0), rated 10A

**Nets:**
- Net-P20: Connects all 4 components

**Purpose:** Test multi-node topology detection (star pattern)

---

#### 4. Multi-Node Circuit (Daisy-Chain)
**Filename:** `tests/fixtures/test_04_multi_node_daisy.net`

**Status:** `[ ]` Not created

**Description:** One net connecting 4 components in linear sequence

**Components:**
- BAT1: Battery at (25.0, 15.0, 0.0), rated 50A
- CB1: Circuit breaker at (75.0, 20.0, 0.0), rated 30A
- SW1: Switch at (125.0, 25.0, 0.0), rated 20A
- LOAD1: Load device at (200.0, 35.0, 5.0), drawing 15A

**Nets:**
- Net-P10: Connects BAT1→CB1→SW1→LOAD1

**Purpose:** Test multi-node topology detection (daisy-chain pattern), signal flow ordering

---

#### 5. Multiple Independent Circuits
**Filename:** `tests/fixtures/test_05_multiple_circuits.net`

**Status:** `[ ]` Not created

**Description:** 3 separate circuits in one netlist (Lighting, Power, Ground)

**Components:**
- J1: Main connector (source) at (50.0, 20.0, 0.0)
- LIGHT1: Landing light at (200.0, 40.0, 15.0), 5A load
- LIGHT2: Nav light at (180.0, 35.0, -15.0), 2A load
- RADIO1: Radio at (120.0, 30.0, -5.0), 8A load
- GND_BUS: Ground bus at (60.0, 15.0, 0.0)

**Nets:**
- Net-L105: Landing light circuit (J1→LIGHT1)
- Net-L110: Nav light circuit (J1→LIGHT2)
- Net-R200: Radio circuit (J1→RADIO1)
- Net-G001: Ground return (LIGHT1→GND_BUS)
- Net-G002: Ground return (LIGHT2→GND_BUS)
- Net-G003: Ground return (RADIO1→GND_BUS)

**Purpose:** Test multiple systems (L, R, G), system code parsing, BOM grouping/sorting

---

#### 6. Missing/Incomplete Data (Permissive Mode Test)
**Filename:** `tests/fixtures/test_06_missing_data.net`

**Status:** `[ ]` Not created

**Description:** Components with missing footprint encodings

**Components:**
- J1: Has encoding - `Connector:Conn_01x02|(100.0,25.0,0.0)R15`
- SW1: Missing encoding - `Button_Switch_THT:SW_PUSH_6mm` (no `|` data)
- LIGHT1: Missing encoding - `LED_THT:LED_D5.0mm`

**Nets:**
- Net-L105: Connects J1→SW1→LIGHT1

**Purpose:** Test permissive mode (defaults, warnings), strict mode (errors)

---

#### 7. Negative Coordinates
**Filename:** `tests/fixtures/test_07_negative_coords.net`

**Status:** `[ ]` Not created

**Description:** Components with negative BL (left side of aircraft)

**Components:**
- J1: Centerline at (100.0, 25.0, 0.0)
- LIGHT_L: Left wing light at (200.0, 35.0, -50.0), 2.5A load (negative BL)
- LIGHT_R: Right wing light at (200.0, 35.0, 50.0), 2.5A load (positive BL)

**Nets:**
- Net-L105: J1→LIGHT_L
- Net-L110: J1→LIGHT_R

**Purpose:** Test negative coordinate handling (BL=-50.0), symmetrical left/right

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
- Mix of system codes (P, L, R, G, A)

**Purpose:** Integration testing, realistic calculations, end-to-end validation

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

**Status:** `[ ]` Not extracted

**Source:** `docs/ea_wire_marking_standard.md`

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

**Status:** `[ ]` Decision needed

**Question:** What default wire specification should the tool use?

**Options:**
- M22759/16 (most common aircraft wire)
- M22759/32 (higher temperature rating)
- Other?

**Current assumption:** M22759/16 (can be changed later)

---

### Default System Voltage

**Status:** `[x]` Decided: 12V (configurable via CLI)

**Confirmed:** 12V default is fine, users can override with `--system-voltage` flag

---

### Slack Length Default

**Status:** `[x]` Decided: 24 inches (configurable via CLI)

**Confirmed:** 24" (12" per end) is reasonable default

---

## Implementation Priorities

### Which Work Package to Start First?

**Status:** `[ ]` Decision needed

**Question:** If implementing yourself (Programmer role), which package should you start with?

**Recommendation:** Start with foundational packages in Phase 1:
- Package 01 (Reference Data) - 8-12 hours
- Package 02 (Component Model) - 6-8 hours

These have no dependencies and let other work proceed in parallel later.

**Alternative:** Start with Package 03 (Parser) if you want to see data flowing through the system quickly.

---

### Multiple Programmers?

**Status:** `[ ]` Decision needed

**Question:** Will this be:
- Solo implementation (you as Programmer)?
- Team implementation (distributing packages)?
- Hybrid (you do some, others do some)?

**Impact:** Affects which packages to prioritize and coordination strategy

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

## Documentation Clarifications

### Anything Unclear in Plans?

**Status:** `[ ]` Awaiting Tom's review with `@@TOM:` markers

**Action:** Review documents and mark any:
- Unclear explanations
- Missing information
- Technical questions
- Implementation concerns
- Timeline concerns

---

## Next Steps

1. **Tom reviews documents** - Add `@@TOM:` markers for questions/corrections
2. **Tom creates test fixtures** - Generate KiCad netlists with footprint encoding
3. **Claude extracts review comments** - Pull all `@@TOM:` markers and address them
4. **Tom decides implementation approach** - Solo vs team, which packages first
5. **Begin implementation** - Switch to Programmer role and start with Phase 1

---

## Notes

- This document will be updated as items are completed or new needs identified
- Check boxes `[x]` indicate completion
- Add new items to appropriate sections as they come up
- Use `@@TOM:` markers in this document too if you have questions about what's needed
