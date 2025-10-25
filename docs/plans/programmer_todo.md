# Programmer TODO: kicad2wireBOM

**Status**: All Planned Features Implemented ✅
**Last Updated**: 2025-10-25

---

## CURRENT STATUS

✅ **196/196 tests passing** - Phase 1-9 complete

**The tool is production-ready for generating wire BOMs from KiCad schematics with circuit-based wire gauge calculation.**

---

## KEY REFERENCES

**Design Documents**:
- `docs/plans/kicad2wireBOM_design.md` v3.1 - Complete design specification
- `docs/ea_wire_marking_standard.md` - Wire marking standard (EAWMS)
- `docs/acronyms.md` - Domain terminology

**Test Fixtures**:
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way multipoint connection
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection
- `tests/fixtures/test_05*.kicad_sch` - Validation test cases
- `tests/fixtures/test_06_*.kicad_sch` - Hierarchical schematic (main + 2 sub-sheets)
- `tests/fixtures/test_07_fixture.kicad_sch` - Circuit-based wire sizing (single load, parallel loads, power distribution)

---

## DEVELOPMENT WORKFLOW

### TDD Cycle (ALWAYS FOLLOW)
1. **RED**: Write failing test
2. **Verify**: Run test, confirm it fails correctly
3. **GREEN**: Write minimal code to pass test
4. **Verify**: Run test, confirm it passes
5. **REFACTOR**: Clean up while keeping tests green
6. **COMMIT**: Commit with updated todo

### Pre-Commit Checklist
1. Update this programmer_todo.md with completed tasks
2. Run full test suite (`pytest -v`)
3. Include updated programmer_todo.md in commit

### Circle K Protocol
If you encounter design inconsistencies, architectural ambiguities, or blockers:
1. Say "Strange things are afoot at the Circle K"
2. Explain the issue clearly
3. Suggest options or ask for guidance
4. Wait for architectural decision

---

## ✅ COMPLETED PHASE: Phase 9 - Circuit-Based Wire Gauge Calculation

**Status**: ✅ COMPLETE (2025-10-25)
**Design**: `docs/plans/kicad2wireBOM_design.md` Section 5.2 (Revised 2025-10-25)
**Test Fixture**: `tests/fixtures/test_07_fixture.kicad_sch`
**Tests Added**: 7 new tests (189→196 total)

### Overview

Redesigned wire gauge calculation from per-wire analysis to circuit-based grouping. All wires with the same circuit_id (e.g., L1A, L1B) are now sized together based on total circuit current.

### Tasks

#### [x] Task 9.1: Create Circuit Grouping Function
**File**: `kicad2wireBOM/wire_calculator.py`
**Status**: Complete

Add function to group wires by circuit_id:

```python
def group_wires_by_circuit(wire_connections: List[WireConnection]) -> Dict[str, List[WireConnection]]:
    """
    Group wire connections by circuit_id (system_code + circuit_num).

    Args:
        wire_connections: List of all wire connections from BOM

    Returns:
        Dict mapping circuit_id to list of WireConnections
        Example: {'L1': [L1A_conn, L1B_conn], 'L2': [L2A_conn, L2B_conn, L2C_conn]}
    """
```

**Implementation Notes**:
- Use `parse_net_name()` to extract system_code and circuit_num from wire label
- Circuit ID = f"{system_code}{circuit_num}" (e.g., "L1", "G2", "P1")
- Handle wires that fail to parse (skip or warn?)

**TDD Steps**:
1. Write test with 3 circuits (L1A+L1B, L2A+L2B+L2C, G1A)
2. Verify test fails
3. Implement function
4. Verify test passes

#### [x] Task 9.2: Create Circuit Current Determination Function
**File**: `kicad2wireBOM/wire_calculator.py`
**Status**: Complete

Add function to determine total current for a circuit:

```python
def determine_circuit_current(
    circuit_wires: List[WireConnection],
    all_components: List[Component],
    connectivity_graph
) -> float:
    """
    Determine total current for a circuit by finding all components connected
    to any wire in the circuit group.

    Args:
        circuit_wires: All wires in this circuit group
        all_components: All components in schematic
        connectivity_graph: Connectivity graph for component lookup

    Returns:
        Total circuit current in amps
        Special value: -99 if no loads or sources found (missing data)
    """
```

**Algorithm** (from design doc Section 5.2):
1. For each wire in circuit_wires, find connected components via graph
2. Collect all unique components across all wires in circuit
3. Extract loads and sources:
   - `loads = [comp.load for comp in components if comp.is_load]`
   - `sources = [comp.source for comp in components if comp.source]`
4. Determine current:
   - If loads exist: return `sum(loads)`
   - Elif sources exist: return `max(sources)`
   - Else: return `-99` (sentinel for missing data)

**TDD Steps**:
1. Write test for single load circuit (L1A+L1B with L1=10A) → expect 10A
2. Write test for parallel loads (L2A+L2B+L2C with L2=7A, L3=7A) → expect 14A
3. Write test for power distribution (P1A with BT1=40A source, no loads) → expect 40A
4. Write test for missing data (only passthroughs) → expect -99
5. Verify all tests fail
6. Implement function
7. Verify all tests pass

#### [x] Task 9.3: Modify `determine_min_gauge()` to Handle -99 Sentinel
**File**: `kicad2wireBOM/wire_calculator.py`
**Status**: Complete

Update existing `determine_min_gauge()` function:

```python
def determine_min_gauge(current: float, length_inches: float, system_voltage: float) -> int:
    """
    Determine minimum wire gauge that meets both voltage drop and ampacity constraints.

    Args:
        current: Load current in amps (or -99 for missing data)
        length_inches: Wire length in inches
        system_voltage: System voltage (e.g., 14V for 12V aircraft system)

    Returns:
        Minimum AWG wire size, or -99 if current is -99
    """
```

**Changes**:
- Add check at start: `if current == -99: return -99`
- Rest of function unchanged

**TDD Steps**:
1. Write test: `determine_min_gauge(-99, 100, 14)` → expect -99
2. Verify test fails
3. Add sentinel check
4. Verify test passes
5. Verify existing tests still pass

#### [x] Task 9.4: Integrate Circuit-Based Sizing into BOM Generation
**File**: `kicad2wireBOM/__main__.py`
**Status**: Complete

Replace per-wire gauge calculation with circuit-based approach:

**Current code** (per-wire):
```python
# Around line 290-303 in __main__.py
for wire in wires:
    # Determine current for THIS wire only
    current = get_current_for_wire(comp1, comp2)
    gauge = determine_min_gauge(current, length, voltage)
```

**New code** (circuit-based):
```python
# After generating all WireConnections but before writing CSV:

# Step 1: Group wires by circuit_id
circuit_groups = group_wires_by_circuit(wire_connections)

# Step 2: For each circuit, determine current and gauge
circuit_gauges = {}  # {circuit_id: gauge}
for circuit_id, circuit_wires in circuit_groups.items():
    # Determine total circuit current
    circuit_current = determine_circuit_current(
        circuit_wires,
        components,
        connectivity_graph
    )

    # Find longest wire in circuit (for voltage drop calculation)
    max_length = max(wire.length for wire in circuit_wires)

    # Determine gauge for entire circuit
    gauge = determine_min_gauge(circuit_current, max_length, args.system_voltage)
    circuit_gauges[circuit_id] = gauge

# Step 3: Apply circuit gauge to each wire
for wire in wire_connections:
    circuit_id = extract_circuit_id_from_label(wire.label)
    wire.gauge = circuit_gauges[circuit_id]
```

**TDD Steps**:
1. Update existing integration tests or create new test_07 integration test
2. Test expects: L1A=18, L1B=18, L2A=12, L2B=12, L2C=12 (based on test_07_fixture)
3. Verify test fails with current implementation
4. Integrate circuit-based logic
5. Verify test passes

#### [x] Task 9.5: Add Warning Message for -99 Sentinel
**File**: `kicad2wireBOM/__main__.py`
**Status**: Complete

When writing CSV output, check for gauge == -99 and add warning:

```python
if wire.gauge == -99:
    warning = "Cannot determine circuit current - missing load/source data"
else:
    warning = ""
```

**TDD Steps**:
1. Create test fixture with circuit that has no load/source
2. Run tool on fixture
3. Verify gauge = -99 and warning message appears in CSV
4. Add warning logic
5. Verify test passes

#### [x] Task 9.6: Update test_07_fixture Expected Output
**File**: `docs/input/test_07_expected.csv`
**Status**: Complete

Update expected output based on circuit-based calculation:
- L1A, L1B: 18 AWG (L1 = 10A)
- L2A, L2B, L2C: 12 AWG (L2 + L3 = 14A)
- G1A: 18 AWG (L1 = 10A)
- G2A: 18 AWG (L2 = 7A)
- G3A: 18 AWG (L3 = 7A)
- G4A: 12 AWG (BT1 = 40A source)
- P1A: 12 AWG (BT1 = 40A source)

#### [x] Task 9.7: Create End-to-End Integration Test
**File**: `tests/test_integration_multipoint.py`
**Status**: Complete

Add comprehensive test for circuit-based sizing:

```python
def test_circuit_based_wire_sizing():
    """
    Verify all wires in same circuit get same gauge based on total circuit current.

    Uses test_07_fixture with:
    - Circuit L1 (single load): L1A, L1B → 18 AWG
    - Circuit L2 (parallel loads): L2A, L2B, L2C → 12 AWG
    - Circuit P1 (power distribution): P1A → 12 AWG
    """
```

**TDD Steps**:
1. Write test that loads test_07_fixture and checks all wire gauges
2. Verify test fails
3. Complete Tasks 9.1-9.5
4. Verify test passes

---

### Implementation Order

Follow this order for systematic TDD development:
1. Task 9.1: Group wires by circuit (foundation)
2. Task 9.2: Determine circuit current (core logic)
3. Task 9.3: Handle -99 sentinel (safety)
4. Task 9.4: Integrate into BOM generation (integration)
5. Task 9.5: Add warning messages (UX)
6. Task 9.6: Update expected output (verification)
7. Task 9.7: End-to-end test (validation)

---

## FUTURE PHASES

**Awaiting Architectural Direction** - See `docs/notes/opportunities_for_improvement.md` for potential features.
