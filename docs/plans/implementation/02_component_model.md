# Work Package 02: Component Model

## Overview

**Module:** `kicad2wireBOM/component.py`

**Purpose:** Represent components with aircraft coordinates and electrical properties. Provide component type identification and validation logic.

**Dependencies:** None (foundation module, though will be enhanced with reference_data later)

**Estimated Effort:** 6-8 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 2: component.py" for complete interface.

**Key Exports:**
- `Component` dataclass
- `identify_component_type(ref: str) -> str`
- `validate_component(component: Component, permissive: bool) -> list[str]`

---

## Tasks

### Task 2.1: Implement Component Dataclass

**TDD Steps:**

1. **Write test** (RED):
```python
# tests/test_component.py
# ABOUTME: Tests for component data model
# ABOUTME: Validates Component dataclass and property methods

from kicad2wireBOM.component import Component

def test_create_component_with_required_fields():
    """Test creating component with minimum required fields"""
    comp = Component(
        ref="J1",
        fs=100.0,
        wl=25.0,
        bl=-5.0
    )

    assert comp.ref == "J1"
    assert comp.fs == 100.0
    assert comp.wl == 25.0
    assert comp.bl == -5.0

def test_component_coordinates_property():
    """Test that coordinates property returns tuple"""
    comp = Component(ref="SW1", fs=120.0, wl=30.0, bl=0.0)

    coords = comp.coordinates
    assert coords == (120.0, 30.0, 0.0)
    assert isinstance(coords, tuple)

def test_component_with_load_value():
    """Test component with load (consuming device)"""
    comp = Component(
        ref="LIGHT1",
        fs=200.0,
        wl=35.0,
        bl=10.0,
        load=5.0  # 5 amp load
    )

    assert comp.load == 5.0
    assert comp.rating is None

def test_component_with_rating_value():
    """Test component with rating (pass-through device)"""
    comp = Component(
        ref="SW1",
        fs=120.0,
        wl=30.0,
        bl=0.0,
        rating=15.0  # 15 amp rating
    )

    assert comp.rating == 15.0
    assert comp.load is None
```

2. **Implement** (GREEN):
```python
# ABOUTME: Component data model for aircraft electrical system
# ABOUTME: Represents components with coordinates and electrical properties

from dataclasses import dataclass
from typing import Optional

@dataclass
class Component:
    """
    Component with aircraft coordinates and electrical properties.

    Coordinates use standard aircraft reference system:
    - FS (Fuselage Station): longitudinal position (inches from datum)
    - WL (Waterline): vertical position (inches from datum)
    - BL (Buttline): lateral position (inches from centerline, +right/-left)
    """
    # Required fields
    ref: str                          # Reference designator (e.g., "J1", "SW1")
    fs: float                         # Fuselage Station (inches)
    wl: float                         # Waterline (inches)
    bl: float                         # Buttline (inches)

    # Electrical properties (mutually exclusive)
    load: Optional[float] = None      # Current drawn (amps) - for consuming devices
    rating: Optional[float] = None    # Current capacity (amps) - for pass-through devices

    # Optional wire specifications
    wire_type: Optional[str] = None       # e.g., "M22759/16"
    wire_color: Optional[str] = None      # Color override
    wire_gauge: Optional[str] = None      # e.g., "20 AWG"
    connector_type: Optional[str] = None  # e.g., "D-Sub"

    @property
    def coordinates(self) -> tuple[float, float, float]:
        """Return (FS, WL, BL) coordinate tuple"""
        return (self.fs, self.wl, self.bl)
```

3. **Commit:**
```bash
git commit -m "Add Component dataclass with aircraft coordinates

- Implement Component with FS/WL/BL coordinates
- Add load/rating electrical properties
- Add optional wire specification fields
- Implement coordinates property
- Test component creation and properties"
```

---

### Task 2.2: Implement Component Type Properties

**TDD Steps:**

1. **Write tests** (RED):
```python
def test_component_is_source_property():
    """Test identification of source components"""
    bat = Component(ref="BAT1", fs=50.0, wl=10.0, bl=0.0)
    gen = Component(ref="GEN1", fs=60.0, wl=15.0, bl=0.0)
    j_conn = Component(ref="J1", fs=100.0, wl=20.0, bl=5.0)
    light = Component(ref="LIGHT1", fs=200.0, wl=30.0, bl=10.0)

    assert bat.is_source == True
    assert gen.is_source == True
    assert j_conn.is_source == True  # J-designated connectors are sources
    assert light.is_source == False

def test_component_is_load_property():
    """Test identification of load components"""
    light = Component(ref="LIGHT1", fs=200.0, wl=30.0, bl=10.0, load=5.0)
    radio = Component(ref="RADIO1", fs=150.0, wl=25.0, bl=-10.0, load=2.5)
    bat = Component(ref="BAT1", fs=50.0, wl=10.0, bl=0.0)

    assert light.is_load == True
    assert radio.is_load == True
    assert bat.is_load == False

def test_component_is_passthrough_property():
    """Test identification of pass-through components"""
    sw = Component(ref="SW1", fs=120.0, wl=30.0, bl=0.0, rating=15.0)
    cb = Component(ref="CB1", fs=80.0, wl=20.0, bl=0.0, rating=10.0)
    light = Component(ref="LIGHT1", fs=200.0, wl=30.0, bl=10.0, load=5.0)

    assert sw.is_passthrough == True
    assert cb.is_passthrough == True
    assert light.is_passthrough == False
```

2. **Implement properties** (GREEN):
```python
    @property
    def is_source(self) -> bool:
        """True if component is a power source"""
        source_prefixes = ('BAT', 'GEN', 'ALT', 'J')
        return any(self.ref.startswith(prefix) for prefix in source_prefixes)

    @property
    def is_load(self) -> bool:
        """True if component consumes power (has load value)"""
        return self.load is not None

    @property
    def is_passthrough(self) -> bool:
        """True if component passes power through (has rating value)"""
        return self.rating is not None
```

3. **Commit:**
```bash
git commit -m "Add component type identification properties

- Implement is_source property (BAT, GEN, ALT, J prefixes)
- Implement is_load property (has load value)
- Implement is_passthrough property (has rating value)
- Test type identification for various components"
```

---

### Task 2.3: Implement identify_component_type Function

**TDD Steps:**

1. **Write tests** (RED):
```python
from kicad2wireBOM.component import identify_component_type

def test_identify_component_type_sources():
    """Test source component identification"""
    assert identify_component_type("BAT1") == "source"
    assert identify_component_type("GEN1") == "source"
    assert identify_component_type("ALT1") == "source"
    assert identify_component_type("J1") == "source"

def test_identify_component_type_passthrough():
    """Test pass-through component identification"""
    assert identify_component_type("SW1") == "passthrough"
    assert identify_component_type("CB1") == "passthrough"
    assert identify_component_type("RELAY1") == "passthrough"
    assert identify_component_type("FUSE1") == "passthrough"

def test_identify_component_type_loads():
    """Test load component identification (everything else)"""
    assert identify_component_type("LIGHT1") == "load"
    assert identify_component_type("RADIO1") == "load"
    assert identify_component_type("MOTOR1") == "load"
    assert identify_component_type("DISPLAY1") == "load"
```

2. **Implement function** (GREEN):
```python
def identify_component_type(ref: str) -> str:
    """
    Determine component role from reference designator.

    Args:
        ref: Reference designator (e.g., "J1", "SW1", "LIGHT1")

    Returns:
        "source", "load", or "passthrough"
    """
    source_prefixes = ('BAT', 'GEN', 'ALT', 'J')
    passthrough_prefixes = ('SW', 'CB', 'RELAY', 'FUSE')

    ref_upper = ref.upper()

    for prefix in source_prefixes:
        if ref_upper.startswith(prefix):
            return "source"

    for prefix in passthrough_prefixes:
        if ref_upper.startswith(prefix):
            return "passthrough"

    return "load"
```

3. **Commit:**
```bash
git commit -m "Add identify_component_type function

- Identify sources (BAT, GEN, ALT, J)
- Identify pass-through (SW, CB, RELAY, FUSE)
- Default to load for all others
- Test all component type categories"
```

---

### Task 2.4: Implement Component Validation

**TDD Steps:**

1. **Write tests** (RED):
```python
from kicad2wireBOM.component import validate_component

def test_validate_component_with_all_required_fields():
    """Test that valid component passes validation"""
    comp = Component(
        ref="J1",
        fs=100.0,
        wl=25.0,
        bl=-5.0,
        rating=15.0
    )

    errors = validate_component(comp, permissive=False)
    assert len(errors) == 0

def test_validate_component_missing_coordinates_strict_mode():
    """Test that missing coordinates generates errors in strict mode"""
    comp = Component(ref="J1", fs=100.0, wl=25.0, bl=-5.0)
    comp.fs = None  # Simulate missing field

    errors = validate_component(comp, permissive=False)
    assert len(errors) > 0
    assert any("FS" in error for error in errors)

def test_validate_component_missing_coordinates_permissive_mode():
    """Test that missing coordinates generates warnings in permissive mode"""
    comp = Component(ref="J1", fs=None, wl=25.0, bl=-5.0)

    errors = validate_component(comp, permissive=True)
    # In permissive mode, should warn but not block
    assert len(errors) >= 0  # May have warnings

def test_validate_component_both_load_and_rating():
    """Test that component cannot have both load and rating"""
    comp = Component(
        ref="SW1",
        fs=100.0,
        wl=25.0,
        bl=0.0,
        load=5.0,
        rating=15.0
    )

    errors = validate_component(comp, permissive=False)
    assert len(errors) > 0
    assert any("load" in error.lower() and "rating" in error.lower() for error in errors)

def test_validate_component_neither_load_nor_rating():
    """Test that component must have either load or rating"""
    comp = Component(ref="SW1", fs=100.0, wl=25.0, bl=0.0)

    errors = validate_component(comp, permissive=False)
    assert len(errors) > 0
    assert any("load" in error.lower() or "rating" in error.lower() for error in errors)
```

2. **Implement validation** (GREEN):
```python
def validate_component(component: Component, permissive: bool) -> list[str]:
    """
    Validate component has required fields.

    Args:
        component: Component to validate
        permissive: If True, generate warnings instead of errors for missing fields

    Returns:
        List of validation error/warning messages (empty if valid)
    """
    errors = []

    # Check required coordinate fields
    if component.fs is None:
        msg = f"Component {component.ref}: Missing FS (Fuselage Station)"
        errors.append(msg if not permissive else f"WARNING: {msg}")

    if component.wl is None:
        msg = f"Component {component.ref}: Missing WL (Waterline)"
        errors.append(msg if not permissive else f"WARNING: {msg}")

    if component.bl is None:
        msg = f"Component {component.ref}: Missing BL (Buttline)"
        errors.append(msg if not permissive else f"WARNING: {msg}")

    # Check load XOR rating (exactly one, not both, not neither)
    has_load = component.load is not None
    has_rating = component.rating is not None

    if has_load and has_rating:
        errors.append(
            f"Component {component.ref}: Cannot have both 'load' and 'rating' - "
            "use 'load' for consuming devices, 'rating' for pass-through devices"
        )
    elif not has_load and not has_rating:
        msg = f"Component {component.ref}: Must have either 'load' or 'rating' value"
        errors.append(msg if not permissive else f"WARNING: {msg}")

    return errors
```

3. **Commit:**
```bash
git commit -m "Add component validation function

- Validate required fields (FS, WL, BL)
- Validate load XOR rating (exactly one required)
- Support strict vs permissive modes
- Test all validation scenarios"
```

---

### Task 2.5: Add Module Documentation

1. Add comprehensive docstrings
2. Document aircraft coordinate system
3. Explain load vs rating distinction
4. Add usage examples in docstrings

**Commit:**
```bash
git commit -m "Add comprehensive module documentation

- Document aircraft coordinate system (FS/WL/BL)
- Explain load vs rating for component types
- Add usage examples in docstrings"
```

---

## Testing Checklist

- [ ] Component creation with required fields works
- [ ] Optional fields work correctly
- [ ] coordinates property returns correct tuple
- [ ] is_source property identifies sources correctly
- [ ] is_load property identifies loads correctly
- [ ] is_passthrough property identifies pass-through devices
- [ ] identify_component_type function works for all types
- [ ] Validation catches missing required fields
- [ ] Validation enforces load XOR rating rule
- [ ] Permissive mode generates warnings instead of errors
- [ ] All tests pass: `pytest tests/test_component.py -v`

---

## Integration Notes

**No dependencies** - can implement independently.

**Used by:**
- parser.py (creates Component objects)
- circuit.py (analyzes components)
- wire_calculator.py (uses coordinates)
- validator.py (validates components)

---

## Estimated Timeline

- Task 2.1: 2 hours
- Task 2.2: 1.5 hours
- Task 2.3: 1 hour
- Task 2.4: 2 hours
- Task 2.5: 0.5 hours

**Total: ~7 hours**

---

## Completion Criteria

- All tests pass
- Module exports match interface contract
- Code follows CLAUDE.md standards
- Committed with proper messages
