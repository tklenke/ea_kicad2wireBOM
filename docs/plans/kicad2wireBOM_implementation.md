# kicad2wireBOM Implementation Plan

## Project Overview

**Goal:** Convert KiCad schematic netlist files into a CSV-formatted wire Bill of Materials (BOM) for experimental aircraft wiring harnesses.

**What this tool does:**
- Reads KiCad v9 netlist files (`.net` or `.xml` format)
- Extracts wire connection information from the netlist
- Generates a CSV file listing all wire connections with proper wire marking labels
- Follows the Experimental Aircraft Wire Marking Standard (EAWMS)

**Why this matters:**
- Aircraft wiring harnesses require precise documentation for safety and maintenance
- Manual BOM creation from schematics is error-prone and tedious
- Proper wire marking (per MIL-W-5088L) is critical for aircraft certification

---

## Prerequisites

### Knowledge Required
- **Python 3.x**: Basic to intermediate Python programming
- **Test-Driven Development (TDD)**: Write tests first, then implementation
- **CSV format**: Understand CSV structure and encoding
- **Git**: Basic commit workflows

### Domain Knowledge (Provided Here)
You do NOT need to know these in advance - this plan explains everything:
- KiCad netlist format
- Wire marking standards
- Aircraft wiring conventions
- The `kinparse` library

### Tools & Environment
- Python 3.13 (or 3.10+)
- Virtual environment at `venv/`
- pytest for testing
- kinparse library (already installed)

---

## Project Structure

```
ea_tools/
├── kicad2wireBOM/           # Main package
│   ├── __init__.py          # Package initialization (mostly empty)
│   ├── __main__.py          # CLI entry point (argparse, file handling)
│   ├── parser.py            # [TO CREATE] Netlist parsing logic
│   ├── wire_bom.py          # [TO CREATE] Wire BOM data model
│   └── csv_writer.py        # [TO CREATE] CSV output generation
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_kicad2wireBOM_cli.py         # CLI tests (existing)
│   ├── test_kicad2wireBOM_file_handling.py  # File I/O tests (existing)
│   ├── test_parser.py       # [TO CREATE] Parser tests
│   ├── test_wire_bom.py     # [TO CREATE] Wire BOM model tests
│   ├── test_csv_writer.py   # [TO CREATE] CSV writer tests
│   └── fixtures/            # [TO CREATE] Test netlist files
├── docs/
│   ├── ea_wire_marking_standard.md  # EAWMS reference (read-only for your purposes)
│   └── plans/               # This file
├── requirements.txt         # Python dependencies
└── pytest.ini               # Pytest configuration
```

---

## Background: Understanding the Domain

### What is a KiCad Netlist?

A **netlist** is a text file that describes all electrical connections in a schematic:
- **Components**: Batteries, switches, Line Replaceable Units (LRU), Lights
- **Nets**: Electrical connections between component pins
- **Pin associations**: Which pins connect to which nets

**Example snippet** (simplified):
```xml
<net code="1" name="Net-L105">
  <node ref="J1" pin="1"/>
  <node ref="SW1" pin="2"/>
</net>
```

This means: Pin 1 of connector J1 connects to Pin 2 of switch SW1 via net "Net-L105".

### What is a Wire BOM?

A **Wire BOM** lists every physical wire segment needed to build the harness:

| Wire Label | From | To | Wire Gauge | Wire Color | Length | Notes |
|------------|------|----|-----------| -----------|--------|-------|
| L-105-A | J1-1 | SW1-2 | 20 AWG | Red | 24" | Landing light power |

**Key fields:**
- **Wire Label**: Following EAWMS format (e.g., `L-105-A`)
- **From/To**: Component pin references (e.g., `J1-1` means connector J1, pin 1)
- **Wire Gauge**: AWG size (20, 22, 18, etc.)
- **Wire Color**: Physical wire color for identification
- **Length**: Physical wire length (optional, often added later)
- **Notes**: Circuit description or purpose

### Wire Marking Standard (EAWMS)

The project follows a simplified MIL-SPEC wire marking system:

**Format:** `SYSTEM-CIRCUIT-SEGMENT`

- **System Code** (1 char): Circuit function (L=Lighting, P=Power, R=Radio, etc.)
- **Circuit ID** (3-5 digits): Unique circuit number from schematic
- **Segment ID** (1 char, optional): Physical wire segment (A, B, C...)

**Example:** `L-105-C`
- `L` = Lighting system
- `105` = Circuit 105 (landing light)
- `C` = Third segment of this circuit

**Reference:** See `docs/ea_wire_marking_standard.md` for complete system codes.

### The kinparse Library

`kinparse` is a Python library that parses KiCad netlists:

```python
from kinparse import parse_netlist

# Parse netlist file
netlist = parse_netlist('schematic.net')

# Access netlist data
# netlist is a pyparsing object with nested attributes
# You'll explore its structure in Task 1
```

**Key point:** You don't need to understand pyparsing deeply. You'll write code to explore the `netlist` object structure and extract what you need.

---

## Development Principles

### Test-Driven Development (TDD)

**ALWAYS follow this cycle:**

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to make it pass
3. **REFACTOR**: Clean up code while keeping tests green
4. **COMMIT**: Commit after each passing test

**Example workflow:**
```bash
# 1. Write test
vim tests/test_parser.py

# 2. Run test (should FAIL)
pytest tests/test_parser.py::test_parse_simple_netlist -v

# 3. Write code
vim kicad2wireBOM/parser.py

# 4. Run test (should PASS)
pytest tests/test_parser.py::test_parse_simple_netlist -v

# 5. Commit
git add tests/test_parser.py kicad2wireBOM/parser.py
git commit -m "Add parser for simple two-component netlist"
```

### YAGNI (You Aren't Gonna Need It)

**Only build what's needed NOW. Don't add features for "maybe later".**

❌ **Bad:**
```python
class WireBOM:
    def __init__(self):
        self.wires = []
        self.connectors = []  # Maybe we'll need this?
        self.switches = []     # Could be useful?
        self.cache = {}        # Optimization for later?
```

✅ **Good:**
```python
class WireBOM:
    def __init__(self):
        self.wires = []  # Only what we need now
```

**Add features only when tests require them.**

### DRY (Don't Repeat Yourself)

**Refactor duplication AFTER tests pass, not before.**

**First pass** (duplication is OK while learning):
```python
def format_wire_from(component, pin):
    return f"{component}-{pin}"

def format_wire_to(component, pin):
    return f"{component}-{pin}"
```

**Second pass** (refactor when you see the pattern):
```python
def format_pin_reference(component, pin):
    return f"{component}-{pin}"
```

### Good Test Design

Since you're learning, here are the key principles:

#### 1. Test One Thing at a Time

❌ **Bad** (tests multiple things):
```python
def test_everything():
    netlist = parse_file("test.net")
    bom = generate_bom(netlist)
    csv = write_csv(bom)
    assert "L-105" in csv
    assert len(bom.wires) == 5
```

✅ **Good** (focused tests):
```python
def test_parse_netlist_returns_components():
    netlist = parse_file("simple.net")
    assert len(netlist.components) == 2

def test_generate_bom_creates_wire_entries():
    netlist = MockNetlist(nets=[net1, net2])
    bom = generate_bom(netlist)
    assert len(bom.wires) == 2
```

#### 2. Use Descriptive Test Names

Test names should describe **what** is being tested and **what** should happen:

```python
def test_parse_netlist_with_missing_file_raises_file_not_found()
def test_wire_label_follows_eawms_format()
def test_csv_output_has_header_row()
```

#### 3. Arrange-Act-Assert Pattern

```python
def test_example():
    # ARRANGE: Set up test data
    netlist_file = "tests/fixtures/simple.net"

    # ACT: Perform the action
    result = parse_netlist(netlist_file)

    # ASSERT: Check the outcome
    assert result is not None
    assert len(result.nets) > 0
```

#### 4. Use Fixtures for Test Data

Create sample netlist files in `tests/fixtures/`:
- `simple_two_component.net` - Minimal valid netlist
- `multi_net.net` - Multiple nets between components
- `complex_circuit.net` - Realistic circuit

**Do NOT hardcode long XML strings in tests.** Use fixture files.

---

## Implementation Tasks

Each task follows this structure:
1. **What**: Description of the task
2. **Why**: Business/technical reason
3. **How**: Step-by-step implementation
4. **Files**: Which files to create/modify
5. **Test**: How to verify it works
6. **Commit**: What to commit

---

## TASK 1: Explore kinparse and Create Sample Netlist Fixtures

**What:** Understand how kinparse parses KiCad netlists and create test fixture files.

**Why:** Before we can write parsers, we need to understand the data structures kinparse returns. We also need real netlist examples for testing.

**Prerequisites:** None (starting point)

**Files to create:**
- `tests/fixtures/simple_two_component.net` - Minimal netlist (connector to switch)
- `tests/fixtures/multi_net.net` - Multiple connections
- `exploration/explore_kinparse.py` - Temporary exploration script (not committed)

### Step 1.1: Create a Sample KiCad Netlist Fixture

KiCad v9 netlists are XML format. Create a minimal example:

```bash
mkdir -p tests/fixtures
```

**File:** `tests/fixtures/simple_two_component.net`

```xml
<?xml version="1.0" encoding="utf-8"?>
<export version="E">
  <design>
    <source>simple_circuit.kicad_sch</source>
    <date>2025-01-15</date>
    <tool>Eeschema</tool>
  </design>
  <components>
    <comp ref="J1">
      <value>Conn_01x02</value>
      <libsource lib="Connector" part="Conn_01x02"/>
      <property name="Reference" value="J1"/>
    </comp>
    <comp ref="SW1">
      <value>SW_SPST</value>
      <libsource lib="Device" part="SW_SPST"/>
      <property name="Reference" value="SW1"/>
    </comp>
  </components>
  <nets>
    <net code="1" name="Net-L105">
      <node ref="J1" pin="1" pinfunction="Pin_1"/>
      <node ref="SW1" pin="1"/>
    </net>
  </nets>
</export>
```

**What this represents:**
- Two components: J1 (connector) and SW1 (switch)
- One net: "Net-L105" connecting J1 pin 1 to SW1 pin 1

### Step 1.2: Explore kinparse Data Structure

Create a temporary exploration script (NOT part of final codebase):

**File:** `exploration/explore_kinparse.py`

```bash
mkdir exploration
```

```python
#!/usr/bin/env python3
"""
TEMPORARY exploration script to understand kinparse output.
This file will NOT be committed to the repo.
"""

from kinparse import parse_netlist
import pprint

# Parse the simple fixture
netlist = parse_netlist('tests/fixtures/simple_two_component.net')

print("=== Netlist Object Type ===")
print(type(netlist))
print()

print("=== Netlist Attributes (dir) ===")
print([attr for attr in dir(netlist) if not attr.startswith('_')])
print()

print("=== Trying to access common attributes ===")
# Try different attribute access patterns
try:
    print("netlist.components:", netlist.components)
except AttributeError as e:
    print(f"No 'components' attribute: {e}")

try:
    print("netlist.nets:", netlist.nets)
except AttributeError as e:
    print(f"No 'nets' attribute: {e}")

try:
    print("netlist.parts:", netlist.parts)
except AttributeError as e:
    print(f"No 'parts' attribute: {e}")

print()
print("=== Full netlist dump ===")
pprint.pprint(netlist.asDict() if hasattr(netlist, 'asDict') else str(netlist))
```

**Run it:**
```bash
source venv/bin/activate
python exploration/explore_kinparse.py
```

### Step 1.3: Document Your Findings

Based on the exploration output, create a document:

**File:** `docs/kinparse_data_structure.md`

```markdown
# kinparse Data Structure Reference

## Overview
This document describes the data structure returned by `kinparse.parse_netlist()`.

## Netlist Object

[Document what you discovered, for example:]

- Type: `pyparsing.ParseResults`
- Key attributes:
  - `netlist.component` or `netlist.comp`: List of components
  - `netlist.net`: List of nets
  - `netlist.design`: Design metadata

## Component Structure

[Example - adjust based on reality:]

```python
component = netlist.comp[0]
component.ref        # "J1"
component.value      # "Conn_01x02"
```

## Net Structure

[Example:]

```python
net = netlist.net[0]
net.name            # "Net-L105"
net.code            # "1"
net.node            # List of node connections
net.node[0].ref     # "J1"
net.node[0].pin     # "1"
```

[Adjust these based on your actual findings]
```

### Step 1.4: Create Additional Test Fixtures

Create more complex fixtures for later testing:

**File:** `tests/fixtures/multi_net.net`

[Create a netlist with 3 components and 2 nets - expand on the simple example]

### What to Test

At this stage, no automated tests yet. Manual exploration only.

### What to Commit

```bash
git add tests/fixtures/simple_two_component.net
git add tests/fixtures/multi_net.net
git add docs/kinparse_data_structure.md
git commit -m "Add test fixtures and document kinparse data structure

- Create minimal two-component netlist fixture for testing
- Add multi-net fixture for complex test cases
- Document kinparse ParseResults structure from exploration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**DO NOT COMMIT** `exploration/` directory. Add it to `.gitignore`:

```bash
echo "exploration/" >> .gitignore
git add .gitignore
git commit -m "Ignore exploration directory"
```

---

## TASK 2: Implement Netlist Parser (TDD)

**What:** Create `kicad2wireBOM/parser.py` to parse KiCad netlists using kinparse.

**Why:** This is the core data extraction logic. We need structured data from the netlist before we can generate a BOM.

**Prerequisites:** Task 1 complete (fixtures and kinparse understanding)

**Files to create:**
- `kicad2wireBOM/parser.py`
- `tests/test_parser.py`

### Step 2.1: Write First Test (RED)

**File:** `tests/test_parser.py`

```python
# ABOUTME: Tests for KiCad netlist parser
# ABOUTME: Validates netlist parsing using kinparse and data extraction

import pytest
from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file


def test_parse_simple_netlist_file_returns_parsed_data():
    """Test that parser can read and parse a simple netlist file"""
    # ARRANGE
    fixture_path = Path("tests/fixtures/simple_two_component.net")

    # ACT
    result = parse_netlist_file(fixture_path)

    # ASSERT
    assert result is not None
    assert result.nets is not None  # Adjust based on your Task 1 findings
```

**Run test (should FAIL):**
```bash
pytest tests/test_parser.py::test_parse_simple_netlist_file_returns_parsed_data -v
```

Expected: `ModuleNotFoundError: No module named 'kicad2wireBOM.parser'`

### Step 2.2: Implement Minimal Parser (GREEN)

**File:** `kicad2wireBOM/parser.py`

```python
# ABOUTME: KiCad netlist parser using kinparse library
# ABOUTME: Extracts component and net information from KiCad v9 netlist files

from pathlib import Path
from kinparse import parse_netlist as kinparse_parse


def parse_netlist_file(file_path):
    """
    Parse a KiCad netlist file using kinparse.

    Args:
        file_path: Path to .net file (str or Path object)

    Returns:
        pyparsing.ParseResults: Parsed netlist object

    Raises:
        FileNotFoundError: If file_path does not exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Netlist file not found: {file_path}")

    return kinparse_parse(str(path))
```

**Run test (should PASS):**
```bash
pytest tests/test_parser.py::test_parse_simple_netlist_file_returns_parsed_data -v
```

**Commit:**
```bash
git add kicad2wireBOM/parser.py tests/test_parser.py
git commit -m "Add basic netlist file parser

- Implement parse_netlist_file() wrapper around kinparse
- Add test for simple two-component netlist parsing
- Validate file existence before parsing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 2.3: Test Invalid File Handling (RED → GREEN)

**Add test to** `tests/test_parser.py`:

```python
def test_parse_nonexistent_file_raises_file_not_found():
    """Test that parsing nonexistent file raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError):
        parse_netlist_file("does_not_exist.net")
```

**Run test** (should already PASS due to existing implementation, but verify):
```bash
pytest tests/test_parser.py -v
```

**Commit if you added code:**
```bash
git add tests/test_parser.py
git commit -m "Add test for nonexistent netlist file handling"
```

### Step 2.4: Extract Nets from Parsed Netlist (RED → GREEN)

Now we need a function to extract connection information.

**Add test:**

```python
def test_extract_nets_from_simple_netlist():
    """Test extracting net information from parsed netlist"""
    from kicad2wireBOM.parser import extract_nets

    # ARRANGE
    fixture_path = Path("tests/fixtures/simple_two_component.net")
    parsed = parse_netlist_file(fixture_path)

    # ACT
    nets = extract_nets(parsed)

    # ASSERT
    assert len(nets) == 1
    assert nets[0]['name'] == 'Net-L105'  # Adjust based on fixture
    assert len(nets[0]['nodes']) == 2
```

**Run test (FAIL):**
```bash
pytest tests/test_parser.py::test_extract_nets_from_simple_netlist -v
```

**Implement `extract_nets`:**

Add to `kicad2wireBOM/parser.py`:

```python
def extract_nets(parsed_netlist):
    """
    Extract net connection information from parsed netlist.

    Args:
        parsed_netlist: ParseResults from kinparse

    Returns:
        List of dict with keys: 'name', 'code', 'nodes'
        where nodes is list of dict with keys: 'ref', 'pin'
    """
    nets = []

    # Access nets - adjust based on your Task 1 findings
    for net in parsed_netlist.net:
        net_info = {
            'name': net.name,
            'code': net.code,
            'nodes': []
        }

        for node in net.node:
            net_info['nodes'].append({
                'ref': node.ref,
                'pin': node.pin
            })

        nets.append(net_info)

    return nets
```

**Run test (PASS):**
```bash
pytest tests/test_parser.py -v
```

**Commit:**
```bash
git add kicad2wireBOM/parser.py tests/test_parser.py
git commit -m "Add extract_nets() to parse net connections

- Extract net name, code, and node connections
- Return structured dict for easy BOM generation
- Test with simple two-component fixture

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 2.5: Test with Multi-Net Fixture

**Add test:**

```python
def test_extract_nets_from_multi_net_fixture():
    """Test extracting multiple nets from complex netlist"""
    fixture_path = Path("tests/fixtures/multi_net.net")
    parsed = parse_netlist_file(fixture_path)

    nets = extract_nets(parsed)

    assert len(nets) >= 2  # Adjust based on your fixture
```

**Run test:**
```bash
pytest tests/test_parser.py -v
```

If it fails, debug and fix `extract_nets()`. Then commit.

---

## TASK 3: Implement Wire BOM Data Model

**What:** Create `kicad2wireBOM/wire_bom.py` with data classes for wire connections.

**Why:** We need a clean data model to represent wires before CSV generation. This separates parsing concerns from output formatting.

**Prerequisites:** Task 2 complete

**Files to create:**
- `kicad2wireBOM/wire_bom.py`
- `tests/test_wire_bom.py`

### Step 3.1: Design the Data Model (Test First)

**File:** `tests/test_wire_bom.py`

```python
# ABOUTME: Tests for wire BOM data model
# ABOUTME: Validates WireConnection and WireBOM classes

from kicad2wireBOM.wire_bom import WireConnection, WireBOM


def test_create_wire_connection_with_required_fields():
    """Test creating a basic wire connection"""
    # ACT
    wire = WireConnection(
        wire_label="L-105-A",
        from_ref="J1-1",
        to_ref="SW1-2"
    )

    # ASSERT
    assert wire.wire_label == "L-105-A"
    assert wire.from_ref == "J1-1"
    assert wire.to_ref == "SW1-2"
```

**Run (FAIL):**
```bash
pytest tests/test_wire_bom.py::test_create_wire_connection_with_required_fields -v
```

### Step 3.2: Implement WireConnection Class (GREEN)

**File:** `kicad2wireBOM/wire_bom.py`

```python
# ABOUTME: Data model for wire Bill of Materials
# ABOUTME: Defines WireConnection and WireBOM classes for structured wire data

from dataclasses import dataclass
from typing import Optional


@dataclass
class WireConnection:
    """Represents a single wire connection in the BOM"""
    wire_label: str           # EAWMS format: L-105-A
    from_ref: str             # Component pin reference: J1-1
    to_ref: str               # Component pin reference: SW1-2
    wire_gauge: Optional[str] = None   # AWG size: "20 AWG"
    wire_color: Optional[str] = None   # Physical color: "Red"
    length: Optional[str] = None       # Physical length: "24 inches"
    notes: Optional[str] = None        # Circuit description
```

**Run (PASS):**
```bash
pytest tests/test_wire_bom.py -v
```

**Commit:**
```bash
git add kicad2wireBOM/wire_bom.py tests/test_wire_bom.py
git commit -m "Add WireConnection data model

- Implement dataclass for wire connection representation
- Include required fields (label, from, to) and optional metadata
- Test basic instantiation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 3.3: Add WireBOM Container Class (RED → GREEN)

**Add test:**

```python
def test_wire_bom_stores_multiple_connections():
    """Test WireBOM can hold multiple wire connections"""
    # ARRANGE
    bom = WireBOM()
    wire1 = WireConnection("L-105-A", "J1-1", "SW1-2")
    wire2 = WireConnection("L-105-B", "SW1-1", "LIGHT1-1")

    # ACT
    bom.add_wire(wire1)
    bom.add_wire(wire2)

    # ASSERT
    assert len(bom.wires) == 2
    assert bom.wires[0].wire_label == "L-105-A"
    assert bom.wires[1].wire_label == "L-105-B"
```

**Implement WireBOM:**

Add to `kicad2wireBOM/wire_bom.py`:

```python
class WireBOM:
    """Container for wire BOM entries"""

    def __init__(self):
        self.wires = []

    def add_wire(self, wire: WireConnection):
        """Add a wire connection to the BOM"""
        self.wires.append(wire)
```

**Test and commit:**
```bash
pytest tests/test_wire_bom.py -v
git add kicad2wireBOM/wire_bom.py tests/test_wire_bom.py
git commit -m "Add WireBOM container class

- Implement WireBOM to store multiple wire connections
- Add add_wire() method
- Test adding multiple wires to BOM

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## TASK 4: Generate Wire Labels (EAWMS Format)

**What:** Implement wire label generation following the EAWMS standard.

**Why:** Wire labels must follow `SYSTEM-CIRCUIT-SEGMENT` format per project standards.

**Prerequisites:** Task 3 complete

**Files to modify:**
- `kicad2wireBOM/wire_bom.py` (add label generation)
- `tests/test_wire_bom.py` (add label tests)

### Step 4.1: Understand Label Generation Requirements

Read `docs/ea_wire_marking_standard.md` again. Key points:

- **System code**: Must be extracted from net name (e.g., "Net-L105" → "L")
- **Circuit ID**: Numeric portion (e.g., "Net-L105" → "105")
- **Segment ID**: Sequential (A, B, C...) for multiple segments

**Challenge:** How do we assign segment IDs?

**Solution:** For each net with multiple connections, create segments:
- If net connects A→B→C, create segments: A-B, B-C
- Each gets sequential letter: `-A`, `-B`

### Step 4.2: Test Label Generation from Net Name (RED)

**Add test:**

```python
def test_generate_wire_label_from_net_name():
    """Test generating EAWMS-format label from KiCad net name"""
    from kicad2wireBOM.wire_bom import generate_wire_label

    # ACT
    label = generate_wire_label(net_name="Net-L105", segment="A")

    # ASSERT
    assert label == "L-105-A"
```

**Run (FAIL):**
```bash
pytest tests/test_wire_bom.py::test_generate_wire_label_from_net_name -v
```

### Step 4.3: Implement Label Generation (GREEN)

Add to `kicad2wireBOM/wire_bom.py`:

```python
import re


def generate_wire_label(net_name: str, segment: str) -> str:
    """
    Generate EAWMS-format wire label from KiCad net name.

    Format: SYSTEM-CIRCUIT-SEGMENT
    Example: "Net-L105" → "L-105-A"

    Args:
        net_name: KiCad net name (e.g., "Net-L105")
        segment: Segment letter (A, B, C, ...)

    Returns:
        Wire label string in EAWMS format

    Raises:
        ValueError: If net_name doesn't match expected pattern
    """
    # Match pattern: "Net-" followed by letter(s) and number(s)
    match = re.match(r'Net-([A-Z]+)(\d+)', net_name, re.IGNORECASE)

    if not match:
        raise ValueError(f"Invalid net name format: {net_name}")

    system_code = match.group(1).upper()
    circuit_id = match.group(2)

    return f"{system_code}-{circuit_id}-{segment}"
```

**Test (PASS):**
```bash
pytest tests/test_wire_bom.py -v
```

### Step 4.4: Test Invalid Net Names (RED → GREEN)

**Add test:**

```python
def test_generate_wire_label_with_invalid_net_name_raises_error():
    """Test that invalid net names raise ValueError"""
    from kicad2wireBOM.wire_bom import generate_wire_label

    with pytest.raises(ValueError):
        generate_wire_label("InvalidName", "A")
```

**Test (should already PASS), then commit:**

```bash
pytest tests/test_wire_bom.py -v
git add kicad2wireBOM/wire_bom.py tests/test_wire_bom.py
git commit -m "Add EAWMS wire label generation

- Implement generate_wire_label() following SYSTEM-CIRCUIT-SEGMENT format
- Parse KiCad net names (e.g., Net-L105 → L-105-A)
- Validate net name format and raise ValueError for invalid names
- Test label generation and error handling

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## TASK 5: Convert Nets to Wire BOM Entries

**What:** Create function to convert parsed nets into WireBOM with proper labels.

**Why:** Connect the parser output to the BOM data model.

**Prerequisites:** Tasks 2, 3, 4 complete

**Files to create/modify:**
- `kicad2wireBOM/wire_bom.py` (add conversion function)
- `tests/test_wire_bom.py` (add conversion tests)

### Step 5.1: Test Net-to-BOM Conversion (RED)

**Add test:**

```python
def test_convert_nets_to_wire_bom():
    """Test converting parsed nets to WireBOM"""
    from kicad2wireBOM.wire_bom import convert_nets_to_bom

    # ARRANGE
    nets = [
        {
            'name': 'Net-L105',
            'code': '1',
            'nodes': [
                {'ref': 'J1', 'pin': '1'},
                {'ref': 'SW1', 'pin': '2'}
            ]
        }
    ]

    # ACT
    bom = convert_nets_to_bom(nets)

    # ASSERT
    assert len(bom.wires) == 1
    wire = bom.wires[0]
    assert wire.wire_label == "L-105-A"
    assert wire.from_ref == "J1-1"
    assert wire.to_ref == "SW1-2"
```

**Run (FAIL):**
```bash
pytest tests/test_wire_bom.py::test_convert_nets_to_wire_bom -v
```

### Step 5.2: Implement Conversion (GREEN)

Add to `kicad2wireBOM/wire_bom.py`:

```python
def convert_nets_to_bom(nets: list) -> WireBOM:
    """
    Convert parsed nets to WireBOM.

    For each net with 2+ nodes, create wire connections between nodes.
    For nets with >2 nodes, create segments connecting adjacent nodes.

    Args:
        nets: List of net dicts from parser.extract_nets()

    Returns:
        WireBOM containing wire connections
    """
    bom = WireBOM()

    for net in nets:
        net_name = net['name']
        nodes = net['nodes']

        if len(nodes) < 2:
            # Skip nets with <2 nodes (can't make a wire)
            continue

        # Create wire connections between adjacent nodes
        for i in range(len(nodes) - 1):
            segment_letter = chr(ord('A') + i)  # A, B, C, ...

            from_node = nodes[i]
            to_node = nodes[i + 1]

            wire_label = generate_wire_label(net_name, segment_letter)
            from_ref = f"{from_node['ref']}-{from_node['pin']}"
            to_ref = f"{to_node['ref']}-{to_node['pin']}"

            wire = WireConnection(
                wire_label=wire_label,
                from_ref=from_ref,
                to_ref=to_ref
            )

            bom.add_wire(wire)

    return bom
```

**Test (PASS):**
```bash
pytest tests/test_wire_bom.py -v
```

**Commit:**
```bash
git add kicad2wireBOM/wire_bom.py tests/test_wire_bom.py
git commit -m "Add net-to-BOM conversion logic

- Implement convert_nets_to_bom() to create wire connections
- Handle multi-node nets with segment letters (A, B, C...)
- Format pin references as COMPONENT-PIN
- Test conversion with two-node net

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 5.3: Test Multi-Node Net Conversion (RED → GREEN)

**Add test:**

```python
def test_convert_multi_node_net_creates_segments():
    """Test that net with 3+ nodes creates multiple wire segments"""
    from kicad2wireBOM.wire_bom import convert_nets_to_bom

    # ARRANGE: Net connecting 3 components
    nets = [
        {
            'name': 'Net-P12',
            'code': '2',
            'nodes': [
                {'ref': 'BAT1', 'pin': '1'},
                {'ref': 'SW1', 'pin': '1'},
                {'ref': 'FUSE1', 'pin': '1'}
            ]
        }
    ]

    # ACT
    bom = convert_nets_to_bom(nets)

    # ASSERT
    assert len(bom.wires) == 2  # BAT→SW and SW→FUSE
    assert bom.wires[0].wire_label == "P-12-A"
    assert bom.wires[1].wire_label == "P-12-B"
```

**Test (should PASS with existing implementation):**
```bash
pytest tests/test_wire_bom.py -v
```

**Commit if needed:**
```bash
git add tests/test_wire_bom.py
git commit -m "Add test for multi-node net segment creation"
```

---

## TASK 6: Implement CSV Writer

**What:** Create `kicad2wireBOM/csv_writer.py` to output BOM as CSV.

**Why:** Final output format for wire harness builders.

**Prerequisites:** Task 5 complete

**Files to create:**
- `kicad2wireBOM/csv_writer.py`
- `tests/test_csv_writer.py`

### Step 6.1: Define CSV Format

**Target CSV format:**

```csv
Wire Label,From,To,Wire Gauge,Wire Color,Length,Notes
L-105-A,J1-1,SW1-2,,,,"Landing light power"
L-105-B,SW1-1,LIGHT1-1,,,,"Landing light power"
```

**Columns:**
- Wire Label (required)
- From (required)
- To (required)
- Wire Gauge (optional, empty for now)
- Wire Color (optional, empty for now)
- Length (optional, empty for now)
- Notes (optional, empty for now)

### Step 6.2: Test CSV Output (RED)

**File:** `tests/test_csv_writer.py`

```python
# ABOUTME: Tests for CSV wire BOM writer
# ABOUTME: Validates CSV output format and content

import csv
import tempfile
from pathlib import Path
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.csv_writer import write_bom_to_csv


def test_write_bom_to_csv_creates_file():
    """Test that CSV file is created with header and data"""
    # ARRANGE
    bom = WireBOM()
    bom.add_wire(WireConnection("L-105-A", "J1-1", "SW1-2"))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)

    try:
        # ACT
        write_bom_to_csv(bom, csv_path)

        # ASSERT
        assert csv_path.exists()

        # Read and verify content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['Wire Label'] == 'L-105-A'
        assert rows[0]['From'] == 'J1-1'
        assert rows[0]['To'] == 'SW1-2'
    finally:
        csv_path.unlink()  # Cleanup
```

**Run (FAIL):**
```bash
pytest tests/test_csv_writer.py -v
```

### Step 6.3: Implement CSV Writer (GREEN)

**File:** `kicad2wireBOM/csv_writer.py`

```python
# ABOUTME: CSV writer for wire Bill of Materials
# ABOUTME: Outputs WireBOM as CSV file with proper formatting

import csv
from pathlib import Path
from kicad2wireBOM.wire_bom import WireBOM


def write_bom_to_csv(bom: WireBOM, output_path: Path):
    """
    Write WireBOM to CSV file.

    Args:
        bom: WireBOM to write
        output_path: Path to output CSV file
    """
    fieldnames = [
        'Wire Label',
        'From',
        'To',
        'Wire Gauge',
        'Wire Color',
        'Length',
        'Notes'
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for wire in bom.wires:
            writer.writerow({
                'Wire Label': wire.wire_label,
                'From': wire.from_ref,
                'To': wire.to_ref,
                'Wire Gauge': wire.wire_gauge or '',
                'Wire Color': wire.wire_color or '',
                'Length': wire.length or '',
                'Notes': wire.notes or ''
            })
```

**Test (PASS):**
```bash
pytest tests/test_csv_writer.py -v
```

**Commit:**
```bash
git add kicad2wireBOM/csv_writer.py tests/test_csv_writer.py
git commit -m "Add CSV writer for wire BOM

- Implement write_bom_to_csv() with standard column headers
- Handle optional fields (wire gauge, color, length, notes)
- Test CSV creation and content validation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 6.4: Test Empty BOM (RED → GREEN)

**Add test:**

```python
def test_write_empty_bom_creates_header_only():
    """Test that empty BOM still creates valid CSV with header"""
    bom = WireBOM()  # Empty

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)

    try:
        write_bom_to_csv(bom, csv_path)

        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 1  # Header only
        assert 'Wire Label' in rows[0]
    finally:
        csv_path.unlink()
```

**Test and commit:**
```bash
pytest tests/test_csv_writer.py -v
git add tests/test_csv_writer.py
git commit -m "Add test for empty BOM CSV output"
```

---

## TASK 7: Integrate Everything into CLI

**What:** Wire up all components in `kicad2wireBOM/__main__.py`.

**Why:** Make the tool functional end-to-end.

**Prerequisites:** Tasks 1-6 complete

**Files to modify:**
- `kicad2wireBOM/__main__.py`
- Tests already exist in `tests/test_kicad2wireBOM_cli.py` and `tests/test_kicad2wireBOM_file_handling.py`

### Step 7.1: Review Existing Tests

Run existing tests to see what's failing:

```bash
pytest tests/test_kicad2wireBOM_cli.py tests/test_kicad2wireBOM_file_handling.py -v
```

Most tests should pass (help text, file handling). One test will fail:

```python
def test_successful_processing_with_new_destination():
    """Test that processing succeeds with non-existent destination file"""
```

This is our integration target.

### Step 7.2: Implement Main Processing Logic

**Modify** `kicad2wireBOM/__main__.py`:

Replace the placeholder:

```python
    # Implementation will go here
    print(f"Processing {args.source}...")
    return 0
```

With:

```python
    # Import our modules
    from kicad2wireBOM.parser import parse_netlist_file, extract_nets
    from kicad2wireBOM.wire_bom import convert_nets_to_bom
    from kicad2wireBOM.csv_writer import write_bom_to_csv
    from pathlib import Path

    try:
        # Parse netlist
        print(f"Parsing netlist: {args.source}")
        parsed_netlist = parse_netlist_file(args.source)

        # Extract nets
        print("Extracting net connections...")
        nets = extract_nets(parsed_netlist)
        print(f"  Found {len(nets)} nets")

        # Convert to BOM
        print("Generating wire BOM...")
        bom = convert_nets_to_bom(nets)
        print(f"  Created {len(bom.wires)} wire connections")

        # Write CSV
        print(f"Writing CSV: {args.dest}")
        write_bom_to_csv(bom, Path(args.dest))

        print("✓ Wire BOM generated successfully")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

### Step 7.3: Test Integration

**Run all tests:**
```bash
pytest -v
```

All tests should pass.

**Manual test:**
```bash
source venv/bin/activate
python -m kicad2wireBOM tests/fixtures/simple_two_component.net output.csv
cat output.csv
```

Expected output:
```csv
Wire Label,From,To,Wire Gauge,Wire Color,Length,Notes
L-105-A,J1-1,SW1-2,,,
```

**Commit:**
```bash
git add kicad2wireBOM/__main__.py
git commit -m "Integrate parser, BOM generator, and CSV writer in CLI

- Wire up parse_netlist_file, extract_nets, convert_nets_to_bom, write_bom_to_csv
- Add progress output for user feedback
- Handle exceptions and return appropriate exit codes
- All tests now pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"
```

---

## TASK 8: Add End-to-End Integration Test

**What:** Create a full integration test with realistic fixture.

**Why:** Ensure all components work together correctly with real-world data.

**Prerequisites:** Task 7 complete

**Files to create:**
- `tests/fixtures/realistic_circuit.net` - Multi-net circuit
- `tests/test_integration.py` - End-to-end test

### Step 8.1: Create Realistic Fixture

**File:** `tests/fixtures/realistic_circuit.net`

[Create a more complex netlist with 4-5 components and 3-4 nets representing a realistic aircraft circuit like landing lights, navigation lights, etc.]

Example structure:
- Battery connector
- Master switch
- Circuit breaker
- Light switch
- Landing light
- Nav light

### Step 8.2: Write Integration Test

**File:** `tests/test_integration.py`

```python
# ABOUTME: End-to-end integration tests for kicad2wireBOM
# ABOUTME: Tests complete workflow from netlist file to CSV output

import subprocess
import sys
import csv
import tempfile
from pathlib import Path


def test_end_to_end_realistic_circuit():
    """Test complete workflow with realistic aircraft circuit netlist"""
    # ARRANGE
    fixture_path = "tests/fixtures/realistic_circuit.net"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_csv = Path(f.name)

    try:
        # ACT
        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", fixture_path, str(output_csv)],
            capture_output=True,
            text=True
        )

        # ASSERT
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_csv.exists()

        # Verify CSV content
        with open(output_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check we have wires
        assert len(rows) > 0, "No wires generated"

        # Check EAWMS format
        for row in rows:
            label = row['Wire Label']
            assert '-' in label, f"Invalid label format: {label}"

            # Check pattern: LETTER-NUMBER-LETTER
            parts = label.split('-')
            assert len(parts) == 3, f"Label should have 3 parts: {label}"
            assert parts[0].isalpha(), f"System code should be alpha: {parts[0]}"
            assert parts[1].isdigit(), f"Circuit ID should be numeric: {parts[1]}"
            assert parts[2].isalpha(), f"Segment should be alpha: {parts[2]}"

        print(f"✓ Generated {len(rows)} wires")

    finally:
        output_csv.unlink()
```

**Run test:**
```bash
pytest tests/test_integration.py -v -s
```

**Commit:**
```bash
git add tests/fixtures/realistic_circuit.net tests/test_integration.py
git commit -m "Add end-to-end integration test with realistic circuit

- Create multi-component aircraft circuit fixture
- Test complete CLI workflow from netlist to CSV
- Validate EAWMS label format in output
- Verify all wire segments are generated

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"
```

---

## TASK 9: Documentation and Final Polish

**What:** Update README, add usage examples, document limitations.

**Why:** Make the tool usable by others.

**Prerequisites:** Tasks 1-8 complete

**Files to modify:**
- `README.md`
- `kicad2wireBOM/__init__.py` (add version)

### Step 9.1: Update README

**File:** `README.md`

```markdown
# ea_tools

Miscellaneous Python programs for Experimental Aircraft projects.

## kicad2wireBOM

Convert KiCad schematic netlist files to wire Bill of Materials (BOM) CSV format.

### Features

- Parses KiCad v9 netlist files (`.net`, `.xml`)
- Generates wire labels following EAWMS (Experimental Aircraft Wire Marking Standard)
- Outputs CSV format for wire harness construction
- Handles multi-node nets with automatic segment labeling

### Installation

```bash
git clone https://github.com/yourusername/ea_tools.git
cd ea_tools
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Usage

```bash
# Basic usage
python -m kicad2wireBOM input.net output.csv

# Force overwrite existing file
python -m kicad2wireBOM -f input.net output.csv

# Get help
python -m kicad2wireBOM --help
```

### Example Output

```csv
Wire Label,From,To,Wire Gauge,Wire Color,Length,Notes
L-105-A,J1-1,SW1-2,,,
L-105-B,SW1-1,LIGHT1-1,,,
P-12-A,BAT1-1,SW2-1,,,
```

### Wire Label Format

Wire labels follow the EAWMS format: `SYSTEM-CIRCUIT-SEGMENT`

- **SYSTEM**: Single letter system code (L=Lighting, P=Power, R=Radio, etc.)
- **CIRCUIT**: Numeric circuit ID from schematic net name
- **SEGMENT**: Letter for physical wire segment (A, B, C...)

Example: `L-105-C` = Lighting system, circuit 105, segment C

See `docs/ea_wire_marking_standard.md` for complete system codes.

### Requirements

- KiCad net names must follow format: `Net-LNNN` where:
  - `L` is the system letter
  - `NNN` is the circuit number

Example valid net names:
- `Net-L105` (Lighting circuit 105)
- `Net-P12` (Power circuit 12)
- `Net-R200` (Radio circuit 200)

### Testing

```bash
pytest
```

### Limitations

- Only supports KiCad v9 netlist format
- Wire gauge, color, and length must be added manually to CSV
- Assumes net names follow EAWMS naming convention
- Multi-component nets create sequential segments (may not match physical routing)

### License

MIT License - See LICENSE file

### Contributing

See CLAUDE.md for development guidelines.
```

**Commit:**
```bash
git add README.md
git commit -m "Update README with kicad2wireBOM usage documentation

- Add installation instructions
- Document CLI usage and examples
- Explain wire label format (EAWMS)
- List requirements and limitations
- Add testing instructions

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com)"
```

### Step 9.2: Add Version to Package

**Modify** `kicad2wireBOM/__init__.py`:

```python
# ABOUTME: kicad2wireBOM package initialization
# ABOUTME: Processes KiCad v9 netlist files and generates wire BOM CSV output

__version__ = "0.1.0"
```

**Commit:**
```bash
git add kicad2wireBOM/__init__.py
git commit -m "Add version 0.1.0 to package"
```

---

## TASK 10: Final Testing and Verification

**What:** Run all tests, verify complete functionality.

**Why:** Ensure everything works before considering the project complete.

**Prerequisites:** All previous tasks complete

### Step 10.1: Run Complete Test Suite

```bash
# Run all tests with coverage
pytest --cov=kicad2wireBOM --cov-report=term-missing

# Expected: All tests pass, good coverage
```

### Step 10.2: Manual Testing with Real Netlist

If you have access to a real KiCad project:

```bash
# Export netlist from KiCad:
# In KiCad Eeschema: Tools → Generate Netlist File → Select format

# Generate BOM
python -m kicad2wireBOM /path/to/real/netlist.net wire_bom.csv

# Inspect output
cat wire_bom.csv
```

### Step 10.3: Create Final Commit

```bash
git status
# Ensure everything is committed

git log --oneline -10
# Review commit history
```

---

## Common Issues and Troubleshooting

### Issue: kinparse returns unexpected data structure

**Solution:** Re-run Task 1 exploration script and update `docs/kinparse_data_structure.md`. Adjust parser accordingly.

### Issue: Net names don't match EAWMS pattern

**Example:** Net named "Net-LandingLight" instead of "Net-L105"

**Solution:** Update `generate_wire_label()` to handle different patterns or document naming requirements clearly.

### Issue: Tests fail with "ModuleNotFoundError"

**Solution:** Ensure you're in the virtual environment:
```bash
source venv/bin/activate
which python  # Should point to venv/bin/python
```

### Issue: CSV encoding errors

**Solution:** Specify UTF-8 encoding in `csv_writer.py`:
```python
with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
```

---

## Future Enhancements (Not in This Plan)

These are out of scope for initial implementation:

1. **Auto-populate wire gauge** from component specifications
2. **Length calculation** from PCB coordinates
3. **Multi-file support** (process entire project)
4. **GUI interface** for non-CLI users
5. **KiCad plugin** for direct integration
6. **BOM comparison** tool for design revisions

---

## Glossary

**AWG**: American Wire Gauge - wire sizing standard
**BOM**: Bill of Materials
**EAWMS**: Experimental Aircraft Wire Marking Standard
**KiCad**: Open-source electronics design automation suite
**Net**: Electrical connection in a schematic
**Netlist**: File describing all connections in a schematic
**Node**: Connection point (component pin) in a net
**pyparsing**: Python library for parsing structured text
**TDD**: Test-Driven Development

---

## Success Criteria

You've successfully completed this implementation when:

- ✅ All tests pass (`pytest -v`)
- ✅ CLI processes simple netlist and produces valid CSV
- ✅ Wire labels follow EAWMS format (SYSTEM-CIRCUIT-SEGMENT)
- ✅ Integration test passes with realistic fixture
- ✅ README documents usage clearly
- ✅ Commits are frequent and descriptive
- ✅ No code duplication
- ✅ YAGNI: No unused features or over-engineering

---

## Questions?

If you get stuck:

1. Re-read the relevant section of this plan
2. Check `docs/kinparse_data_structure.md` for data format
3. Run exploration scripts to inspect data
4. Read test failures carefully - they tell you what's wrong
5. Ask for help (mention which task and step you're on)

---

**Good luck! Take it one task at a time, write tests first, commit frequently, and you'll build this tool successfully.**
