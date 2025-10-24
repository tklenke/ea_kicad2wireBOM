# ABOUTME: Schematic parser module for KiCad schematic files
# ABOUTME: Parses .kicad_sch files using sexpdata and extracts wires, labels, and components

from pathlib import Path
from typing import Union, List, Any, Optional
import sexpdata
from sexpdata import Symbol

from kicad2wireBOM.schematic import WireSegment, Label, Junction, SheetElement, SheetPin
from kicad2wireBOM.component import Component


def parse_schematic_file(file_path: Union[str, Path]) -> Any:
    """
    Parse a KiCad schematic file into s-expression data structure.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        Parsed s-expression as nested Python lists
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding='utf-8')
    sexp = sexpdata.loads(content)
    return sexp


def extract_wires(sexp: Any) -> List[Any]:
    """
    Extract all (wire ...) elements from schematic s-expression.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of wire elements (each is an s-expression)
    """
    wires = []

    def walk(node):
        """Recursively walk s-expression tree"""
        if isinstance(node, list):
            # Check if this is a wire element
            if len(node) > 0:
                first = node[0]
                # Handle both Symbol and string types
                if isinstance(first, Symbol):
                    if first.value() == 'wire':
                        wires.append(node)
                elif str(first) == 'wire':
                    wires.append(node)

            # Recurse into children
            for child in node:
                walk(child)

    walk(sexp)
    return wires


def extract_labels(sexp: Any) -> List[Any]:
    """
    Extract all (label ...) elements from schematic s-expression.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of label elements (each is an s-expression)
    """
    labels = []

    def walk(node):
        """Recursively walk s-expression tree"""
        if isinstance(node, list):
            # Check if this is a label element
            if len(node) > 0:
                first = node[0]
                # Handle both Symbol and string types
                if isinstance(first, Symbol):
                    if first.value() == 'label':
                        labels.append(node)
                elif str(first) == 'label':
                    labels.append(node)

            # Recurse into children
            for child in node:
                walk(child)

    walk(sexp)
    return labels


def extract_symbols(sexp: Any) -> List[Any]:
    """
    Extract all symbol (component instance) elements from schematic.

    Note: We're looking for symbol instances (components placed in schematic),
    not symbol definitions in lib_symbols section.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of symbol instance elements
    """
    symbols = []

    def walk(node, depth=0):
        """Recursively walk s-expression tree"""
        if isinstance(node, list) and len(node) > 0:
            first = node[0]

            # Check if this is a symbol instance
            # Symbol instances have properties like Reference and Footprint
            if isinstance(first, Symbol) and first.value() == 'symbol':
                # Check if it has lib_id (indicates it's an instance, not definition)
                has_lib_id = any(
                    isinstance(child, list) and len(child) > 0 and
                    isinstance(child[0], Symbol) and child[0].value() == 'lib_id'
                    for child in node
                )
                if has_lib_id:
                    symbols.append(node)
                    return  # Don't recurse into symbol instances

            # Recurse into children
            for child in node:
                walk(child, depth + 1)

    walk(sexp)
    return symbols


def find_element(sexp: List, name: str) -> Optional[Any]:
    """
    Helper: Find first element in sexp list with given name.

    Args:
        sexp: S-expression list
        name: Element name to find

    Returns:
        Element if found, None otherwise
    """
    for elem in sexp:
        if isinstance(elem, list) and len(elem) > 0:
            first = elem[0]
            if isinstance(first, Symbol):
                if first.value() == name:
                    return elem
            elif str(first) == name:
                return elem
    return None


def parse_wire_element(wire_sexp: Any) -> WireSegment:
    """
    Parse wire s-expression into WireSegment object.

    Wire format:
    (wire
      (pts (xy x1 y1) (xy x2 y2))
      (stroke ...)
      (uuid "...")
    )

    Args:
        wire_sexp: S-expression for wire element

    Returns:
        WireSegment object
    """
    # Extract pts element
    pts = find_element(wire_sexp, 'pts')
    if not pts:
        raise ValueError("Wire element missing 'pts'")

    # Extract xy points
    xy_points = [e for e in pts if isinstance(e, list) and len(e) > 0 and
                 ((isinstance(e[0], Symbol) and e[0].value() == 'xy') or str(e[0]) == 'xy')]

    if len(xy_points) < 2:
        raise ValueError("Wire 'pts' must contain at least 2 xy points")

    start_point = (float(xy_points[0][1]), float(xy_points[0][2]))
    end_point = (float(xy_points[1][1]), float(xy_points[1][2]))

    # Extract uuid
    uuid_elem = find_element(wire_sexp, 'uuid')
    uuid = None
    if uuid_elem and len(uuid_elem) > 1:
        uuid = str(uuid_elem[1]).strip('"')

    return WireSegment(
        uuid=uuid,
        start_point=start_point,
        end_point=end_point
    )


def parse_label_element(label_sexp: Any) -> Label:
    """
    Parse label s-expression into Label object.

    Label format:
    (label "P1A"
      (at x y rotation)
      (effects ...)
      (uuid "...")
    )

    Args:
        label_sexp: S-expression for label element

    Returns:
        Label object
    """
    # Label text is second element
    if len(label_sexp) < 2:
        raise ValueError("Label element missing text")

    text = str(label_sexp[1]).strip('"')

    # Extract 'at' element for position
    at_elem = find_element(label_sexp, 'at')
    if not at_elem or len(at_elem) < 3:
        raise ValueError("Label missing 'at' position")

    position = (float(at_elem[1]), float(at_elem[2]))

    # Rotation is optional (3rd element in 'at')
    rotation = 0.0
    if len(at_elem) > 3:
        rotation = float(at_elem[3])

    # Extract uuid
    uuid_elem = find_element(label_sexp, 'uuid')
    uuid = None
    if uuid_elem and len(uuid_elem) > 1:
        uuid = str(uuid_elem[1]).strip('"')

    return Label(
        text=text,
        position=position,
        uuid=uuid,
        rotation=rotation
    )


def parse_locload_encoding(locload_str: str) -> Optional[dict]:
    """
    Parse LocLoad encoding from LocLoad field string.

    Format: (fs,wl,bl)<L|R|S|G><amps>
    Example: "(100.0,25.0,0.0)R15" or "(10,0,0)S40" or "(0,0,10)G"

    Args:
        locload_str: LocLoad field string

    Returns:
        Dict with parsed values if encoding found, None otherwise:
            - fs: Fuselage Station (float)
            - wl: Water Line (float)
            - bl: Butt Line (float)
            - type: 'L' for Load, 'R' for Rating, 'S' for Source, 'G' for Ground
            - amperage: Amperage value (float), or None for Ground type
    """
    import re

    # Pattern: (fs,wl,bl)<L|R|S|G><amps>
    # Coordinates can be negative, amperage can be decimal
    # Amperage is optional for G type (ground)
    pattern = r'\(([-\d.]+),([-\d.]+),([-\d.]+)\)([LRSG])([-\d.]*)'

    match = re.search(pattern, locload_str)
    if not match:
        return None

    try:
        type_char = match.group(4)
        amperage_str = match.group(5)

        # For Ground type, amperage is optional
        if type_char == 'G':
            amperage = None if amperage_str == '' else float(amperage_str)
        else:
            # For S, L, R types, amperage is required
            if amperage_str == '':
                return None
            amperage = float(amperage_str)

        return {
            'fs': float(match.group(1)),
            'wl': float(match.group(2)),
            'bl': float(match.group(3)),
            'type': type_char,
            'amperage': amperage
        }
    except ValueError:
        # If conversion to float fails, return None
        return None


def parse_symbol_element(symbol_sexp: Any) -> Component:
    """
    Parse symbol s-expression into Component object.

    Symbol format:
    (symbol (lib_id "...")
      (at x y rotation)
      (property "Reference" "BT1" ...)
      (property "LocLoad" "(10,0,0)S40" ...)
      (property "Value" "Battery" ...)
      ...
    )

    Args:
        symbol_sexp: S-expression for symbol element

    Returns:
        Component object
    """
    # Extract property elements
    properties = {}
    for elem in symbol_sexp:
        if isinstance(elem, list) and len(elem) > 2:
            first = elem[0]
            if isinstance(first, Symbol) and first.value() == 'property':
                prop_name = str(elem[1]).strip('"')
                prop_value = str(elem[2]).strip('"')
                properties[prop_name] = prop_value

    # Get reference designator
    ref = properties.get('Reference', 'UNKNOWN')

    # Get LocLoad field and parse encoding
    locload = properties.get('LocLoad', '')
    encoding = parse_locload_encoding(locload)

    if encoding is None:
        raise ValueError(f"Component {ref} missing LocLoad encoding")

    # Determine load, rating, or source based on type
    load = encoding['amperage'] if encoding['type'] == 'L' else None
    rating = encoding['amperage'] if encoding['type'] == 'R' else None
    source = encoding['amperage'] if encoding['type'] == 'S' else None

    return Component(
        ref=ref,
        fs=encoding['fs'],
        wl=encoding['wl'],
        bl=encoding['bl'],
        load=load,
        rating=rating,
        source=source,
        value=properties.get('Value', ''),
        desc=properties.get('Description', '')
    )


def extract_junctions(sexp: Any) -> List[Any]:
    """
    Extract all (junction ...) elements from schematic s-expression.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of junction elements (each is an s-expression)
    """
    junctions = []

    def walk(node):
        """Recursively walk s-expression tree"""
        if isinstance(node, list):
            # Check if this is a junction element
            if len(node) > 0:
                first = node[0]
                if isinstance(first, Symbol):
                    if first.value() == 'junction':
                        junctions.append(node)
                elif first == 'junction':
                    junctions.append(node)

            # Recursively process child nodes
            for item in node:
                walk(item)

    walk(sexp)
    return junctions


def parse_junction_element(junction_sexp: Any) -> Junction:
    """
    Parse a (junction ...) s-expression into Junction object.

    Args:
        junction_sexp: Junction s-expression element

    Returns:
        Junction object with position, uuid, diameter, color
    """
    position = None
    uuid = None
    diameter = 0.0
    color = (0, 0, 0, 0)

    for item in junction_sexp[1:]:
        if isinstance(item, list) and len(item) > 0:
            key = item[0]
            if isinstance(key, Symbol):
                key = key.value()

            if key == 'at':
                # (at x y)
                position = (item[1], item[2])
            elif key == 'uuid':
                # (uuid "string")
                uuid = item[1]
            elif key == 'diameter':
                # (diameter value)
                diameter = item[1]
            elif key == 'color':
                # (color r g b a)
                color = tuple(item[1:5])

    return Junction(
        uuid=uuid,
        position=position,
        diameter=diameter,
        color=color
    )


def extract_sheets(sexp: Any) -> List[SheetElement]:
    """
    Extract all (sheet ...) elements from schematic s-expression.

    Args:
        sexp: Parsed s-expression (nested lists)

    Returns:
        List of SheetElement objects
    """
    sheets_raw = []

    def walk(node):
        """Recursively walk s-expression tree"""
        if isinstance(node, list):
            if len(node) > 0:
                first = node[0]
                if isinstance(first, Symbol):
                    if first.value() == 'sheet':
                        sheets_raw.append(node)
                elif str(first) == 'sheet':
                    sheets_raw.append(node)

            for child in node:
                walk(child)

    walk(sexp)

    # Parse each raw sheet element into SheetElement object
    sheets = [parse_sheet_element(sheet_sexp) for sheet_sexp in sheets_raw]
    return sheets


def parse_sheet_element(sheet_sexp: Any) -> SheetElement:
    """
    Parse a (sheet ...) s-expression into SheetElement object.

    Args:
        sheet_sexp: Sheet s-expression element

    Returns:
        SheetElement object with uuid, sheetname, sheetfile, and pins
    """
    uuid = None
    sheetname = None
    sheetfile = None
    pins = []

    for item in sheet_sexp[1:]:
        if isinstance(item, list) and len(item) > 0:
            key = item[0]
            if isinstance(key, Symbol):
                key = key.value()

            if key == 'uuid':
                # (uuid "string")
                uuid = item[1]
            elif key == 'property':
                # (property "Name" "value" ...)
                if len(item) >= 3:
                    prop_name = item[1]
                    prop_value = item[2]
                    if prop_name == "Sheetname":
                        sheetname = prop_value
                    elif prop_name == "Sheetfile":
                        sheetfile = prop_value
            elif key == 'pin':
                # (pin "name" direction (at x y angle) ...)
                if len(item) >= 3:
                    pin_name = item[1]
                    pin_direction = item[2]
                    if isinstance(pin_direction, Symbol):
                        pin_direction = pin_direction.value()

                    # Find (at x y ...) element
                    pin_position = None
                    for pin_item in item[3:]:
                        if isinstance(pin_item, list) and len(pin_item) > 0:
                            pin_key = pin_item[0]
                            if isinstance(pin_key, Symbol):
                                pin_key = pin_key.value()
                            if pin_key == 'at':
                                # (at x y) or (at x y angle)
                                pin_position = (pin_item[1], pin_item[2])
                                break

                    if pin_position:
                        pin = SheetPin(
                            name=pin_name,
                            direction=pin_direction,
                            position=pin_position
                        )
                        pins.append(pin)

    return SheetElement(
        uuid=uuid,
        sheetname=sheetname,
        sheetfile=sheetfile,
        pins=pins
    )
