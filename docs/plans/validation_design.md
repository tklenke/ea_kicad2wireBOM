# Validation & Error Handling Design

**Date**: 2025-10-22
**Purpose**: Design validation architecture to catch schematic errors and provide helpful feedback
**Status**: Planning Phase

---

## Overview

The tool currently processes schematics but doesn't adequately validate inputs or report errors. This design addresses validation requirements discovered from test_05 fixture variants.

---

## Test Fixtures Driving Design

### test_05A: Missing All Wire Labels
- **Issue**: All 7 circuit ID labels missing from schematic
- **Current Behavior**: Produces empty BOM (CSV header only)
- **Expected Behavior**:
  - **Strict Mode**: Error with clear message "No circuit ID labels found in schematic"
  - **Permissive Mode**: Warning, generate fallback labels (UNK1A, UNK2A, etc.)

### test_05B: Duplicate Circuit Label
- **Issue**: Label "G3A" appears twice, "G4A" missing
- **Current Behavior**: Silently produces 6 wires instead of 7, missing G4A connection
- **Expected Behavior**:
  - **Strict Mode**: Error "Duplicate circuit ID 'G3A' found on wire segments"
  - **Permissive Mode**: Warning, rename duplicates (G3A, G3A-2), flag in warnings column

### test_05C: Non-Circuit Labels Present
- **Issue**: Labels "24AWG" and "10AWG" present (don't match circuit ID pattern)
- **Current Behavior**: Produces correct 7 wires, ignores invalid labels
- **Expected Behavior**:
  - Validate labels against circuit ID pattern: `^[A-Z]\d+[A-Z]$` or `^[A-Z]-\d+-[A-Z]$`
  - Invalid labels → move to wire "notes" field
  - Generate warning: "Non-circuit label '24AWG' found, added to notes"
  - Multiple invalid labels → concatenate with spaces in notes field

---

## Validation Architecture

### 1. Data Model Changes

**Add `notes` field to WireConnection**:
```python
@dataclass
class WireConnection:
    wire_label: str
    from_component: Optional[str]
    from_pin: Optional[str]
    to_component: Optional[str]
    to_pin: Optional[str]
    wire_gauge: int
    wire_color: str
    length: float
    wire_type: str
    notes: str  # NEW: Concatenated non-circuit labels and annotations
    warnings: List[str]
```

**CSV Output Columns**:
- Add "Notes" column after "Wire Type", before "Warnings"

---

### 2. Label Classification

**Circuit ID Pattern** (from design doc Section 2.3):
- Compact: `^[A-Z]\d+[A-Z]$` (e.g., L1A, P12B, G105C)
- Dashes: `^[A-Z]-\d+-[A-Z]$` (e.g., L-1-A, P-12-B)

**Label Processing Algorithm**:
```python
def classify_labels(labels: List[str]) -> tuple[Optional[str], List[str]]:
    """
    Classify labels as circuit ID or notes.

    Returns:
        (circuit_id, notes_list)
        - circuit_id: First valid circuit ID found, or None
        - notes_list: All non-circuit labels
    """
    circuit_id_pattern = re.compile(r'^[A-Z]-?\d+-?[A-Z]$')

    circuit_id = None
    notes = []

    for label in labels:
        if circuit_id_pattern.match(label):
            if circuit_id is None:
                circuit_id = label  # First valid ID
            else:
                # Multiple circuit IDs - validation error handled separately
                pass
        else:
            notes.append(label)

    return circuit_id, notes
```

---

### 3. Validation Checks

#### Check 1: Wire Has No Circuit ID Label

**Detection**: Wire segment has labels but none match circuit ID pattern

**Strict Mode**:
- Error: "Wire segment {uuid} at ({x1},{y1})-({x2},{y2}) has no valid circuit ID label"
- Suggestion: "Add circuit ID label (e.g., L1A, P12B) to wire in schematic"
- Exit code: 1

**Permissive Mode**:
- Warning: "Wire segment has no valid circuit ID, generating fallback label"
- Generate: `UNK{index}A` (e.g., UNK1A, UNK2A)
- Add to warnings column
- Continue processing

#### Check 2: Wire Has Multiple Circuit ID Labels

**Detection**: Wire segment has 2+ labels matching circuit ID pattern

**Strict Mode**:
- Error: "Wire segment has multiple circuit IDs: {label1}, {label2}"
- Suggestion: "Remove extra labels or use one as circuit ID, others as notes"
- Exit code: 1

**Permissive Mode**:
- Warning: "Multiple circuit IDs on wire, using first: {label1}"
- Use first circuit ID found
- Add others to notes field
- Add to warnings column

#### Check 3: Duplicate Circuit IDs Across Wires (test_05B)

**Detection**: Same circuit ID appears on multiple wire segments

**Example**: test_05B has G3A twice, G4A missing

**Strict Mode**:
- Error: "Duplicate circuit ID 'G3A' found on {N} wire segments"
- List wire segments with positions
- Suggestion: "Each wire must have unique circuit ID. Check segment letters (A, B, C...)"
- Exit code: 1

**Permissive Mode**:
- Warning: "Duplicate circuit ID 'G3A', making unique"
- Rename: First keeps original, subsequent get suffix: G3A-2, G3A-3
- Add to warnings column
- Continue processing

#### Check 4: No Circuit IDs Found in Entire Schematic (test_05A)

**Detection**: Schematic parsed successfully but zero circuit ID labels found

**Strict Mode**:
- Error: "No circuit ID labels found in schematic"
- Suggestion: "Add wire labels matching pattern [SYSTEM][CIRCUIT][SEGMENT] (e.g., L1A, P12B)"
- Exit code: 1

**Permissive Mode**:
- Warning: "No circuit ID labels found, generating fallback labels for all wires"
- Generate: UNK1A, UNK2A, ... UNK{N}A
- Add to warnings column for each wire
- Continue processing (produces BOM with fallback labels)

#### Check 5: Non-Circuit Labels (test_05C)

**Detection**: Label on wire doesn't match circuit ID pattern

**Examples**: "24AWG", "10AWG", "HIGH_CURRENT", "SHIELDED"

**Behavior** (Both Modes - No Error):
- Info/Debug message: "Non-circuit label '{label}' found on wire, adding to notes"
- Add label to wire notes field
- Multiple non-circuit labels: concatenate with spaces
- No warning in warnings column (this is expected behavior)

#### Check 6: Orphaned Labels

**Detection**: Label positioned far from any wire segment (distance > threshold)

**Behavior** (Both Modes):
- Warning: "Label '{label}' at position ({x},{y}) not associated with any wire"
- Suggestion: "Move label closer to wire or check wire routing"
- Distance threshold: 10mm (configurable)
- Add to global warnings, not per-wire warnings

---

### 4. Operating Modes

#### Strict Mode (Default)
- Error and abort on validation failures
- Ensures complete, validated schematics
- Exit code 1 on error
- Recommended for final BOMs

#### Permissive Mode (`--permissive` flag)
- Warnings instead of errors
- Apply fallback values (UNK labels, duplicate renaming)
- Continue processing, flag issues in warnings column
- Useful for iterative design and draft BOMs
- Always exits with code 0 if parsing succeeds

---

### 5. Output Changes

#### CSV Columns (Updated)
```
Wire Label, From Component, From Pin, To Component, To Pin,
Wire Gauge, Wire Color, Length, Wire Type, Notes, Warnings
```

**Notes Column**:
- Concatenated non-circuit labels (space-separated)
- Empty if no non-circuit labels
- Example: "24AWG HIGH_CURRENT"

**Warnings Column**:
- Concatenated validation warnings (semicolon-separated)
- Empty if no warnings
- Examples:
  - "No valid circuit ID, generated fallback label UNK1A"
  - "Duplicate circuit ID, renamed to G3A-2"
  - "Multiple circuit IDs on wire, using first"

---

### 6. Implementation Modules

#### New Module: `kicad2wireBOM/validator.py`

```python
"""
ABOUTME: Validation module for schematic data quality checks
ABOUTME: Detects missing labels, duplicates, and malformed circuit IDs
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import re

@dataclass
class ValidationError:
    """Validation error or warning"""
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None
    wire_uuid: Optional[str] = None
    position: Optional[tuple[float, float]] = None

@dataclass
class ValidationResult:
    """Result of validation checks"""
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def should_abort(self, strict_mode: bool) -> bool:
        return strict_mode and self.has_errors()

class SchematicValidator:
    """Validates schematic data for BOM generation"""

    CIRCUIT_ID_PATTERN = re.compile(r'^[A-Z]-?\d+-?[A-Z]$')

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.result = ValidationResult(errors=[], warnings=[])

    def validate_all(self, wires, labels, components) -> ValidationResult:
        """Run all validation checks"""
        self._check_no_labels(wires, labels)
        self._check_wire_labels(wires)
        self._check_duplicate_circuit_ids(wires)
        self._check_orphaned_labels(labels, wires)
        return self.result

    def _check_no_labels(self, wires, labels):
        """Check for schematic with no circuit ID labels"""
        circuit_labels = [l for l in labels if self.CIRCUIT_ID_PATTERN.match(l.text)]
        if len(circuit_labels) == 0:
            self._add_error(
                "No circuit ID labels found in schematic",
                suggestion="Add wire labels matching pattern [SYSTEM][CIRCUIT][SEGMENT] (e.g., L1A, P12B)"
            )

    def _check_wire_labels(self, wires):
        """Check each wire has valid circuit ID"""
        for wire in wires:
            circuit_ids = [l for l in wire.labels if self.CIRCUIT_ID_PATTERN.match(l)]

            if len(circuit_ids) == 0:
                self._add_error(
                    f"Wire segment {wire.uuid} has no valid circuit ID label",
                    suggestion="Add circuit ID label to wire",
                    wire_uuid=wire.uuid
                )
            elif len(circuit_ids) > 1:
                self._add_error(
                    f"Wire has multiple circuit IDs: {', '.join(circuit_ids)}",
                    suggestion="Remove extra labels or move to notes",
                    wire_uuid=wire.uuid
                )

    def _check_duplicate_circuit_ids(self, wires):
        """Check for duplicate circuit IDs across wires"""
        circuit_id_counts: Dict[str, int] = {}
        for wire in wires:
            if wire.circuit_id:
                circuit_id_counts[wire.circuit_id] = circuit_id_counts.get(wire.circuit_id, 0) + 1

        for circuit_id, count in circuit_id_counts.items():
            if count > 1:
                self._add_error(
                    f"Duplicate circuit ID '{circuit_id}' found on {count} wire segments",
                    suggestion="Each wire must have unique circuit ID. Check segment letters."
                )

    def _check_orphaned_labels(self, labels, wires, threshold=10.0):
        """Check for labels not associated with wires"""
        # Implementation: Check label-to-wire distances
        pass

    def _add_error(self, message: str, suggestion: Optional[str] = None,
                   wire_uuid: Optional[str] = None):
        """Add error or warning based on strict mode"""
        error = ValidationError(
            severity="error" if self.strict_mode else "warning",
            message=message,
            suggestion=suggestion,
            wire_uuid=wire_uuid
        )

        if self.strict_mode:
            self.result.errors.append(error)
        else:
            self.result.warnings.append(error)
```

---

### 7. Integration Points

#### In `label_association.py`:
- Classify labels into circuit IDs vs notes using pattern matching
- Store both circuit_id and notes list on WireSegment

#### In `bom_generator.py`:
- Pass notes to WireConnection when creating BOM entries
- Concatenate notes list with space separator

#### In `__main__.py`:
- Add `--permissive` flag for mode selection
- Run validator before BOM generation
- If validation fails in strict mode: print errors and exit(1)
- If validation succeeds or permissive mode: continue with warnings

#### In `output_csv.py`:
- Add "Notes" column to CSV output
- Format warnings column (semicolon-separated if multiple)

---

### 8. Expected Test Results

After implementing validation:

**test_05A** (no labels):
- **Strict Mode**: Error "No circuit ID labels found", exit 1, no CSV output
- **Permissive Mode**: Warning, generates CSV with UNK1A...UNK7A, warnings column populated

**test_05B** (duplicate G3A):
- **Strict Mode**: Error "Duplicate circuit ID 'G3A'", exit 1, no CSV output
- **Permissive Mode**: Warning, generates CSV with G3A and G3A-2, warnings column shows "Duplicate circuit ID, renamed to G3A-2"

**test_05C** (24AWG, 10AWG labels):
- **Both Modes**: Success, generates 7 wires with valid circuit IDs
- Notes column contains "24AWG" and "10AWG" on respective wires
- No warnings (expected behavior)

---

## Implementation Priority

**Phase 6A**: Input Validation & Error Handling

**Tasks**:
1. Add `notes` field to WireConnection data model
2. Create `validator.py` module with SchematicValidator class
3. Update label_association.py to classify labels (circuit ID vs notes)
4. Update bom_generator.py to pass notes to WireConnection
5. Add validation checks 1-6
6. Add `--permissive` flag to CLI
7. Update CSV output to include Notes column
8. Write unit tests for validator
9. Write integration tests using test_05A, test_05B, test_05C
10. Update documentation

**Success Criteria**:
- test_05A: Errors in strict mode, generates fallback labels in permissive mode
- test_05B: Detects duplicates, renames in permissive mode
- test_05C: Moves non-circuit labels to notes field
- All validation checks produce clear, actionable error messages
- Strict/permissive modes work as specified

---

## Open Questions

1. Should orphaned labels (far from wires) be errors or warnings in strict mode?
   - **Recommendation**: Warnings in both modes (informational, not blocking)

2. Should missing component data (footprint encoding) be part of this validation phase?
   - **Recommendation**: Yes, add Check 7 for missing/malformed footprint data

3. What should the distance threshold be for orphaned labels?
   - **Current**: 10mm default (from design doc)
   - **Recommendation**: Keep 10mm, make configurable via `--label-threshold`

4. Should we validate system codes (L, P, G, etc.)?
   - **Recommendation**: Warning if system code not in known list, not error

---

## References

- **Design Doc**: `docs/plans/kicad2wireBOM_design.md` Section 6 (Validation and Error Handling)
- **Test Fixtures**: `tests/fixtures/test_05*.kicad_sch`
- **Expected Outputs**: `docs/input/test_05*_out_current.csv`
