# Work Package 08: CSV Output

## Overview

**Module:** `kicad2wireBOM/output_csv.py`

**Purpose:** Generate CSV files from WireBOM in builder and engineering modes.

**Dependencies:** wire_bom.py

**Estimated Effort:** 4-5 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 8: output_csv.py"

**Key Functions:**
- `write_builder_csv(bom, output_path)`
- `write_engineering_csv(bom, output_path)`

---

## Key Tasks

### Task 8.1: Implement write_builder_csv (2 hours)

**Column Order:**
- Wire Label, From, To, Wire Gauge, Wire Color, Length, Wire Type, Warnings

**Tests:**
- Create CSV with header row
- Write single wire
- Write multiple wires
- Handle empty BOM (header only)
- Optional fields write as empty string if None
- Warnings column lists all warnings (comma-separated or newline-separated)

**Implementation:**
```python
import csv
from pathlib import Path

def write_builder_csv(bom: WireBOM, output_path: Path) -> None:
    fieldnames = [
        'Wire Label', 'From', 'To', 'Wire Gauge',
        'Wire Color', 'Length', 'Wire Type', 'Warnings'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for wire in bom.wires:
            writer.writerow({
                'Wire Label': wire.wire_label,
                'From': wire.from_ref,
                'To': wire.to_ref,
                'Wire Gauge': wire.wire_gauge or '',
                'Wire Color': wire.wire_color or '',
                'Length': wire.length or '',
                'Wire Type': wire.wire_type or '',
                'Warnings': '; '.join(wire.warnings) if wire.warnings else ''
            })
```

### Task 8.2: Implement write_engineering_csv (2 hours)

**Column Order:**
- All builder columns +
- Calculated Min Gauge, Current, Voltage Drop (V), Voltage Drop (%),
- From Coords, To Coords, Calculated Length

**Tests:**
- Write CSV with all columns
- Engineering fields write correctly
- Coordinates formatted as tuples or "FS,WL,BL"
- Numeric values formatted appropriately

**Implementation:** Similar to builder but with extended fieldnames.

### Task 8.3: Test CSV Validity (1 hour)

**Tests:**
- Generated CSV can be read back with csv.DictReader
- No encoding issues with special characters
- Commas in warnings don't break CSV format
- Newlines handled correctly

---

## Testing Checklist

- [ ] Builder CSV has correct columns
- [ ] Engineering CSV has all columns
- [ ] Empty BOM creates valid CSV (header only)
- [ ] Multiple wires write correctly
- [ ] CSV can be read back and parsed
- [ ] Optional fields handled (None → empty string)
- [ ] All tests pass

---

## Integration Notes

**Depends on:** wire_bom.py

**Used by:** CLI

---

## Estimated Timeline

~5 hours total

---

## Completion Criteria

- Both CSV modes work
- Generated CSV is valid and parseable
- Module exports match interface contract
