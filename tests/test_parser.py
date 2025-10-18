# ABOUTME: Tests for the netlist parser module
# ABOUTME: Validates parsing of KiCad netlists and extraction of nets and components

import pytest
from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file, extract_nets, extract_components, parse_footprint_encoding


def test_parse_netlist_file():
    """Test that parse_netlist_file returns a kinparse object"""
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_01.net"
    result = parse_netlist_file(fixture_path)

    # kinparse returns a ParseResults object with various sections
    assert result is not None
    assert hasattr(result, 'nets')
    assert hasattr(result, 'parts')  # kinparse calls components "parts"


def test_extract_nets():
    """Test extraction of net information from parsed netlist"""
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_01.net"
    parsed = parse_netlist_file(fixture_path)
    nets = extract_nets(parsed)

    # Should extract list of net dicts
    assert isinstance(nets, list)
    assert len(nets) > 0

    # Each net should have code, name, and class
    net = nets[0]
    assert 'code' in net
    assert 'name' in net
    assert 'class' in net

    # Verify we got the expected nets from the fixture
    net_codes = [n['code'] for n in nets]
    assert '1' in net_codes  # Net-(J1-Pin_1)


def test_extract_components():
    """Test extraction of component information from parsed netlist"""
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_01.net"
    parsed = parse_netlist_file(fixture_path)
    components = extract_components(parsed)

    # Should extract list of component dicts
    assert isinstance(components, list)
    assert len(components) == 2  # BT1 and L1

    # Each component should have ref and footprint
    comp = components[0]
    assert 'ref' in comp
    assert 'footprint' in comp

    # Verify expected components
    refs = [c['ref'] for c in components]
    assert 'BT1' in refs
    assert 'L1' in refs

    # Verify footprint field contains full string including encoding
    bt1 = next(c for c in components if c['ref'] == 'BT1')
    assert '|(10,0,0)S40' in bt1['footprint']


def test_parse_footprint_encoding():
    """Test parsing of footprint encoding format: |(fs,wl,bl)<L|R|S><amps>"""

    # Test Load type (L)
    result = parse_footprint_encoding("Connector:Conn_01x02|(100.0,25.0,0.0)L15")
    assert result is not None
    assert result['fs'] == 100.0
    assert result['wl'] == 25.0
    assert result['bl'] == 0.0
    assert result['type'] == 'L'
    assert result['amperage'] == 15.0

    # Test Rating type (R)
    result = parse_footprint_encoding("Button_Switch_THT:SW_PUSH_6mm|(150.0,30.0,0.0)R20")
    assert result is not None
    assert result['fs'] == 150.0
    assert result['wl'] == 30.0
    assert result['bl'] == 0.0
    assert result['type'] == 'R'
    assert result['amperage'] == 20.0

    # Test Source type (S)
    result = parse_footprint_encoding("Device:Battery|(10,0,0)S40")
    assert result is not None
    assert result['fs'] == 10.0
    assert result['wl'] == 0.0
    assert result['bl'] == 0.0
    assert result['type'] == 'S'
    assert result['amperage'] == 40.0

    # Test with negative coordinates
    result = parse_footprint_encoding("SomeFootprint|(10.5,-20.3,5.0)L5")
    assert result is not None
    assert result['fs'] == 10.5
    assert result['wl'] == -20.3
    assert result['bl'] == 5.0
    assert result['amperage'] == 5.0

    # Test with decimal amperage
    result = parse_footprint_encoding("SomeFootprint|(0.0,0.0,0.0)R0.5")
    assert result is not None
    assert result['amperage'] == 0.5

    # Test without encoding - should return None
    result = parse_footprint_encoding("Connector:Conn_01x02")
    assert result is None

    # Test with malformed encoding
    result = parse_footprint_encoding("Bad|(a,b,c)L5")
    assert result is None
