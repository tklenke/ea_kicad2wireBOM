# Work Package 05: Wire Calculator

## Overview

**Module:** `kicad2wireBOM/wire_calculator.py`

**Purpose:** Calculate wire lengths, gauge, voltage drop, assign colors, generate labels.

**Dependencies:** reference_data.py, component.py

**Estimated Effort:** 10-12 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 5: wire_calculator.py"

**Key Functions:**
- `calculate_length(component1, component2, slack)`
- `calculate_voltage_drop(current, awg_size, length)`
- `determine_min_gauge(current, length, system_voltage, slack)`
- `assign_wire_color(system_code, color_override=None)`
- `generate_wire_label(net_name, circuit_id, system_code, segment_letter)`
- `round_to_standard_awg(calculated_gauge)`

---

## Key Tasks

### Task 5.1: Implement calculate_length (2 hours)

**Formula:** Manhattan distance + slack
```python
Length = |FS₁ - FS₂| + |WL₁ - WL₂| + |BL₁ - BL₂| + slack
```

**Tests:**
- Calculate length between two components
- Verify Manhattan distance (not Euclidean)
- Add slack correctly
- Handle negative BL values

**Example:**
- Comp1: (100, 25, -5)
- Comp2: (150, 30, 10)
- Manhattan: |100-150| + |25-30| + |-5-10| = 50 + 5 + 15 = 70"
- With 24" slack: 94"

### Task 5.2: Implement calculate_voltage_drop (2 hours)

**Formula:** `Vdrop = Current × Resistance_per_foot × (Length/12)`

**Tests:**
- Calculate drop for various current/gauge/length combinations
- Use WIRE_RESISTANCE table from reference_data
- Return voltage in volts

### Task 5.3: Implement determine_min_gauge (3 hours)

**Complex:** Find minimum AWG meeting both constraints.

**Tests:**
- Calculate for various current/length/voltage combinations
- Verify voltage drop ≤ 5% of system voltage
- Verify current ≤ ampacity for gauge
- Return (awg_size, voltage_drop_volts, voltage_drop_percent)
- Test edge cases (very high current, very long wire)

**Algorithm:**
1. Try each AWG size from largest to smallest
2. Calculate voltage drop
3. Check if Vdrop ≤ 0.05 × Vsystem
4. Check if current ≤ ampacity
5. Return first size meeting both constraints

### Task 5.4: Implement assign_wire_color (1 hour)

**Tests:**
- Lookup color from SYSTEM_COLOR_MAP
- Use override if provided
- Return default color for unmapped codes
- Log warning for unmapped codes

### Task 5.5: Implement generate_wire_label (2 hours)

**Format:** `SYSTEM-CIRCUIT-SEGMENT`

**Tests:**
- Parse net name "Net-L105" → system="L", circuit="105"
- Use override values if provided
- Raise ValueError for invalid net names
- Format as "L-105-A"
- Handle various net name formats

**Regex:** `r'Net-([A-Z]+)(\d+)'`

### Task 5.6: Implement round_to_standard_awg (1 hour)

**Tests:**
- Round calculated gauge UP to next standard size
- 18.7 → 18 AWG
- 17.2 → 16 AWG
- Handle edge cases (< 22, > 2)

---

## Testing Checklist

- [ ] Manhattan distance calculated correctly
- [ ] Slack added to length
- [ ] Voltage drop formula correct
- [ ] Gauge determination meets both constraints (drop & ampacity)
- [ ] Color lookup works
- [ ] Label generation follows EAWMS format
- [ ] AWG rounding works correctly
- [ ] All tests pass

---

## Integration Notes

**Depends on:** reference_data.py (resistance, ampacity, colors), component.py (coordinates)

**Used by:** BOM generation, output modules

---

## Estimated Timeline

~11 hours total

---

## Completion Criteria

- All calculations verified against hand calculations
- Tests include realistic aircraft scenarios
- Module exports match interface contract
