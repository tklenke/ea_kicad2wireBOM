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
    Integration test for fixture 01: BT1 to L1 minimal circuit.

    Validates complete pipeline:
    1. Parse netlist
    2. Extract components with coordinates (including Source type)
    3. Calculate wire length
    4. Determine wire gauge
    5. Detect system code
    6. Generate wire label
    7. Create BOM
    8. Write CSV output
    """
    # 1. Parse netlist
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_01.net"
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
        source = encoding['amperage'] if encoding['type'] == 'S' else None

        comp = Component(
            ref=comp_raw['ref'],
            fs=encoding['fs'],
            wl=encoding['wl'],
            bl=encoding['bl'],
            load=load,
            rating=rating,
            source=source
        )
        components.append(comp)

    bt1 = next(c for c in components if c.ref == 'BT1')
    l1 = next(c for c in components if c.ref == 'L1')

    # 3. Calculate wire length
    slack = DEFAULT_CONFIG['slack_length']
    length = calculate_length(bt1, l1, slack)

    # BT1: (10, 0, 0), L1: (20, 0, 0)
    # Manhattan: |20-10| + |0-0| + |0-0| = 10
    # Plus slack: 10 + 24 = 34
    assert length == 34.0

    # 4. Determine wire gauge
    # L1 is a load drawing 1.5A
    current = l1.load
    system_voltage = DEFAULT_CONFIG['system_voltage']
    wire_gauge = determine_min_gauge(current, length, system_voltage)

    # Should select appropriate gauge for 1.5A over 34 inches
    assert wire_gauge in [18, 20, 22]

    # 5. Detect system code
    system_code = detect_system_code([bt1, l1], "/P1A")

    # Should detect Power system from net name /P1A
    assert system_code == 'P'

    # 6. Generate wire label
    wire_label = generate_wire_label(system_code, '1', 'A')
    assert wire_label == 'P-1-A'

    # 7. Create BOM
    bom = WireBOM(config=DEFAULT_CONFIG)
    wire = WireConnection(
        wire_label=wire_label,
        from_ref='BT1',
        to_ref='L1',
        wire_gauge=wire_gauge,
        wire_color='Red',  # Power system color
        length=length,
        wire_type='Standard',
        warnings=[]
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
    assert row['Wire Label'] == 'P-1-A'
    assert row['From'] == 'BT1'
    assert row['To'] == 'L1'
    assert int(row['Wire Gauge']) in [18, 20, 22]
    assert row['Wire Color'] == 'Red'
    assert float(row['Length']) == 34.0
    assert row['Wire Type'] == 'Standard'

    print("\n=== FIXTURE 01 INTEGRATION TEST PASSED ===")
    print(f"Generated wire: {row['Wire Label']}")
    print(f"  From {row['From']} to {row['To']}")
    print(f"  AWG {row['Wire Gauge']}, {row['Wire Color']}, {row['Length']} inches")
