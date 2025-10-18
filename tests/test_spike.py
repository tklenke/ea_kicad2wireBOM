# ABOUTME: Spike integration test for Phase 0
# ABOUTME: Validates end-to-end parsing of test fixture 01 and data extraction

from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file, extract_nets, extract_components, parse_footprint_encoding
from kicad2wireBOM.component import Component


def test_spike_integration():
    """
    Spike test: Parse test_fixture_01.net and extract all data.

    This test validates:
    - KiCad netlist parsing works
    - Net codes can be extracted
    - Component refs can be extracted
    - Footprint encoding can be parsed (including S type for source)
    - Coordinates and load/rating/source values are extracted correctly
    """
    fixture_path = Path(__file__).parent / "fixtures" / "test_fixture_01.net"

    # Parse netlist
    parsed = parse_netlist_file(fixture_path)
    assert parsed is not None

    # Extract nets
    nets = extract_nets(parsed)
    print("\n=== NETS ===")
    for net in nets:
        print(f"Net {net['code']}: {net['name']} (class: {net['class']})")

    assert len(nets) == 2  # /P1A and /G1A

    # Extract components
    components_raw = extract_components(parsed)
    print("\n=== COMPONENTS (Raw) ===")
    for comp in components_raw:
        print(f"{comp['ref']}: {comp['footprint']}")

    assert len(components_raw) == 2  # BT1 and L1

    # Parse footprint encoding and create Component objects
    components = []
    print("\n=== COMPONENTS (Parsed) ===")
    for comp_raw in components_raw:
        encoding = parse_footprint_encoding(comp_raw['footprint'])
        assert encoding is not None, f"Failed to parse encoding for {comp_raw['ref']}"

        # Determine load/rating/source based on type
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

        print(f"{comp.ref}:")
        print(f"  Coordinates: {comp.coordinates}")
        if comp.is_source:
            print(f"  Type: Source")
            print(f"  Value: {comp.source}A")
        elif comp.is_load:
            print(f"  Type: Load")
            print(f"  Value: {comp.load}A")
        elif comp.is_passthrough:
            print(f"  Type: Pass-through")
            print(f"  Value: {comp.rating}A")

    # Verify BT1 (battery with source)
    bt1 = next(c for c in components if c.ref == 'BT1')
    assert bt1.fs == 10.0
    assert bt1.wl == 0.0
    assert bt1.bl == 0.0
    assert bt1.source == 40.0
    assert bt1.load is None
    assert bt1.rating is None
    assert bt1.is_source is True
    assert bt1.is_load is False
    assert bt1.is_passthrough is False

    # Verify L1 (lamp with load)
    l1 = next(c for c in components if c.ref == 'L1')
    assert l1.fs == 20.0
    assert l1.wl == 0.0
    assert l1.bl == 0.0
    assert l1.load == 1.5
    assert l1.rating is None
    assert l1.source is None
    assert l1.is_load is True
    assert l1.is_source is False
    assert l1.is_passthrough is False

    print("\n=== SPIKE TEST PASSED ===")
    print(" Netlist parsing works")
    print(" Net extraction works")
    print(" Component extraction works")
    print(" Footprint encoding parsing works")
    print(" Component data model works")
