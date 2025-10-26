# ABOUTME: Component BOM CSV output generation
# ABOUTME: Creates CSV file with component references, values, descriptions, datasheets, and coordinates

import csv
from typing import List
from kicad2wireBOM.component import Component


def write_component_bom(components: List[Component], output_path: str) -> None:
    """
    Write component BOM to CSV file.

    Args:
        components: List of Component objects
        output_path: Path to output CSV file

    Output CSV columns:
        Reference, Value, Description, Datasheet, Type, Amps, FS, WL, BL

    Type column:
        L = Load (consuming device)
        R = Rating (pass-through device like circuit breaker or switch)
        S = Source (power source like battery)

    Amps column:
        The amperage value (load, rating, or source capacity)

    Components are sorted by reference designator.
    """
    # Sort components by reference
    sorted_components = sorted(components, key=lambda c: c.ref)

    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(['Reference', 'Value', 'Description', 'Datasheet', 'Type', 'Amps', 'FS', 'WL', 'BL'])

        # Write component rows
        for comp in sorted_components:
            # Determine type and amps
            if comp.load is not None:
                comp_type = 'L'
                amps = str(comp.load)
            elif comp.rating is not None:
                comp_type = 'R'
                amps = str(comp.rating)
            elif comp.source is not None:
                comp_type = 'S'
                amps = str(comp.source)
            else:
                comp_type = ''
                amps = ''

            writer.writerow([
                comp.ref,
                comp.value,
                comp.desc,
                comp.datasheet,
                comp_type,
                amps,
                str(comp.fs),
                str(comp.wl),
                str(comp.bl)
            ])
