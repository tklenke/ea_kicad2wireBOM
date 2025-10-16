# ABOUTME: Netlist parser module for KiCad netlists
# ABOUTME: Extracts nets, components, and footprint encoding from KiCad netlist files

from pathlib import Path
from typing import Union, List, Dict, Any, Optional
import kinparse
import re


def parse_netlist_file(file_path: Union[str, Path]) -> Any:
    """
    Parse a KiCad netlist file using kinparse.

    Args:
        file_path: Path to the KiCad netlist (.net) file

    Returns:
        kinparse ParseResults object containing the parsed netlist data
    """
    file_path = Path(file_path)
    return kinparse.parse_netlist(str(file_path))


def extract_nets(parsed_netlist: Any) -> List[Dict[str, str]]:
    """
    Extract net information from a parsed netlist.

    Args:
        parsed_netlist: kinparse ParseResults object

    Returns:
        List of dicts, each containing:
            - code: Net code (string)
            - name: Net name (string)
            - class: Net class (string, typically "Default")
    """
    nets = []

    for net in parsed_netlist.nets:
        net_dict = {
            'code': str(net.code),
            'name': net.name,
            'class': getattr(net, 'class', 'Default')  # Handle optional class attribute
        }
        nets.append(net_dict)

    return nets


def extract_components(parsed_netlist: Any) -> List[Dict[str, str]]:
    """
    Extract component information from a parsed netlist.

    Args:
        parsed_netlist: kinparse ParseResults object

    Returns:
        List of dicts, each containing:
            - ref: Component reference designator (e.g., "J1", "SW1")
            - footprint: Full footprint field string (including encoding)
            - value: Component value field (e.g., "Landing Light", "Conn_01x02")
            - desc: Component description field
    """
    components = []

    for comp in parsed_netlist.parts:
        comp_dict = {
            'ref': comp.ref,
            'footprint': comp.footprint,
            'value': getattr(comp, 'value', ''),
            'desc': getattr(comp, 'desc', '')
        }
        components.append(comp_dict)

    return components


def parse_footprint_encoding(footprint_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse footprint encoding from footprint field string.

    Format: |(fs,wl,bl)<L|R><amps>
    Example: "Connector:Conn_01x02|(100.0,25.0,0.0)R15"

    Args:
        footprint_str: Full footprint field string

    Returns:
        Dict with parsed values if encoding found, None otherwise:
            - fs: Fuselage Station (float)
            - wl: Water Line (float)
            - bl: Butt Line (float)
            - type: 'L' for Load or 'R' for Rating
            - amperage: Amperage value (float)
    """
    # Pattern: |(fs,wl,bl)<L|R><amps>
    # Coordinates can be negative, amperage can be decimal
    pattern = r'\|\(([-\d.]+),([-\d.]+),([-\d.]+)\)([LR])([-\d.]+)'

    match = re.search(pattern, footprint_str)
    if not match:
        return None

    try:
        return {
            'fs': float(match.group(1)),
            'wl': float(match.group(2)),
            'bl': float(match.group(3)),
            'type': match.group(4),
            'amperage': float(match.group(5))
        }
    except ValueError:
        # If conversion to float fails, return None
        return None
