# Hierarchical Schematic Validation Design

**Date**: 2025-10-25
**Purpose**: Extend validation architecture for hierarchical schematics with connectivity-aware duplicate detection
**Status**: Architectural Design Complete - Ready for Implementation
**Version**: 1.0

---

## Design Revision History

### Version 1.0 (2025-10-25): Initial Design
**Why**: test_06 hierarchical fixture validation fails incorrectly. Validator detects "duplicate circuit IDs" (L2B appears on main and lighting sheets, A9A appears on main and avionics sheets) but these are CORRECT - they represent electrically connected wire segments across hierarchical boundaries.

**Problem Statement**: Current validation (`validator.py`) checks for duplicate circuit IDs by simple string matching across all wire segments. This is correct for flat schematics but fails for hierarchical schematics where the SAME circuit ID should appear on both sides of a sheet boundary to indicate electrical continuity.

**Key Insight**: Circuit labels are descriptive annotations, not the authoritative connectivity mechanism. Hierarchical pins/labels establish electrical connectivity. The connectivity graph is the source of truth.

---

## Overview

This design extends the validation architecture to handle hierarchical schematics by making duplicate detection **connectivity-aware**. Instead of treating all duplicate circuit IDs as errors, the validator must distinguish between:

1. **Valid duplicates**: Same circuit ID on electrically CONNECTED wire segments (expected, correct)
2. **Invalid duplicates**: Same circuit ID on electrically UNCONNECTED wire segments (error, ambiguous)

Additionally, this design handles:
- **Pipe notation** (`|`) in circuit labels indicating cross-sheet multipoint connections
- **Cross-sheet label consistency** validation
- **Hierarchical-aware error messages** with sheet context

---

## Key Concepts

### 1. Electrical Connectivity is Authoritative

**Principle**: The connectivity graph determines which wires are electrically connected, NOT the circuit labels.

**Examples**:
- Main sheet wire labeled "L2B" connects to TIP_LT sheet pin
- Lighting sheet hierarchical label "TIP_LT" connects to wire labeled "L2B"
- These are electrically connected through the sheet boundary
- Having the same circuit ID "L2B" on both is **correct and expected**

### 2. Pipe Notation for Cross-Sheet Multipoint

**Pattern**: `"CircuitA|CircuitB"` on a wire label indicates cross-sheet multipoint connection

**Topology**:
- Parent sheet: Component → hierarchical sheet pin (wire labeled with `|`)
- Child sheet: Hierarchical label → junction → 3+ component pins

**Example (test_06)**:
- Main sheet: SW2 → TIP_LT sheet pin, wire labeled `"L3B|L10A"`
- Lighting sheet: TIP_LT label → junction → L1 and L3
  - Wire to L1 labeled "L3B"
  - Wire to L3 labeled "L10A"
  - One segment unlabeled (identifies L1 as common endpoint per multipoint rules)

**Parsing Rule**: Split label on `|` character to extract multiple circuit IDs from one wire segment

### 3. Validation Rules for Hierarchical Schematics

| Scenario | Wire A | Wire B | Electrically Connected? | Validation Result |
|----------|--------|--------|------------------------|-------------------|
| 1 | L2B | L2B | ✅ Yes (via sheet boundary) | ✅ **Valid** - Consistent labeling |
| 2 | L2B | L2C | ✅ Yes (via sheet boundary) | ⚠️ **Warning** - Inconsistent labels |
| 3 | L2B | L2B | ❌ No (separate circuits) | ❌ **Error** - Duplicate ID, ambiguous |
| 4 | L2B | L2C | ❌ No (separate circuits) | ✅ **Valid** - Different IDs |

---

## Architectural Design

### 1. Pipe Notation Label Parser

**Location**: `label_association.py`

**Current Behavior**:
```python
def parse_circuit_id(label_text: str) -> Optional[str]:
    """Returns single circuit ID or None"""
    pattern = re.compile(r'^[A-Z]-?\d+-?[A-Z]$')
    if pattern.match(label_text):
        return label_text
    return None
```

**New Behavior**:
```python
def parse_circuit_ids(label_text: str) -> List[str]:
    """
    Parse circuit ID(s) from label text.

    Handles pipe notation for cross-sheet multipoint:
    - "L2B" → ["L2B"]
    - "L3B|L10A" → ["L3B", "L10A"]
    - "24AWG" → [] (not a circuit ID)

    Returns:
        List of circuit IDs found (empty list if none)
    """
    pattern = re.compile(r'^[A-Z]-?\d+-?[A-Z]$')

    # Split on pipe character
    parts = label_text.split('|')

    circuit_ids = []
    for part in parts:
        part = part.strip()
        if pattern.match(part):
            circuit_ids.append(part)

    return circuit_ids
```

**Impact**:
- Label `"L3B|L10A"` parsed as TWO circuit IDs: `["L3B", "L10A"]`
- Wire segment participates in multiple circuits
- Each circuit ID validated independently

---

### 2. Connectivity-Aware Duplicate Detection

**Location**: `validator.py` - new class `HierarchicalValidator`

**Current Algorithm** (INCORRECT for hierarchical):
```python
def _check_duplicate_circuit_ids(self, wires):
    """Check for duplicate circuit IDs across wires"""
    circuit_id_counts = {}
    for wire in wires:
        if wire.circuit_id:
            circuit_id_counts[wire.circuit_id] = circuit_id_counts.get(wire.circuit_id, 0) + 1

    for circuit_id, count in circuit_id_counts.items():
        if count > 1:
            self._add_error(f"Duplicate circuit ID '{circuit_id}' found on {count} wire segments")
```

**Problem**: Counts ALL occurrences, doesn't check electrical connectivity.

**New Algorithm** (CORRECT for hierarchical):

```python
def _check_duplicate_circuit_ids_hierarchical(self, labeled_wires, connectivity_graph):
    """
    Check for duplicate circuit IDs on electrically UNCONNECTED wires.

    Algorithm:
    1. Group wires by circuit ID
    2. For each circuit ID with multiple wires:
       a. Check if all wires are electrically connected via connectivity graph
       b. If connected → Valid (consistent cross-sheet labeling)
       c. If NOT all connected → Error (ambiguous duplicate)
    3. Optionally warn if connected but labels inconsistent

    Args:
        labeled_wires: List of (WireSegment, circuit_id, sheet_uuid) tuples
        connectivity_graph: ConnectivityGraph for electrical connectivity checks
    """
    # Group wires by circuit ID
    circuit_id_to_wires: Dict[str, List[tuple]] = {}
    for wire, circuit_id, sheet_uuid in labeled_wires:
        if circuit_id not in circuit_id_to_wires:
            circuit_id_to_wires[circuit_id] = []
        circuit_id_to_wires[circuit_id].append((wire, sheet_uuid))

    # Check each circuit ID with multiple occurrences
    for circuit_id, wire_list in circuit_id_to_wires.items():
        if len(wire_list) <= 1:
            continue  # No duplicates

        # Check if all wires with this circuit ID are electrically connected
        if self._are_all_wires_connected(wire_list, connectivity_graph):
            # Valid: electrically connected wires with consistent labels
            # This is expected for cross-sheet circuits
            pass  # No error
        else:
            # Error: same circuit ID on electrically unconnected wires
            sheet_info = [f"  - Sheet {sheet}" for wire, sheet in wire_list]
            self._add_error(
                f"Duplicate circuit ID '{circuit_id}' found on {len(wire_list)} "
                f"UNCONNECTED wire segments",
                suggestion="Each electrically distinct circuit must have unique ID. "
                           "Check if wires should be connected or use different segment letters.",
                details="\n".join(sheet_info)
            )

def _are_all_wires_connected(self, wire_list, connectivity_graph) -> bool:
    """
    Check if all wires in the list are part of the same electrical circuit.

    Uses connectivity graph to determine if there's an electrical path
    between all wire segments.

    Algorithm:
    1. Build set of all nodes involved in these wire segments
    2. Use graph connectivity (BFS/DFS) to check if all nodes are reachable from first node
    3. Return True if all nodes in same connected component

    Args:
        wire_list: List of (WireSegment, sheet_uuid) tuples
        connectivity_graph: ConnectivityGraph

    Returns:
        True if all wire segments are electrically connected
    """
    if len(wire_list) <= 1:
        return True

    # Collect all wire endpoint nodes for these wire segments
    all_nodes = set()
    for wire, sheet_uuid in wire_list:
        # Get wire endpoint nodes from connectivity graph
        # Node IDs include sheet UUID prefix: "{sheet_uuid}:wire_endpoint:{wire_uuid}:{end}"
        start_node_id = f"{sheet_uuid}:wire_endpoint:{wire.uuid}:start"
        end_node_id = f"{sheet_uuid}:wire_endpoint:{wire.uuid}:end"

        if start_node_id in connectivity_graph.nodes:
            all_nodes.add(start_node_id)
        if end_node_id in connectivity_graph.nodes:
            all_nodes.add(end_node_id)

    if len(all_nodes) == 0:
        return False

    # Check if all nodes are in same connected component
    # Use BFS from first node
    start_node = next(iter(all_nodes))
    reachable = self._bfs_reachable_nodes(connectivity_graph, start_node)

    # All nodes reachable from start node?
    return all_nodes.issubset(reachable)

def _bfs_reachable_nodes(self, graph, start_node_id) -> set:
    """
    Find all nodes reachable from start_node via BFS traversal.

    Returns:
        Set of node IDs reachable from start_node
    """
    visited = set()
    queue = [start_node_id]
    visited.add(start_node_id)

    while queue:
        node_id = queue.pop(0)

        # Get connected nodes
        for neighbor_id in graph.get_connected_nodes(node_id):
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append(neighbor_id)

    return visited
```

**Key Changes**:
- Receives connectivity graph as parameter
- Groups wires by circuit ID
- Checks electrical connectivity using graph
- Only errors on duplicates that are NOT electrically connected

---

### 3. Cross-Sheet Label Consistency Check (Optional Warning)

**Purpose**: Detect when electrically connected wires have DIFFERENT labels (inconsistent but not error)

```python
def _check_cross_sheet_label_consistency(self, connectivity_graph, labeled_wires):
    """
    Warn when electrically connected wires have inconsistent labels.

    Example:
    - Main sheet: wire labeled "L2B" connects to TAIL_LT sheet pin
    - Lighting sheet: wire from TAIL_LT label is labeled "L2C" (different!)
    - Warning: "Cross-sheet label inconsistency: L2B on main sheet,
                L2C on lighting sheet (electrically connected)"

    This is not an error (connectivity is authoritative), but suggests
    possible labeling mistake.
    """
    # Implementation: For each cross-sheet edge in graph:
    # - Find wire segments on both sides of hierarchical boundary
    # - Check if their circuit IDs match
    # - Warn if different
    pass
```

**Note**: This is optional - may add noise for legitimate cases where builder uses different naming on sub-sheets. Consider implementing only if requested.

---

### 4. Enhanced Validation Result with Sheet Context

**Update**: `ValidationError` dataclass to include sheet information

```python
@dataclass
class ValidationError:
    """Validation error or warning"""
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None
    wire_uuid: Optional[str] = None
    sheet_uuid: Optional[str] = None  # NEW: Which sheet this error is on
    sheet_name: Optional[str] = None  # NEW: Human-readable sheet name
    position: Optional[tuple[float, float]] = None
    details: Optional[str] = None  # NEW: Multi-line details (e.g., list of sheets)
```

**Error Message Format**:
```
ERROR: Duplicate circuit ID 'L2B' found on 3 UNCONNECTED wire segments
       Suggestion: Each electrically distinct circuit must have unique ID.
       Details:
         - Sheet main (6f32b1c6-d0dc-4a69-b565-c121d7833096)
         - Sheet lighting (b1093350-cedd-46df-81c4-dadfdf2715f8)
         - Sheet avionics (3f34c49e-ae58-4433-8ae6-817967dac1be)
```

---

### 5. Integration with CLI

**Location**: `__main__.py`

**Current Validation Call**:
```python
validator = SchematicValidator(strict_mode=not args.permissive)
result = validator.validate_all(wires, labels, components)
```

**New Validation Call**:
```python
# Parse schematic (now returns HierarchicalSchematic)
hierarchical_sch = parse_schematic_hierarchical(args.source)

# Build connectivity graph
connectivity_graph = build_connectivity_graph(hierarchical_sch, lib)

# Collect labeled wires from all sheets
labeled_wires = []
for sheet_uuid, sheet in hierarchical_sch.all_sheets():
    for wire in sheet.wires:
        circuit_ids = parse_circuit_ids(wire.label_text)  # Handles pipe notation
        for circuit_id in circuit_ids:
            labeled_wires.append((wire, circuit_id, sheet_uuid))

# Run hierarchical validation
validator = HierarchicalValidator(strict_mode=not args.permissive)
result = validator.validate_all(
    hierarchical_sch=hierarchical_sch,
    labeled_wires=labeled_wires,
    connectivity_graph=connectivity_graph
)

if result.should_abort(strict_mode=not args.permissive):
    print_errors(result.errors)
    sys.exit(1)
```

**Key Changes**:
- Validator receives connectivity graph
- Validator receives labeled_wires with sheet context
- Validator is connectivity-aware

---

## Validation Rules Summary

### Rule 1: Missing Circuit ID Labels
**Unchanged** from flat schematic validation.

### Rule 2: Multiple Circuit IDs on Single Wire Segment
**Updated** to handle pipe notation:

**Before**: Wire with label `"L3B|L10A"` → Error "Multiple circuit IDs"

**After**: Wire with label `"L3B|L10A"` → Parsed as TWO circuit IDs, wire participates in both circuits

**Validation**:
- Pipe notation (`|`) is ALLOWED
- Each circuit ID component must match pattern: `^[A-Z]-?\d+-?[A-Z]$`
- Invalid components treated as notes (e.g., `"L3B|NOTES"` → circuit ID "L3B", note "NOTES")

### Rule 3: Duplicate Circuit IDs (REVISED)
**Key Change**: Connectivity-aware duplicate detection

**Algorithm**:
1. Group wire segments by circuit ID
2. For each group with 2+ wire segments:
   - Check if all segments are electrically connected (using connectivity graph)
   - **If connected**: ✅ Valid (expected cross-sheet labeling)
   - **If NOT all connected**: ❌ Error (ambiguous duplicate)

**Example Valid Cases**:
- L2B on main sheet + L2B on lighting sheet, connected via TAIL_LT hierarchical pin/label
- A9A on main sheet + A9A on avionics sheet, connected via avionics hierarchical pin/label

**Example Error Cases**:
- L2B on lighting sheet + L2B on avionics sheet, NOT electrically connected
- P1A on two unconnected power distribution branches

### Rule 4: Non-Circuit Labels
**Unchanged** from flat schematic validation - treated as notes.

### Rule 5: Cross-Sheet Label Consistency (Optional)
**New** rule for hierarchical schematics:

**Check**: Electrically connected wires across sheet boundaries should have matching circuit IDs

**Result**: ⚠️ Warning (not error) if mismatched

**Example**:
- Main sheet: L2B connects to TAIL_LT pin
- Lighting sheet: TAIL_LT label connects to wire labeled L2C (different!)
- Warning: "Cross-sheet label inconsistency detected"

**Note**: This is optional - may not implement if adds too much noise.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Parse Hierarchical Schematic                             │
│    parse_schematic_hierarchical() → HierarchicalSchematic   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Extract Labels with Sheet Context                        │
│    For each sheet:                                           │
│      For each wire with labels:                              │
│        circuit_ids = parse_circuit_ids(label) # Pipe support│
│        labeled_wires.append((wire, circuit_id, sheet_uuid)) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Build Connectivity Graph                                 │
│    build_connectivity_graph(hierarchical_sch, lib)          │
│    → Graph with nodes across all sheets, cross-sheet edges  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Run Hierarchical Validation                              │
│    validator = HierarchicalValidator(strict_mode=...)       │
│    result = validator.validate_all(                         │
│        hierarchical_sch=hierarchical_sch,                   │
│        labeled_wires=labeled_wires,                         │
│        connectivity_graph=connectivity_graph                │
│    )                                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Check Duplicate Circuit IDs (Connectivity-Aware)         │
│    Group by circuit_id                                       │
│    For each group with 2+ wires:                            │
│      if are_all_wires_connected(wires, graph):              │
│        → Valid (cross-sheet circuit)                        │
│      else:                                                   │
│        → Error (true duplicate)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Return ValidationResult                                   │
│    - Errors: True duplicates only                           │
│    - Warnings: Optional cross-sheet inconsistencies         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Pipe Notation Support
**Module**: `label_association.py`

**Tasks**:
1. Add `parse_circuit_ids(label_text) -> List[str]` function
2. Update label association logic to handle multiple circuit IDs per label
3. Update WireSegment data model to store `circuit_ids: List[str]` instead of `circuit_id: str`
4. Write unit tests for pipe notation parsing

**Test Cases**:
- `"L2B"` → `["L2B"]`
- `"L3B|L10A"` → `["L3B", "L10A"]`
- `"L3B|L10A|P1A"` → `["L3B", "L10A", "P1A"]` (3-way split)
- `"L3B|NOTES"` → `["L3B"]` (invalid part ignored, added to notes)
- `"24AWG"` → `[]` (not a circuit ID)

### Phase 2: Connectivity-Aware Duplicate Detection
**Module**: `validator.py`

**Tasks**:
1. Create `HierarchicalValidator` class extending `SchematicValidator`
2. Implement `_check_duplicate_circuit_ids_hierarchical()` method
3. Implement `_are_all_wires_connected()` helper
4. Implement `_bfs_reachable_nodes()` helper
5. Update `ValidationError` dataclass with sheet context fields
6. Write unit tests for connectivity checking

**Test Cases**:
- Two wires with same ID, electrically connected → No error
- Two wires with same ID, NOT connected → Error
- Three wires with same ID, all connected → No error
- Three wires with same ID, only two connected → Error

### Phase 3: CLI Integration
**Module**: `__main__.py`

**Tasks**:
1. Pass connectivity graph to validator
2. Collect labeled_wires with sheet context
3. Use `HierarchicalValidator` instead of `SchematicValidator`
4. Update error printing to show sheet context
5. Write integration tests using test_06 fixture

**Expected Behavior (test_06)**:
- **Strict mode**: No errors, all wires valid
- **Permissive mode**: No errors, all wires valid
- L2B appears on main and lighting sheets → Valid (connected)
- A9A appears on main and avionics sheets → Valid (connected)

### Phase 4: Optional Cross-Sheet Consistency Check
**Module**: `validator.py`

**Tasks**:
1. Implement `_check_cross_sheet_label_consistency()` (optional)
2. Add `--strict-cross-sheet-labels` flag to enable check
3. Write tests for consistency warnings

**Note**: Implement only if explicitly requested by Tom. May add noise.

---

## Test Strategy

### Unit Tests

**test_pipe_notation_parsing.py**:
- Test `parse_circuit_ids()` with various inputs
- Verify split on `|` character
- Verify invalid components filtered out

**test_connectivity_aware_validation.py**:
- Mock connectivity graph
- Test duplicate detection with connected/unconnected scenarios
- Test BFS reachable nodes algorithm

### Integration Tests

**test_hierarchical_validation_integration.py**:
- Use test_06 fixture (hierarchical schematic)
- Verify L2B and A9A duplicates NOT flagged as errors
- Verify strict mode passes
- Create test_06_invalid fixture with true duplicate (same ID on unconnected wires)
- Verify that fixture fails validation

**Expected Test Results**:
```python
def test_06_hierarchical_duplicate_validation():
    """test_06 has L2B on two sheets (connected) - should be valid"""
    result = validate_hierarchical_schematic("test_06_fixture.kicad_sch", strict=True)
    assert not result.has_errors()
    # L2B appears on main and lighting sheets but is electrically connected
    # A9A appears on main and avionics sheets but is electrically connected

def test_06_invalid_true_duplicate():
    """test_06_invalid has L2B on two UNCONNECTED wires - should error"""
    result = validate_hierarchical_schematic("test_06_invalid_fixture.kicad_sch", strict=True)
    assert result.has_errors()
    assert "Duplicate circuit ID 'L2B'" in result.errors[0].message
    assert "UNCONNECTED" in result.errors[0].message
```

---

## Success Criteria

Hierarchical validation is complete when:

1. ✅ Pipe notation (`|`) correctly parsed into multiple circuit IDs
2. ✅ Duplicate detection is connectivity-aware
3. ✅ test_06 fixture passes validation in both strict and permissive modes
4. ✅ L2B and A9A duplicates recognized as valid (electrically connected)
5. ✅ True duplicates (unconnected wires with same ID) still caught as errors
6. ✅ Error messages include sheet context
7. ✅ All existing validation tests still pass (backward compatibility)
8. ✅ Integration tests verify correct behavior on hierarchical schematics

---

## Backward Compatibility

**Flat Schematics**: All existing validation behavior unchanged

- Single-sheet schematics don't use hierarchical pins/labels
- All wires are on same sheet (sheet_uuid all identical)
- Connectivity check still works (just faster - all in one connected component)
- No pipe notation in flat schematics (existing behavior preserved)

**Existing Tests**: All test_01 through test_05C should continue to pass without modification

---

## Open Questions

1. **Should cross-sheet label consistency be a warning or just logged?**
   - Recommendation: Start without this check, add only if Tom requests it

2. **What if pipe notation has more than 2 components (e.g., `"A|B|C"`)?**
   - Recommendation: Support arbitrary number of components, validate each independently

3. **Should validator check that pipe notation matches multipoint topology?**
   - Example: Wire with `"L3B|L10A"` should have hierarchical pin on one end, junction on other sheet
   - Recommendation: No - too complex, connectivity graph is source of truth

4. **Error message verbosity - show all sheet UUIDs or just counts?**
   - Recommendation: Show sheet names if available, UUIDs if not, limit to 5 sheets in error message

---

## References

- **Existing Validation Design**: `docs/plans/validation_design.md`
- **Hierarchical Schematic Design**: `docs/plans/kicad2wireBOM_design.md` Section 8
- **Test Fixture**: `tests/fixtures/test_06_fixture.kicad_sch`
- **Current Implementation**: `kicad2wireBOM/validator.py`
- **Expected Behavior**: `docs/input/test_06_expected.csv`
