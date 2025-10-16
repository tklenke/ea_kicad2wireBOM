# Work Package 06: Wire BOM Model

## Overview

**Module:** `kicad2wireBOM/wire_bom.py`

**Purpose:** Data structures for wire Bill of Materials.

**Dependencies:** component.py

**Estimated Effort:** 6-8 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 6: wire_bom.py"

**Key Exports:**
- `WireConnection` dataclass
- `WireBOM` class

---

## Key Tasks

### Task 6.1: Implement WireConnection Dataclass (2 hours)

**Tests:**
- Create wire with core fields (label, from, to, gauge, color, length, type)
- Create wire with engineering fields
- warnings list initializes correctly
- All fields accessible

**Fields:**
- Core: wire_label, from_ref, to_ref, wire_gauge, wire_color, length, wire_type
- Engineering: calculated_min_gauge, voltage_drop_volts, voltage_drop_percent, current, from_coords, to_coords, calculated_length
- Validation: warnings (list)

### Task 6.2: Implement WireBOM Class (2 hours)

**Tests:**
- Create empty BOM
- Add wires to BOM
- wires list grows correctly
- config and components attributes work

**Methods:**
- `add_wire(wire)` - append to list
- `sort_by_system_code()` - sort by system/circuit/segment
- `get_wire_summary()` - return {(gauge, color): total_length}
- `get_validation_summary()` - return all warnings

### Task 6.3: Implement Sorting (1 hour)

**Tests:**
- Sort by system code alphabetically
- Sort by circuit number numerically within system
- Sort by segment letter within circuit
- Mixed systems sorted correctly

**Algorithm:**
- Parse label "L-105-A" into (system, circuit, segment)
- Sort by (system, int(circuit), segment) tuple

### Task 6.4: Implement get_wire_summary (1 hour)

**Tests:**
- Calculate total length per gauge/color combination
- Return dict {("20 AWG", "Red"): 240.5}
- Handle multiple wires same gauge/color
- Round totals appropriately

### Task 6.5: Implement get_validation_summary (1 hour)

**Tests:**
- Collect warnings from all wires
- Return flat list of warning strings
- Empty if no warnings

---

## Testing Checklist

- [ ] WireConnection created with all fields
- [ ] WireBOM stores multiple wires
- [ ] Sorting works correctly
- [ ] Wire summary calculates totals
- [ ] Validation summary collects warnings
- [ ] All tests pass

---

## Integration Notes

**Depends on:** component.py (for type hints)

**Used by:** Output modules, validation

---

## Estimated Timeline

~7 hours total

---

## Completion Criteria

- Data model complete and tested
- Sorting works correctly
- Summary functions work
- Module exports match interface contract
