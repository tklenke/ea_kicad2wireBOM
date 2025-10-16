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

### Task 3.3: Implement extract_components

**Critical:** Parse custom fields (FS, WL, BL, Load, Rating, etc.)

**Tests:**
- Extract basic component data (ref)
- Extract custom coordinate fields (FS, WL, BL)
- Extract Load and Rating fields
- Extract optional fields (Wire_Type, Wire_Color, etc.)
- Handle missing custom fields gracefully (return None)
- Handle various field name formats KiCad might use

**Implementation Notes:**
- Must experimentally verify which custom field formats KiCad exports
- May need helper function `parse_custom_field()` to handle variations
- Test with actual KiCad schematic, not just example.xml

**Time: 4-5 hours** (includes experimental validation)

---

### Task 3.4: Implement extract_nets

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
- `simple_two_component.net` - Minimal J1→SW1 connection
- `with_custom_fields.net` - Components with FS/WL/BL/Load/Rating
- `multi_net.net` - Multiple nets
- `missing_fields.net` - Components without custom fields

**Important:** Must create test fixtures using actual KiCad to verify field export format!

---

## Critical Validation Task

**Task 3.5: KiCad Field Export Validation**

1. Create test schematic in KiCad with custom fields
2. Add FS, WL, BL fields to components
3. Export netlist
4. Parse and verify fields appear
5. Document exact field names/formats KiCad uses
6. Adjust parser if needed

This may reveal that KiCad doesn't export custom component fields to netlist, requiring design changes!

**Time: 2 hours**

---

## Testing Checklist

- [ ] parse_netlist_file works with valid files
- [ ] FileNotFoundError for missing files
- [ ] extract_components returns Component objects
- [ ] Custom fields parsed correctly (FS, WL, BL, Load, Rating)
- [ ] Missing fields return None (not error)
- [ ] extract_nets returns correct dict structure
- [ ] Multi-node nets handled
- [ ] Real KiCad netlist tested (not just example.xml)

---

## Integration Notes

**Depends on:** component.py (imports Component)

**Used by:** All other modules need parsed data

---

## Estimated Timeline

- Task 3.1 (Explore): 2.5 hours
- Task 3.2 (Parse file): 1.5 hours
- Task 3.3 (Extract components): 4.5 hours
- Task 3.4 (Extract nets): 2.5 hours
- Task 3.5 (Validation): 2 hours

**Total: ~13 hours**

---

## Completion Criteria

- All tests pass with real KiCad netlists
- Custom fields reliably extracted
- Module exports match interface contract
- KiCad field export documented
