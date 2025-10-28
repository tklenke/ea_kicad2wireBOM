# ABOUTME: Command line entry point for kicad2wireBOM
# ABOUTME: Orchestrates conversion of KiCad schematic files to wire BOM CSV

import argparse
import re
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
    parse_symbol_element,
    parse_title_block
)
from kicad2wireBOM.label_association import associate_labels_with_wires
from kicad2wireBOM.wire_calculator import (
    calculate_length,
    determine_min_gauge,
    group_wires_by_circuit,
    determine_circuit_current
)
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv
from kicad2wireBOM.reference_data import DEFAULT_CONFIG, SYSTEM_COLOR_MAP
from kicad2wireBOM.graph_builder import build_connectivity_graph, build_connectivity_graph_hierarchical
from kicad2wireBOM.bom_generator import generate_bom_entries
from kicad2wireBOM.validator import SchematicValidator, HierarchicalValidator
from kicad2wireBOM.output_manager import create_output_directory, capture_output
from kicad2wireBOM.output_component_bom import write_component_bom
from kicad2wireBOM.output_engineering_report import write_engineering_report
from kicad2wireBOM.output_html_index import write_html_index


def should_swap_components(comp1, comp2) -> bool:
    """
    Return True if comp1 and comp2 should be swapped in wire connection.

    Determines component order based on aircraft coordinate system:
    1. Priority 1: Largest abs(BL) first (furthest from centerline)
    2. Priority 2: Largest FS first (furthest aft) if BL equal
    3. Priority 3: Largest WL first (topmost) if BL and FS equal
    4. Equal on all: keep current order (return False)

    Args:
        comp1: First component (or None)
        comp2: Second component (or None)

    Returns:
        True if components should be swapped (comp2 should be FROM), False otherwise
    """
    # Handle missing components
    if not comp1 or not comp2:
        return False

    # Priority 1: abs(BL) - furthest from centerline first
    abs_bl1 = abs(comp1.bl)
    abs_bl2 = abs(comp2.bl)
    if abs_bl1 != abs_bl2:
        return abs_bl2 > abs_bl1  # Swap if comp2 further from centerline

    # Priority 2: FS - furthest aft first
    if comp1.fs != comp2.fs:
        return comp2.fs > comp1.fs  # Swap if comp2 further aft

    # Priority 3: WL - topmost first
    if comp1.wl != comp2.wl:
        return comp2.wl > comp1.wl  # Swap if comp2 higher

    # Equal on all coordinates - keep current order
    return False


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
        help='Output directory (optional, defaults to current directory)'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force overwrite of existing output directory without prompting'
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

    parser.add_argument(
        '--3d',
        dest='three_d',
        action='store_true',
        help='Generate 3D diagrams with WL axis projection (default: 2D diagrams with FS/BL only)'
    )

    args = parser.parse_args()

    # Check if source file exists
    if not os.path.exists(args.source):
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1

    # Create output directory
    output_dir = create_output_directory(args.source, args.dest, force=args.force)

    # Wrap processing in capture_output context manager to tee stdout/stderr to files
    with capture_output(output_dir):
        # Process the schematic
        print(f"Processing {args.source}...")

        try:
            # First, check if this is a hierarchical schematic
            sexp_check = parse_schematic_file(args.source)
            sheet_elements = extract_sheets(sexp_check)
            is_hierarchical = len(sheet_elements) > 0

            # Parse title_block (applies to all schematics)
            title_block = parse_title_block(sexp_check)
            if title_block:
                print(f"  Project: {title_block.get('title', 'Untitled')} Rev {title_block.get('rev', 'N/A')} ({title_block.get('date', 'N/A')})")

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
                missing_locload_components = []  # TODO: Handle hierarchical missing LocLoad

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
                missing_locload_components = []
                for s in symbol_sexps:
                    try:
                        components.append(parse_symbol_element(s))
                    except ValueError as e:
                        # Component missing LocLoad encoding - track for validation
                        # Extract component reference from error message "Component {ref} missing LocLoad encoding"
                        match = re.search(r'Component (\S+) missing', str(e))
                        if match:
                            missing_locload_components.append(match.group(1))
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
                # Use flat validator with connectivity graph for enhanced error messages
                validator = SchematicValidator(strict_mode=strict_mode, connectivity_graph=graph)
            validation_result = validator.validate_all(wires, labels, components, missing_locload_components)

            # Handle validation errors/warnings
            if validation_result.has_errors():
                print("\nValidation Errors:", file=sys.stderr)
                for error in validation_result.errors:
                    print(f"  ERROR: {error.message}", file=sys.stderr)
                    if error.suggestion:
                        print(f"         Suggestion: {error.suggestion}", file=sys.stderr)

                # Create index.html before exiting so user can access logs
                print("\nWriting index.html with error logs...", file=sys.stderr)
                index_path = str(output_dir / 'index.html')
                write_html_index(output_dir, index_path, title_block)
                print(f"See {index_path} for details", file=sys.stderr)

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

            # FIRST PASS: Create all WireConnection objects with placeholder gauge
            # (gauge will be determined by circuit-based calculation after grouping)
            for entry in bom_entries:
                circuit_id = entry['circuit_id']
                from_component = entry['from_component']
                from_pin = entry['from_pin']
                to_component = entry['to_component']
                to_pin = entry['to_pin']

                # Look up components
                comp1 = comp_map.get(from_component) if from_component else None
                comp2 = comp_map.get(to_component) if to_component else None

                # Look up wire segment for this circuit (needed for color and fallback length)
                wire = wire_map.get(circuit_id)

                # Calculate wire length (if we have both components)
                if comp1 and comp2:
                    length = calculate_length(comp1, comp2, slack=args.slack_length)
                else:
                    # Use wire segment length as fallback
                    import math
                    if wire:
                        dx = wire.end_point[0] - wire.start_point[0]
                        dy = wire.end_point[1] - wire.start_point[1]
                        length_mm = math.sqrt(dx*dx + dy*dy)
                        length = length_mm / 25.4  # Convert mm to inches
                        length += args.slack_length
                    else:
                        # No wire found and no components - use default length
                        length = 12.0 + args.slack_length  # Default 12" + slack

                # Get wire color from system code
                system_code = wire.system_code if wire else None
                wire_color = SYSTEM_COLOR_MAP.get(system_code, 'White')

                # Get notes from BOM entry
                notes = entry.get('notes', '')

                # Order components by aircraft coordinates (furthest from centerline first)
                if should_swap_components(comp1, comp2):
                    # Swap components
                    from_component, to_component = to_component, from_component
                    from_pin, to_pin = to_pin, from_pin

                # Create wire connection with placeholder gauge (-99)
                # Actual gauge will be determined by circuit-based calculation
                wire_conn = WireConnection(
                    wire_label=circuit_id,
                    from_component=from_component,
                    from_pin=from_pin,
                    to_component=to_component,
                    to_pin=to_pin,
                    wire_gauge=-99,  # Placeholder - will be updated by circuit-based sizing
                    wire_color=wire_color,
                    length=length,
                    wire_type=DEFAULT_CONFIG['default_wire_type'],
                    notes=notes,
                    warnings=[]
                )

                bom.add_wire(wire_conn)

            # SECOND PASS: Circuit-based wire gauge calculation
            # Group wires by circuit_id (e.g., L1, L2, G1)
            circuit_groups = group_wires_by_circuit(bom.wires)

            # For each circuit, determine total current and calculate gauge
            circuit_gauges = {}  # {circuit_id: gauge}
            for circuit_id, circuit_wires in circuit_groups.items():
                # Determine total circuit current
                circuit_current = determine_circuit_current(circuit_wires, components, graph)

                # Find longest wire in circuit (for voltage drop calculation)
                max_length = max(wire.length for wire in circuit_wires)

                # Determine gauge for entire circuit
                gauge = determine_min_gauge(circuit_current, max_length, args.system_voltage)
                circuit_gauges[circuit_id] = gauge

            # THIRD PASS: Apply circuit gauge to each wire and add warnings for missing data
            for wire in bom.wires:
                # Extract circuit_id from wire label (e.g., "L-1-A" → "L1")
                from kicad2wireBOM.wire_calculator import parse_net_name
                parsed = parse_net_name(f"/{wire.wire_label}")
                if parsed:
                    circuit_id = f"{parsed['system']}{parsed['circuit']}"
                    wire.wire_gauge = circuit_gauges.get(circuit_id, -99)

                    # Add warning if gauge is -99 (missing load/source data)
                    if wire.wire_gauge == -99:
                        wire.warnings.append("Cannot determine circuit current - missing load/source data")

            # Sort BOM by system code, circuit number, segment letter
            def parse_wire_label_for_sort(label):
                """Parse wire label to extract system_code, circuit_num, segment_letter for sorting"""
                pattern = r'^([A-Z])-?(\d+)-?([A-Z])$'
                match = re.match(pattern, label)
                if match:
                    system_code = match.group(1)
                    circuit_num = int(match.group(2))
                    segment_letter = match.group(3)
                    return (system_code, circuit_num, segment_letter)
                return ('', 0, '')  # Fallback for invalid labels

            bom.wires.sort(key=lambda w: parse_wire_label_for_sort(w.wire_label))

            # Write wire BOM CSV to output directory
            write_builder_csv(bom, str(output_dir / 'wire_bom.csv'), title_block)

            print(f"\nSuccessfully generated wire BOM: {output_dir / 'wire_bom.csv'}")
            print(f"  Total wires: {len(bom.wires)}")

            # Always generate routing diagrams (Phase 11: diagrams always generated)
            from kicad2wireBOM.diagram_generator import generate_routing_diagrams

            # Convert components list to dict
            components_dict = {comp.ref: comp for comp in components}

            # Generate diagrams
            diagram_mode = "3D (FS/WL/BL projection)" if args.three_d else "2D (FS/BL only)"
            print(f"\nGenerating routing diagrams ({diagram_mode})...")
            generate_routing_diagrams(bom.wires, components_dict, output_dir, title_block, use_2d=not args.three_d)

            # Generate component BOM
            print(f"\nGenerating component BOM...")
            write_component_bom(components, str(output_dir / 'component_bom.csv'), title_block)
            print(f"  Generated: {output_dir / 'component_bom.csv'}")

            # Generate engineering report
            print(f"\nGenerating engineering report...")
            write_engineering_report(components, bom.wires, str(output_dir / 'engineering_report.md'), title_block)
            print(f"  Generated: {output_dir / 'engineering_report.md'}")

            # Generate HTML index
            print(f"\nGenerating HTML index...")
            write_html_index(output_dir, str(output_dir / 'index.html'), title_block)
            print(f"  Generated: {output_dir / 'index.html'}")

            print(f"\nAll outputs written to: {output_dir}")

            return 0

        except Exception as e:
            print(f"Error processing schematic: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

            # Create index.html before exiting so user can access logs
            print("\nWriting index.html with error logs...", file=sys.stderr)
            index_path = str(output_dir / 'index.html')
            write_html_index(output_dir, index_path, title_block)
            print(f"See {index_path} for details", file=sys.stderr)

            return 1


if __name__ == '__main__':
    sys.exit(main())
