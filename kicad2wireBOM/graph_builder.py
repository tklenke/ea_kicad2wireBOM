# ABOUTME: Graph builder for schematic connectivity
# ABOUTME: Builds complete connectivity graph from parsed schematic with pins, junctions, wires

from typing import Any
from kicad2wireBOM.connectivity_graph import ConnectivityGraph
from kicad2wireBOM.parser import (
    extract_wires,
    extract_junctions,
    extract_symbols,
    parse_wire_element,
    parse_junction_element
)
from kicad2wireBOM.symbol_library import parse_symbol_library
from kicad2wireBOM.pin_calculator import calculate_pin_position
import sexpdata


def build_connectivity_graph(schematic_sexp: Any) -> ConnectivityGraph:
    """
    Build complete connectivity graph from parsed schematic.

    Process:
    1. Parse symbol libraries and cache pin definitions
    2. Extract and parse all component symbols
    3. Calculate all component pin positions
    4. Add all junctions to graph
    5. Add all component pins to graph
    6. Add all wires to graph (connects to existing nodes)

    Args:
        schematic_sexp: Parsed schematic S-expression

    Returns:
        ConnectivityGraph with all nodes and connections
    """
    graph = ConnectivityGraph()

    # Step 1: Parse symbol library
    # Convert sexp back to string for symbol library parser
    schematic_str = _sexp_to_string(schematic_sexp)
    symbol_lib = parse_symbol_library(schematic_str)

    # Step 2 & 3: Extract symbols and calculate pin positions
    symbol_sexps = extract_symbols(schematic_sexp)

    for symbol_sexp in symbol_sexps:
        # Extract symbol placement info
        lib_id = None
        position = None
        rotation = 0

        for item in symbol_sexp:
            if isinstance(item, list) and len(item) > 0:
                key = item[0]
                if isinstance(key, sexpdata.Symbol):
                    key = key.value()

                if key == 'lib_id':
                    lib_id = item[1]
                    if hasattr(lib_id, 'strip'):
                        lib_id = lib_id.strip('"')
                elif key == 'at':
                    # (at x y rotation)
                    position = (item[1], item[2])
                    if len(item) > 3:
                        rotation = item[3]

        # Get reference designator from properties
        ref = None
        for item in symbol_sexp:
            if isinstance(item, list) and len(item) > 2:
                first = item[0]
                if isinstance(first, sexpdata.Symbol) and first.value() == 'property':
                    prop_name = str(item[1]).strip('"')
                    if prop_name == 'Reference':
                        ref = str(item[2]).strip('"')
                        break

        if not lib_id or not position or not ref:
            continue

        # Get pin definitions for this symbol
        pins = symbol_lib.get_pins(lib_id)

        # Calculate and add each pin to graph
        for pin_def in pins:
            # Create simple object with x, y for pin calculator
            class ComponentPosition:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            comp_pos = ComponentPosition(position[0], position[1])
            pin_position = calculate_pin_position(pin_def, comp_pos, rotation=rotation)

            pin_key = f"{ref}-{pin_def.number}"
            graph.add_component_pin(pin_key, ref, pin_def.number, pin_position)

    # Step 4: Add all junctions
    junction_sexps = extract_junctions(schematic_sexp)
    for junction_sexp in junction_sexps:
        junction = parse_junction_element(junction_sexp)
        graph.add_junction(junction.uuid, junction.position)

    # Step 5: Add all wires
    wire_sexps = extract_wires(schematic_sexp)
    for wire_sexp in wire_sexps:
        wire = parse_wire_element(wire_sexp)
        graph.add_wire(wire)

    return graph


def _sexp_to_string(sexp: Any) -> str:
    """
    Convert S-expression back to string format.

    This is needed because parse_symbol_library expects a string.
    """
    # Use sexpdata to dump back to string
    return sexpdata.dumps(sexp)
