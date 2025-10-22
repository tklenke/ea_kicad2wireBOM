# ABOUTME: CSV output module for wire BOM
# ABOUTME: Generates CSV files in builder format with wire specifications

import csv
from pathlib import Path
from typing import Union
from kicad2wireBOM.wire_bom import WireBOM


def write_builder_csv(bom: WireBOM, output_path: Union[str, Path]) -> None:
    """
    Write wire BOM to CSV file in builder format.

    Builder format includes essential wire information for harness construction:
    - Wire Label, From Component, From Pin, To Component, To Pin, Wire Gauge, Wire Color, Length, Wire Type, Notes, Warnings

    Args:
        bom: WireBOM object containing wire connections
        output_path: Path to output CSV file
    """
    output_path = Path(output_path)

    headers = ['Wire Label', 'From Component', 'From Pin', 'To Component', 'To Pin', 'Wire Gauge', 'Wire Color', 'Length', 'Wire Type', 'Notes', 'Warnings']

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for wire in bom.wires:
            # Join warnings with semicolons
            warnings_str = '; '.join(wire.warnings) if wire.warnings else ''

            row = {
                'Wire Label': wire.wire_label,
                'From Component': wire.from_component or '',
                'From Pin': wire.from_pin or '',
                'To Component': wire.to_component or '',
                'To Pin': wire.to_pin or '',
                'Wire Gauge': wire.wire_gauge,
                'Wire Color': wire.wire_color,
                'Length': wire.length,
                'Wire Type': wire.wire_type,
                'Notes': wire.notes or '',
                'Warnings': warnings_str
            }
            writer.writerow(row)
