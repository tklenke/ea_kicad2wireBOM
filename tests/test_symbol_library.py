# ABOUTME: Tests for symbol library parsing and pin definition extraction
# ABOUTME: Tests parsing KiCad symbol definitions from schematic files

from kicad2wireBOM.symbol_library import PinDefinition, SymbolLibrary, parse_symbol_library


def test_parse_pin_definition_basic():
    """Parse a simple pin definition from S-expression"""
    # Pin from S700-1-1 switch symbol: pin 2 at (-6.35, 0)
    pin_sexp = [
        'pin', 'passive', 'line',
        ['at', -6.35, 0, 0],
        ['length', 2.54],
        ['name', 'IN', ['effects', ['font', ['size', 1.27, 1.27]]]],
        ['number', '2', ['effects', ['font', ['size', 1.27, 1.27]]]]
    ]

    pin = PinDefinition.from_sexp(pin_sexp)

    assert pin.number == '2'
    assert pin.position == (-6.35, 0)
    assert pin.angle == 0
    assert pin.length == 2.54
    assert pin.name == 'IN'


def test_parse_pin_definition_with_angle():
    """Parse pin definition with non-zero angle"""
    # Pin from S700-1-1: pin 1 at (6.35, 2.54, 180)
    pin_sexp = [
        'pin', 'passive', 'line',
        ['at', 6.35, 2.54, 180],
        ['length', 2.54],
        ['name', 'ON', ['effects', ['font', ['size', 1.27, 1.27]]]],
        ['number', '1', ['effects', ['font', ['size', 1.27, 1.27]]]]
    ]

    pin = PinDefinition.from_sexp(pin_sexp)

    assert pin.number == '1'
    assert pin.position == (6.35, 2.54)
    assert pin.angle == 180
    assert pin.name == 'ON'


def test_parse_symbol_library_extracts_pins():
    """Parse symbol library section and extract pin definitions"""
    # Load test_03A_fixture which has S700-1-1 symbol with 3 pins
    with open('tests/fixtures/test_03A_fixture.kicad_sch', 'r') as f:
        content = f.read()

    lib = parse_symbol_library(content)

    # Should have the S700-1-1 symbol
    assert 'AeroElectricConnectionSymbols:S700-1-1' in lib.symbols

    # Should have 3 pins
    pins = lib.get_pins('AeroElectricConnectionSymbols:S700-1-1')
    assert len(pins) == 3

    # Check pin numbers
    pin_numbers = {p.number for p in pins}
    assert pin_numbers == {'1', '2', '3'}


def test_symbol_library_get_pins():
    """SymbolLibrary can retrieve pins by lib_id"""
    lib = SymbolLibrary()

    # Add test pins
    lib.symbols['Test:Component'] = [
        PinDefinition(number='1', position=(0, 0), angle=0, length=2.54, name='A'),
        PinDefinition(number='2', position=(5, 0), angle=180, length=2.54, name='B'),
    ]

    pins = lib.get_pins('Test:Component')

    assert len(pins) == 2
    assert pins[0].number == '1'
    assert pins[1].number == '2'


def test_symbol_library_missing_symbol():
    """get_pins returns empty list for unknown symbol"""
    lib = SymbolLibrary()

    pins = lib.get_pins('Unknown:Component')

    assert pins == []
