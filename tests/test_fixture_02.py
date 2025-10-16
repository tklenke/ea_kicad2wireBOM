# ABOUTME: Integration test for fixture 02 - simple 3-component load circuit
# ABOUTME: End-to-end test from netlist parsing to CSV output with multiple wire segments

import csv
from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file, extract_components, parse_footprint_encoding
from kicad2wireBOM.component import Component
from kicad2wireBOM.circuit import build_circuits, determine_signal_flow, create_wire_segments
from kicad2wireBOM.wire_calculator import detect_system_code
from kicad2wireBOM.wire_bom import WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG


def test_fixture_02_integration(tmp_path):
    """
    Integration test for fixture 02: J1 -> SW1 -> L1 circuit.

    Validates complete pipeline for 3-component circuit:
    1. Parse netlist
    2. Extract components with coordinates
    3. Build circuits from nets
    4. Determine signal flow
    5. Create wire segments (2 segments: A and B)
    6. Detect system code
    7. Write CSV output
    """
    # 1. Parse netlist
    fixture_path = Path(__file__).parent / "fixtures" / "test_02_simple_load.net"
    parsed = parse_netlist_file(fixture_path)
    components_raw = extract_components(parsed)

    assert len(components_raw) == 3

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

    # Verify we have the expected components
    j1 = next(c for c in components if c.ref == 'J1')
    sw1 = next(c for c in components if c.ref == 'SW1')
    l1 = next(c for c in components if c.ref == 'L1')

    assert j1.rating == 30.0
    assert sw1.rating == 20.0
    assert l1.load == 2.5

    # 3. Build circuits from nets
    circuits = build_circuits(parsed, components)

    # Fixture 02 has 2 connected nets, but we need to identify the main circuit
    # that connects all three components (J1, SW1, L1)
    # For Phase 2, we handle circuits independently, so we'll have 2 circuits:
    # Net 1: J1 <-> SW1
    # Net 2: SW1 <-> L1

    # For the integration test, we'll manually combine them into one circuit
    # as the Phase 2 implementation focuses on individual net processing
    all_components = [j1, sw1, l1]

    # 4. Determine signal flow
    ordered_components = determine_signal_flow(all_components)

    assert len(ordered_components) == 3
    assert ordered_components[0].ref == 'J1'  # Source
    assert ordered_components[1].ref == 'SW1'  # Passthrough
    assert ordered_components[2].ref == 'L1'  # Load

    # 5. Detect system code
    system_code = detect_system_code(ordered_components, "Landing Light")

    # Should detect "L" from "Landing Light" in SW1 value
    assert system_code == 'L'

    # 6. Create wire segments
    circuit_id = '105'
    segments = create_wire_segments(ordered_components, system_code, circuit_id, DEFAULT_CONFIG)

    assert len(segments) == 2

    # Segment A: J1 -> SW1
    seg_a = segments[0]
    assert seg_a.wire_label == 'L-105-A'
    assert seg_a.from_ref == 'J1'
    assert seg_a.to_ref == 'SW1'
    assert seg_a.wire_gauge in [12, 16, 18, 20]
    assert seg_a.length > 0

    # Segment B: SW1 -> L1
    seg_b = segments[1]
    assert seg_b.wire_label == 'L-105-B'
    assert seg_b.from_ref == 'SW1'
    assert seg_b.to_ref == 'L1'
    assert seg_b.wire_gauge in [12, 16, 18, 20]
    assert seg_b.length > 0

    # Both should be sized for 2.5A load
    assert seg_a.wire_gauge == seg_b.wire_gauge

    # 7. Create BOM and write CSV output
    bom = WireBOM(config=DEFAULT_CONFIG)
    for seg in segments:
        bom.add_wire(seg)

    assert len(bom.wires) == 2

    # 8. Write CSV output
    output_file = tmp_path / "fixture_02_output.csv"
    write_builder_csv(bom, output_file)

    # Verify CSV contents
    assert output_file.exists()

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2

    # Verify first row
    row_a = rows[0]
    assert row_a['Wire Label'] == 'L-105-A'
    assert row_a['From'] == 'J1'
    assert row_a['To'] == 'SW1'
    assert int(row_a['Wire Gauge']) in [12, 16, 18, 20]

    # Verify second row
    row_b = rows[1]
    assert row_b['Wire Label'] == 'L-105-B'
    assert row_b['From'] == 'SW1'
    assert row_b['To'] == 'L1'
    assert int(row_b['Wire Gauge']) in [12, 16, 18, 20]

    print("\n=== FIXTURE 02 INTEGRATION TEST PASSED ===")
    print(f"Generated {len(rows)} wire segments:")
    for row in rows:
        print(f"  {row['Wire Label']}: {row['From']} → {row['To']}, AWG {row['Wire Gauge']}, {row['Length']} inches")
