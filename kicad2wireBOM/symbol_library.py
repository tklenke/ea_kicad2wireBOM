# ABOUTME: Symbol library parsing for KiCad schematic files
# ABOUTME: Extracts pin definitions from lib_symbols section

from dataclasses import dataclass
import sexpdata


def _to_str(obj):
    """Convert sexpdata Symbol to string, or return as-is"""
    if isinstance(obj, sexpdata.Symbol):
        return obj.value()
    return obj


@dataclass
class PinDefinition:
    """Pin definition from symbol library"""
    number: str                    # "1", "2", "3"
    position: tuple[float, float]  # (x, y) relative to symbol origin
    angle: float                   # Pin direction in degrees
    length: float                  # Pin length
    name: str                      # "IN", "ON", etc.

    @classmethod
    def from_sexp(cls, sexp: list):
        """Parse pin definition from S-expression"""
        # sexp format: ['pin', 'passive', 'line', ['at', x, y, angle], ...]
        number = None
        position = None
        angle = 0
        length = 0
        name = ""

        for item in sexp:
            if isinstance(item, list):
                key = _to_str(item[0])
                if key == 'at':
                    # ['at', x, y] or ['at', x, y, angle]
                    position = (item[1], item[2])
                    if len(item) > 3:
                        angle = item[3]
                elif key == 'length':
                    length = item[1]
                elif key == 'name':
                    name = _to_str(item[1])
                elif key == 'number':
                    number = _to_str(item[1])

        return cls(
            number=number,
            position=position,
            angle=angle,
            length=length,
            name=name
        )


class SymbolLibrary:
    """Cache of symbol pin definitions by lib_id"""

    def __init__(self):
        self.symbols: dict[str, list[PinDefinition]] = {}

    def get_pins(self, lib_id: str) -> list[PinDefinition]:
        """Get pin definitions for a symbol by lib_id"""
        return self.symbols.get(lib_id, [])


def parse_symbol_library(schematic_content: str) -> SymbolLibrary:
    """Parse lib_symbols section from schematic file"""
    # Parse the entire schematic
    parsed = sexpdata.loads(schematic_content)

    lib = SymbolLibrary()

    # Find the lib_symbols section
    lib_symbols = None
    for item in parsed:
        if isinstance(item, list) and _to_str(item[0]) == 'lib_symbols':
            lib_symbols = item
            break

    if not lib_symbols:
        return lib

    # Process each symbol definition
    for item in lib_symbols[1:]:  # Skip 'lib_symbols' keyword
        if isinstance(item, list) and _to_str(item[0]) == 'symbol':
            _parse_symbol_definition(item, lib)

    return lib


def _parse_symbol_definition(symbol_sexp: list, lib: SymbolLibrary, parent_lib_id: str = None):
    """Parse a single symbol definition and add to library"""
    # Symbol name is second element: ['symbol', 'Name:Part', ...]
    symbol_name = _to_str(symbol_sexp[1])

    # Determine lib_id for this symbol
    if ':' in symbol_name:
        # Top-level symbol with qualified name: "Library:PartName"
        current_lib_id = symbol_name
    elif parent_lib_id:
        # Nested symbol - use parent's lib_id
        current_lib_id = parent_lib_id
    else:
        # Nested symbol without parent (shouldn't happen)
        current_lib_id = None

    # Collect pins at this level
    pins = []
    for item in symbol_sexp[2:]:
        if isinstance(item, list):
            key = _to_str(item[0])
            if key == 'symbol':
                # Recursive symbol definition (unit level)
                _parse_symbol_definition(item, lib, current_lib_id)
            elif key == 'pin':
                # Pin definition at this level
                pin = PinDefinition.from_sexp(item)
                pins.append(pin)

    # Store pins if any found and we have a valid lib_id
    if pins and current_lib_id:
        if current_lib_id not in lib.symbols:
            lib.symbols[current_lib_id] = []
        lib.symbols[current_lib_id].extend(pins)
