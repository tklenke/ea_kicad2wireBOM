# ABOUTME: Tests for hierarchical schematic data models
# ABOUTME: Tests HierarchicalSchematic, SheetConnection, GlobalNet, PowerSymbol, SheetElement, HierarchicalLabel

from pathlib import Path
from kicad2wireBOM.schematic import (
    HierarchicalSchematic,
    SheetConnection,
    GlobalNet,
    PowerSymbol,
    SheetElement,
    SheetPin,
    HierarchicalLabel,
    Sheet,
)
from kicad2wireBOM.parser import parse_schematic_hierarchical


def test_hierarchical_schematic_creation():
    """Test creating HierarchicalSchematic with root_sheet, sub_sheets, sheet_connections, global_nets"""
    root_sheet = Sheet(
        uuid="root",
        name="Main",
        file_path="main.kicad_sch",
        wire_segments=[],
        junctions=[],
        labels=[],
        components=[],
        sheet_elements=[],
        hierarchical_labels=[]
    )

    sub_sheet = Sheet(
        uuid="sub1",
        name="Lighting",
        file_path="lighting.kicad_sch",
        wire_segments=[],
        junctions=[],
        labels=[],
        components=[],
        sheet_elements=[],
        hierarchical_labels=[]
    )

    connection = SheetConnection(
        parent_sheet_uuid="root",
        child_sheet_uuid="sub1",
        pin_name="TAIL_LT",
        parent_pin_position=(100.0, 50.0),
        parent_wire_net=None,
        child_label_position=(38.1, 63.5),
        child_wire_net=None
    )

    power_symbol = PowerSymbol(
        reference="#PWR01",
        sheet_uuid="root",
        position=(50.0, 50.0),
        loc_load=None
    )

    global_net = GlobalNet(
        net_name="GND",
        power_symbols=[power_symbol]
    )

    hierarchical_schematic = HierarchicalSchematic(
        root_sheet=root_sheet,
        sub_sheets={"sub1": sub_sheet},
        sheet_connections=[connection],
        global_nets={"GND": global_net}
    )

    assert hierarchical_schematic.root_sheet == root_sheet
    assert hierarchical_schematic.sub_sheets == {"sub1": sub_sheet}
    assert hierarchical_schematic.sheet_connections == [connection]
    assert hierarchical_schematic.global_nets == {"GND": global_net}


def test_sheet_connection_creation():
    """Test creating SheetConnection with parent/child UUIDs, pin_name, positions, wire_nets"""
    connection = SheetConnection(
        parent_sheet_uuid="root",
        child_sheet_uuid="b1093350-cedd-46df-81c4-dadfdf2715f8",
        pin_name="TAIL_LT",
        parent_pin_position=(168.91, 60.96),
        parent_wire_net=None,
        child_label_position=(38.1, 63.5),
        child_wire_net=None
    )

    assert connection.parent_sheet_uuid == "root"
    assert connection.child_sheet_uuid == "b1093350-cedd-46df-81c4-dadfdf2715f8"
    assert connection.pin_name == "TAIL_LT"
    assert connection.parent_pin_position == (168.91, 60.96)
    assert connection.parent_wire_net is None
    assert connection.child_label_position == (38.1, 63.5)
    assert connection.child_wire_net is None


def test_global_net_and_power_symbol_creation():
    """Test creating GlobalNet with net_name and list of PowerSymbol instances"""
    power_symbol1 = PowerSymbol(
        reference="#PWR01",
        sheet_uuid="root",
        position=(50.0, 50.0),
        loc_load=None
    )

    power_symbol2 = PowerSymbol(
        reference="#PWR02",
        sheet_uuid="sub1",
        position=(30.0, 40.0),
        loc_load="(100,50,5)G"
    )

    global_net = GlobalNet(
        net_name="GND",
        power_symbols=[power_symbol1, power_symbol2]
    )

    assert global_net.net_name == "GND"
    assert len(global_net.power_symbols) == 2
    assert global_net.power_symbols[0] == power_symbol1
    assert global_net.power_symbols[1] == power_symbol2
    assert power_symbol2.loc_load == "(100,50,5)G"


def test_sheet_element_creation():
    """Test creating SheetElement with uuid, sheetname, sheetfile, pins list"""
    pin1 = SheetPin(
        name="TAIL_LT",
        direction="input",
        position=(168.91, 60.96)
    )

    pin2 = SheetPin(
        name="TIP_LT",
        direction="input",
        position=(168.91, 67.31)
    )

    sheet_element = SheetElement(
        uuid="b1093350-cedd-46df-81c4-dadfdf2715f8",
        sheetname="Lighting",
        sheetfile="test_06_lighting.kicad_sch",
        pins=[pin1, pin2]
    )

    assert sheet_element.uuid == "b1093350-cedd-46df-81c4-dadfdf2715f8"
    assert sheet_element.sheetname == "Lighting"
    assert sheet_element.sheetfile == "test_06_lighting.kicad_sch"
    assert len(sheet_element.pins) == 2
    assert sheet_element.pins[0].name == "TAIL_LT"
    assert sheet_element.pins[0].direction == "input"
    assert sheet_element.pins[0].position == (168.91, 60.96)


def test_hierarchical_label_creation():
    """Test creating HierarchicalLabel with name, position, shape"""
    label = HierarchicalLabel(
        name="TAIL_LT",
        position=(38.1, 63.5),
        shape="input"
    )

    assert label.name == "TAIL_LT"
    assert label.position == (38.1, 63.5)
    assert label.shape == "input"


def test_sheet_creation():
    """Test creating Sheet with all required fields"""
    sheet = Sheet(
        uuid="root",
        name="Main",
        file_path="main.kicad_sch",
        wire_segments=[],
        junctions=[],
        labels=[],
        components=[],
        sheet_elements=[],
        hierarchical_labels=[]
    )

    assert sheet.uuid == "root"
    assert sheet.name == "Main"
    assert sheet.file_path == "main.kicad_sch"
    assert sheet.wire_segments == []
    assert sheet.junctions == []
    assert sheet.labels == []
    assert sheet.components == []
    assert sheet.sheet_elements == []
    assert sheet.hierarchical_labels == []


def test_parse_schematic_hierarchical():
    """Test parsing hierarchical schematic with main sheet and sub-sheets"""
    fixture_path = Path("tests/fixtures/test_06_fixture.kicad_sch")
    hierarchical_schematic = parse_schematic_hierarchical(fixture_path)

    # Verify it's a HierarchicalSchematic object
    assert isinstance(hierarchical_schematic, HierarchicalSchematic)

    # Verify root sheet exists
    assert hierarchical_schematic.root_sheet is not None
    assert hierarchical_schematic.root_sheet.uuid == "6f32b1c6-d0dc-4a69-b565-c121d7833096"
    assert hierarchical_schematic.root_sheet.file_path == str(fixture_path)

    # Verify 2 sub-sheets loaded (lighting and avionics)
    assert len(hierarchical_schematic.sub_sheets) == 2
    assert "b1093350-cedd-46df-81c4-dadfdf2715f8" in hierarchical_schematic.sub_sheets  # lighting
    assert "3f34c49e-ae58-4433-8ae6-817967dac1be" in hierarchical_schematic.sub_sheets  # avionics

    # Verify lighting sheet loaded correctly
    lighting_sheet = hierarchical_schematic.sub_sheets["b1093350-cedd-46df-81c4-dadfdf2715f8"]
    assert lighting_sheet.name == "Lighting"
    assert "test_06_lighting.kicad_sch" in lighting_sheet.file_path
    assert len(lighting_sheet.hierarchical_labels) == 2

    # Verify avionics sheet loaded correctly
    avionics_sheet = hierarchical_schematic.sub_sheets["3f34c49e-ae58-4433-8ae6-817967dac1be"]
    assert avionics_sheet.name == "avionics"
    assert "test_06_avionics.kicad_sch" in avionics_sheet.file_path
    assert len(avionics_sheet.hierarchical_labels) == 1

    # Verify sheet connections created
    # Should have 3 connections: TAIL_LT, TIP_LT (lighting), avionics (avionics)
    assert len(hierarchical_schematic.sheet_connections) == 3

    # Verify one of the connections (TAIL_LT)
    tail_connection = next(
        (c for c in hierarchical_schematic.sheet_connections if c.pin_name == "TAIL_LT"),
        None
    )
    assert tail_connection is not None
    assert tail_connection.parent_sheet_uuid == "6f32b1c6-d0dc-4a69-b565-c121d7833096"
    assert tail_connection.child_sheet_uuid == "b1093350-cedd-46df-81c4-dadfdf2715f8"
    assert tail_connection.parent_pin_position == (168.91, 60.96)
    assert tail_connection.child_label_position == (38.1, 63.5)
