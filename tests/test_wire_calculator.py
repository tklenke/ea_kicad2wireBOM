# ABOUTME: Tests for wire calculator module
# ABOUTME: Validates wire length and gauge calculations

import pytest
from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_calculator import (
    calculate_length,
    calculate_voltage_drop,
    determine_min_gauge,
    parse_net_name,
    infer_system_code_from_components,
    detect_system_code,
    generate_wire_label,
    group_wires_by_circuit
)
from kicad2wireBOM.wire_bom import WireConnection


def test_calculate_length_simple():
    """Test wire length calculation with simple coordinates"""
    comp1 = Component(ref='J1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=15.0)
    comp2 = Component(ref='SW1', fs=10.0, wl=5.0, bl=2.0, load=None, rating=20.0)
    slack = 24.0

    length = calculate_length(comp1, comp2, slack)

    # Manhattan distance: |10-0| + |5-0| + |2-0| = 17
    # Plus slack: 17 + 24 = 41
    assert length == 41.0


def test_calculate_length_negative_coordinates():
    """Test wire length calculation with negative coordinates"""
    comp1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    comp2 = Component(ref='LIGHT1', fs=150.0, wl=-10.0, bl=5.0, load=None, rating=None)
    slack = 24.0

    length = calculate_length(comp1, comp2, slack)

    # Manhattan distance: |150-100| + |-10-25| + |5-0| = 50 + 35 + 5 = 90
    # Plus slack: 90 + 24 = 114
    assert length == 114.0


def test_calculate_length_same_location():
    """Test wire length when components at same location (edge case)"""
    comp1 = Component(ref='J1', fs=50.0, wl=25.0, bl=10.0, load=None, rating=15.0)
    comp2 = Component(ref='SW1', fs=50.0, wl=25.0, bl=10.0, load=None, rating=20.0)
    slack = 24.0

    length = calculate_length(comp1, comp2, slack)

    # Manhattan distance: 0 + 0 + 0 = 0
    # Plus slack: 0 + 24 = 24
    assert length == 24.0


def test_calculate_length_zero_slack():
    """Test wire length calculation with no slack"""
    comp1 = Component(ref='J1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=15.0)
    comp2 = Component(ref='SW1', fs=10.0, wl=10.0, bl=10.0, load=None, rating=20.0)
    slack = 0.0

    length = calculate_length(comp1, comp2, slack)

    # Manhattan distance: |10-0| + |10-0| + |10-0| = 30
    # Plus slack: 30 + 0 = 30
    assert length == 30.0


def test_calculate_length_from_fixture():
    """Test wire length with components from test fixture 01"""
    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    sw1 = Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)
    slack = 24.0

    length = calculate_length(j1, sw1, slack)

    # Manhattan distance: |150-100| + |30-25| + |0-0| = 50 + 5 + 0 = 55
    # Plus slack: 55 + 24 = 79
    assert length == 79.0


def test_calculate_voltage_drop():
    """Test voltage drop calculation"""
    # AWG 20: 0.01015 ohm/ft from reference data
    # 5A current, 100 inches (8.33 ft)
    # Vdrop = I * R * L = 5 * 0.01015 * 8.33 = 0.422V
    vdrop = calculate_voltage_drop(current=5.0, awg_size=20, length_inches=100.0)
    assert abs(vdrop - 0.422) < 0.01

    # AWG 12: 0.001588 ohm/ft
    # 10A current, 79 inches (6.58 ft)
    # Vdrop = 10 * 0.001588 * 6.58 = 0.105V
    vdrop = calculate_voltage_drop(current=10.0, awg_size=12, length_inches=79.0)
    assert abs(vdrop - 0.105) < 0.01


def test_determine_min_gauge_voltage_drop_constraint():
    """Test that gauge selection meets voltage drop constraint"""
    # 5A load, 79 inches, 14V system, 5% max drop (0.7V)
    # Try each gauge and verify smallest one that meets constraint
    min_gauge = determine_min_gauge(current=5.0, length_inches=79.0, system_voltage=14.0)

    # Verify returned gauge meets voltage drop constraint
    vdrop = calculate_voltage_drop(5.0, min_gauge, 79.0)
    max_vdrop = 14.0 * 0.05
    assert vdrop <= max_vdrop

    # Should be AWG 22 or smaller (lower number = larger wire)
    assert min_gauge in [12, 16, 18, 20, 22]


def test_determine_min_gauge_ampacity_constraint():
    """Test that gauge selection meets ampacity constraint"""
    # 15A load - requires AWG 14 or larger (16 is 12.8A, 14 is 19A, 12 is 25.2A)
    # Short wire so voltage drop won't be the limiting factor
    min_gauge = determine_min_gauge(current=15.0, length_inches=24.0, system_voltage=14.0)

    # Must be AWG 14 since AWG 16 only handles 12.8A (AWG 14 handles 19A)
    assert min_gauge == 14


def test_determine_min_gauge_returns_smallest_suitable():
    """Test that function returns smallest gauge that meets both constraints"""
    # Low current, short wire - should select smallest (highest AWG number)
    min_gauge = determine_min_gauge(current=2.0, length_inches=24.0, system_voltage=14.0)

    # Should be AWG 24 (smallest wire that meets requirements - 2.0A ampacity)
    assert min_gauge == 24


def test_determine_min_gauge_handles_missing_data_sentinel():
    """Test that gauge determination returns -99 when current is -99 (missing data)"""
    min_gauge = determine_min_gauge(current=-99, length_inches=100.0, system_voltage=14.0)

    # Should return -99 sentinel unchanged
    assert min_gauge == -99


def test_parse_net_name_compact():
    """Test parsing net name in compact format (no dashes)"""
    result = parse_net_name('/P1A')
    assert result is not None
    assert result['system'] == 'P'
    assert result['circuit'] == '1'
    assert result['segment'] == 'A'


def test_parse_net_name_dashed():
    """Test parsing net name with dashes"""
    result = parse_net_name('/L-105-B')
    assert result is not None
    assert result['system'] == 'L'
    assert result['circuit'] == '105'
    assert result['segment'] == 'B'


def test_parse_net_name_leading_zeros():
    """Test parsing net name with leading zeros"""
    result = parse_net_name('/G-001-A')
    assert result is not None
    assert result['system'] == 'G'
    assert result['circuit'] == '001'
    assert result['segment'] == 'A'


def test_parse_net_name_mixed():
    """Test parsing net name with partial dashes"""
    result = parse_net_name('/R12-C')
    assert result is not None
    assert result['system'] == 'R'
    assert result['circuit'] == '12'
    assert result['segment'] == 'C'


def test_parse_net_name_invalid():
    """Test parsing invalid net names returns None"""
    assert parse_net_name('Net-(J1-Pin_1)') is None
    assert parse_net_name('/P1') is None  # Missing segment
    assert parse_net_name('/PA') is None  # Missing circuit
    assert parse_net_name('P1A') is None  # Missing leading slash
    assert parse_net_name('') is None


def test_detect_system_code_from_net_name():
    """Test system code detection from properly formatted net names"""
    comp = Component(ref='C1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=None, source=None)

    # Should detect from net name (primary method)
    assert detect_system_code([comp], '/P1A') == 'P'
    assert detect_system_code([comp], '/L-105-B') == 'L'
    assert detect_system_code([comp], '/G1A') == 'G'
    assert detect_system_code([comp], '/R3C') == 'R'


def test_detect_system_code_light():
    """Test system code detection for lighting circuits"""
    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    light = Component(ref='LIGHT1', fs=150.0, wl=30.0, bl=0.0, load=5.0, rating=None)

    code = detect_system_code([j1, light], "Net-(J1-LIGHT1)")
    assert code == 'L'  # Lighting system


def test_detect_system_code_battery():
    """Test system code detection for battery/power circuits"""
    bat = Component(ref='BAT1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=50.0)
    sw = Component(ref='SW1', fs=10.0, wl=0.0, bl=0.0, load=None, rating=20.0)

    code = detect_system_code([bat, sw], "BAT_POWER")
    assert code == 'P'  # Power system


def test_detect_system_code_switch_hint():
    """Test system code detection from switch reference"""
    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    sw = Component(ref='SW_LIGHT', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)

    code = detect_system_code([j1, sw], "Net-(J1-SW)")
    # Should detect LIGHT in switch ref
    assert code == 'L'


def test_detect_system_code_unknown():
    """Test system code detection fallback to Unknown"""
    j1 = Component(ref='J1', fs=100.0, wl=25.0, bl=0.0, load=None, rating=15.0)
    j2 = Component(ref='J2', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)

    code = detect_system_code([j1, j2], "Net-(J1-J2)")
    assert code == 'U'  # Unknown system


def test_generate_wire_label():
    """Test wire label generation in EAWMS format"""
    label = generate_wire_label('L', '105', 'A')
    assert label == 'L-105-A'

    label = generate_wire_label('P', '12', 'B')
    assert label == 'P-12-B'

    label = generate_wire_label('U', '1', 'C')
    assert label == 'U-1-C'


def test_group_wires_by_circuit():
    """Test grouping wire connections by circuit ID"""
    # Create test wires for 3 circuits:
    # Circuit L1: L-1-A, L-1-B
    # Circuit L2: L-2-A, L-2-B, L-2-C
    # Circuit G1: G-1-A
    wires = [
        WireConnection('L-1-A', 'J1', '1', 'SW1', '1', 18, 'White', 79.0, 'Standard', '', []),
        WireConnection('L-1-B', 'SW1', '2', 'LIGHT1', '1', 18, 'White', 55.0, 'Standard', '', []),
        WireConnection('L-2-A', 'J1', '2', 'SW2', '1', 16, 'Red', 100.0, 'Standard', '', []),
        WireConnection('L-2-B', 'SW2', '2', 'LIGHT2', '1', 16, 'Red', 60.0, 'Standard', '', []),
        WireConnection('L-2-C', 'SW2', '2', 'LIGHT3', '1', 16, 'Red', 65.0, 'Standard', '', []),
        WireConnection('G-1-A', 'LIGHT1', '2', 'GND', '1', 18, 'Black', 50.0, 'Standard', '', []),
    ]

    result = group_wires_by_circuit(wires)

    # Should have 3 circuit groups
    assert len(result) == 3

    # Verify circuit L1 has 2 wires
    assert 'L1' in result
    assert len(result['L1']) == 2
    assert result['L1'][0].wire_label == 'L-1-A'
    assert result['L1'][1].wire_label == 'L-1-B'

    # Verify circuit L2 has 3 wires
    assert 'L2' in result
    assert len(result['L2']) == 3
    assert result['L2'][0].wire_label == 'L-2-A'
    assert result['L2'][1].wire_label == 'L-2-B'
    assert result['L2'][2].wire_label == 'L-2-C'

    # Verify circuit G1 has 1 wire
    assert 'G1' in result
    assert len(result['G1']) == 1
    assert result['G1'][0].wire_label == 'G-1-A'


def test_determine_circuit_current_single_load():
    """Test circuit current determination for single load circuit"""
    from kicad2wireBOM.wire_calculator import determine_circuit_current

    # Circuit L1: J1 --L1A--> SW1 --L1B--> LIGHT1 (10A load)
    circuit_wires = [
        WireConnection('L-1-A', 'J1', '1', 'SW1', '1', 18, 'White', 79.0, 'Standard', '', []),
        WireConnection('L-1-B', 'SW1', '2', 'LIGHT1', '1', 18, 'White', 55.0, 'Standard', '', []),
    ]

    components = [
        Component(ref='J1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=15.0, source=None),
        Component(ref='SW1', fs=50.0, wl=0.0, bl=0.0, load=None, rating=20.0, source=None),
        Component(ref='LIGHT1', fs=100.0, wl=0.0, bl=0.0, load=10.0, rating=None, source=None),
    ]

    current = determine_circuit_current(circuit_wires, components, None)

    # Should return sum of loads = 10A
    assert current == 10.0


def test_determine_circuit_current_parallel_loads():
    """Test circuit current determination for parallel loads"""
    from kicad2wireBOM.wire_calculator import determine_circuit_current

    # Circuit L2: J1 --L2A--> SW2 --L2B--> LIGHT2 (7A)
    #                              \--L2C--> LIGHT3 (7A)
    circuit_wires = [
        WireConnection('L-2-A', 'J1', '2', 'SW2', '1', 16, 'Red', 100.0, 'Standard', '', []),
        WireConnection('L-2-B', 'SW2', '2', 'LIGHT2', '1', 16, 'Red', 60.0, 'Standard', '', []),
        WireConnection('L-2-C', 'SW2', '2', 'LIGHT3', '1', 16, 'Red', 65.0, 'Standard', '', []),
    ]

    components = [
        Component(ref='J1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=15.0, source=None),
        Component(ref='SW2', fs=50.0, wl=0.0, bl=0.0, load=None, rating=20.0, source=None),
        Component(ref='LIGHT2', fs=100.0, wl=0.0, bl=0.0, load=7.0, rating=None, source=None),
        Component(ref='LIGHT3', fs=100.0, wl=10.0, bl=0.0, load=7.0, rating=None, source=None),
    ]

    current = determine_circuit_current(circuit_wires, components, None)

    # Should return sum of loads = 7 + 7 = 14A
    assert current == 14.0


def test_determine_circuit_current_power_source():
    """Test circuit current determination for power distribution (source only, no loads)"""
    from kicad2wireBOM.wire_calculator import determine_circuit_current

    # Circuit P1: BT1 --P1A--> BUS (power distribution, no loads in circuit)
    circuit_wires = [
        WireConnection('P-1-A', 'BT1', '1', 'BUS', '1', 12, 'Red', 50.0, 'Standard', '', []),
    ]

    components = [
        Component(ref='BT1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=None, source=40.0),
        Component(ref='BUS', fs=50.0, wl=0.0, bl=0.0, load=None, rating=50.0, source=None),
    ]

    current = determine_circuit_current(circuit_wires, components, None)

    # Should return max of sources = 40A
    assert current == 40.0


def test_determine_circuit_current_missing_data():
    """Test circuit current determination when no loads or sources found"""
    from kicad2wireBOM.wire_calculator import determine_circuit_current

    # Circuit with only passthrough components (no load, no source)
    circuit_wires = [
        WireConnection('X-1-A', 'J1', '1', 'J2', '1', 18, 'White', 50.0, 'Standard', '', []),
    ]

    components = [
        Component(ref='J1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=15.0, source=None),
        Component(ref='J2', fs=50.0, wl=0.0, bl=0.0, load=None, rating=15.0, source=None),
    ]

    current = determine_circuit_current(circuit_wires, components, None)

    # Should return -99 (sentinel for missing data)
    assert current == -99
