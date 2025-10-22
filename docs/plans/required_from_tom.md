# Items Required from Tom

This document tracks items that need Tom's input, decisions, or action.

**Status Codes:**
- `[ ]` - Not started / Needs decision
- `[x]` - Complete / Resolved

---

## CURRENT OPEN QUESTIONS

### Hierarchical Schematic Support

**Status:** `[ ]` Needs information

**Question:** Are your aircraft electrical schematics:
- **Flat**: Single `.kicad_sch` file with all circuits
- **Hierarchical**: Multiple sheets with interconnections

**Impact**:
- Flat schematics: Current implementation handles this ✅
- Hierarchical: Would need additional design work (sheet interconnections, global label tracking)

**Current Design**: Assumes flat schematics. Hierarchical support noted in OFI document as future enhancement.

---

## NEXT PHASE DIRECTION

### What Should We Work On Next?

**Status:** `[ ]` Awaiting Tom's direction

**Context**: Phases 1-5 complete (125/125 tests passing). Core functionality working.

**Options for Phase 6**:

1. **Validation & Error Handling**
   - Better error messages for malformed schematics
   - Strict vs permissive mode implementation
   - Comprehensive validation reporting

2. **CLI Enhancements**
   - Markdown output format
   - Engineering mode (detailed calculations)
   - Validation-only mode
   - Verbose/quiet output options

3. **Wire Calculation Features**
   - Actual wire length calculation (not just defaults)
   - Wire gauge calculation based on load
   - Voltage drop analysis
   - Color assignment from system codes

4. **New Features** (see `docs/notes/opportunities_for_improvement.md`)
   - Configuration file support
   - Wire specification overrides
   - Hierarchical schematic support
   - Additional output formats

5. **Production Readiness**
   - User documentation
   - Installation/packaging
   - README with usage examples
   - Distribution preparation

**Question:** Which direction would be most valuable for your immediate needs?

---

## COMPLETED ITEMS ARCHIVE

<details>
<summary>Expand to see resolved design decisions and completed items</summary>

### Architecture & Design ✅
- **Schematic-based parsing** (vs netlist-based) - Implemented
- **S-expression parsing library** - Using `sexpdata`
- **Pin position calculation** - Precise calculation with rotation/mirroring implemented
- **Label association threshold** - 10mm default (configurable)
- **Default wire type** - M22759/16
- **Default system voltage** - 12V (configurable via CLI)
- **Slack length default** - 24 inches (configurable via CLI)

### Test Fixtures ✅
- test_01_fixture.kicad_sch - Simple 2-component circuit ✅
- test_03A_fixture.kicad_sch - 3-way multipoint connection ✅
- test_04_fixture.kicad_sch - 4-way ground connection ✅
- All fixtures verified and working with implementation

### Reference Data ✅
- Wire resistance values extracted from Aeroelectric Connection
- Wire ampacity values implemented
- System code color mapping complete (from ea_wire_marking_standard.md)

### Implementation Approach ✅
- TDD methodology followed throughout Phases 1-5
- All 125 tests passing
- Core features complete

</details>
