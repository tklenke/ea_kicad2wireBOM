# ABOUTME: Command line entry point for kicad2wireBOM
# ABOUTME: Orchestrates conversion of KiCad schematic files to wire BOM CSV

import argparse
import sys
import os
from pathlib import Path

from kicad2wireBOM.parser import (
    parse_schematic_file,
    extract_wires,
    extract_labels,
    extract_symbols,
    parse_wire_element,
    parse_label_element,
    parse_symbol_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.wire_calculator import calculate_length, determine_min_gauge
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG, SYSTEM_COLOR_MAP


def main():
    """Main entry point for kicad2wireBOM command line tool"""
    parser = argparse.ArgumentParser(
        prog='kicad2wireBOM',
        description='Convert KiCad schematic files to wire BOM CSV format. '
                    'Processes wire harness schematics from experimental aircraft (EA) '
                    'projects and generates a Bill of Materials for wire connections.'
    )

    parser.add_argument(
        'source',
        help='Input KiCad schematic file (.kicad_sch)'
    )

    parser.add_argument(
        'dest',
        nargs='?',
        help='Output CSV file (optional, auto-generated if not provided)'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force overwrite of existing destination file without prompting'
    )

    parser.add_argument(
        '--label-threshold',
        type=float,
        default=DEFAULT_CONFIG['label_threshold'],
        help=f'Maximum distance (mm) for label-to-wire association (default: {DEFAULT_CONFIG["label_threshold"]}mm)'
    )

    parser.add_argument(
        '--slack-length',
        type=float,
        default=DEFAULT_CONFIG['slack_length'],
        help=f'Extra wire length in inches (default: {DEFAULT_CONFIG["slack_length"]}")'
    )

    parser.add_argument(
        '--system-voltage',
        type=float,
        default=DEFAULT_CONFIG['system_voltage'],
        help=f'System voltage in volts (default: {DEFAULT_CONFIG["system_voltage"]}V)'
    )

    args = parser.parse_args()

    # Check if source file exists
    if not os.path.exists(args.source):
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1

    # Auto-generate destination if not provided
    if not args.dest:
        source_path = Path(args.source)
        args.dest = str(source_path.with_suffix('.csv'))

    # Check if destination exists and prompt if needed
    if os.path.exists(args.dest) and not args.force:
        response = input(f"Destination file '{args.dest}' already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.", file=sys.stderr)
            return 1

    # Process the schematic
    print(f"Processing {args.source}...")

    try:
        # Parse schematic
        sexp = parse_schematic_file(args.source)

        # Extract elements
        wire_sexps = extract_wires(sexp)
        label_sexps = extract_labels(sexp)
        symbol_sexps = extract_symbols(sexp)

        print(f"  Found {len(wire_sexps)} wire segments")
        print(f"  Found {len(label_sexps)} labels")
        print(f"  Found {len(symbol_sexps)} components")

        # Convert to data objects
        wires = [parse_wire_element(w) for w in wire_sexps]
        labels = [parse_label_element(l) for l in label_sexps]
        components = [parse_symbol_element(s) for s in symbol_sexps]

        # Associate labels with wires
        associate_labels_with_wires(wires, labels, threshold=args.label_threshold)

        # Count labeled wires
        labeled_wires = [w for w in wires if w.circuit_id]
        print(f"  Associated {len(labeled_wires)} wires with labels")

        # Create component lookup map
        comp_map = {comp.ref: comp for comp in components}

        # Build wire BOM
        bom = WireBOM(config=DEFAULT_CONFIG)

        # For each labeled wire, create a wire connection
        # Note: This is simplified - assumes wire connects two adjacent components
        # A more complete implementation would trace wire connectivity through junctions
        for wire in wires:
            if not wire.circuit_id:
                continue  # Skip unlabeled wires

            # For now, we need to determine which components this wire connects
            # This is a simplified approach - real implementation would trace connectivity
            # TODO: Implement proper wire-to-component endpoint matching

            # As a simple heuristic: if we have 2 components, connect them
            if len(components) >= 2:
                comp1 = components[0]
                comp2 = components[1]

                # Calculate wire length
                length = calculate_length(comp1, comp2, slack=args.slack_length)

                # Determine current (use load if available)
                current = 0.0
                if comp1.is_load:
                    current = comp1.load
                elif comp2.is_load:
                    current = comp2.load
                elif comp1.source:
                    current = comp1.source
                elif comp2.source:
                    current = comp2.source

                # Determine wire gauge
                gauge = determine_min_gauge(current, length, args.system_voltage)

                # Get wire color from system code
                wire_color = SYSTEM_COLOR_MAP.get(wire.system_code, 'White')

                # Create wire connection
                wire_conn = WireConnection(
                    wire_label=wire.circuit_id,
                    from_ref=comp1.ref,
                    to_ref=comp2.ref,
                    wire_gauge=gauge,
                    wire_color=wire_color,
                    length=length,
                    wire_type=DEFAULT_CONFIG['default_wire_type'],
                    warnings=[]
                )

                bom.add_wire(wire_conn)

        # Write output
        write_builder_csv(bom, args.dest)

        print(f"\nSuccessfully generated wire BOM: {args.dest}")
        print(f"  Total wires: {len(bom.wires)}")

        return 0

    except Exception as e:
        print(f"Error processing schematic: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
