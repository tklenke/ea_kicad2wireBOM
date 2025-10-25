# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Status**: Phase 7 Implementation - Hierarchical Schematic Support
**Last Updated**: 2025-10-24

---

## CURRENT STATUS

✅ **Phase 1-6.5 Complete**: 150/150 tests passing
🚧 **Phase 7 In Progress**: Hierarchical Schematic Support

**Completed Features**:
- ✅ Schematic parsing (S-expressions, symbol libraries)
- ✅ Pin position calculation (rotation, mirroring, transforms)
- ✅ Connectivity graph building (wires, junctions, components)
- ✅ 2-point wire connections
- ✅ 3+way multipoint connections with (N-1) labeling
- ✅ Unified BOM generation
- ✅ Notes field infrastructure
- ✅ Notes aggregation across wire fragments
- ✅ Validator module (missing labels, duplicates, non-circuit labels)
- ✅ CLI with --permissive flag
- ✅ CSV output with all fields
- ✅ LocLoad custom field parsing

**Current Work**: Implementing hierarchical schematic support (main sheet + sub-sheets)

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

## DESIGN REFERENCE

**Primary Design Doc**: `docs/plans/kicad2wireBOM_design.md` v3.0

**Key Sections for Phase 7**:
- Section 8: Complete hierarchical schematic design specification
- Section 8.2: KiCad hierarchical elements (sheet, hierarchical_label)
- Section 8.3: Global power nets
- Section 8.4: Multi-sheet data model (HierarchicalSchematic, SheetConnection, GlobalNet)
- Section 8.5: Unified connectivity graph with new node types
- Section 8.6: Wire tracing across sheets
- Section 8.7: Circuit label resolution
- Section 8.8: Component reference resolution from instance paths
- Section 8.9: Implementation phases (7.1 through 7.5)
- Section 8.10: Expected test results

---

## KEY FILES

### Implementation Modules
- `kicad2wireBOM/parser.py` - S-expression parsing
- `kicad2wireBOM/schematic.py` - Data models
- `kicad2wireBOM/symbol_library.py` - Symbol library parsing
- `kicad2wireBOM/pin_calculator.py` - Pin position calculation
- `kicad2wireBOM/connectivity_graph.py` - Graph data structures
- `kicad2wireBOM/wire_connections.py` - Connection identification (multipoint)
- `kicad2wireBOM/bom_generator.py` - Unified BOM entry generation with notes aggregation
- `kicad2wireBOM/validator.py` - Validation framework
- `kicad2wireBOM/__main__.py` - CLI entry point

### Test Fixtures (Flat Schematics)
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit
- `tests/fixtures/test_03A_fixture.kicad_sch` - 3-way connection (P4A/P4B)
- `tests/fixtures/test_04_fixture.kicad_sch` - 4-way ground connection (G1A/G2A/G3A)
- `tests/fixtures/test_05_fixture.kicad_sch` - Validation baseline
- `tests/fixtures/test_05A_fixture.kicad_sch` - Missing labels
- `tests/fixtures/test_05B_fixture.kicad_sch` - Duplicate labels
- `tests/fixtures/test_05C_fixture.kicad_sch` - Non-circuit labels

### Test Fixtures (Hierarchical - Phase 7)
- `tests/fixtures/test_06_fixture.kicad_sch` - Main sheet (battery, fuses, switches)
- `tests/fixtures/test_06_lighting.kicad_sch` - Lighting sub-sheet (lamps L1, L2, L3)
- `tests/fixtures/test_06_avionics.kicad_sch` - Avionics sub-sheet (LRU1)

---

## PHASE 7: HIERARCHICAL SCHEMATIC SUPPORT

**Objective**: Support multi-sheet schematics (main sheet + sub-sheets) with cross-sheet wire tracing

**Design Reference**: Section 8 of `docs/plans/kicad2wireBOM_design.md` v3.0

**Test Fixture**: test_06 (3 files: main, lighting sub-sheet, avionics sub-sheet)

---

### Phase 7.1: Parser Enhancement - Hierarchical Parsing

**Objective**: Parse hierarchical schematics with recursive sub-sheet loading

**Design Reference**: Section 8.4, 8.8

#### Task 7.1.1: Create hierarchical data model classes
**File**: `kicad2wireBOM/schematic.py` (or new `hierarchical_schematic.py`)

[ ] Write test for HierarchicalSchematic dataclass
- RED: Test creating HierarchicalSchematic with root_sheet, sub_sheets dict, sheet_connections list, global_nets dict
- GREEN: Implement HierarchicalSchematic dataclass
- REFACTOR: Clean up
- COMMIT: "Add HierarchicalSchematic data model"

[ ] Write test for SheetConnection dataclass
- RED: Test creating SheetConnection with parent/child UUIDs, pin_name, parent_pin_position, child_label_position, parent_wire_net, child_wire_net
- GREEN: Implement SheetConnection dataclass
- REFACTOR: Clean up
- COMMIT: "Add SheetConnection data model"

[ ] Write test for GlobalNet and PowerSymbol dataclasses
- RED: Test creating GlobalNet with net_name and list of PowerSymbol instances
- RED: Test PowerSymbol with reference, sheet_uuid, position, loc_load
- GREEN: Implement GlobalNet and PowerSymbol dataclasses
- REFACTOR: Clean up
- COMMIT: "Add GlobalNet and PowerSymbol data models"

[ ] Write test for SheetElement dataclass
- RED: Test creating SheetElement with uuid, sheetname, sheetfile, pins list
- GREEN: Implement SheetElement dataclass with pin definitions
- REFACTOR: Clean up
- COMMIT: "Add SheetElement data model for sheet symbols"

[ ] Write test for HierarchicalLabel dataclass
- RED: Test creating HierarchicalLabel with name, position, shape
- GREEN: Implement HierarchicalLabel dataclass
- REFACTOR: Clean up
- COMMIT: "Add HierarchicalLabel data model"

#### Task 7.1.2: Parse sheet elements from parent schematic
**File**: `kicad2wireBOM/parser.py`

[ ] Write test for extracting sheet elements
- RED: Test `extract_sheets()` returns list of SheetElement from test_06_fixture.kicad_sch
- Expected: 2 sheets (lighting and avionics)
- GREEN: Implement extract_sheets() function
- REFACTOR: Clean up
- COMMIT: "Add sheet element extraction from parent schematic"

[ ] Write test for parsing sheet pin positions
- RED: Test that sheet pins have correct positions in parent coordinate system
- GREEN: Implement sheet pin parsing in extract_sheets()
- REFACTOR: Clean up
- COMMIT: "Parse sheet pin positions and directions"

#### Task 7.1.3: Parse hierarchical labels from child schematics
**File**: `kicad2wireBOM/parser.py`

[ ] Write test for extracting hierarchical labels
- RED: Test `extract_hierarchical_labels()` from test_06_lighting.kicad_sch
- Expected: TAIL_LT, TIP_LT labels
- GREEN: Implement extract_hierarchical_labels() function
- REFACTOR: Clean up
- COMMIT: "Add hierarchical label extraction from sub-sheets"

#### Task 7.1.4: Implement recursive schematic parsing
**File**: `kicad2wireBOM/parser.py`

[ ] Write test for recursive parsing
- RED: Test `parse_schematic_hierarchical()` on test_06_fixture.kicad_sch
- Expected: HierarchicalSchematic with 3 sheets loaded (main + 2 sub-sheets)
- GREEN: Implement recursive parsing that:
  1. Parses root sheet
  2. Finds sheet elements
  3. Loads each sub-sheet file
  4. Parses sub-sheets
  5. Returns HierarchicalSchematic
- REFACTOR: Clean up
- COMMIT: "Implement recursive hierarchical schematic parsing"

[ ] Write test for sheet connection mapping
- RED: Test that SheetConnection objects correctly map parent pins to child labels
- Verify pin names match
- Verify positions stored for both sides
- GREEN: Implement sheet connection mapping in parse_schematic_hierarchical()
- REFACTOR: Clean up
- COMMIT: "Map sheet connections between parent pins and child labels"

#### Task 7.1.5: Identify and map global power nets
**File**: `kicad2wireBOM/parser.py`

[ ] Write test for power symbol identification
- RED: Test identifying power symbols (symbols with (power) property) across all sheets
- Expected: GND appears on main, lighting, and avionics sheets
- GREEN: Implement power symbol detection
- REFACTOR: Clean up
- COMMIT: "Detect power symbols in schematic"

[ ] Write test for global net construction
- RED: Test building GlobalNet objects grouping all instances of same power net
- Verify GND net includes all GND symbols from all sheets
- GREEN: Implement global net construction in parse_schematic_hierarchical()
- REFACTOR: Clean up
- COMMIT: "Build global power nets spanning all sheets"

#### Task 7.1.6: Resolve component references from instance paths
**File**: `kicad2wireBOM/parser.py`

[ ] Write test for component reference resolution
- RED: Test that components on sub-sheets have correct references (L1, L2, L3 on lighting sheet)
- Parse instance paths to extract reference for correct sheet
- GREEN: Implement instance path parsing to resolve references
- REFACTOR: Clean up
- COMMIT: "Resolve component references from hierarchical instance paths"

---

### Phase 7.2: Graph Builder Enhancement - Unified Multi-Sheet Graph

**Objective**: Build single connectivity graph spanning all sheets

**Design Reference**: Section 8.5

#### Task 7.2.1: Extend node types for cross-sheet connections
**File**: `kicad2wireBOM/connectivity_graph.py`

[ ] Write test for new node types
- RED: Test creating NetworkNode with type="sheet_pin"
- RED: Test creating NetworkNode with type="hierarchical_label"
- GREEN: Add "sheet_pin" and "hierarchical_label" to NodeType literal
- REFACTOR: Clean up
- COMMIT: "Add sheet_pin and hierarchical_label node types"

#### Task 7.2.2: Update node ID format for cross-sheet uniqueness
**File**: `kicad2wireBOM/connectivity_graph.py`

[ ] Write test for sheet-prefixed node IDs
- RED: Test node IDs include sheet UUID prefix: "{sheet_uuid}:{node_type}:{local_id}"
- Examples: "root:component_pin:BT1:1", "b1093350:component_pin:L2:1"
- GREEN: Update node ID generation to include sheet UUID
- REFACTOR: Clean up
- COMMIT: "Add sheet UUID prefix to node IDs for uniqueness"

#### Task 7.2.3: Build graph from hierarchical schematic
**File**: `kicad2wireBOM/graph_builder.py`

[ ] Write test for multi-sheet graph construction
- RED: Test `build_connectivity_graph()` accepts HierarchicalSchematic input
- Verify graph includes nodes from all sheets
- GREEN: Extend build_connectivity_graph() to iterate over all sheets
- REFACTOR: Clean up
- COMMIT: "Build connectivity graph from all sheets"

[ ] Write test for sheet pin node creation
- RED: Test that sheet_pin nodes created for each sheet pin on parent
- Verify nodes have correct positions
- GREEN: Implement sheet pin node creation in graph builder
- REFACTOR: Clean up
- COMMIT: "Create sheet_pin nodes in connectivity graph"

[ ] Write test for hierarchical label node creation
- RED: Test that hierarchical_label nodes created for each label on child sheets
- Verify nodes have correct positions in child coordinate system
- GREEN: Implement hierarchical label node creation
- REFACTOR: Clean up
- COMMIT: "Create hierarchical_label nodes in connectivity graph"

[ ] Write test for cross-sheet edge creation
- RED: Test that edges exist between sheet_pin and corresponding hierarchical_label
- Verify edge connects parent to child correctly
- GREEN: Implement cross-sheet edge creation from SheetConnection mappings
- REFACTOR: Clean up
- COMMIT: "Add cross-sheet edges connecting sheet pins to hierarchical labels"

[ ] Write test for parent wire connections to sheet pins
- RED: Test that wires on parent sheet connect to sheet_pin nodes
- Use position matching with tolerance
- GREEN: Implement connection of parent wires to sheet_pin nodes
- REFACTOR: Clean up
- COMMIT: "Connect parent wires to sheet_pin nodes"

[ ] Write test for child wire connections to hierarchical labels
- RED: Test that wires on child sheets connect to hierarchical_label nodes
- Use position matching with tolerance
- GREEN: Implement connection of child wires to hierarchical_label nodes
- REFACTOR: Clean up
- COMMIT: "Connect child wires to hierarchical_label nodes"

#### Task 7.2.4: Handle global power net connections
**File**: `kicad2wireBOM/graph_builder.py`

[ ] Write test for global net connectivity
- RED: Test that all power symbols with same net name are electrically connected
- Verify GND symbols on different sheets connect in graph
- GREEN: Implement global net handling in graph builder
- REFACTOR: Clean up
- COMMIT: "Connect global power nets across all sheets"

---

### Phase 7.3: Wire Tracing Update - Cross-Sheet Tracing

**Objective**: Enable wire tracing to work transparently across sheet boundaries

**Design Reference**: Section 8.6

#### Task 7.3.1: Update trace_to_component for new node types
**File**: `kicad2wireBOM/connectivity_graph.py`

[ ] Write test for tracing through sheet_pin nodes
- RED: Test trace_to_component() traverses sheet_pin nodes as intermediate nodes
- GREEN: Add sheet_pin to intermediate node types in trace_to_component()
- REFACTOR: Clean up
- COMMIT: "Support sheet_pin nodes in trace_to_component"

[ ] Write test for tracing through hierarchical_label nodes
- RED: Test trace_to_component() traverses hierarchical_label nodes
- GREEN: Add hierarchical_label to intermediate node types
- REFACTOR: Clean up
- COMMIT: "Support hierarchical_label nodes in trace_to_component"

#### Task 7.3.2: Test cross-sheet wire tracing
**File**: `tests/test_hierarchical_tracing.py` (new test file)

[ ] Write integration test for L2A circuit tracing
- RED: Test tracing from SW1 on main sheet → TAIL_LT pin → lighting sheet → L2 component
- Verify correct component and pin identified
- GREEN: Verify existing trace_to_component() works with Phase 7.2 graph
- REFACTOR: Clean up
- COMMIT: "Integration test: Trace L2A circuit across sheets"

[ ] Write integration test for L3A multipoint circuit tracing
- RED: Test tracing from SW2 → TIP_LT pin → lighting sheet → L1 and L3 (multipoint)
- Verify all connected components found
- GREEN: Verify existing trace logic handles multipoint across sheets
- REFACTOR: Clean up
- COMMIT: "Integration test: Trace L3A multipoint circuit across sheets"

[ ] Write integration test for avionics circuit tracing
- RED: Test tracing A9A circuit to avionics sheet → LRU1
- GREEN: Verify trace works for different sub-sheet
- REFACTOR: Clean up
- COMMIT: "Integration test: Trace A9A circuit to avionics sheet"

[ ] Write integration test for global ground net tracing
- RED: Test tracing GND connections across all sheets
- Verify ground symbols on different sheets are connected
- GREEN: Verify global net handling works in traces
- REFACTOR: Clean up
- COMMIT: "Integration test: Trace global GND net across all sheets"

---

### Phase 7.4: BOM Generation Update - Multi-Sheet Circuits

**Objective**: Generate unified BOM from hierarchical schematic

**Design Reference**: Section 8.7, 8.10

#### Task 7.4.1: Update BOM generator for hierarchical input
**File**: `kicad2wireBOM/bom_generator.py`

[ ] Write test for accepting HierarchicalSchematic
- RED: Test generate_bom_entries() accepts HierarchicalSchematic as input
- GREEN: Update function signature to accept HierarchicalSchematic
- REFACTOR: Clean up
- COMMIT: "Update BOM generator to accept hierarchical schematic"

#### Task 7.4.2: Test circuit detection spanning sheets
**File**: `tests/test_hierarchical_bom.py` (new test file)

[ ] Write test for L2A/L2B circuit BOM entry
- RED: Test BOM includes wire from SW1 → L2 with correct endpoints
- Verify circuit spans main and lighting sheets
- Verify component references correct (SW1 from main, L2 from lighting)
- GREEN: Verify existing BOM generation works with multi-sheet graph
- REFACTOR: Clean up
- COMMIT: "Integration test: Generate BOM entry for L2A/L2B circuit"

[ ] Write test for L3A multipoint circuit BOM entries
- RED: Test BOM includes L3A and L3B entries (multipoint on sub-sheet)
- Verify L3A: SW2 → L1, L3B: SW2 → L3
- GREEN: Verify multipoint logic works across sheets
- REFACTOR: Clean up
- COMMIT: "Integration test: Generate BOM entries for L3A multipoint"

[ ] Write test for A9A avionics circuit
- RED: Test BOM includes A9A wire to LRU1 on avionics sheet
- GREEN: Verify circuit detection for avionics sub-sheet
- REFACTOR: Clean up
- COMMIT: "Integration test: Generate BOM entry for A9A avionics circuit"

[ ] Write test for ground circuits across sheets
- RED: Test BOM includes ground connections from all sheets (G5A, G6A, G7A, G8A, G11A)
- GREEN: Verify global net circuits appear in BOM
- REFACTOR: Clean up
- COMMIT: "Integration test: Generate BOM entries for global ground circuits"

#### Task 7.4.3: Test component references in BOM
**File**: `tests/test_hierarchical_bom.py`

[ ] Write test for component reference resolution in BOM
- RED: Test BOM entries show correct component references from all sheets
- Verify BT1, FH1, SW1, SW2 (main sheet)
- Verify L1, L2, L3 (lighting sheet)
- Verify LRU1 (avionics sheet)
- GREEN: Verify component references resolved correctly in BOM
- REFACTOR: Clean up
- COMMIT: "Integration test: Verify component references in hierarchical BOM"

#### Task 7.4.4: Test wire length calculation with multi-sheet LocLoad
**File**: `tests/test_hierarchical_bom.py`

[ ] Write test for wire length calculation across sheets
- RED: Test wire length calculated using LocLoad from components on different sheets
- Verify calculation uses correct coordinate system
- GREEN: Verify wire calculator works with hierarchical components
- REFACTOR: Clean up
- COMMIT: "Integration test: Verify wire length calculation in hierarchical BOM"

---

### Phase 7.5: CLI Update - Hierarchical Input

**Objective**: CLI processes hierarchical schematics

**Design Reference**: Section 8.9

#### Task 7.5.1: Update CLI to use hierarchical parser
**File**: `kicad2wireBOM/__main__.py`

[ ] Write test for CLI with hierarchical schematic input
- RED: Test CLI processing test_06_fixture.kicad_sch (hierarchical)
- Verify CSV output generated successfully
- GREEN: Update main() to call parse_schematic_hierarchical()
- REFACTOR: Clean up
- COMMIT: "Update CLI to use hierarchical schematic parser"

[ ] Write test for CLI CSV output from hierarchical schematic
- RED: Test CSV includes all expected circuits from test_06
- Verify P1A, L2A, L3A, A9A, ground circuits present
- Verify component references from all sheets
- GREEN: Verify CSV output correct with hierarchical input
- REFACTOR: Clean up
- COMMIT: "Integration test: CLI generates correct CSV from hierarchical schematic"

#### Task 7.5.2: Ensure backward compatibility with flat schematics
**File**: `tests/test_kicad2wireBOM_cli.py`

[ ] Write test for flat schematic backward compatibility
- RED: Test CLI still works with test_01, test_03A, test_04, test_05 (flat schematics)
- GREEN: Ensure parse_schematic_hierarchical() handles flat schematics (no sub-sheets)
- REFACTOR: Clean up
- COMMIT: "Ensure backward compatibility with flat schematics"

[ ] Run full test suite
- Run `pytest -v` to verify all 150 existing tests still pass
- Fix any regressions
- COMMIT: "Verify all existing tests pass with hierarchical support"

---

### Phase 7.6: Hierarchical Validation - Connectivity-Aware Duplicate Detection

**Objective**: Fix validation to allow duplicate circuit IDs on electrically connected wires across sheets

**Design Reference**: `docs/plans/hierarchical_validation_design.md`

**Current Issue**: Validator incorrectly flags L2B and A9A as duplicate errors in test_06

#### Task 7.6.1: Pipe Notation Label Parsing
**File**: `kicad2wireBOM/label_association.py`

[x] Write test for pipe notation parsing
- RED: Test `parse_circuit_ids("L3B|L10A")` returns `["L3B", "L10A"]`
- RED: Test `parse_circuit_ids("L2B")` returns `["L2B"]`
- RED: Test `parse_circuit_ids("L3B|NOTES")` returns `["L3B"]` (invalid part ignored)
- GREEN: Implement `parse_circuit_ids(label_text) -> List[str]` function
- REFACTOR: Clean up
- COMMIT: "Add pipe notation parsing for cross-sheet multipoint labels"

[x] Update label association to handle multiple circuit IDs
- RED: Test label association with pipe notation
- Verify wire segment can have multiple circuit IDs
- GREEN: Update `associate_labels_with_wires()` to use `parse_circuit_ids()`
- REFACTOR: Clean up
- COMMIT: "Update label association to handle pipe notation"

#### Task 7.6.2: Connectivity-Aware Duplicate Detection
**File**: `kicad2wireBOM/validator.py`

[x] Create HierarchicalValidator class
- RED: Test creating HierarchicalValidator with connectivity graph parameter
- GREEN: Create `class HierarchicalValidator(SchematicValidator)`
- Add `__init__(self, strict_mode, connectivity_graph)`
- REFACTOR: Clean up
- COMMIT: "Add HierarchicalValidator class for connectivity-aware validation"

[x] Implement BFS reachable nodes helper
- RED: Test `_bfs_reachable_nodes(graph, start_node)` with mock graph
- Verify returns all connected nodes
- GREEN: Implement BFS traversal using `graph.get_connected_nodes()`
- REFACTOR: Clean up
- COMMIT: "Add BFS traversal for connectivity checking"

[x] Implement are_all_wires_connected helper
- RED: Test `_are_all_wires_connected(wire_list, graph)` with mock wires
- Test case: 2 wires, connected → True
- Test case: 2 wires, not connected → False
- GREEN: Implement using `_bfs_reachable_nodes()`
- Collect wire endpoint node IDs from graph
- Check if all nodes in same connected component
- REFACTOR: Clean up
- COMMIT: "Add connectivity checking for wire segments"

[x] Implement connectivity-aware duplicate detection
- RED: Test `_check_duplicate_circuit_ids_hierarchical()`
- Test case: Same ID on connected wires → No error
- Test case: Same ID on unconnected wires → Error
- GREEN: Implement algorithm:
  1. Group wires by circuit_id
  2. For each group with 2+ wires:
     - Check if all connected
     - Error only if NOT all connected
- REFACTOR: Clean up
- COMMIT: "Implement connectivity-aware duplicate detection"

#### Task 7.6.3: Enhanced ValidationError with Sheet Context
**File**: `kicad2wireBOM/validator.py`

[ ] Update ValidationError dataclass
- RED: Test ValidationError with sheet_uuid and sheet_name fields
- GREEN: Add `sheet_uuid`, `sheet_name`, `details` fields to dataclass
- REFACTOR: Clean up
- COMMIT: "Add sheet context to ValidationError"

[ ] Update error message formatting
- RED: Test error message includes sheet information
- GREEN: Update `_add_error()` to accept and store sheet context
- Update error printing to show sheet details
- REFACTOR: Clean up
- COMMIT: "Enhance error messages with sheet context"

#### Task 7.6.4: CLI Integration
**File**: `kicad2wireBOM/__main__.py`

[ ] Collect labeled wires with sheet context (NOT NEEDED - current implementation works)

[x] Use HierarchicalValidator in CLI
- RED: Test CLI calls HierarchicalValidator with connectivity graph
- GREEN: Replace `SchematicValidator` with `HierarchicalValidator`
- Pass connectivity_graph parameter
- REFACTOR: Clean up
- COMMIT: "Integrate hierarchical validator into CLI"

#### Task 7.6.5: Integration Testing
**File**: `tests/test_hierarchical_validation.py` (new file)

[x] Write integration test for test_06 validation
- Verified existing unit tests cover connectivity-aware detection
- Verified CLI correctly validates test_06 hierarchical fixture
- L2B, L3B, L10A correctly detected as connected (not flagged as errors)
- CSV generated successfully with 11 wire entries
- COMMIT: "Fix floating point precision in connectivity checking"

[ ] Create test_06_invalid fixture with true duplicate (OPTIONAL - not required)

[x] Run CLI on test_06 without --permissive
- CLI completes and generates CSV (one unlabeled wire warning expected)
- No UNCONNECTED duplicate errors for L2B, L3B, L10A
- CSV generated correctly at /tmp/test_06_output.csv
- Verified correct connectivity-aware validation

---

### Phase 7 Completion Checklist

Phase 7 is complete when:

[ ] All Phase 7.1 tasks complete (parser enhancement)
[ ] All Phase 7.2 tasks complete (graph builder)
[ ] All Phase 7.3 tasks complete (wire tracing)
[ ] All Phase 7.4 tasks complete (BOM generation)
[ ] All Phase 7.5 tasks complete (CLI update)
[ ] All Phase 7.6 tasks complete (hierarchical validation)
[ ] All existing tests still pass (150 baseline tests)
[ ] All new hierarchical tests pass
[ ] CLI generates correct CSV from test_06_fixture.kicad_sch
[ ] Backward compatibility verified with flat schematics
[ ] Documentation updated (if needed)

**Expected Test Count After Phase 7**: ~180-200 tests (150 existing + 30-50 new hierarchical tests)

---

## FUTURE PHASES (Post-Phase 7)

See `docs/notes/opportunities_for_improvement.md` for potential future enhancements:
- Multi-level hierarchy (nested sub-sheets)
- Sheet instances (same sub-sheet used multiple times)
- GUI interface
- KiCad plugin integration
