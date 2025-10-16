# Work Package 07: Validator

## Overview

**Module:** `kicad2wireBOM/validator.py`

**Purpose:** Validation logic for components, wires, and circuits.

**Dependencies:** component.py, circuit.py (from circuit_analysis), wire_bom.py, reference_data.py

**Estimated Effort:** 8-10 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 7: validator.py"

**Key Exports:**
- `ValidationResult` dataclass
- `validate_required_fields(components, permissive_mode)`
- `validate_wire_gauge(wire, calculated_min_gauge)`
- `validate_rating_vs_load(circuit_path)`
- `validate_gauge_progression(circuit_path, wire_segments)`
- `collect_all_warnings(bom, circuits, components, permissive)`

---

## Key Tasks

### Task 7.1: Implement ValidationResult Dataclass (1 hour)

**Fields:**
- component_ref, net_name, severity ("error"/"warning"), message, suggestion

**Tests:**
- Create validation result
- All fields accessible

### Task 7.2: Implement validate_required_fields (2 hours)

**Tests:**
- Valid components pass
- Missing FS/WL/BL generates errors (strict) or warnings (permissive)
- Missing load/rating generates errors/warnings
- Both load and rating generates errors
- Return list of ValidationResult objects

### Task 7.3: Implement validate_wire_gauge (1 hour)

**Tests:**
- Wire with no specified gauge passes
- Wire with adequate gauge passes
- Wire with undersized gauge generates warning
- Parse AWG from "20 AWG" string format

### Task 7.4: Implement validate_rating_vs_load (2 hours)

**Purpose:** Check that no component rating is exceeded by downstream loads.

**Tests:**
- Simple path: source → 10A switch → 5A load (passes)
- Overload: source → 10A switch → 15A load (warns)
- Multiple loads: sum loads correctly

**Algorithm:**
- Walk circuit path from source to load
- At each passthrough component, check cumulative downstream load ≤ rating

### Task 7.5: Implement validate_gauge_progression (2 hours)

**Purpose:** Wire gauge shouldn't decrease (get heavier) along path.

**Tests:**
- Consistent gauge path passes
- Lighter upstream, heavier downstream passes
- Heavier upstream, lighter downstream warns (wrong direction)

**Algorithm:**
- Compare adjacent wire segments
- Warn if downstream AWG number decreases (heavier wire)

### Task 7.6: Implement collect_all_warnings (1 hour)

**Tests:**
- Run all validation functions
- Collect all ValidationResult objects
- Attach warnings to appropriate wires
- Return summary list

---

## Testing Checklist

- [ ] ValidationResult stores all data
- [ ] Required fields validation works (strict and permissive)
- [ ] Wire gauge validation works
- [ ] Rating vs load catches overloads
- [ ] Gauge progression catches design errors
- [ ] collect_all_warnings runs all checks
- [ ] All tests pass

---

## Integration Notes

**Depends on:** component.py, circuit.py, wire_bom.py, reference_data.py

**Used by:** CLI (for validation reporting)

---

## Estimated Timeline

~9 hours total

---

## Completion Criteria

- All validation checks implemented
- Tests cover normal and error cases
- Module exports match interface contract
