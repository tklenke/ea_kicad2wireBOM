# kicad2wireBOM Implementation Plans

## Overview

This directory contains modular implementation plans for the kicad2wireBOM project. Each work package can be implemented independently by different programmers with minimal integration overhead.

## Getting Started

1. **Start here:** Read `00_overview_and_contracts.md` first to understand:
   - Module dependencies
   - Interface contracts between modules
   - Data flow
   - Integration strategy

2. **Pick a work package** based on dependencies and your skills

3. **Follow TDD:** Each plan includes test-first development steps

4. **Commit frequently:** After each passing test

## Work Package Index

### Phase 1: Foundation (No Dependencies - Can Work in Parallel)

| Package | Module | Effort | Skills Needed |
|---------|--------|--------|---------------|
| [01 - Reference Data](01_reference_data.md) | `reference_data.py` | 8-12 hrs | Data extraction, lookup tables |
| [02 - Component Model](02_component_model.md) | `component.py` | 6-8 hrs | Dataclasses, validation logic |

**Start with these!** They have no dependencies and other modules need them.

---

### Phase 2: Core Logic (Depends on Phase 1)

| Package | Module | Effort | Dependencies | Skills Needed |
|---------|--------|--------|--------------|---------------|
| [03 - Parser](03_parser.md) | `parser.py` | 10-12 hrs | component.py | kinparse library, XML parsing |
| [04 - Circuit Analysis](04_circuit_analysis.md) | `circuit.py` | 12-15 hrs | component.py | Algorithms, spatial analysis |
| [05 - Wire Calculator](05_wire_calculator.md) | `wire_calculator.py` | 10-12 hrs | reference_data.py, component.py | Electrical calculations, formulas |
| [06 - Wire BOM Model](06_wire_bom_model.md) | `wire_bom.py` | 6-8 hrs | component.py | Data structures |

**These can be worked on in parallel** once Phase 1 is complete.

---

### Phase 3: Validation and Output (Depends on Phase 2)

| Package | Module | Effort | Dependencies | Skills Needed |
|---------|--------|--------|--------------|---------------|
| [07 - Validator](07_validator.md) | `validator.py` | 8-10 hrs | component, circuit, wire_bom, reference_data | Validation logic |
| [08 - CSV Output](08_output_csv.md) | `output_csv.py` | 4-5 hrs | wire_bom.py | CSV formatting |
| [09 - Markdown Output](09_output_markdown.md) | `output_markdown.py` | 8-10 hrs | wire_bom.py, component.py | Markdown formatting, reporting |

**These can be worked in parallel** once their dependencies are complete.

---

### Phase 4: Integration (Depends on All Modules)

| Package | Modules | Effort | Dependencies | Skills Needed |
|---------|---------|--------|--------------|---------------|
| [10 - CLI and Integration](10_cli_and_integration.md) | `__main__.py`, `schematic_help.py` | 12-15 hrs | ALL modules | CLI design, orchestration |

**Start this last!** After all other modules are complete and tested.

---

## Dependency Graph

```
Phase 1 (parallel):
├── reference_data (no deps)
└── component_model (no deps)

Phase 2 (parallel after Phase 1):
├── parser (→ component)
├── circuit_analysis (→ component)
├── wire_calculator (→ reference_data, component)
└── wire_bom_model (→ component)

Phase 3 (parallel after Phase 2):
├── validator (→ component, circuit, wire_bom, reference_data)
├── output_csv (→ wire_bom)
└── output_markdown (→ wire_bom, component)

Phase 4 (serial after Phase 3):
└── cli_and_integration (→ ALL)
```

## Module Size Comparison

| Size | Packages | Total Effort |
|------|----------|--------------|
| Small (< 8 hrs) | 02, 06, 08 | 3 packages |
| Medium (8-12 hrs) | 01, 03, 05, 07, 09 | 5 packages |
| Large (> 12 hrs) | 04, 10 | 2 packages |

**Total estimated effort:** ~85-100 hours

## Recommended Team Assignment

### Solo Implementation
Work through phases sequentially:
1. Week 1-2: Phase 1 (foundation)
2. Week 3-4: Phase 2 (core logic)
3. Week 5: Phase 3 (validation & output)
4. Week 6: Phase 4 (integration)

### Two-Programmer Team
- **Programmer A:** 01 → 03 → 05 → 08 → 10 (parsing & calculations track)
- **Programmer B:** 02 → 04 → 06 → 07 → 09 (modeling & validation track)

### Three-Programmer Team
- **Programmer A:** 01, 05, 08 (data & calculations)
- **Programmer B:** 02, 04, 07 (modeling & validation)
- **Programmer C:** 03, 06, 09 (parsing & output)
- **All together:** 10 (integration)

### Four+ Programmer Team
Assign one package per programmer in Phase 1-2, then regroup for Phase 3-4.

---

## Development Process

### For Each Work Package:

1. **Read the plan** completely before starting
2. **Check dependencies** are complete
3. **Read interface contract** in `00_overview_and_contracts.md`
4. **Follow TDD:**
   - Write test (RED)
   - Implement code (GREEN)
   - Refactor if needed
   - Commit with proper message
5. **Mark tasks complete** as you go
6. **Run full test suite** before marking package complete

### Test-Driven Development Cycle

```
RED → GREEN → REFACTOR → COMMIT → repeat
```

**Never skip tests!** They're your safety net for integration.

---

## Integration Strategy

### Continuous Integration
- Each package should have passing tests before integration
- Integration happens at phase boundaries
- Package 10 (CLI) performs final integration

### Testing Levels
1. **Unit tests:** Each function/class (within packages)
2. **Integration tests:** Between packages (at phase boundaries)
3. **End-to-end tests:** Complete workflow (in Package 10)

---

## Code Standards

All implementations must follow `CLAUDE.md` requirements:

- **ABOUTME comments:** Two-line header in every file
- **Type hints:** All function signatures
- **Docstrings:** All public functions
- **TDD:** Test first, always
- **No temporal names:** No "new", "old", "improved" in code
- **YAGNI:** Only implement what's needed now
- **DRY:** Refactor duplication after tests pass
- **Frequent commits:** After each passing test

---

## Test Fixtures

Shared test fixtures are in `tests/fixtures/`:

- `simple_two_component.net` - Minimal netlist (J1 → SW1)
- `with_custom_fields.net` - Components with FS/WL/BL/Load/Rating
- `multi_net.net` - Multiple nets
- `multi_node.net` - Net with 3+ components
- `missing_fields.net` - Components without custom fields
- `realistic_ea_system.net` - Complete aircraft electrical system

**Create these fixtures early** (during Package 03 - Parser)

---

## Questions & Communication

### Before Starting a Package
- Have you read `00_overview_and_contracts.md`?
- Are all dependencies complete?
- Do you understand the interface contract?

### During Implementation
- Unclear interface? Check `00_overview_and_contracts.md`
- Test failing? Check design spec: `docs/plans/kicad2wireBOM_design.md`
- Integration issue? Check dependency graph above

### After Completing a Package
- All tests pass? ✓
- Interface matches contract? ✓
- Code follows CLAUDE.md? ✓
- Committed with proper messages? ✓

---

## Reference Documents

- **Design Specification:** `docs/plans/kicad2wireBOM_design.md`
- **Original Implementation Plan:** `docs/plans/kicad2wireBOM_implementation.md` (older, less modular)
- **Interface Contracts:** `00_overview_and_contracts.md` (this directory)
- **Wire Marking Standard:** `docs/ea_wire_marking_standard.md`
- **Project Guidance:** `CLAUDE.md` (root directory)
- **Reference Materials:** `docs/references/` (Aeroelectric Connection, MIL-SPECs)

---

## Success Criteria

A work package is **complete** when:

- [ ] All tests pass
- [ ] Module exports match interface contract
- [ ] Code follows CLAUDE.md standards
- [ ] Comprehensive test coverage
- [ ] Committed to git with proper messages
- [ ] Documentation complete (docstrings, comments)
- [ ] Integration checklist verified (if applicable)

---

## Final Integration Checklist

Before marking project complete:

- [ ] All 10 work packages complete
- [ ] Full test suite passes: `pytest -v`
- [ ] Integration tests pass
- [ ] End-to-end test with real KiCad netlist works
- [ ] Both output formats (CSV, Markdown) work
- [ ] Both output modes (builder, engineering) work
- [ ] CLI handles all arguments correctly
- [ ] Error handling works
- [ ] README updated with usage examples
- [ ] Version tagged (v0.1.0)

---

**Ready to start? Begin with Package 00 (overview), then choose Package 01 or 02!**
