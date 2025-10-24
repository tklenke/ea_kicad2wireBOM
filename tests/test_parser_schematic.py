# ABOUTME: Tests for schematic parser module
# ABOUTME: Validates parsing of .kicad_sch files using sexpdata

from pathlib import Path
from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    extract_symbols,
    extract_junctions,
    extract_sheets,
    parse_wire_element,
    parse_label_element,
    parse_symbol_element,
    parse_junction_element
)
from kicad2wireBOM.schematic import WireSegment, Label, Junction, SheetElement
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


def test_extract_junctions():
    """Extract junction elements from parsed schematic"""
    # Use test_03A_fixture which has junctions
    fixture_path = Path("tests/fixtures/test_03A_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    junctions = extract_junctions(sexp)

    # test_03A has 2 junctions
    assert len(junctions) == 2
    # Check first element is 'junction' (Symbol or string)
    for j in junctions:
        first = str(j[0]).lower()
        assert 'junction' in first


def test_parse_junction_element():
    """Parse junction element into Junction object"""
    junction_sexp = [
        'junction',
        ['at', 144.78, 86.36],
        ['diameter', 0],
        ['color', 0, 0, 0, 0],
        ['uuid', '01c5e486-ede8-4b12-be44-e41a287d34af']
    ]

    junction = parse_junction_element(junction_sexp)

    assert isinstance(junction, Junction)
    assert junction.uuid == '01c5e486-ede8-4b12-be44-e41a287d34af'
    assert junction.position == (144.78, 86.36)
    assert junction.diameter == 0
    assert junction.color == (0, 0, 0, 0)


def test_extract_sheets():
    """Extract sheet elements from hierarchical schematic"""
    fixture_path = Path("tests/fixtures/test_06_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)
    sheets = extract_sheets(sexp)

    # test_06 has 2 sheets (lighting and avionics)
    assert len(sheets) == 2

    # Check that sheets are SheetElement objects
    assert all(isinstance(sheet, SheetElement) for sheet in sheets)

    # Verify avionics sheet
    avionics = next((s for s in sheets if s.sheetname == "avionics"), None)
    assert avionics is not None
    assert avionics.uuid == "3f34c49e-ae58-4433-8ae6-817967dac1be"
    assert avionics.sheetfile == "test_06_avionics.kicad_sch"
    assert len(avionics.pins) == 1
    assert avionics.pins[0].name == "avionics"
    assert avionics.pins[0].direction == "input"
    assert avionics.pins[0].position == (81.28, 43.18)

    # Verify lighting sheet
    lighting = next((s for s in sheets if s.sheetname == "Lighting"), None)
    assert lighting is not None
    assert lighting.uuid == "b1093350-cedd-46df-81c4-dadfdf2715f8"
    assert lighting.sheetfile == "test_06_lighting.kicad_sch"
    assert len(lighting.pins) == 2
    pin_names = [p.name for p in lighting.pins]
    assert "TAIL_LT" in pin_names
    assert "TIP_LT" in pin_names
