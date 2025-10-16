# ABOUTME: Integration test for fixture 01 - minimal two-component circuit
# ABOUTME: End-to-end test from netlist parsing to CSV output

import csv
from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file, extract_components, parse_footprint_encoding
from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_calculator import calculate_length, determine_min_gauge, detect_system_code, generate_wire_label
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG


def test_fixture_01_integration(tmp_path):
    """
    Integration test for fixture 01: J1 to SW1 minimal circuit.

    Validates complete pipeline:
    1. Parse netlist
    2. Extract components with coordinates
    3. Calculate wire length
    4. Determine wire gauge
    5. Detect system code
    6. Generate wire label
    7. Create BOM
    8. Write CSV output
    """
    # 1. Parse netlist
    fixture_path = Path(__file__).parent / "fixtures" / "test_01_minimal_two_component.net"
    parsed = parse_netlist_file(fixture_path)
    components_raw = extract_components(parsed)

    assert len(components_raw) == 2

    # 2. Extract components with coordinates
    components = []
    for comp_raw in components_raw:
        encoding = parse_footprint_encoding(comp_raw['footprint'])
        assert encoding is not None

        load = encoding['amperage'] if encoding['type'] == 'L' else None
        rating = encoding['amperage'] if encoding['type'] == 'R' else None

        comp = Component(
            ref=comp_raw['ref'],
            fs=encoding['fs'],
            wl=encoding['wl'],
            bl=encoding['bl'],
            load=load,
            rating=rating
        )
        components.append(comp)

    j1 = next(c for c in components if c.ref == 'J1')
    sw1 = next(c for c in components if c.ref == 'SW1')

    # 3. Calculate wire length
    slack = DEFAULT_CONFIG['slack_length']
    length = calculate_length(j1, sw1, slack)

    # J1: (100.0, 25.0, 0.0), SW1: (150.0, 30.0, 0.0)
    # Manhattan: |150-100| + |30-25| + |0-0| = 55
    # Plus slack: 55 + 24 = 79
    assert length == 79.0

    # 4. Determine wire gauge
    # Both are Rating type, so use the smaller rating (15A from J1)
    current = min(j1.rating, sw1.rating)
    system_voltage = DEFAULT_CONFIG['system_voltage']
    wire_gauge = determine_min_gauge(current, length, system_voltage)

    # Should select appropriate gauge for 15A over 79 inches
    assert wire_gauge in [12, 16, 18, 20]

    # 5. Detect system code
    system_code = detect_system_code([j1, sw1], "Net-(J1-Pin_1)")

    # No clear lighting/power indicators, should be Unknown
    assert system_code == 'U'

    # 6. Generate wire label
    wire_label = generate_wire_label(system_code, '1', 'A')
    assert wire_label == 'U-1-A'

    # 7. Create BOM
    bom = WireBOM(config=DEFAULT_CONFIG)
    wire = WireConnection(
        wire_label=wire_label,
        from_ref='J1',
        to_ref='SW1',
        wire_gauge=wire_gauge,
        wire_color='White',  # Default for Unknown
        length=length,
        wire_type='Standard',
        warnings=['Unknown system code - manual verification required'] if system_code == 'U' else []
    )
    bom.add_wire(wire)

    assert len(bom.wires) == 1

    # 8. Write CSV output
    output_file = tmp_path / "fixture_01_output.csv"
    write_builder_csv(bom, output_file)

    # Verify CSV contents
    assert output_file.exists()

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]

    # Verify all fields
    assert row['Wire Label'] == 'U-1-A'
    assert row['From'] == 'J1'
    assert row['To'] == 'SW1'
    assert int(row['Wire Gauge']) in [12, 16, 18, 20]
    assert row['Wire Color'] == 'White'
    assert float(row['Length']) == 79.0
    assert row['Wire Type'] == 'Standard'
    assert 'Unknown system code' in row['Warnings']

    print("\n=== FIXTURE 01 INTEGRATION TEST PASSED ===")
    print(f"Generated wire: {row['Wire Label']}")
    print(f"  From {row['From']} to {row['To']}")
    print(f"  AWG {row['Wire Gauge']}, {row['Wire Color']}, {row['Length']} inches")
    print(f"  Warnings: {row['Warnings']}")
