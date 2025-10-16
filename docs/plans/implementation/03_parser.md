# Work Package 03: Netlist Parser

## Overview

**Module:** `kicad2wireBOM/parser.py`

**Purpose:** Parse KiCad netlist files using kinparse library and extract component/net data.

**Dependencies:** component.py

**Estimated Effort:** 10-12 hours (includes kinparse exploration)

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 3: parser.py"

**Key Exports:**
- `parse_netlist_file(file_path: Path) -> object`
- `extract_components(parsed_netlist: object) -> list[Component]`
- `extract_nets(parsed_netlist: object) -> list[dict]`

---

## Key Tasks

### Task 3.1: Explore kinparse Data Structure

**Critical:** Before implementing, must understand kinparse output format.

1. Create `exploration/explore_kinparse.py` (temporary, not committed)
2. Use `data/example.xml` as test input
3. Document findings in code comments
4. Determine actual attribute names for components and nets

**Time: 2-3 hours**

---

### Task 3.2: Implement parse_netlist_file

**Tests:**
- Parse valid netlist file
- Handle missing file (FileNotFoundError)
- Handle malformed netlist (parse error)

**Implementation:**
```python
from pathlib import Path
from kinparse import parse_netlist as kinparse_parse

def parse_netlist_file(file_path: Path) -> object:
    """Parse KiCad netlist using kinparse"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Netlist file not found: {file_path}")
    return kinparse_parse(str(path))
```

**Time: 1-2 hours**

---

### Task 3.3: Implement parse_footprint_encoding Helper

**Purpose:** Parse component data embedded in footprint field.

**Format:** `<original_footprint>|(<fs>,<wl>,<bl>)<L|R><amps>`

**Tests:**
- Parse valid footprint encoding
- Extract coordinates (fs, wl, bl) as floats
- Extract type letter (L or R)
- Extract amperage as float
- Return original footprint (before |)
- Return None for footprint without encoding (no |)
- Raise ValueError for malformed encoding
- Handle negative coordinates (e.g., BL=-12.5)

**Implementation:**
```python
import re
from typing import Optional

def parse_footprint_encoding(footprint: str) -> Optional[dict]:
    """
    Parse footprint field with embedded component data.

    Format: <footprint>|(fs,wl,bl)<L|R><amps>
    Example: "LED_THT:LED_D5.0mm|(200.0,35.5,10.0)L2.5"

    Returns: {
        'footprint': 'LED_THT:LED_D5.0mm',
        'fs': 200.0,
        'wl': 35.5,
        'bl': 10.0,
        'load': 2.5,  # if type is L
        'rating': None  # if type is R, set rating instead
    }
    Or None if no encoding present.

    Raises: ValueError for malformed encoding
    """
    # Pattern: |(float,float,float)[LR]number
    pattern = r'\|([-\d.]+),([-\d.]+),([-\d.]+)\)([LR])([\d.]+)'
    match = re.search(pattern, footprint)

    if not match:
        # No encoding - check if | present (malformed) or just missing
        if '|' in footprint:
            raise ValueError(f"Malformed footprint encoding: {footprint}")
        return None  # No encoding present

    fs = float(match.group(1))
    wl = float(match.group(2))
    bl = float(match.group(3))
    type_letter = match.group(4)
    amps = float(match.group(5))

    # Extract original footprint (everything before |)
    original_footprint = footprint.split('|')[0]

    result = {
        'footprint': original_footprint,
        'fs': fs,
        'wl': wl,
        'bl': bl,
        'load': amps if type_letter == 'L' else None,
        'rating': amps if type_letter == 'R' else None
    }

    return result
```

**Time: 2 hours**

---

### Task 3.4: Implement extract_components

**Purpose:** Extract components from netlist with footprint-encoded data.

**Tests:**
- Extract basic component data (ref, footprint)
- Parse footprint encoding using parse_footprint_encoding()
- Create Component objects with extracted data
- Handle components without encoding (permissive mode)
- Test with multiple component types (L and R)
- Test with negative coordinates

**Implementation Notes:**
- For each component in netlist:
  - Get ref designator
  - Get footprint field value
  - Parse footprint encoding
  - Create Component with extracted data
- If encoding missing and strict mode: collect as error
- If encoding missing and permissive mode: use defaults, collect as warning

**Time: 3 hours**

---

### Task 3.5: Implement extract_nets

**Tests:**
- Extract net name and code
- Extract node connections (ref + pin)
- Extract optional Circuit_ID and System_Code fields
- Handle multi-node nets (3+ components)
- Return consistent dict structure

**Expected output format:**
```python
{
    'name': 'Net-L105',
    'code': '1',
    'nodes': [
        {'ref': 'J1', 'pin': '1'},
        {'ref': 'SW1', 'pin': '2'}
    ],
    'circuit_id': None,  # or string if present
    'system_code': None  # or string if present
}
```

**Time: 2-3 hours**

---

## Test Fixtures Required

Create in `tests/fixtures/`:
- `simple_two_component.net` - Minimal J1→SW1 connection with footprint encoding
- `with_footprint_encoding.net` - Various components with encoded data (L and R types)
- `multi_net.net` - Multiple nets
- `missing_encoding.net` - Components without footprint encoding (for permissive mode)
- `malformed_encoding.net` - Components with incorrect encoding format (for error handling)

**Example footprint field content:**
```
LED_THT:LED_D5.0mm|(200.0,35.5,10.0)L2.5
Button_Switch_THT:SW_PUSH_6mm|(150.0,30.0,0.0)R20
Connector:Conn_01x02|(100.5,25.0,-12.5)R15
```

**Important:** Test fixtures should be created from actual KiCad netlists to ensure field export works correctly!

---

## Footprint Field Export Confirmation

**CONFIRMED**: KiCad v9 reliably exports the full Footprint field content to netlists, including data after the `|` delimiter. Tested delimiters `,|{}[]#!` all export correctly.

No additional validation task needed - proceed with implementation using footprint encoding.

---

## Testing Checklist

- [ ] parse_netlist_file works with valid files
- [ ] FileNotFoundError for missing files
- [ ] parse_footprint_encoding extracts data correctly
- [ ] parse_footprint_encoding handles missing encoding (returns None)
- [ ] parse_footprint_encoding raises ValueError for malformed encoding
- [ ] extract_components returns Component objects with encoded data
- [ ] Footprint encoding parsed correctly (FS, WL, BL, Load/Rating)
- [ ] Negative coordinates handled (BL=-12.5)
- [ ] Both L and R type letters work correctly
- [ ] extract_nets returns correct dict structure
- [ ] Multi-node nets handled
- [ ] Real KiCad netlist tested (not just example.xml)

---

## Integration Notes

**Depends on:** component.py (imports Component)

**Used by:** All other modules need parsed data

---

## Estimated Timeline

- Task 3.1 (Explore kinparse): 2.5 hours
- Task 3.2 (Parse file): 1.5 hours
- Task 3.3 (parse_footprint_encoding): 2 hours
- Task 3.4 (extract_components): 3 hours
- Task 3.5 (extract_nets): 2.5 hours

**Total: ~11.5 hours**

---

## Completion Criteria

- All tests pass with real KiCad netlists
- Footprint encoding reliably parsed
- Module exports match interface contract
- Component data (FS, WL, BL, Load/Rating) correctly extracted
- parse_footprint_encoding helper function complete and tested
