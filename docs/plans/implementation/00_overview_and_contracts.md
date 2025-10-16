# Implementation Overview and Interface Contracts

## Purpose

This document defines the interfaces and contracts between implementation modules, allowing multiple programmers to work independently without integration conflicts.

## Work Package Organization

The implementation is divided into 10 independent work packages:

1. **Reference Data** (`01_reference_data.md`) - Foundation data tables
2. **Component Model** (`02_component_model.md`) - Component representation
3. **Parser** (`03_parser.md`) - Netlist parsing
4. **Circuit Analysis** (`04_circuit_analysis.md`) - Net topology and signal flow
5. **Wire Calculator** (`05_wire_calculator.md`) - Length and gauge calculations
6. **Wire BOM Model** (`06_wire_bom_model.md`) - BOM data structures
7. **Validator** (`07_validator.md`) - Validation logic
8. **CSV Output** (`08_output_csv.md`) - CSV generation
9. **Markdown Output** (`09_output_markdown.md`) - Markdown generation
10. **CLI and Integration** (`10_cli_and_integration.md`) - Orchestration

## Dependency Graph

```
reference_data (no dependencies)
    ↓
component_model (depends on: reference_data)
    ↓
parser (depends on: component_model)
    ↓
circuit_analysis (depends on: component_model)
    ↓
wire_calculator (depends on: reference_data, component_model)
wire_bom_model (depends on: component_model)
validator (depends on: component_model, reference_data)
    ↓
output_csv (depends on: wire_bom_model)
output_markdown (depends on: wire_bom_model)
    ↓
cli (depends on: all modules)
```

## Interface Contracts

### Module 1: reference_data.py

**Exports:**
```python
# Constants
STANDARD_AWG_SIZES: list[int]
DEFAULT_CONFIG: dict

# Data tables
WIRE_RESISTANCE: dict[int, float]  # {awg_size: ohms_per_foot}
WIRE_AMPACITY: dict[int, float]    # {awg_size: max_amps}
SYSTEM_COLOR_MAP: dict[str, str]   # {system_code: color_name}

# Functions
def load_custom_resistance_table(config_dict: dict) -> dict[int, float]
def load_custom_ampacity_table(config_dict: dict) -> dict[int, float]
def load_custom_color_map(config_dict: dict) -> dict[str, str]
```

**No dependencies.**

---

### Module 2: component.py

**Exports:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Component:
    """Component with aircraft coordinates and electrical properties"""
    ref: str                          # Reference designator (e.g., "J1")
    fs: float                         # Fuselage Station (inches)
    wl: float                         # Waterline (inches)
    bl: float                         # Buttline (inches)
    load: Optional[float] = None      # Current drawn (amps)
    rating: Optional[float] = None    # Current capacity (amps)
    wire_type: Optional[str] = None
    wire_color: Optional[str] = None
    wire_gauge: Optional[str] = None
    connector_type: Optional[str] = None

    @property
    def coordinates(self) -> tuple[float, float, float]:
        """Return (fs, wl, bl) tuple"""
        return (self.fs, self.wl, self.bl)

    @property
    def is_source(self) -> bool:
        """True if component is a power source"""
        pass

    @property
    def is_load(self) -> bool:
        """True if component consumes power"""
        pass

    @property
    def is_passthrough(self) -> bool:
        """True if component passes power through"""
        pass

def identify_component_type(ref: str) -> str:
    """
    Determine component role from reference designator.

    Returns: "source", "load", or "passthrough"
    """
    pass

def validate_component(component: Component, permissive: bool) -> list[str]:
    """
    Validate component has required fields.

    Returns: List of validation error/warning messages
    """
    pass
```

**Dependencies:** None

---

### Module 3: parser.py

**Exports:**
```python
from pathlib import Path
from component import Component

def parse_netlist_file(file_path: Path) -> object:
    """
    Parse KiCad netlist using kinparse.

    Returns: kinparse ParseResults object
    Raises: FileNotFoundError if file doesn't exist
    """
    pass

def extract_components(parsed_netlist: object) -> list[Component]:
    """
    Extract components from parsed netlist.

    Returns: List of Component objects
    """
    pass

def extract_nets(parsed_netlist: object) -> list[dict]:
    """
    Extract nets from parsed netlist.

    Returns: List of dicts with structure:
        {
            'name': str,              # Net name (e.g., "Net-L105")
            'code': str,              # Net code from netlist
            'nodes': [                # Connection points
                {'ref': str, 'pin': str},
                ...
            ],
            'circuit_id': Optional[str],    # From Circuit_ID field
            'system_code': Optional[str]    # From System_Code field
        }
    """
    pass
```

**Dependencies:** component.py

---

### Module 4: circuit.py

**Exports:**
```python
from component import Component
from typing import Optional

class Circuit:
    """Represents a circuit with its nodes and topology"""

    def __init__(self, net_dict: dict, components: list[Component]):
        self.net_name: str = net_dict['name']
        self.system_code: Optional[str] = None
        self.circuit_id: Optional[str] = None
        self.nodes: list[tuple[Component, str]] = []  # (component, pin) tuples
        self.topology: str = "simple"  # "simple", "star", "daisy"
        self.signal_flow: list[tuple[Component, str]] = []  # Ordered nodes
        self.segments: list[dict] = []  # Wire segment definitions

def build_circuits(nets: list[dict], components: list[Component]) -> list[Circuit]:
    """
    Convert net dicts into Circuit objects.

    Links nodes to Component objects and parses system/circuit codes.
    """
    pass

def detect_multi_node_topology(circuit: Circuit) -> str:
    """
    Analyze circuit with 3+ nodes to determine topology.

    Returns: "star" or "daisy"
    """
    pass

def determine_signal_flow(circuit: Circuit) -> list[tuple[Component, str]]:
    """
    Order nodes from source to load.

    Returns: Ordered list of (component, pin) tuples
    """
    pass

def create_wire_segments(circuit: Circuit) -> list[dict]:
    """
    Create wire segment definitions from circuit.

    Returns: List of dicts:
        {
            'from_comp': Component,
            'from_pin': str,
            'to_comp': Component,
            'to_pin': str,
            'segment_letter': str  # A, B, C, ...
        }
    """
    pass
```

**Dependencies:** component.py

---

### Module 5: wire_calculator.py

**Exports:**
```python
from component import Component

def calculate_length(component1: Component, component2: Component, slack: float) -> float:
    """
    Calculate Manhattan distance between components plus slack.

    Returns: Length in inches
    """
    pass

def calculate_voltage_drop(current: float, awg_size: int, length: float) -> float:
    """
    Calculate voltage drop for given wire parameters.

    Returns: Voltage drop in volts
    """
    pass

def determine_min_gauge(
    current: float,
    length: float,
    system_voltage: float,
    slack: float
) -> tuple[int, float, float]:
    """
    Determine minimum wire gauge meeting voltage drop and ampacity constraints.

    Returns: (awg_size, voltage_drop_volts, voltage_drop_percent)
    """
    pass

def assign_wire_color(system_code: str, color_override: Optional[str] = None) -> str:
    """
    Assign wire color based on system code.

    Returns: Color name string
    """
    pass

def generate_wire_label(
    net_name: str,
    circuit_id: Optional[str],
    system_code: Optional[str],
    segment_letter: str
) -> str:
    """
    Generate EAWMS-format wire label.

    Format: SYSTEM-CIRCUIT-SEGMENT
    Returns: Wire label string (e.g., "L-105-A")
    Raises: ValueError if unable to parse net_name
    """
    pass

def round_to_standard_awg(calculated_gauge: float) -> int:
    """
    Round calculated gauge up to next standard AWG size.

    Returns: Standard AWG size
    """
    pass
```

**Dependencies:** reference_data.py, component.py

---

### Module 6: wire_bom.py

**Exports:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class WireConnection:
    """Single wire connection in BOM"""
    # Core fields
    wire_label: str
    from_ref: str              # "J1-1"
    to_ref: str                # "SW1-2"
    wire_gauge: str            # "20 AWG"
    wire_color: str
    length: float              # inches
    wire_type: str             # "M22759/16"

    # Engineering fields
    calculated_min_gauge: Optional[str] = None
    voltage_drop_volts: Optional[float] = None
    voltage_drop_percent: Optional[float] = None
    current: Optional[float] = None
    from_coords: Optional[tuple[float, float, float]] = None
    to_coords: Optional[tuple[float, float, float]] = None
    calculated_length: Optional[float] = None

    # Validation
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class WireBOM:
    """Container for wire BOM"""

    def __init__(self):
        self.wires: list[WireConnection] = []
        self.config: dict = {}
        self.components: list[Component] = []

    def add_wire(self, wire: WireConnection) -> None:
        """Add wire to BOM"""
        pass

    def sort_by_system_code(self) -> None:
        """Sort wires by system, circuit, segment"""
        pass

    def get_wire_summary(self) -> dict[tuple[str, str], float]:
        """
        Get purchasing summary.

        Returns: {(gauge, color): total_length}
        """
        pass

    def get_validation_summary(self) -> list[str]:
        """Return all warnings/errors collected"""
        pass
```

**Dependencies:** component.py

---

### Module 7: validator.py

**Exports:**
```python
from dataclasses import dataclass
from component import Component
from circuit import Circuit
from wire_bom import WireConnection, WireBOM

@dataclass
class ValidationResult:
    """Single validation issue"""
    component_ref: str
    net_name: Optional[str]
    severity: str  # "error" or "warning"
    message: str
    suggestion: Optional[str] = None

def validate_required_fields(
    components: list[Component],
    permissive_mode: bool
) -> list[ValidationResult]:
    """Validate components have required fields"""
    pass

def validate_wire_gauge(
    wire: WireConnection,
    calculated_min_gauge: int
) -> Optional[ValidationResult]:
    """Validate specified gauge meets minimum"""
    pass

def validate_rating_vs_load(
    circuit_path: list[tuple[Component, str]]
) -> list[ValidationResult]:
    """Validate ratings not exceeded by loads"""
    pass

def validate_gauge_progression(
    circuit_path: list[tuple[Component, str]],
    wire_segments: list[dict]
) -> list[ValidationResult]:
    """Validate gauge doesn't decrease along path"""
    pass

def collect_all_warnings(
    bom: WireBOM,
    circuits: list[Circuit],
    components: list[Component],
    permissive: bool
) -> list[ValidationResult]:
    """Run all validation checks and collect results"""
    pass
```

**Dependencies:** component.py, circuit.py, wire_bom.py, reference_data.py

---

### Module 8: output_csv.py

**Exports:**
```python
from pathlib import Path
from wire_bom import WireBOM

def write_builder_csv(bom: WireBOM, output_path: Path) -> None:
    """Write builder-mode CSV (essential columns only)"""
    pass

def write_engineering_csv(bom: WireBOM, output_path: Path) -> None:
    """Write engineering-mode CSV (all columns including calculations)"""
    pass
```

**Dependencies:** wire_bom.py

---

### Module 9: output_markdown.py

**Exports:**
```python
from pathlib import Path
from wire_bom import WireBOM
from component import Component

def write_builder_markdown(bom: WireBOM, output_path: Path) -> None:
    """Write builder-mode markdown report"""
    pass

def write_engineering_markdown(
    bom: WireBOM,
    output_path: Path,
    components: list[Component],
    config: dict
) -> None:
    """Write engineering-mode markdown report with detailed analysis"""
    pass

# Helper functions
def format_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate markdown table string"""
    pass

def format_component_table(components: list[Component]) -> str:
    """Format component list as markdown table"""
    pass

def format_wire_summary(summary_dict: dict[tuple[str, str], float]) -> str:
    """Format purchasing summary as markdown table"""
    pass

def format_validation_warnings(warnings: list[str]) -> str:
    """Group and format warnings"""
    pass
```

**Dependencies:** wire_bom.py, component.py

---

### Module 10: __main__.py and schematic_help.py

**__main__.py Exports:**
```python
def main() -> int:
    """CLI entry point. Returns exit code (0=success, 1=error)"""
    pass

def generate_output_filename(input_path: Path, format: str, output_dir: Path) -> Path:
    """Generate filename with REVnnn suffix"""
    pass

def load_config(config_path: Optional[Path]) -> dict:
    """Load and merge configuration from file"""
    pass
```

**schematic_help.py Exports:**
```python
def print_schematic_requirements(config: dict) -> None:
    """Print formatted requirements documentation to stdout"""
    pass
```

**Dependencies:** All other modules

---

## Data Flow

The typical processing flow:

1. **Parse** netlist → `Component` list + net dicts
2. **Build circuits** from nets + components → `Circuit` list
3. **Calculate** wire specs for each circuit segment → wire parameters
4. **Create** `WireConnection` objects → `WireBOM`
5. **Validate** BOM → warnings attached to wires
6. **Output** BOM → CSV or Markdown

## Test Data Requirements

Each work package needs test fixtures. Create in `tests/fixtures/`:

- `simple_two_component.net` - Minimal valid netlist (J1 → SW1)
- `multi_net.net` - Multiple nets between components
- `multi_node.net` - Net with 3+ components
- `missing_fields.net` - Components with missing data
- `realistic_ea_system.net` - Complete aircraft electrical system

## Integration Strategy

Work packages can be implemented in parallel following the dependency graph. Integration points:

1. **Phase 1** (parallel): reference_data, component_model
2. **Phase 2** (parallel): parser, circuit_analysis, wire_calculator, wire_bom_model
3. **Phase 3** (parallel): validator, output_csv, output_markdown
4. **Phase 4** (serial): cli integration

## Testing Approach

Each module must include:

- Unit tests for all exported functions/classes
- Test fixtures in `tests/fixtures/`
- Test file: `tests/test_<module_name>.py`
- Follow TDD: RED → GREEN → REFACTOR → COMMIT

## Code Style

All modules must follow CLAUDE.md requirements:

- Two-line `ABOUTME:` comment at top of each file
- Type hints on all function signatures
- Docstrings for public functions
- No temporal/implementation names in code
- TDD with frequent commits

## Questions?

If interface contracts are unclear, ask in the project discussion before implementing.
