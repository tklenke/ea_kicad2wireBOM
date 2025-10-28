# ABOUTME: Engineering report text file generation
# ABOUTME: Creates summary report with component and wire statistics

from typing import List, Dict
from collections import defaultdict
import re

from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.wire_calculator import group_wires_by_circuit, determine_circuit_current, calculate_voltage_drop, parse_net_name
from kicad2wireBOM.reference_data import WIRE_RESISTANCE, WIRE_AMPACITY, DEFAULT_CONFIG


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


def _generate_wire_engineering_analysis(wires: List[WireConnection], circuit_currents: Dict[str, float]) -> List[str]:
    """
    Generate wire engineering analysis table with electrical calculations.

    Args:
        wires: List of WireConnection objects
        circuit_currents: Dict mapping circuit_id to current in amps

    Returns:
        List of formatted Markdown table lines
    """
    system_voltage = DEFAULT_CONFIG['system_voltage']  # 14V

    headers = [
        'Wire Label',
        'Current (A)',
        'Gauge',
        'Length (in)',
        'Voltage Drop (V)',
        'Vdrop %',
        'Ampacity (A)',
        'Utilization %',
        'Resistance (Ω)',
        'Power Loss (W)'
    ]

    rows = []
    total_length = 0.0
    total_vdrop = 0.0
    total_power_loss = 0.0

    # Sort wires by wire_label
    sorted_wires = sorted(wires, key=lambda w: w.wire_label)

    for wire in sorted_wires:
        # Extract circuit_id from wire_label (e.g., "L1" from "L-1-A")
        parsed = parse_net_name(f"/{wire.wire_label}")
        if not parsed:
            continue

        circuit_id = f"{parsed['system']}{parsed['circuit']}"
        current = circuit_currents.get(circuit_id, -99)

        # Skip wires with missing current data
        if current == -99:
            continue

        gauge = int(wire.wire_gauge)
        length_inches = wire.length
        length_feet = length_inches / 12.0

        # Calculate voltage drop
        vdrop_volts = calculate_voltage_drop(current, gauge, length_inches)
        vdrop_percent = (vdrop_volts / system_voltage) * 100.0

        # Ampacity utilization
        ampacity = WIRE_AMPACITY.get(gauge, 0)
        utilization_percent = (current / ampacity) * 100.0 if ampacity > 0 else 0.0

        # Resistance
        resistance_per_foot = WIRE_RESISTANCE.get(gauge, 0)
        total_resistance = resistance_per_foot * length_feet

        # Power loss (I² × R)
        power_loss_watts = (current ** 2) * total_resistance

        # Accumulate totals
        total_length += length_inches
        total_vdrop += vdrop_volts
        total_power_loss += power_loss_watts

        # Format row
        rows.append([
            wire.wire_label,
            f'{current:.1f}',
            str(gauge),
            f'{length_inches:.1f}',
            f'{vdrop_volts:.2f}',
            f'{vdrop_percent:.1f}%',
            f'{ampacity:.1f}',
            f'{utilization_percent:.1f}%',
            f'{total_resistance:.4f}',
            f'{power_loss_watts:.2f}'
        ])

    # Add totals row
    if rows:
        rows.append([
            '**Total**',
            '',
            '',
            f'**{total_length:.1f}**',
            f'**{total_vdrop:.2f}**',
            '',
            '',
            '',
            '',
            f'**{total_power_loss:.2f}**'
        ])

    # Format as markdown table
    alignments = ['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right']
    return _format_markdown_table(headers, rows, alignments)


def _generate_engineering_summary(wires: List[WireConnection], circuit_currents: Dict[str, float]) -> List[str]:
    """
    Generate engineering summary with safety warnings and totals.

    Args:
        wires: List of WireConnection objects
        circuit_currents: Dict mapping circuit_id to current in amps

    Returns:
        List of formatted Markdown lines with summary and warnings
    """
    system_voltage = DEFAULT_CONFIG['system_voltage']  # 14V

    # Track metrics for summary
    total_power_loss = 0.0
    worst_vdrop_percent = 0.0
    worst_vdrop_label = ''
    overloaded_wires = []
    high_vdrop_wires = []

    # Analyze each wire
    sorted_wires = sorted(wires, key=lambda w: w.wire_label)

    for wire in sorted_wires:
        # Extract circuit_id from wire_label
        parsed = parse_net_name(f"/{wire.wire_label}")
        if not parsed:
            continue

        circuit_id = f"{parsed['system']}{parsed['circuit']}"
        current = circuit_currents.get(circuit_id, -99)

        # Skip wires with missing current data
        if current == -99:
            continue

        gauge = int(wire.wire_gauge)
        length_inches = wire.length
        length_feet = length_inches / 12.0

        # Calculate voltage drop
        vdrop_volts = calculate_voltage_drop(current, gauge, length_inches)
        vdrop_percent = (vdrop_volts / system_voltage) * 100.0

        # Ampacity utilization
        ampacity = WIRE_AMPACITY.get(gauge, 0)
        utilization_percent = (current / ampacity) * 100.0 if ampacity > 0 else 0.0

        # Resistance
        resistance_per_foot = WIRE_RESISTANCE.get(gauge, 0)
        total_resistance = resistance_per_foot * length_feet

        # Power loss (I² × R)
        power_loss_watts = (current ** 2) * total_resistance

        # Accumulate totals
        total_power_loss += power_loss_watts

        # Track worst voltage drop
        if vdrop_percent > worst_vdrop_percent:
            worst_vdrop_percent = vdrop_percent
            worst_vdrop_label = wire.wire_label

        # Check for warnings
        if utilization_percent > 100.0:
            overloaded_wires.append((wire.wire_label, utilization_percent))

        if vdrop_percent > 5.0:
            high_vdrop_wires.append((wire.wire_label, vdrop_percent))

    # Generate summary lines
    lines = []
    lines.append('')
    lines.append('**Summary**:')
    lines.append(f'- **Total Power Loss**: {total_power_loss:.2f} W (heat dissipated in wire harness)')

    if worst_vdrop_label:
        warning = ' ⚠️' if worst_vdrop_percent > 5.0 else ''
        lines.append(f'- **Worst Voltage Drop**: {worst_vdrop_label} at {worst_vdrop_percent:.1f}%{warning}')

    # Safety warnings
    if overloaded_wires:
        wire_plural = 'wire' if len(overloaded_wires) == 1 else 'wires'
        lines.append(f'- **Safety Warnings**: {len(overloaded_wires)} {wire_plural} exceed ampacity rating')
        for wire_label, util_pct in overloaded_wires:
            lines.append(f'  - {wire_label} at {util_pct:.0f}% utilization')
    else:
        lines.append('- **Safety Warnings**: No wires exceed ampacity rating')

    if high_vdrop_wires and not overloaded_wires:
        # Only show as separate warning if not already showing overload warnings
        wire_plural = 'wire' if len(high_vdrop_wires) == 1 else 'wires'
        lines.append(f'- **High Voltage Drop**: {len(high_vdrop_wires)} {wire_plural} exceed 5% limit')
        for wire_label, vdrop_pct in high_vdrop_wires:
            lines.append(f'  - {wire_label} at {vdrop_pct:.1f}%')

    lines.append('')
    lines.append('**Notes**:')
    lines.append('- Voltage drop % based on 14V system (12V nominal + charging)')
    lines.append('- Utilization > 100% indicates wire undersized for circuit current')
    lines.append('- Power loss calculated as I² × R for each wire segment')

    return lines


def _generate_wire_bom_table(wires: List[WireConnection]) -> List[str]:
    """
    Generate wire BOM table with all wire details.

    Args:
        wires: List of WireConnection objects

    Returns:
        List of formatted Markdown table lines
    """
    headers = [
        'Wire Label',
        'From Component',
        'From Pin',
        'To Component',
        'To Pin',
        'Gauge',
        'Color',
        'Length (in)',
        'Type',
        'Notes',
        'Warnings'
    ]

    rows = []

    # Sort wires by wire_label
    sorted_wires = sorted(wires, key=lambda w: w.wire_label)

    for wire in sorted_wires:
        # Format warnings list as comma-separated string
        warnings_str = ', '.join(wire.warnings) if wire.warnings else ''

        rows.append([
            wire.wire_label,
            wire.from_component if wire.from_component else '',
            wire.from_pin if wire.from_pin else '',
            wire.to_component if wire.to_component else '',
            wire.to_pin if wire.to_pin else '',
            str(wire.wire_gauge),
            wire.wire_color,
            f'{wire.length:.1f}',
            wire.wire_type,
            wire.notes if wire.notes else '',
            warnings_str
        ])

    # Format as markdown table (right-align length column)
    alignments = ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'right', 'left', 'left', 'left']
    return _format_markdown_table(headers, rows, alignments)


def _generate_component_bom_table(components: List[Component]) -> List[str]:
    """
    Generate component BOM table with all component details.

    Args:
        components: List of Component objects

    Returns:
        List of formatted Markdown table lines
    """
    headers = [
        'Reference',
        'Value',
        'Description',
        'Datasheet',
        'Type',
        'Amps',
        'FS',
        'WL',
        'BL'
    ]

    rows = []

    # Sort components by reference
    sorted_components = sorted(components, key=lambda c: c.ref)

    for comp in sorted_components:
        # Determine component type and amps
        comp_type = ''
        amps = ''

        if comp.load is not None:
            comp_type = 'L'
            amps = f'{comp.load:.1f}'
        elif comp.rating is not None:
            comp_type = 'R'
            amps = f'{comp.rating:.1f}'
        elif comp.source is not None:
            comp_type = 'S'
            amps = f'{comp.source:.1f}'

        rows.append([
            comp.ref,
            comp.value if comp.value else '',
            comp.desc if comp.desc else '',
            comp.datasheet if comp.datasheet else '',
            comp_type,
            amps,
            f'{comp.fs:.1f}' if comp.fs is not None else '',
            f'{comp.wl:.1f}' if comp.wl is not None else '',
            f'{comp.bl:.1f}' if comp.bl is not None else ''
        ])

    # Format as markdown table
    # Text columns left-aligned, numeric columns (Amps, FS, WL, BL) right-aligned
    alignments = ['left', 'left', 'left', 'left', 'left', 'right', 'right', 'right', 'right']
    return _format_markdown_table(headers, rows, alignments)


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
