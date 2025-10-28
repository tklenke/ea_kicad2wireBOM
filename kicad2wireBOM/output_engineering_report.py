# ABOUTME: Engineering report text file generation
# ABOUTME: Creates summary report with component and wire statistics

from typing import List, Dict
from collections import defaultdict
import re

from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.wire_calculator import group_wires_by_circuit, determine_circuit_current


def _format_markdown_table(headers: List[str], rows: List[List[str]], alignments: List[str] = None) -> List[str]:
    """
    Format data as Markdown table.

    Args:
        headers: Column headers
        rows: Data rows (each row is list of cell values)
        alignments: List of 'left', 'center', 'right' for each column
                   Default: all left-aligned

    Returns:
        List of formatted table lines
    """
    if alignments is None:
        alignments = ['left'] * len(headers)

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    lines = []

    # Header row
    header_cells = [headers[i].ljust(col_widths[i]) for i in range(len(headers))]
    lines.append('| ' + ' | '.join(header_cells) + ' |')

    # Separator row with alignment
    sep_cells = []
    for i, align in enumerate(alignments):
        width = col_widths[i]
        if align == 'center':
            sep_cells.append(':' + '-' * (width - 2) + ':')
        elif align == 'right':
            sep_cells.append('-' * (width - 1) + ':')
        else:  # left
            sep_cells.append('-' * width)
    lines.append('| ' + ' | '.join(sep_cells) + ' |')

    # Data rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if alignments[i] == 'right':
                cells.append(cell_str.rjust(col_widths[i]))
            elif alignments[i] == 'center':
                cells.append(cell_str.center(col_widths[i]))
            else:
                cells.append(cell_str.ljust(col_widths[i]))
        lines.append('| ' + ' | '.join(cells) + ' |')

    return lines


def _generate_wire_purchasing_summary(wires: List[WireConnection]) -> List[str]:
    """
    Generate wire purchasing summary table grouped by gauge and type.

    Args:
        wires: List of WireConnection objects

    Returns:
        List of formatted Markdown table lines
    """
    # Group wires by (gauge, type) and sum lengths
    wire_groups = defaultdict(float)
    for wire in wires:
        key = (wire.wire_gauge, wire.wire_type)
        wire_groups[key] += wire.length

    # Sort by gauge (numeric), then type
    sorted_groups = sorted(wire_groups.items(),
                          key=lambda x: (int(x[0][0]), x[0][1]))

    # Build table rows
    headers = ['Wire Gauge', 'Wire Type', 'Total Length (in)', 'Total Length (ft)']
    rows = []

    total_inches = 0.0
    for (gauge, wire_type), length_inches in sorted_groups:
        length_feet = length_inches / 12.0
        total_inches += length_inches

        rows.append([
            f'{gauge} AWG',
            wire_type,
            f'{length_inches:.1f}',
            f'{length_feet:.1f}'
        ])

    # Add totals row
    if rows:
        total_feet = total_inches / 12.0
        rows.append([
            '**Total**',
            '',
            f'**{total_inches:.1f}**',
            f'**{total_feet:.1f}**'
        ])

    # Format as markdown table
    alignments = ['left', 'left', 'right', 'right']
    return _format_markdown_table(headers, rows, alignments)


def _generate_component_purchasing_summary(components: List[Component]) -> List[str]:
    """
    Generate component purchasing summary table grouped by value and datasheet.

    Args:
        components: List of Component objects

    Returns:
        List of formatted Markdown table lines
    """
    # Group components by (value, datasheet) and collect refs
    comp_groups = defaultdict(list)
    for comp in components:
        value = comp.value if comp.value else '~'
        datasheet = comp.datasheet if comp.datasheet else ''
        key = (value, datasheet)
        comp_groups[key].append(comp.ref)

    # Sort by value, then datasheet
    sorted_groups = sorted(comp_groups.items(),
                          key=lambda x: (x[0][0], x[0][1]))

    # Build table rows
    headers = ['Value', 'Datasheet', 'Quantity', 'Example Refs']
    rows = []

    total_count = 0
    for (value, datasheet), refs in sorted_groups:
        quantity = len(refs)
        total_count += quantity

        # Format example refs (limit to first 5)
        sorted_refs = sorted(refs)
        if len(sorted_refs) <= 5:
            example_refs = ', '.join(sorted_refs)
        else:
            example_refs = ', '.join(sorted_refs[:5]) + f', ... ({len(sorted_refs)} total)'

        rows.append([
            value,
            datasheet,
            str(quantity),
            example_refs
        ])

    # Add totals row
    if rows:
        rows.append([
            '**Total**',
            '',
            f'**{total_count}**',
            ''
        ])

    # Format as markdown table
    alignments = ['left', 'left', 'right', 'left']
    return _format_markdown_table(headers, rows, alignments)


def _calculate_circuit_currents(wires: List[WireConnection], components: List[Component]) -> Dict[str, float]:
    """
    Calculate current for each circuit by grouping wires and determining circuit current.

    Args:
        wires: List of WireConnection objects
        components: List of Component objects

    Returns:
        Dict mapping circuit_id (e.g., "L1", "P2") to current in amps
        Uses -99 as sentinel for missing data
    """
    # Group wires by circuit
    circuit_groups = group_wires_by_circuit(wires)

    # Calculate current for each circuit
    circuit_currents = {}
    for circuit_id, circuit_wires in circuit_groups.items():
        current = determine_circuit_current(circuit_wires, components, None)
        circuit_currents[circuit_id] = current

    return circuit_currents


def write_engineering_report(components: List[Component], wires: List[WireConnection], output_path: str, title_block: Dict[str, str] = None) -> None:
    """
    Write engineering report to text file.

    Args:
        components: List of Component objects
        wires: List of WireConnection objects
        output_path: Path to output text file
        title_block: Optional dict with title, date, rev from schematic title_block

    Report includes:
        - Project title block information
        - Overall summary statistics
        - Component breakdown by type
        - Wire breakdown by system
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("ENGINEERING REPORT")
    lines.append("kicad2wireBOM Wire Harness Analysis")
    lines.append("=" * 60)
    lines.append("")

    # Title block information
    if title_block:
        lines.append("PROJECT INFORMATION")
        lines.append("-" * 60)
        if 'title' in title_block:
            lines.append(f"Project:     {title_block['title']}")
        if 'rev' in title_block:
            lines.append(f"Revision:    {title_block['rev']}")
        if 'date' in title_block:
            lines.append(f"Issue Date:  {title_block['date']}")
        if 'company' in title_block:
            lines.append(f"Company:     {title_block['company']}")
        lines.append("")

    # Overall summary
    lines.append("OVERALL SUMMARY")
    lines.append("-" * 60)
    lines.append(f"Total Components: {len(components)}")
    lines.append(f"Total Wires: {len(wires)}")
    lines.append("")

    # Component breakdown by type
    lines.append("COMPONENT SUMMARY")
    lines.append("-" * 60)

    if components:
        component_types = defaultdict(int)
        for comp in components:
            # Extract component type prefix (e.g., "CB" from "CB1", "LIGHT" from "LIGHT1")
            match = re.match(r'([A-Z]+)', comp.ref)
            if match:
                comp_type = match.group(1)
                component_types[comp_type] += 1

        # Sort by type name
        for comp_type in sorted(component_types.keys()):
            count = component_types[comp_type]
            # Generate friendly name
            friendly_name = get_component_type_name(comp_type)
            lines.append(f"{friendly_name} ({comp_type}): {count}")
    else:
        lines.append("No components found")

    lines.append("")

    # Wire breakdown by system
    lines.append("WIRE SUMMARY")
    lines.append("-" * 60)

    if wires:
        system_counts = defaultdict(int)
        for wire in wires:
            # Extract system code from wire label (e.g., "L" from "L1A")
            match = re.match(r'([A-Z])\d+[A-Z]?', wire.wire_label)
            if match:
                system_code = match.group(1)
                system_counts[system_code] += 1

        # Sort by system code
        for system_code in sorted(system_counts.keys()):
            count = system_counts[system_code]
            # Generate friendly name
            friendly_name = get_system_name(system_code)
            lines.append(f"{friendly_name} ({system_code}): {count}")
    else:
        lines.append("No wires found")

    lines.append("")
    lines.append("=" * 60)
    lines.append("End of Report")
    lines.append("=" * 60)

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def get_component_type_name(comp_type: str) -> str:
    """
    Get friendly name for component type prefix.

    Args:
        comp_type: Component type prefix (e.g., "CB", "SW", "LIGHT")

    Returns:
        Friendly name (e.g., "Circuit Breakers", "Switches", "Lights")
    """
    type_names = {
        'CB': 'Circuit Breakers',
        'SW': 'Switches',
        'LIGHT': 'Lights',
        'BT': 'Batteries',
        'J': 'Jacks/Connectors',
        'K': 'Relays',
        'F': 'Fuses',
    }
    return type_names.get(comp_type, comp_type)


def get_system_name(system_code: str) -> str:
    """
    Get friendly name for system code.

    Args:
        system_code: System code (e.g., "L", "P", "G")

    Returns:
        Friendly name (e.g., "Lighting", "Power", "Ground")
    """
    system_names = {
        'A': 'Avionics',
        'E': 'Engine Instrument',
        'F': 'Flight Instrument',
        'G': 'Ground',
        'K': 'Engine Control',
        'L': 'Lighting',
        'M': 'Miscellaneous Electrical',
        'P': 'Power',
        'R': 'Radio',
        'U': 'Miscellaneous Electronic',
        'V': 'AC Power',
        'W': 'Warning and Emergency',
    }
    return system_names.get(system_code, system_code)
