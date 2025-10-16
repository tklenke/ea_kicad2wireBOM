# ABOUTME: Spike integration test for Phase 0
# ABOUTME: Validates end-to-end parsing of test fixture 01 and data extraction

from pathlib import Path
from kicad2wireBOM.parser import parse_netlist_file, extract_nets, extract_components, parse_footprint_encoding
from kicad2wireBOM.component import Component


def test_spike_integration():
    """
    Spike test: Parse test_01_minimal_two_component.net and extract all data.

    This test validates:
    - KiCad netlist parsing works
    - Net codes can be extracted
    - Component refs can be extracted
    - Footprint encoding can be parsed
    - Coordinates and load/rating values are extracted correctly
    """
    fixture_path = Path(__file__).parent / "fixtures" / "test_01_minimal_two_component.net"

    # Parse netlist
    parsed = parse_netlist_file(fixture_path)
    assert parsed is not None

    # Extract nets
    nets = extract_nets(parsed)
    print("\n=== NETS ===")
    for net in nets:
        print(f"Net {net['code']}: {net['name']} (class: {net['class']})")

    assert len(nets) == 4  # 4 nets in the fixture

    # Extract components
    components_raw = extract_components(parsed)
    print("\n=== COMPONENTS (Raw) ===")
    for comp in components_raw:
        print(f"{comp['ref']}: {comp['footprint']}")

    assert len(components_raw) == 2  # J1 and SW1

    # Parse footprint encoding and create Component objects
    components = []
    print("\n=== COMPONENTS (Parsed) ===")
    for comp_raw in components_raw:
        encoding = parse_footprint_encoding(comp_raw['footprint'])
        assert encoding is not None, f"Failed to parse encoding for {comp_raw['ref']}"

        # Determine load vs rating based on type
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

        print(f"{comp.ref}:")
        print(f"  Coordinates: {comp.coordinates}")
        print(f"  Type: {'Load' if comp.is_load else 'Pass-through'}")
        print(f"  Value: {comp.load if comp.is_load else comp.rating}A")

    # Verify J1 (connector with rating)
    j1 = next(c for c in components if c.ref == 'J1')
    assert j1.fs == 100.0
    assert j1.wl == 25.0
    assert j1.bl == 0.0
    assert j1.rating == 15.0
    assert j1.load is None
    assert j1.is_passthrough is True
    assert j1.is_load is False

    # Verify SW1 (switch with rating)
    sw1 = next(c for c in components if c.ref == 'SW1')
    assert sw1.fs == 150.0
    assert sw1.wl == 30.0
    assert sw1.bl == 0.0
    assert sw1.rating == 20.0
    assert sw1.load is None
    assert sw1.is_passthrough is True
    assert sw1.is_load is False

    print("\n=== SPIKE TEST PASSED ===")
    print(" Netlist parsing works")
    print(" Net extraction works")
    print(" Component extraction works")
    print(" Footprint encoding parsing works")
    print(" Component data model works")
