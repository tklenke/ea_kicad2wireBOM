# Work Package 04: Circuit Analysis

## Overview

**Module:** `kicad2wireBOM/circuit.py`

**Purpose:** Convert nets to circuits, detect topology, determine signal flow, create wire segments.

**Dependencies:** component.py

**Estimated Effort:** 12-15 hours

---

## Module Interface Contract

See `00_overview_and_contracts.md` section "Module 4: circuit.py"

**Key Exports:**
- `Circuit` class
- `build_circuits(nets, components)`
- `detect_multi_node_topology(circuit)`
- `determine_signal_flow(circuit)`
- `create_wire_segments(circuit)`

---

## Key Tasks

### Task 4.1: Implement Circuit Class (3 hours)

**Tests:**
- Create circuit from net dict
- Store net name, system code, circuit ID
- Link nodes to Component objects by reference
- Store nodes as (Component, pin) tuples

### Task 4.2: Implement build_circuits (3 hours)

**Tests:**
- Convert net dicts to Circuit objects
- Parse system code from net name ("Net-L105" → "L")
- Parse circuit ID from net name ("Net-L105" → "105")
- Use Circuit_ID/System_Code fields if present (override parsing)
- Link nodes to actual Component objects

### Task 4.3: Implement detect_multi_node_topology (4 hours)

**Complex:** Analyze spatial coordinates to infer routing.

**Tests:**
- Detect 2-node net as "simple"
- Detect star topology (components cluster around hub)
- Detect daisy-chain topology (linear arrangement)
- Log informational message about topology inference

**Algorithm:**
- Calculate centroid of all component coordinates
- Measure distance from each component to centroid
- If one component is central (closest to centroid of others) → star
- Otherwise → daisy-chain

### Task 4.4: Implement determine_signal_flow (3 hours)

**Purpose:** Order nodes from source → intermediates → load

**Tests:**
- Identify source component (is_source property)
- Order components logically
- Handle ambiguous cases (warn, make best guess)

**Algorithm:**
- Find source component
- Find load component
- Order remaining components spatially between them

### Task 4.5: Implement create_wire_segments (2 hours)

**Tests:**
- Simple net creates 1 segment
- Multi-node creates multiple segments
- Segments have sequential letters (A, B, C...)
- Return segment dicts with from/to component/pin

---

## Testing Checklist

- [ ] Circuit class stores all required data
- [ ] build_circuits links nodes to components
- [ ] System code and circuit ID parsed correctly
- [ ] Topology detection works for 2, 3, 4+ node nets
- [ ] Signal flow ordering is logical
- [ ] Wire segments created correctly
- [ ] All tests pass

---

## Integration Notes

**Depends on:** component.py

**Used by:** wire_calculator.py, validator.py

---

## Estimated Timeline

~14 hours total

---

## Completion Criteria

- All tests pass
- Topology detection handles common cases
- Signal flow determination works reasonably
- Module exports match interface contract
