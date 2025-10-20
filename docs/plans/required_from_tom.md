# Items Required from Tom

This document tracks items that need Tom's input, decisions, or action before implementation can proceed.

**Status Codes:**
- `[ ]` - Not started
- `[~]` - In progress
- `[x]` - Complete

---

## CRITICAL: Architecture Change - Schematic-Based Parsing

**Date**: 2025-10-18
**Status**: `[x]` Complete - Design rewritten

**Decision**: Parse KiCAD schematic files (`.kicad_sch`) instead of netlists (`.net`)

**Rationale**:
- Netlists collapse wires into nets based on electrical connectivity
- Wire harness manufacturing needs physical wire-level granularity
- Two wires connecting to same terminal = electrically one net, but physically two distinct wires
- Schematic preserves wire segment information before net consolidation

**Impact**:
- Previous netlist-based design archived to `docs/archive/`
- New design specification created: `docs/plans/kicad2wireBOM_design.md` v2.0
- Different parsing approach: S-expressions vs XML
- Different data model: Wire-centric vs net-centric
- Label association by spatial proximity

**Old Documents Archived**:
- `docs/archive/kicad2wireBOM_design.md` (v1.0, v1.1 - netlist-based)
- `docs/archive/incremental_implementation_plan.md`
- `docs/archive/programmer_todo.md`
- `docs/archive/system_code_analysis.md`
- `docs/archive/keyword_extraction_from_657CZ.md`
- `docs/archive/architect_todo.md`

---

## Review and Feedback

### Design Document Review

**Files to review:**
- `docs/plans/kicad2wireBOM_design.md` v2.0 - NEW schematic-based design

**Status:** `[x]` Awaiting Tom's review

**Action:** Review the new schematic-based design document

**Key Sections to Focus On**:
1. **Section 0** - "Critical Architectural Decision" - Why we changed from netlists
2. **Section 2.3** - Wire segment labels and circuit identification
3. **Section 3** - Schematic data extraction (s-expression parsing)
4. **Section 3.4** - Label association by proximity
5. **Section 4** - Wire connection analysis
6. **Section 14** - Programmer implementation notes

**Questions to Consider**:
- Does the schematic-based approach address your wire granularity problem?
- Is the label-to-wire proximity association approach sound?
- Are there any schematic features we're missing?
- Does the footprint encoding format still make sense?

---

## Test Fixtures / Example Schematics

### KiCAD Schematic Fixtures **[UPDATED FOR SCHEMATIC APPROACH]**

We need actual KiCAD `.kicad_sch` files (NOT `.net` netlists) for testing.

**Good News**: You already have three test fixtures!
- `tests/fixtures/test_01_fixture.kicad_sch` ✓
- `tests/fixtures/test_02_fixture.kicad_sch` ✓
- `tests/fixtures/test_03_fixture.kicad_sch` ✓

**Status:** `[x]` Basic fixtures exist

**Review Needed**: `[ ]` Verify fixtures have required data

**Required Elements in Each Fixture**:
1. **Wire segments** with `(wire ...)` blocks
2. **Labels** on wires with circuit IDs (e.g., "P1A", "G1A", "L2B")
3. **Components** with Footprint field encoding: `|(fs,wl,bl)<type><amps>`
4. **Component pins** with connections to wire endpoints
5. **(Optional)** Junctions showing where multiple wires meet

**Analysis from Existing Fixtures**:

From my analysis of your three test fixtures:

**test_01_fixture.kicad_sch**:
- ✓ 6 wire segments with UUIDs
- ✓ 2 labels: "G1A", "P1A"
- ✓ Components: BT1 (battery), L1 (lamp)
- ✓ Footprint encoding: `|(10,0,0)S40`, `|(20,0,0)L1.5`
- ⚠ Need to verify labels are positioned close to wires

**test_02_fixture.kicad_sch**:
- ✓ 7 wire segments
- ✓ 3 labels: "L2B", "L2A", "G1A"
- ✓ Components: BT1 (battery), L1 (lamp), SW1 (switch)
- ✓ Footprint encoding present
- ✓ More complex routing

**test_03_fixture.kicad_sch**:
- ✓ 4 wire segments
- ✓ 1 junction at (144.78, 86.36)
- ✓ 2 labels: "P1A", "P2A"
- ✓ Components: SW1, SW2 (switches), J1 (connector)
- ✓ **Perfect example of multi-wire junction** - exactly the problem we're solving!

**Action Items**:

1. **Verify Label Placement** `[x]`
   - Open each schematic in KiCAD
   - Verify labels are visually close to their intended wire segments
   - Default threshold is 10mm - labels should be within ~10mm of wire

2. **Add Missing Fixtures** `[x]` (Optional - start with existing three)
   - Missing labels fixture (test permissive mode)
   - Orphaned labels fixture (label far from any wire)
   - Complex multi-circuit fixture

3. **Document Expected Outputs** `[x]`
   - For each test fixture, create expected BOM output
   - CSV format with expected wire list
   - Use for validation during testing

---

## Reference Data Extraction

### Wire Resistance Values

**Status:** `[x]` Decision: Programmer extracts from Aeroelectric Connection

**Source:** `docs/references/aeroelectric_connection/` - Chapter 5

**Task for Programmer:** Extract resistance values (ohms per foot) for AWG sizes 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22

**Format**:
```python
WIRE_RESISTANCE = {
    22: 0.016,  # ohms per foot
    20: 0.010,
    18: 0.0064,
    # ... etc
}
```

**Instructions**:
- Extract from Aeroelectric Connection reference materials during Phase 4
- Use actual values from Bob Nuckolls' tables (not placeholder estimates)
- Document source in code comments
- Use bundled/conduit values (conservative), not free-air
- Task 4.1 in programmer_todo.md

---

### Wire Ampacity Values

**Status:** `[x]` Decision: Programmer extracts from Aeroelectric Connection

**Source:** `docs/references/aeroelectric_connection/` - Bob Nuckolls' bundled wire ampacity tables

**Task for Programmer:** Extract max current ratings (amps) for AWG sizes 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22

**Important:** Use **bundled wire** values (conservative), not free-air values

**Format**:
```python
WIRE_AMPACITY = {
    22: 5,    # max amps
    20: 7.5,
    18: 10,
    # ... etc
}
```

**Instructions**:
- Extract from Aeroelectric Connection during Phase 4
- Use bundled/conduit ampacity (not free-air)
- Document source in code comments
- Task 4.1 in programmer_todo.md

---

### System Code Color Mapping

**Status:** `[x]` Complete

**Source:** `docs/ea_wire_marking_standard.md` - Section 3 includes standard wire color mappings

**Format**:
```python
SYSTEM_COLOR_MAP = {
    'L': 'White',     # Lighting
    'P': 'Red',       # Power
    'G': 'Black',     # Ground
    'R': 'Gray',      # Radio/Nav
    # ... etc
}
```

---

## Design Decisions Needed

### Default Wire Type

**Status:** `[x]` Decided: M22759/16

**Decision:** Use M22759/16 as the default wire specification (most common aircraft wire)

---

### Default System Voltage

**Status:** `[x]` Decided: 12V (configurable via CLI)

**Confirmed:** 12V default, users can override with `--system-voltage` flag

---

### Slack Length Default

**Status:** `[x]` Decided: 24 inches (configurable via CLI)

**Confirmed:** 24" (12" per end) is reasonable default

---

### Label Association Distance Threshold

**Status:** `[x]` Decision: 10mm (configurable)

**Decision**: Use 10mm (approximately 0.4 inches in schematic) as default threshold

**Rationale**:
- Reasonable distance for typical label placement in KiCAD schematics
- Based on analysis of test fixtures showing labels within ~5-10mm of wires
- Conservative enough to avoid false associations

**Configuration**:
- Default: 10mm
- Stored in `reference_data.py` as `DEFAULT_CONFIG['label_threshold']`
- Configurable via CLI flag: `--label-threshold MM`
- Easily adjustable if testing shows different value needed

**Instruction for Programmer**:
- Implement with 10mm default
- Make threshold configurable (not hardcoded)
- Add to configuration system for easy tuning
- Document in `--help` and schematic requirements output

---

## S-Expression Parsing Library Choice

### Python Library for Parsing KiCAD Schematics

**Status:** `[x]` Decision: Use sexpdata library

**Decision**: Use `sexpdata` library for s-expression parsing

**Rationale**:
- Mature, well-tested library
- Simple API: `import sexpdata; data = sexpdata.loads(text)`
- Faster implementation than custom parser
- PyPI: https://pypi.org/project/sexpdata/

**Instruction for Programmer**:
- Use `sexpdata` as the primary parsing library
- **If you encounter issues** with `sexpdata` (parsing errors, data structure problems, performance issues):
  1. Document the specific problem
  2. Use Circle K protocol: "Strange things are afoot at the Circle K"
  3. Suggest alternative approach (custom parser or pyparsing)
  4. Wait for architectural decision before switching

---

## Pin Position Calculation Strategy

### How Precisely Do We Need Component Pin Positions?

**Status:** `[ ]` Needs decision

**Context**: Wire endpoints connect to component pins. To find connections, we need to know pin positions in the schematic.

**Challenge**: Component pins are defined in symbol libraries with relative positions. Symbol instances in schematics have:
- Position: `(at x y rotation)`
- Rotation can be 0, 90, 180, 270 degrees
- Sometimes mirroring

**Options**:

**Option 1: Use component position only** (SIMPLE)
- Treat all pins of a component as being at component center
- Wire endpoint matching: "Does this wire end near this component?"
- Pros: Simple, fast, works for most cases
- Cons: Can't distinguish between pins on same component

**Option 2: Calculate exact pin positions** (PRECISE)
- Parse symbol library to get pin relative positions
- Apply rotation/mirroring transforms
- Calculate absolute pin positions in schematic
- Pros: Precise pin-to-pin connections
- Cons: Complex, requires parsing symbol libraries, rotation math

**Option 3: Hybrid approach** (PRAGMATIC)
- Use component position for initial matching
- If component has multiple pins, look up pin numbers from schematic
- Match wire endpoints to pin numbers without needing exact positions
- Pros: Good accuracy without complex math
- Cons: Still needs some pin data extraction

**Recommendation:** Start with Option 1, add precision later if needed

**Question for Tom**:
- Do you have components with multiple wires connecting to different pins? (e.g., multi-pin connectors)
- If so, do labels distinguish which pin? (e.g., "J1-1" vs "J1-2" in component ref)

---

## Hierarchical Schematic Support

### Do You Use KiCAD Hierarchical Sheets?

**Status:** `[ ]` Needs information

**Question:** Are your aircraft electrical schematics:
- **Flat**: Single `.kicad_sch` file with all circuits
- **Hierarchical**: Multiple sheets with interconnections

**Impact**:
- Flat schematics: Can implement immediately
- Hierarchical: Need to defer this feature to later phase

**Current Design**: Assumes flat schematics, notes hierarchical as future enhancement

**Action:** Tom confirms schematic structure

---

## Test Fixture Documentation

### Expected BOM Outputs for Test Fixtures

**Status:** `[ ]` Not created

**Need:** For each test fixture, create expected BOM output for validation

**Format:** CSV files showing expected wire list

**Example for test_01_fixture.kicad_sch**:
```csv
Wire Label,From,To,Wire Gauge,Wire Color,Length,Wire Type,Warnings
P1A,BT1-1,L1-1,22 AWG,Red,46 inches,M22759/16,
G1A,L1-2,BT1-2,22 AWG,Black,46 inches,M22759/16,
```

**Calculation**:
- BT1 at (10,0,0), L1 at (20,0,0)
- Manhattan distance: |20-10| + |0-0| + |0-0| = 10 inches
- + 24" slack = 34 inches
- (Need to recalculate based on actual fixture coordinates)

**Action:** Tom creates expected output CSVs for test fixtures OR defers to programmer

---

## Schematic Creation Guidelines

### Reusable Component Templates

**Status:** `[ ]` Optional but helpful

**Description:** Pre-configured KiCAD components with footprint encoding examples

**Would Include**:
- Battery: `|(10,0,0)B40`
- Switch: `|(100,25,0)R20`
- Lamp: `|(200,35,10)L2.5`
- Connector: `|(50,20,0)R15`
- Instructions as schematic text notes

**Benefit:** Speeds up creating test fixtures and real schematics

**Action:** Tom decides if this would be useful

---

## Implementation Approach

### Test-Driven Development Checkpoints

**Status:** `[ ]` Planning needed

**Question:** Should implementation proceed in strict TDD phases, or more exploratory?

**Option A: Strict TDD**
- Write failing test first, always
- Implement minimal code to pass
- Refactor, repeat
- Pros: High confidence, good coverage
- Cons: Slower initial progress

**Option B: Spike-then-test**
- Explore with proof-of-concept code
- Once approach validated, write tests and refactor
- Pros: Faster initial exploration
- Cons: Risk of untested code

**Option C: Hybrid**
- Core algorithms: Strict TDD (wire calculations, label association)
- Parsing/I/O: Spike-then-test (rapid prototyping)
- Pros: Balance speed and quality

**Recommendation:** Option C (Hybrid)

**Action:** Tom's preference?

---

## Next Steps

1. **Tom reviews new schematic-based design** `[x]`
   - Check `docs/plans/kicad2wireBOM_design.md` v2.0
   - Flag any concerns or questions

2. **Tom verifies test fixtures** `[x]`
   - Open in KiCAD to check label placement
   - Confirm they have all required elements

3. **Tom decides on open questions** `[x]`
   - Label distance threshold
   - S-expression parser library choice
   - Pin position calculation strategy
   - Hierarchical schematic support (now or later)

4. **Architect creates implementation plan** `[x]`
   - Break design into work packages
   - Sequence tasks for TDD approach
   - Create programmer guidance document

5. **Switch to Programmer role and begin implementation** `[x]`
   - Start with s-expression parsing foundation
   - Build up test fixtures and data models
   - Implement wire extraction and label association

---

## Notes

- This document will be updated as items are completed or new needs identified
- Check boxes `[x]` indicate completion
- Tilde `[~]` indicates in progress
- Add new items to appropriate sections as they come up
- **MAJOR CHANGE**: Netlist-based approach abandoned, schematic-based approach adopted
