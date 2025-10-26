# ABOUTME: Engineering report text file generation
# ABOUTME: Creates summary report with component and wire statistics

from typing import List
from collections import defaultdict
import re

from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection


def write_engineering_report(components: List[Component], wires: List[WireConnection], output_path: str) -> None:
    """
    Write engineering report to text file.

    Args:
        components: List of Component objects
        wires: List of WireConnection objects
        output_path: Path to output text file

    Report includes:
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
