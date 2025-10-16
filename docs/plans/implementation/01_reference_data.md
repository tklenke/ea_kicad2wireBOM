# Work Package 01: Reference Data Module

## Overview

**Module:** `kicad2wireBOM/reference_data.py`

**Purpose:** Provide reference data tables and constants for wire calculations (resistance, ampacity, color mappings).

**Dependencies:** None (foundation module)

**Estimated Effort:** 8-12 hours

**Programmer Requirements:**
- Python dataclasses/constants
- Understanding of lookup tables
- Ability to extract data from reference documents

---

## Background

This module provides the factual data needed for wire gauge calculations and color assignments:

- **Wire Resistance**: Ohms per foot for each AWG size (needed for voltage drop calculations)
- **Wire Ampacity**: Maximum safe current for each AWG size
- **System Color Mapping**: System code → wire color assignments per EAWMS
- **Default Configuration**: System-wide defaults (voltage, slack length, etc.)

All data must be extracted from existing reference materials in `docs/references/`.

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 1: reference_data.py" for complete interface definition.

**Key Exports:**
```python
STANDARD_AWG_SIZES: list[int]
DEFAULT_CONFIG: dict
WIRE_RESISTANCE: dict[int, float]
WIRE_AMPACITY: dict[int, float]
SYSTEM_COLOR_MAP: dict[str, str]

def load_custom_resistance_table(config_dict: dict) -> dict[int, float]
def load_custom_ampacity_table(config_dict: dict) -> dict[int, float]
def load_custom_color_map(config_dict: dict) -> dict[str, str]
```

---

## Tasks

### Task 1.1: Extract Wire Resistance Data from Aeroelectric Connection

**Objective:** Create `WIRE_RESISTANCE` lookup table from reference materials.

**Source:** `docs/references/aeroelectric_connection/` - Look for Chapter 5 wire resistance tables.

**TDD Steps:**

1. **Write test** (RED):
```python
# tests/test_reference_data.py
def test_wire_resistance_table_contains_standard_sizes():
    """Test that resistance table includes all standard AWG sizes"""
    from kicad2wireBOM.reference_data import WIRE_RESISTANCE, STANDARD_AWG_SIZES

    for awg in STANDARD_AWG_SIZES:
        assert awg in WIRE_RESISTANCE, f"Missing resistance data for {awg} AWG"
        assert WIRE_RESISTANCE[awg] > 0, f"Invalid resistance for {awg} AWG"

def test_wire_resistance_values_are_reasonable():
    """Test that resistance values decrease as wire size increases"""
    from kicad2wireBOM.reference_data import WIRE_RESISTANCE

    # Larger AWG number = smaller wire = higher resistance
    assert WIRE_RESISTANCE[22] > WIRE_RESISTANCE[20]
    assert WIRE_RESISTANCE[20] > WIRE_RESISTANCE[18]
    assert WIRE_RESISTANCE[10] < WIRE_RESISTANCE[12]
```

2. **Implement** (GREEN):
   - Read Aeroelectric Connection Chapter 5 (check `ae__page61.txt` or similar files)
   - Extract resistance values for AWG sizes: 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2
   - Create `WIRE_RESISTANCE` dict in module
   - Document source in docstring

3. **Commit:**
```bash
git add kicad2wireBOM/reference_data.py tests/test_reference_data.py
git commit -m "Add wire resistance lookup table from Aeroelectric Connection

- Extract resistance values (ohms/foot) for AWG 2-22
- Source: Aeroelectric Connection Chapter 5
- Test resistance table completeness and ordering

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Expected Output:**
```python
WIRE_RESISTANCE = {
    22: 0.016,   # ohms per foot
    20: 0.010,
    18: 0.0064,
    16: 0.004,
    14: 0.0025,
    12: 0.0016,
    10: 0.001,
    8: 0.00063,
    6: 0.0004,
    4: 0.00025,
    2: 0.00016
}
```

---

### Task 1.2: Extract Wire Ampacity Data

**Objective:** Create `WIRE_AMPACITY` lookup table.

**Source:** Aeroelectric Connection ampacity guidance (Bob Nuckolls' recommendations for bundled wire)

**TDD Steps:**

1. **Write test** (RED):
```python
def test_wire_ampacity_table_contains_standard_sizes():
    """Test that ampacity table includes all standard AWG sizes"""
    from kicad2wireBOM.reference_data import WIRE_AMPACITY, STANDARD_AWG_SIZES

    for awg in STANDARD_AWG_SIZES:
        assert awg in WIRE_AMPACITY, f"Missing ampacity data for {awg} AWG"
        assert WIRE_AMPACITY[awg] > 0, f"Invalid ampacity for {awg} AWG"

def test_wire_ampacity_increases_with_wire_size():
    """Test that ampacity increases as wire size increases"""
    from kicad2wireBOM.reference_data import WIRE_AMPACITY

    # Larger AWG number = smaller wire = lower ampacity
    assert WIRE_AMPACITY[22] < WIRE_AMPACITY[20]
    assert WIRE_AMPACITY[20] < WIRE_AMPACITY[18]
    assert WIRE_AMPACITY[10] > WIRE_AMPACITY[12]
```

2. **Implement** (GREEN):
   - Extract ampacity values from Aeroelectric Connection
   - Note: Use bundled wire values (conservative), not free-air
   - Create `WIRE_AMPACITY` dict
   - Document source and assumptions

3. **Commit:**
```bash
git commit -m "Add wire ampacity lookup table

- Extract max current ratings for AWG 2-22
- Use bundled wire values (conservative)
- Source: Aeroelectric Connection practical ampacity guidance
- Test ampacity completeness and ordering"
```

**Expected Output:**
```python
WIRE_AMPACITY = {
    22: 5,      # max amps (bundled)
    20: 7.5,
    18: 10,
    16: 13,
    14: 17,
    12: 23,
    10: 33,
    8: 46,
    6: 60,
    4: 80,
    2: 100
}
```

---

### Task 1.3: Extract System Code Color Mapping

**Objective:** Create `SYSTEM_COLOR_MAP` from EAWMS documentation.

**Source:** `docs/ea_wire_marking_standard.md` - system code definitions and color assignments

**TDD Steps:**

1. **Write test** (RED):
```python
def test_system_color_map_contains_common_codes():
    """Test that color map includes common system codes"""
    from kicad2wireBOM.reference_data import SYSTEM_COLOR_MAP

    # Test common codes exist
    assert 'L' in SYSTEM_COLOR_MAP  # Lighting
    assert 'P' in SYSTEM_COLOR_MAP  # Power
    assert 'G' in SYSTEM_COLOR_MAP  # Ground
    assert 'R' in SYSTEM_COLOR_MAP  # Radio

    # Test values are strings
    assert isinstance(SYSTEM_COLOR_MAP['L'], str)
    assert len(SYSTEM_COLOR_MAP['L']) > 0

def test_system_color_map_follows_standards():
    """Test that standard color assignments are correct"""
    from kicad2wireBOM.reference_data import SYSTEM_COLOR_MAP

    # Verify standard mappings per EAWMS
    assert SYSTEM_COLOR_MAP['G'] == 'Black'  # Ground is always black
    assert SYSTEM_COLOR_MAP['P'] == 'Red'    # Power is red
```

2. **Implement** (GREEN):
   - Read `docs/ea_wire_marking_standard.md`
   - Extract all system codes and their color assignments
   - Create `SYSTEM_COLOR_MAP` dict
   - Document source

3. **Commit:**
```bash
git commit -m "Add system code to color mapping table

- Extract color assignments for all system codes
- Source: docs/ea_wire_marking_standard.md
- Test common codes and standard assignments"
```

**Expected Output:**
```python
SYSTEM_COLOR_MAP = {
    'L': 'White',         # Lighting
    'P': 'Red',           # Power
    'G': 'Black',         # Ground
    'R': 'Gray',          # Radio/Nav
    'A': 'Blue',          # Avionics
    'E': 'Yellow',        # Engine
    # ... etc (extract all codes from EAWMS doc)
}
```

---

### Task 1.4: Define Standard Constants

**Objective:** Create module constants for standard values.

**TDD Steps:**

1. **Write test** (RED):
```python
def test_standard_awg_sizes_is_sorted():
    """Test that standard AWG sizes list is correctly ordered"""
    from kicad2wireBOM.reference_data import STANDARD_AWG_SIZES

    # Should be largest to smallest (descending)
    assert STANDARD_AWG_SIZES[0] > STANDARD_AWG_SIZES[-1]
    assert 22 in STANDARD_AWG_SIZES
    assert 20 in STANDARD_AWG_SIZES
    assert 2 in STANDARD_AWG_SIZES

def test_default_config_has_required_keys():
    """Test that default config contains all required settings"""
    from kicad2wireBOM.reference_data import DEFAULT_CONFIG

    assert 'system_voltage' in DEFAULT_CONFIG
    assert 'slack_length' in DEFAULT_CONFIG
    assert 'voltage_drop_percent' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['system_voltage'] == 12  # Per design spec
    assert DEFAULT_CONFIG['slack_length'] == 24    # Per design spec
```

2. **Implement** (GREEN):
```python
# Standard AWG wire sizes (largest to smallest)
STANDARD_AWG_SIZES = [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]

# Default configuration values
DEFAULT_CONFIG = {
    'system_voltage': 12,          # volts
    'slack_length': 24,            # inches
    'voltage_drop_percent': 0.05,  # 5%
    'permissive_mode': False,
    'engineering_mode': False
}
```

3. **Commit:**
```bash
git commit -m "Add standard AWG sizes and default configuration

- Define STANDARD_AWG_SIZES list (AWG 2-22)
- Create DEFAULT_CONFIG with system defaults
- Test configuration completeness"
```

---

### Task 1.5: Implement Custom Table Loading Functions

**Objective:** Allow configuration files to override default tables.

**TDD Steps:**

1. **Write test** (RED):
```python
def test_load_custom_resistance_table_overrides_defaults():
    """Test that custom resistance values override defaults"""
    from kicad2wireBOM.reference_data import load_custom_resistance_table, WIRE_RESISTANCE

    config = {
        'wire_resistance': {
            22: 0.020,  # Custom value
            20: 0.015
        }
    }

    custom = load_custom_resistance_table(config)

    assert custom[22] == 0.020  # Custom value used
    assert custom[20] == 0.015
    # Other values should come from defaults
    assert custom[18] == WIRE_RESISTANCE[18]

def test_load_custom_resistance_table_with_no_custom_returns_defaults():
    """Test that empty config returns default table"""
    from kicad2wireBOM.reference_data import load_custom_resistance_table, WIRE_RESISTANCE

    config = {}
    custom = load_custom_resistance_table(config)

    assert custom == WIRE_RESISTANCE
```

2. **Implement** (GREEN):
```python
def load_custom_resistance_table(config_dict: dict) -> dict[int, float]:
    """
    Load wire resistance table with optional custom overrides.

    Args:
        config_dict: Configuration dict that may contain 'wire_resistance' key

    Returns:
        Resistance table (ohms per foot) with custom values merged
    """
    result = WIRE_RESISTANCE.copy()

    if 'wire_resistance' in config_dict:
        result.update(config_dict['wire_resistance'])

    return result

def load_custom_ampacity_table(config_dict: dict) -> dict[int, float]:
    """
    Load wire ampacity table with optional custom overrides.

    Args:
        config_dict: Configuration dict that may contain 'wire_ampacity' key

    Returns:
        Ampacity table (max amps) with custom values merged
    """
    result = WIRE_AMPACITY.copy()

    if 'wire_ampacity' in config_dict:
        result.update(config_dict['wire_ampacity'])

    return result

def load_custom_color_map(config_dict: dict) -> dict[str, str]:
    """
    Load system color map with optional custom overrides.

    Args:
        config_dict: Configuration dict that may contain 'system_colors' key

    Returns:
        Color map with custom values merged
    """
    result = SYSTEM_COLOR_MAP.copy()

    if 'system_colors' in config_dict:
        result.update(config_dict['system_colors'])

    return result
```

3. **Write additional tests** for ampacity and color map loading

4. **Commit:**
```bash
git commit -m "Add custom table loading functions

- Implement load_custom_resistance_table()
- Implement load_custom_ampacity_table()
- Implement load_custom_color_map()
- Allow config files to override default values
- Test override behavior and defaults"
```

---

### Task 1.6: Add Module Documentation

**Objective:** Complete module with proper documentation.

1. **Add file header:**
```python
# ABOUTME: Reference data tables for wire calculations and standards
# ABOUTME: Provides resistance, ampacity, and color mapping lookup tables

"""
Reference data for kicad2wireBOM wire calculations.

This module contains factual data extracted from:
- Aeroelectric Connection (Bob Nuckolls) - resistance and ampacity
- Experimental Aircraft Wire Marking Standard (EAWMS) - color mappings
- MIL-W-5088L principles - wire sizing standards

All data is conservative for bundled aircraft wiring applications.
"""
```

2. **Add docstrings** to all data structures and functions

3. **Create module README section** documenting data sources

4. **Commit:**
```bash
git commit -m "Add comprehensive module documentation

- Document data sources and extraction methodology
- Add docstrings for all exports
- Note conservative values for bundled wire"
```

---

## Testing Checklist

Before marking this module complete, verify:

- [ ] All tests pass: `pytest tests/test_reference_data.py -v`
- [ ] `WIRE_RESISTANCE` table complete for AWG 2-22
- [ ] `WIRE_AMPACITY` table complete for AWG 2-22
- [ ] `SYSTEM_COLOR_MAP` includes all codes from EAWMS doc
- [ ] Constants defined correctly
- [ ] Custom loading functions work with overrides
- [ ] Custom loading functions preserve defaults for non-overridden values
- [ ] Module has proper ABOUTME header
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Data sources documented

---

## Integration Notes

This module has **no dependencies** and can be implemented independently.

Other modules will import from this module:
- `wire_calculator.py` - uses resistance, ampacity, and color map
- `validator.py` - uses ampacity for validation
- All modules - use `STANDARD_AWG_SIZES` and `DEFAULT_CONFIG`

Ensure all exports are available at module level (not nested in classes/functions).

---

## Estimated Timeline

- Task 1.1 (Resistance): 2 hours
- Task 1.2 (Ampacity): 1.5 hours
- Task 1.3 (Color Map): 2 hours
- Task 1.4 (Constants): 1 hour
- Task 1.5 (Custom Loading): 2 hours
- Task 1.6 (Documentation): 1.5 hours

**Total: ~10 hours**

---

## Completion Criteria

This work package is complete when:

1. All tests pass
2. Module exports match interface contract in `00_overview_and_contracts.md`
3. Data extracted from reference materials is accurate
4. Code committed to git with proper commit messages
5. Integration checklist verified

---

## Questions?

Refer to:
- Interface contract: `docs/plans/implementation/00_overview_and_contracts.md`
- Design spec: `docs/plans/kicad2wireBOM_design.md`
- Reference materials: `docs/references/`
- Wire marking standard: `docs/ea_wire_marking_standard.md`
