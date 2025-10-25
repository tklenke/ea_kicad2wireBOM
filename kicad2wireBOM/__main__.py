# ABOUTME: Command line entry point for kicad2wireBOM
# ABOUTME: Orchestrates conversion of KiCad schematic files to wire BOM CSV

import argparse
import sys
import os
from pathlib import Path

from kicad2wireBOM.parser import (
    parse_schematic_file,
    parse_schematic_hierarchical,
    extract_wires,
    extract_labels,
    extract_symbols,
    extract_sheets,
    parse_wire_element,
    parse_label_element,
    parse_symbol_element
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.wire_calculator import calculate_length, determine_min_gauge
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG, SYSTEM_COLOR_MAP
from kicad2wireBOM.graph_builder import build_connectivity_graph, build_connectivity_graph_hierarchical
from kicad2wireBOM.bom_generator import generate_bom_entries
from kicad2wireBOM.validator import SchematicValidator, HierarchicalValidator


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

    parser.add_argument(
        '--permissive',
        action='store_true',
        help='Permissive mode: warn about validation errors but continue processing (default: strict mode aborts on errors)'
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
        # First, check if this is a hierarchical schematic
        sexp_check = parse_schematic_file(args.source)
        sheet_elements = extract_sheets(sexp_check)
        is_hierarchical = len(sheet_elements) > 0

        if is_hierarchical:
            print(f"  Detected hierarchical schematic with {len(sheet_elements)} sub-sheets")

            # Parse hierarchical schematic
            hierarchical_schematic = parse_schematic_hierarchical(args.source)

            # Collect all wires, labels, components from all sheets
            all_wires = []
            all_labels = []
            all_components = []

            # Process root sheet
            all_wires.extend(hierarchical_schematic.root_sheet.wire_segments)
            all_labels.extend(hierarchical_schematic.root_sheet.labels)
            all_components.extend(hierarchical_schematic.root_sheet.components)

            # Process sub-sheets
            for sheet_uuid, sheet in hierarchical_schematic.sub_sheets.items():
                all_wires.extend(sheet.wire_segments)
                all_labels.extend(sheet.labels)
                all_components.extend(sheet.components)

            print(f"  Found {len(all_wires)} wire segments across all sheets")
            print(f"  Found {len(all_labels)} labels across all sheets")
            print(f"  Found {len(all_components)} components across all sheets")

            wires = all_wires
            labels = all_labels
            components = all_components

            # Build connectivity graph (hierarchical)
            print(f"  Building hierarchical connectivity graph...")
            graph = build_connectivity_graph_hierarchical(hierarchical_schematic)
            print(f"    Graph has {len(graph.nodes)} nodes, {len(graph.component_pins)} pins, {len(graph.junctions)} junctions")

        else:
            print(f"  Detected single-sheet schematic")

            # Parse single-sheet schematic (existing code path)
            sexp = sexp_check

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

            # Parse components (may fail if LocLoad encodings missing)
            components = []
            for s in symbol_sexps:
                try:
                    components.append(parse_symbol_element(s))
                except ValueError as e:
                    # Component missing LocLoad encoding - skip for BOM but continue for connectivity
                    print(f"  Warning: {e} (skipping for BOM calculations)")
                    pass

            # Build connectivity graph (single-sheet)
            print(f"  Building connectivity graph...")
            graph = build_connectivity_graph(sexp)
            print(f"    Graph has {len(graph.nodes)} nodes, {len(graph.component_pins)} pins, {len(graph.junctions)} junctions")

        # Associate labels with wires (same for both paths)
        associate_labels_with_wires(wires, labels, threshold=args.label_threshold)

        # Count labeled wires
        labeled_wires = [w for w in wires if w.circuit_id]
        print(f"  Associated {len(labeled_wires)} wires with labels")

        # Validate schematic
        strict_mode = not args.permissive
        if is_hierarchical:
            # Use hierarchical validator with connectivity graph for cross-sheet validation
            validator = HierarchicalValidator(strict_mode=strict_mode, connectivity_graph=graph)
        else:
            validator = SchematicValidator(strict_mode=strict_mode)
        validation_result = validator.validate_all(wires, labels, components)

        # Handle validation errors/warnings
        if validation_result.has_errors():
            print("\nValidation Errors:", file=sys.stderr)
            for error in validation_result.errors:
                print(f"  ERROR: {error.message}", file=sys.stderr)
                if error.suggestion:
                    print(f"         Suggestion: {error.suggestion}", file=sys.stderr)
            sys.exit(1)

        if validation_result.warnings:
            print("\nValidation Warnings:")
            for warning in validation_result.warnings:
                print(f"  WARNING: {warning.message}")
                if warning.suggestion:
                    print(f"           Suggestion: {warning.suggestion}")

        # Generate BOM entries (handles both multipoint and regular)
        print(f"  Generating BOM entries...")
        bom_entries = generate_bom_entries(wires, graph)
        print(f"    Generated {len(bom_entries)} BOM entries")

        # Create component lookup map
        comp_map = {comp.ref: comp for comp in components}

        # Create wire lookup map (for system_code)
        wire_map = {wire.circuit_id: wire for wire in wires if wire.circuit_id}

        # Build wire BOM
        bom = WireBOM(config=DEFAULT_CONFIG)

        # For each BOM entry, calculate wire properties
        for entry in bom_entries:
            circuit_id = entry['circuit_id']
            from_component = entry['from_component']
            from_pin = entry['from_pin']
            to_component = entry['to_component']
            to_pin = entry['to_pin']

            # Look up components
            comp1 = comp_map.get(from_component) if from_component else None
            comp2 = comp_map.get(to_component) if to_component else None

            # Calculate wire length (if we have both components)
            if comp1 and comp2:
                length = calculate_length(comp1, comp2, slack=args.slack_length)
            else:
                # Use wire segment length as fallback
                import math
                dx = wire.end_point[0] - wire.start_point[0]
                dy = wire.end_point[1] - wire.start_point[1]
                length_mm = math.sqrt(dx*dx + dy*dy)
                length = length_mm / 25.4  # Convert mm to inches
                length += args.slack_length

            # Determine current (use load if available)
            current = 0.0
            if comp1 and comp1.is_load:
                current = comp1.load
            elif comp2 and comp2.is_load:
                current = comp2.load
            elif comp1 and comp1.source:
                current = comp1.source
            elif comp2 and comp2.source:
                current = comp2.source

            # Determine wire gauge
            gauge = determine_min_gauge(current, length, args.system_voltage)

            # Get wire color from system code (lookup wire by circuit_id)
            wire = wire_map.get(circuit_id)
            system_code = wire.system_code if wire else None
            wire_color = SYSTEM_COLOR_MAP.get(system_code, 'White')

            # Get notes from BOM entry
            notes = entry.get('notes', '')

            # Create wire connection
            wire_conn = WireConnection(
                wire_label=circuit_id,
                from_component=from_component,
                from_pin=from_pin,
                to_component=to_component,
                to_pin=to_pin,
                wire_gauge=gauge,
                wire_color=wire_color,
                length=length,
                wire_type=DEFAULT_CONFIG['default_wire_type'],
                notes=notes,
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
