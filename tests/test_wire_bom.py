# ABOUTME: Tests for wire BOM data model
# ABOUTME: Validates WireConnection and WireBOM classes

import pytest
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.component import Component


def test_wire_connection_creation():
    """Test creating a WireConnection with all fields"""
    wire = WireConnection(
        wire_label='L-105-A',
        from_component='J1',
        from_pin='1',
        to_component='SW1',
        to_pin='3',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        notes='',
        warnings=[]
    )

    assert wire.wire_label == 'L-105-A'
    assert wire.from_component == 'J1'
    assert wire.from_pin == '1'
    assert wire.to_component == 'SW1'
    assert wire.to_pin == '3'
    assert wire.wire_gauge == 20
    assert wire.wire_color == 'White'
    assert wire.length == 79.0
    assert wire.wire_type == 'Standard'
    assert wire.notes == ''
    assert wire.warnings == []


def test_wire_connection_with_warnings():
    """Test WireConnection with warnings"""
    wire = WireConnection(
        wire_label='U-1-A',
        from_component='J1',
        from_pin='2',
        to_component='J2',
        to_pin='1',
        wire_gauge=12,
        wire_color='White',
        length=50.0,
        wire_type='Standard',
        notes='',
        warnings=['Unknown system code']
    )

    assert len(wire.warnings) == 1
    assert 'Unknown' in wire.warnings[0]


def test_wire_connection_with_notes():
    """Test WireConnection with notes field"""
    wire = WireConnection(
        wire_label='L-105-A',
        from_component='J1',
        from_pin='1',
        to_component='SW1',
        to_pin='3',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        notes='24AWG HIGH_CURRENT',
        warnings=[]
    )

    assert wire.notes == '24AWG HIGH_CURRENT'


def test_wire_bom_creation():
    """Test creating a WireBOM"""
    config = {'system_voltage': 14.0, 'slack_length': 24.0}
    bom = WireBOM(config=config)

    assert bom.wires == []
    assert bom.config == config


def test_wire_bom_add_wire():
    """Test adding wires to BOM"""
    bom = WireBOM(config={})

    wire1 = WireConnection(
        wire_label='L-105-A',
        from_component='J1',
        from_pin='1',
        to_component='SW1',
        to_pin='3',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        notes='',
        warnings=[]
    )

    bom.add_wire(wire1)
    assert len(bom.wires) == 1
    assert bom.wires[0] == wire1

    wire2 = WireConnection(
        wire_label='P-12-A',
        from_component='BAT1',
        from_pin='1',
        to_component='SW2',
        to_pin='2',
        wire_gauge=12,
        wire_color='Red',
        length=50.0,
        wire_type='Standard',
        notes='',
        warnings=[]
    )

    bom.add_wire(wire2)
    assert len(bom.wires) == 2
    assert bom.wires[1] == wire2


def test_should_swap_components_different_bl():
    """Test component swapping based on BL (Butt Line) - furthest from centerline first"""
    # Import function from __main__ module
    from kicad2wireBOM.__main__ import should_swap_components

    # comp1 at BL=10, comp2 at BL=0
    # abs(10) > abs(0), so comp1 should stay first (return False)
    comp1 = Component(ref='L1', fs=100.0, wl=25.0, bl=10.0, load=5.0, rating=None)
    comp2 = Component(ref='SW1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    assert should_swap_components(comp1, comp2) == False

    # comp1 at BL=0, comp2 at BL=10
    # abs(0) < abs(10), so should swap (return True)
    comp1 = Component(ref='SW1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    comp2 = Component(ref='L1', fs=100.0, wl=25.0, bl=10.0, load=5.0, rating=None)
    assert should_swap_components(comp1, comp2) == True

    # Test with negative BL values - abs() matters
    # comp1 at BL=-10, comp2 at BL=5
    # abs(-10)=10 > abs(5)=5, so comp1 should stay first (return False)
    comp1 = Component(ref='L1', fs=100.0, wl=25.0, bl=-10.0, load=5.0, rating=None)
    comp2 = Component(ref='SW1', fs=50.0, wl=20.0, bl=5.0, load=None, rating=10.0)
    assert should_swap_components(comp1, comp2) == False


def test_should_swap_components_same_bl_different_fs():
    """Test component swapping based on FS (Fuselage Station) when BL equal - furthest aft first"""
    from kicad2wireBOM.__main__ import should_swap_components

    # Both at BL=0, comp1 FS=100, comp2 FS=50
    # FS 100 > 50 (further aft), so comp1 should stay first (return False)
    comp1 = Component(ref='L1', fs=100.0, wl=25.0, bl=0.0, load=5.0, rating=None)
    comp2 = Component(ref='SW1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    assert should_swap_components(comp1, comp2) == False

    # Both at BL=0, comp1 FS=50, comp2 FS=100
    # FS 50 < 100, so should swap (return True)
    comp1 = Component(ref='SW1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    comp2 = Component(ref='L1', fs=100.0, wl=25.0, bl=0.0, load=5.0, rating=None)
    assert should_swap_components(comp1, comp2) == True


def test_should_swap_components_same_bl_fs_different_wl():
    """Test component swapping based on WL (Water Line) when BL and FS equal - topmost first"""
    from kicad2wireBOM.__main__ import should_swap_components

    # Same BL and FS, comp1 WL=30, comp2 WL=20
    # WL 30 > 20 (higher), so comp1 should stay first (return False)
    comp1 = Component(ref='L1', fs=100.0, wl=30.0, bl=0.0, load=5.0, rating=None)
    comp2 = Component(ref='SW1', fs=100.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    assert should_swap_components(comp1, comp2) == False

    # Same BL and FS, comp1 WL=20, comp2 WL=30
    # WL 20 < 30, so should swap (return True)
    comp1 = Component(ref='SW1', fs=100.0, wl=20.0, bl=0.0, load=None, rating=10.0)
    comp2 = Component(ref='L1', fs=100.0, wl=30.0, bl=0.0, load=5.0, rating=None)
    assert should_swap_components(comp1, comp2) == True


def test_should_swap_components_equal_coordinates():
    """Test that components with equal coordinates don't swap"""
    from kicad2wireBOM.__main__ import should_swap_components

    # Identical coordinates - keep current order
    comp1 = Component(ref='L1', fs=100.0, wl=25.0, bl=10.0, load=5.0, rating=None)
    comp2 = Component(ref='SW1', fs=100.0, wl=25.0, bl=10.0, load=None, rating=10.0)
    assert should_swap_components(comp1, comp2) == False


def test_should_swap_components_missing_component():
    """Test that missing components don't cause swap"""
    from kicad2wireBOM.__main__ import should_swap_components

    comp1 = Component(ref='L1', fs=100.0, wl=25.0, bl=10.0, load=5.0, rating=None)

    # None component
    assert should_swap_components(None, comp1) == False
    assert should_swap_components(comp1, None) == False
    assert should_swap_components(None, None) == False
