# Programmer TODO: kicad2wireBOM Implementation

**Project**: kicad2wireBOM - Wire BOM generator for experimental aircraft
**Architecture**: Schematic-based parsing (NOT netlist-based)
**Approach**: Test-Driven Development (TDD)
**Status**: Phase 1-3 Complete - Basic schematic parsing working

**Last Updated**: 2025-10-19

---

## IMPLEMENTATION STATUS

### ✅ COMPLETED (Phases 0-3)

**Phase 0: Project Setup**
- [x] Package structure created
- [x] Dependencies installed (sexpdata, pytest)
- [x] Test fixtures verified

**Phase 1: S-Expression Parsing Foundation**
- [x] Parse schematic files using sexpdata
- [x] Extract wire elements
- [x] Extract label elements
- [x] Extract symbol (component) elements
- [x] Parse wire elements to WireSegment objects
- [x] Parse label elements to Label objects
- [x] Parse symbol elements to Component objects
- [x] Parse footprint encoding

**Phase 2: Data Model Creation**
- [x] WireSegment dataclass created
- [x] Label dataclass created
- [x] Component dataclass (reused from previous work)

**Phase 3: Label-to-Wire Association**
- [x] Point-to-segment distance calculation
- [x] Circuit ID pattern validation
- [x] Circuit ID parsing
- [x] Proximity-based label association

**Current Status**: Basic end-to-end processing works!
```bash
python -m kicad2wireBOM tests/fixtures/test_01_fixture.kicad_sch output.csv
```
Generates correct wire BOM with labeled wires.

**Test Results**: 69/69 tests passing ✅

---

## 🚧 IN PROGRESS / TODO

### Phase 4: Wire Connectivity and Network Tracing

**Current Limitation**: The CLI currently uses a simplified heuristic (connects first 2 components for all labeled wires). This works for simple 2-component circuits but doesn't properly trace wire connectivity through the schematic.

**What Needs Implementation**:

#### Task 4.1: Junction Extraction and Parsing
- [ ] Extract junction elements from schematic
- [ ] Parse junction positions
- [ ] Create Junction dataclass
- [ ] Add tests for junction extraction

#### Task 4.2: Wire Network Tracing
- [ ] Build connectivity graph from wire segments
- [ ] Trace wire paths from component pins through junctions
- [ ] Identify wire start/end components
- [ ] Handle multi-segment wires (connected via junctions)
- [ ] Add comprehensive tests

**Why This Matters**: test_03_fixture demonstrates the problem - two switches feeding one connector through a junction. We need to correctly identify which components each labeled wire connects.

#### Task 4.3: Component Pin Position Calculation
- [ ] Extract component position and rotation from schematic
- [ ] Calculate pin positions (simple approach initially)
- [ ] Match wire endpoints to nearest component pins
- [ ] Add tests for pin matching

**Reference**: See `docs/plans/kicad2wireBOM_design.md` Section 4.3 for algorithm

### Phase 5: Enhanced Wire Calculations

Current wire calculator reused from previous work - already functional!

**Potential Enhancements** (optional, not blocking):
- [ ] Add validation warnings for wires without labels (permissive mode)
- [ ] Add validation for orphaned labels
- [ ] Add duplicate circuit ID detection
- [ ] Improve current determination algorithm

### Phase 6: Output Generation

**Current Status**: CSV output works for basic cases

**TODO**:
- [ ] Test CSV output with complex multi-wire circuits
- [ ] Implement Markdown output (optional)
- [ ] Add engineering mode output (optional, can defer)

### Phase 7: CLI Polish

**Current Status**: Basic CLI works, tested

**TODO**:
- [ ] Add better error messages
- [ ] Add validation mode (check schematic without generating BOM)
- [ ] Add verbose/debug output option
- [ ] Configuration file loading (optional, can defer)

### Phase 8: Integration Testing

**TODO**:
- [ ] Create integration test for test_01_fixture
- [ ] Create integration test for test_02_fixture
- [ ] **CRITICAL**: Create integration test for test_03_fixture (junction test)
- [ ] Add edge case tests

---

## NEXT SESSION RECOMMENDATIONS

### High Priority (Core Functionality)
1. **Junction handling** - This is the key differentiator for schematic-based parsing
   - Start with test_03_fixture analysis
   - Understand junction positions and wire connectivity
   - Implement network tracing algorithm

2. **Wire-to-component matching** - Currently using simple heuristic
   - Extract component positions from schematic
   - Implement wire endpoint to component pin matching

### Medium Priority (Robustness)
3. **Validation and error handling**
   - Add warnings for unlabeled wires
   - Detect orphaned labels
   - Validate circuit ID uniqueness

### Low Priority (Nice to Have)
4. **Additional output formats** - Markdown, engineering mode
5. **Configuration file support** - YAML/TOML config
6. **Hierarchical schematic support** - Defer to later

---

## KEY FILES

### Implementation
- `kicad2wireBOM/parser.py` - Schematic parsing (✅ complete for basic features)
- `kicad2wireBOM/schematic.py` - Data models (✅ complete)
- `kicad2wireBOM/label_association.py` - Label matching (✅ complete)
- `kicad2wireBOM/component.py` - Component model (✅ reused)
- `kicad2wireBOM/wire_calculator.py` - Calculations (✅ reused)
- `kicad2wireBOM/__main__.py` - CLI (✅ basic version working)

### Tests
- `tests/test_parser_schematic.py` - Parser tests (8 tests ✅)
- `tests/test_schematic.py` - Data model tests (4 tests ✅)
- `tests/test_label_association.py` - Label matching tests (11 tests ✅)
- All other test files - Reused from previous work (46 tests ✅)

### Test Fixtures
- `tests/fixtures/test_01_fixture.kicad_sch` - Simple 2-component circuit ✅ WORKING
- `tests/fixtures/test_02_fixture.kicad_sch` - Multi-segment with switch (untested)
- `tests/fixtures/test_03_fixture.kicad_sch` - Junction example (untested, HIGH PRIORITY)

---

## MIGRATION NOTES

This implementation was completed using a **hybrid migration approach**:

**Kept from netlist-based work:**
- Component dataclass and all tests
- Wire calculator functions (length, gauge, voltage drop)
- Reference data tables
- Wire BOM data structures
- CSV output generation
- 50 existing tests

**Replaced with schematic-based:**
- Parser (now uses sexpdata, not kinparse)
- Removed Circuit abstraction (netlist-specific)
- Added WireSegment and Label models
- Added label-to-wire proximity matching
- Updated CLI orchestration

**Result**: 80% code reuse, 20% new schematic-specific code. All 69 tests passing.

---

## DEVELOPMENT WORKFLOW

### TDD Cycle (ALWAYS FOLLOW)
1. **RED**: Write failing test
2. **Verify**: Run test, confirm it fails correctly
3. **GREEN**: Write minimal code to pass test
4. **Verify**: Run test, confirm it passes
5. **REFACTOR**: Clean up while keeping tests green
6. **COMMIT**: Commit the change with updated todo

### Pre-Commit Checklist
Before EVERY commit:
1. Update this programmer_todo.md with completed tasks
2. Mark tasks `[x]` Complete when done
3. Run full test suite (`pytest -v`)
4. Include updated programmer_todo.md in commit

### Circle K Protocol
If you encounter:
- Design inconsistencies
- Architectural ambiguities
- Blockers requiring decisions

**THEN**:
1. Say "Strange things are afoot at the Circle K"
2. Explain the issue clearly
3. Suggest options or ask for guidance
4. Wait for architectural decision

---

## ARCHIVED DOCUMENTS

**Moved to `docs/archive/`**:
- Old netlist-based design documents
- Previous implementation plans
- `programmer_notes.md` (archived after Phase 1-3 completion)

**DO NOT** reference archived documents - they describe the wrong architecture.

---

## SUCCESS METRICS

**Minimum Viable Product** (Current status):
- [x] Parse .kicad_sch files
- [x] Extract wire segments
- [x] Associate labels with wires
- [x] Calculate wire lengths and gauges
- [x] Generate CSV output
- [x] Handle test_01_fixture correctly ✅

**Full Feature Set** (TODO):
- [ ] Handle junctions correctly (test_03_fixture)
- [ ] Trace multi-segment wire paths
- [ ] Match wire endpoints to component pins
- [ ] Handle all three test fixtures
- [ ] Validation and error messages
- [ ] Complete test coverage

**Production Ready** (Future):
- [ ] Hierarchical schematic support
- [ ] Configuration file support
- [ ] Multiple output formats
- [ ] Comprehensive error handling
- [ ] User documentation

---

**Next Programmer Session**: Start with junction extraction and network tracing (Phase 4)
