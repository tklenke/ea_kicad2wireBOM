# ABOUTME: Tests for wire BOM data model
# ABOUTME: Validates WireConnection and WireBOM classes

import pytest
from kicad2wireBOM.wire_bom import WireConnection, WireBOM


def test_wire_connection_creation():
    """Test creating a WireConnection with all fields"""
    wire = WireConnection(
        wire_label='L-105-A',
        from_ref='J1',
        to_ref='SW1',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        warnings=[]
    )

    assert wire.wire_label == 'L-105-A'
    assert wire.from_ref == 'J1'
    assert wire.to_ref == 'SW1'
    assert wire.wire_gauge == 20
    assert wire.wire_color == 'White'
    assert wire.length == 79.0
    assert wire.wire_type == 'Standard'
    assert wire.warnings == []


def test_wire_connection_with_warnings():
    """Test WireConnection with warnings"""
    wire = WireConnection(
        wire_label='U-1-A',
        from_ref='J1',
        to_ref='J2',
        wire_gauge=12,
        wire_color='White',
        length=50.0,
        wire_type='Standard',
        warnings=['Unknown system code']
    )

    assert len(wire.warnings) == 1
    assert 'Unknown' in wire.warnings[0]


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
        from_ref='J1',
        to_ref='SW1',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        warnings=[]
    )

    bom.add_wire(wire1)
    assert len(bom.wires) == 1
    assert bom.wires[0] == wire1

    wire2 = WireConnection(
        wire_label='P-12-A',
        from_ref='BAT1',
        to_ref='SW2',
        wire_gauge=12,
        wire_color='Red',
        length=50.0,
        wire_type='Standard',
        warnings=[]
    )

    bom.add_wire(wire2)
    assert len(bom.wires) == 2
    assert bom.wires[1] == wire2
