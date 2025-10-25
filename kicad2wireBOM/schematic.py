# ABOUTME: Data models for schematic elements
# ABOUTME: Defines WireSegment, Label, Component, and hierarchical schematic classes

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WireSegment:
    """
    Represents a single wire segment in the schematic.

    Wire segments are the physical wires drawn in the schematic,
    each with distinct start and end points. These are preserved
    at wire-level granularity (not collapsed into nets).
    """
    uuid: str
    start_point: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    end_point: tuple[float, float]    # (x, y) in mm
    circuit_id: Optional[str] = None  # Parsed from label (e.g., "P1A") - first/primary circuit ID
    circuit_ids: list[str] = field(default_factory=list)  # All circuit IDs from pipe notation (e.g., ["L3B", "L10A"])
    system_code: Optional[str] = None # Extracted from circuit_id (e.g., "P")
    circuit_num: Optional[str] = None # Extracted from circuit_id (e.g., "1")
    segment_letter: Optional[str] = None  # Extracted from circuit_id (e.g., "A")
    labels: list[str] = field(default_factory=list)  # All labels associated with this wire
    notes: list[str] = field(default_factory=list)  # Non-circuit labels (e.g., "24AWG", "SHIELDED")
    start_connection: Optional[str] = None  # Connection at start (e.g., "SW1-1", "JUNCTION-abc")
    end_connection: Optional[str] = None    # Connection at end (e.g., "SW2-2", "UNKNOWN")


@dataclass
class Junction:
    """
    Represents a junction in the schematic.

    Junctions are explicit connection points where multiple wires meet.
    Only wires meeting at a junction are electrically connected.
    """
    uuid: str
    position: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    diameter: float = 0.0
    color: tuple[int, int, int, int] = (0, 0, 0, 0)  # RGBA


@dataclass
class Label:
    """
    Represents a label in the schematic.

    Labels are text annotations placed near wires to indicate
    circuit identifiers (e.g., "P1A", "G1A").
    """
    text: str
    position: tuple[float, float]  # (x, y) in mm (schematic coordinates)
    uuid: str
    rotation: float = 0.0  # Rotation in degrees


@dataclass
class SheetPin:
    """
    Represents a pin on a sheet symbol (parent side).

    Sheet pins are connection points on hierarchical sheet boundaries
    that connect to hierarchical labels on child sheets.
    """
    name: str
    direction: str  # "input", "output", "bidirectional"
    position: tuple[float, float]  # (x, y) in parent coordinate system


@dataclass
class SheetElement:
    """
    Represents a hierarchical sheet symbol in the schematic.

    Sheet symbols define sub-sheet boundaries and connection points
    between parent and child sheets.
    """
    uuid: str
    sheetname: str
    sheetfile: str
    pins: list[SheetPin] = field(default_factory=list)


@dataclass
class HierarchicalLabel:
    """
    Represents a hierarchical label on a child sheet.

    Hierarchical labels are connection points on sub-sheets that
    connect to sheet pins on the parent sheet.
    """
    name: str
    position: tuple[float, float]  # (x, y) in child coordinate system
    shape: str  # "input", "output", "bidirectional"


@dataclass
class Sheet:
    """
    Represents a single schematic sheet (root or sub-sheet).

    Contains all schematic elements for one sheet including wires,
    components, junctions, labels, sheet symbols, and hierarchical labels.
    """
    uuid: str
    name: str
    file_path: str
    wire_segments: list[WireSegment] = field(default_factory=list)
    junctions: list[Junction] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    components: list = field(default_factory=list)  # Will be Component objects
    sheet_elements: list[SheetElement] = field(default_factory=list)
    hierarchical_labels: list[HierarchicalLabel] = field(default_factory=list)


@dataclass
class SheetConnection:
    """
    Maps electrical connection between parent sheet pin and child hierarchical label.

    Explicitly defines how sheets connect through hierarchical boundaries.
    """
    parent_sheet_uuid: str
    child_sheet_uuid: str
    pin_name: str
    parent_pin_position: tuple[float, float]
    parent_wire_net: Optional[str]
    child_label_position: tuple[float, float]
    child_wire_net: Optional[str]


@dataclass
class PowerSymbol:
    """
    Represents a power symbol instance (e.g., GND, +12V).

    Power symbols create global nets that span all sheets.
    """
    reference: str  # "#PWR01", "#PWR02", etc.
    sheet_uuid: str
    position: tuple[float, float]
    loc_load: Optional[str]  # Ground point location if specified


@dataclass
class GlobalNet:
    """
    Represents a global power net spanning all sheets.

    All power symbols with the same net_name are electrically connected
    regardless of sheet hierarchy.
    """
    net_name: str  # "GND", "+12V", etc.
    power_symbols: list[PowerSymbol] = field(default_factory=list)


@dataclass
class HierarchicalSchematic:
    """
    Root container for multi-sheet hierarchical schematic.

    Contains root sheet, all sub-sheets, cross-sheet connections,
    and global power nets.
    """
    root_sheet: Sheet
    sub_sheets: dict[str, Sheet] = field(default_factory=dict)  # sheet_uuid → Sheet
    sheet_connections: list[SheetConnection] = field(default_factory=list)
    global_nets: dict[str, GlobalNet] = field(default_factory=dict)  # net_name → GlobalNet
