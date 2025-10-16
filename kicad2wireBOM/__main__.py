# ABOUTME: Command line entry point for kicad2wireBOM
# ABOUTME: Parses arguments and orchestrates conversion of KiCad netlist to wire BOM CSV

import argparse
import sys
import os
from pathlib import Path

from kicad2wireBOM.parser import parse_netlist_file, extract_components, parse_footprint_encoding
from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_calculator import calculate_length, determine_min_gauge, detect_system_code, generate_wire_label
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG


def main():
    """Main entry point for kicad2wireBOM command line tool"""
    parser = argparse.ArgumentParser(
        prog='kicad2wireBOM',
        description='Convert KiCad v9 netlist files to wire BOM CSV format. '
                    'Processes wire harness schematics from experimental aircraft (EA) '
                    'projects and generates a Bill of Materials for wire connections.'
    )

    parser.add_argument(
        'source',
        help='Input KiCad netlist file (.net or .xml)'
    )

    parser.add_argument(
        'dest',
        help='Output CSV file'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force overwrite of existing destination file without prompting'
    )

    args = parser.parse_args()

    # Check if source file exists
    if not os.path.exists(args.source):
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1

    # Check if destination exists and prompt if needed
    if os.path.exists(args.dest) and not args.force:
        response = input(f"Destination file '{args.dest}' already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.", file=sys.stderr)
            return 1

    # Process the netlist
    print(f"Processing {args.source}...")

    try:
        # Parse netlist
        parsed = parse_netlist_file(args.source)
        components_raw = extract_components(parsed)

        # Extract components with coordinates
        components = []
        for comp_raw in components_raw:
            encoding = parse_footprint_encoding(comp_raw['footprint'])
            if encoding is None:
                print(f"Warning: No footprint encoding found for {comp_raw['ref']}", file=sys.stderr)
                continue

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

        if len(components) < 2:
            print("Error: Need at least 2 components to generate wire BOM", file=sys.stderr)
            return 1

        # For Phase 1: Simple two-component circuit
        # In future phases, this will handle multiple circuits
        comp1 = components[0]
        comp2 = components[1]

        # Calculate wire specs
        slack = DEFAULT_CONFIG['slack_length']
        length = calculate_length(comp1, comp2, slack)

        # Determine current (use minimum rating for now)
        current = min(comp1.rating or 0, comp2.rating or 0)
        if current == 0:
            current = max(comp1.load or 0, comp2.load or 0)

        system_voltage = DEFAULT_CONFIG['system_voltage']
        wire_gauge = determine_min_gauge(current, length, system_voltage)

        # Detect system and generate label
        system_code = detect_system_code(components, "circuit-1")
        wire_label = generate_wire_label(system_code, '1', 'A')

        # Create BOM
        bom = WireBOM(config=DEFAULT_CONFIG)
        warnings = []
        if system_code == 'U':
            warnings.append('Unknown system code - manual verification required')

        wire = WireConnection(
            wire_label=wire_label,
            from_ref=comp1.ref,
            to_ref=comp2.ref,
            wire_gauge=wire_gauge,
            wire_color='White',  # Default for Phase 1
            length=length,
            wire_type='Standard',
            warnings=warnings
        )
        bom.add_wire(wire)

        # Write output
        write_builder_csv(bom, args.dest)

        print(f"Successfully generated wire BOM: {args.dest}")
        print(f"  Wires: {len(bom.wires)}")
        return 0

    except Exception as e:
        print(f"Error processing netlist: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
