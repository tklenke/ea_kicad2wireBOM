# ABOUTME: Tests for schematic parser module
# ABOUTME: Validates parsing of .kicad_sch files using sexpdata

from pathlib import Path
from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    extract_symbols,
    parse_wire_element,
    parse_label_element,
    parse_symbol_element
)
from kicad2wireBOM.schematic import WireSegment, Label
from kicad2wireBOM.component import Component


def test_parse_schematic_file():
    """Parse .kicad_sch file into s-expression data structure"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    # Should be a list (s-expression is a list of elements)
    assert isinstance(sexp, list)
    # First element should be the symbol 'kicad_sch'
    first_elem = str(sexp[0])
    assert 'kicad_sch' in first_elem.lower()


def test_extract_wires():
    """Extract all (wire ...) elements from schematic"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    wires = extract_wires(sexp)

    # test_01 has 6 wire segments (verified by inspection)
    assert len(wires) == 6
    # Each wire should be a list starting with 'wire' symbol
    for wire in wires:
        assert isinstance(wire, list)
        wire_str = str(wire[0]).lower()
        assert 'wire' in wire_str


def test_extract_labels():
    """Extract all (label ...) elements from schematic"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    labels = extract_labels(sexp)

    # test_01 has 2 labels: "G1A" and "P1A"
    assert len(labels) == 2
    for label in labels:
        assert isinstance(label, list)
        label_str = str(label[0]).lower()
        assert 'label' in label_str


def test_parse_wire_element():
    """Parse wire s-expression into WireSegment object"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    wire_sexps = extract_wires(sexp)

    # Parse first wire
    wire = parse_wire_element(wire_sexps[0])

    assert isinstance(wire, WireSegment)
    assert wire.uuid is not None
    assert wire.start_point is not None
    assert wire.end_point is not None
    assert isinstance(wire.start_point, tuple)
    assert isinstance(wire.end_point, tuple)
    assert len(wire.start_point) == 2
    assert len(wire.end_point) == 2


def test_parse_wire_element_specific():
    """Parse wire with known coordinates"""
    # From test_01_fixture.kicad_sch line 446-456:
    # (wire
    #   (pts (xy 83.82 52.07) (xy 92.71 52.07))
    #   (uuid "0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd")
    # )
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    wire_sexps = extract_wires(sexp)

    # Find the specific wire by UUID
    target_uuid = "0ed4cddd-6a3a-4c19-b7d6-4bb20dd7ebbd"
    target_wire_sexp = None
    for wire_sexp in wire_sexps:
        # Convert to string to search for UUID
        if target_uuid in str(wire_sexp):
            target_wire_sexp = wire_sexp
            break

    assert target_wire_sexp is not None, "Could not find wire with target UUID"

    wire = parse_wire_element(target_wire_sexp)

    assert wire.start_point == (83.82, 52.07)
    assert wire.end_point == (92.71, 52.07)
    assert wire.uuid == target_uuid


def test_parse_label_element():
    """Parse label s-expression into Label object"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    label_sexps = extract_labels(sexp)

    # Parse first label
    label = parse_label_element(label_sexps[0])

    assert isinstance(label, Label)
    assert label.text in ["G1A", "P1A"]
    assert label.uuid is not None
    assert label.position is not None
    assert isinstance(label.position, tuple)
    assert len(label.position) == 2


def test_extract_symbols():
    """Extract all symbol (component) elements from schematic"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    symbols = extract_symbols(sexp)

    # test_01 has 2 components: BT1 (battery) and L1 (lamp)
    assert len(symbols) == 2


def test_parse_symbol_element():
    """Parse symbol s-expression into Component object"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    symbol_sexps = extract_symbols(sexp)

    # Parse first symbol
    component = parse_symbol_element(symbol_sexps[0])

    assert isinstance(component, Component)
    assert component.ref in ["BT1", "L1"]
    assert component.fs is not None
    assert component.wl is not None
    assert component.bl is not None
