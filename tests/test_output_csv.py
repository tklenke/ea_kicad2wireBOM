# ABOUTME: Tests for CSV output module
# ABOUTME: Validates CSV file generation with correct headers and formatting

import pytest
import csv
from pathlib import Path
from kicad2wireBOM.wire_bom import WireConnection, WireBOM
from kicad2wireBOM.output_csv import write_builder_csv


def test_write_builder_csv(tmp_path):
    """Test writing builder CSV format with 4-column connection format"""
    # Create test BOM with one wire
    bom = WireBOM(config={'system_voltage': 14.0})
    wire = WireConnection(
        wire_label='L-105-A',
        from_component='J1',
        from_pin='1',
        to_component='SW1',
        to_pin='3',
        wire_gauge=20,
        wire_color='White',
        length=79.0,
        wire_type='Standard',
        notes='',
        warnings=[]
    )
    bom.add_wire(wire)

    # Write to temp file
    output_file = tmp_path / "test_output.csv"
    write_builder_csv(bom, output_file)

    # Verify file was created
    assert output_file.exists()

    # Read and verify contents
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check headers (includes Notes column)
    assert reader.fieldnames == ['Wire Label', 'From Component', 'From Pin', 'To Component', 'To Pin', 'Wire Gauge', 'Wire Color', 'Length', 'Wire Type', 'Notes', 'Warnings']

    # Check data
    assert len(rows) == 1
    row = rows[0]
    assert row['Wire Label'] == 'L-105-A'
    assert row['From Component'] == 'J1'
    assert row['From Pin'] == '1'
    assert row['To Component'] == 'SW1'
    assert row['To Pin'] == '3'
    assert row['Wire Gauge'] == '20'
    assert row['Wire Color'] == 'White'
    assert row['Length'] == '79.0'
    assert row['Wire Type'] == 'Standard'
    assert row['Warnings'] == ''


def test_write_builder_csv_with_warnings(tmp_path):
    """Test CSV output with warnings"""
    bom = WireBOM(config={})
    wire = WireConnection(
        wire_label='U-1-A',
        from_component='J1',
        from_pin='2',
        to_component='J2',
        to_pin='1',
        wire_gauge=12,
        wire_color='White',
        length=50.0,
        wire_type='Standard',
        notes='',
        warnings=['Unknown system code', 'Check connections']
    )
    bom.add_wire(wire)

    output_file = tmp_path / "test_warnings.csv"
    write_builder_csv(bom, output_file)

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    row = rows[0]
    assert 'Unknown system code' in row['Warnings']
    assert 'Check connections' in row['Warnings']


def test_write_builder_csv_multiple_wires(tmp_path):
    """Test CSV output with multiple wires"""
    bom = WireBOM(config={})

    wire1 = WireConnection('L-105-A', 'J1', '1', 'SW1', '3', 20, 'White', 79.0, 'Standard', '', [])
    wire2 = WireConnection('P-12-A', 'BAT1', '1', 'SW2', '2', 12, 'Red', 50.0, 'Standard', '', [])
    wire3 = WireConnection('L-105-B', 'SW1', '3', 'LIGHT1', '1', 18, 'White', 45.0, 'Standard', '', [])

    bom.add_wire(wire1)
    bom.add_wire(wire2)
    bom.add_wire(wire3)

    output_file = tmp_path / "test_multiple.csv"
    write_builder_csv(bom, output_file)

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]['Wire Label'] == 'L-105-A'
    assert rows[1]['Wire Label'] == 'P-12-A'
    assert rows[2]['Wire Label'] == 'L-105-B'


def test_bom_wire_sorting():
    """Test that BOM wires are sorted by system code, circuit number, segment letter"""
    import re

    # Create BOM with wires in mixed order
    bom = WireBOM(config={})

    # Add wires in intentionally unsorted order: G, L, P, A
    bom.add_wire(WireConnection('G-11-A', 'L3', '1', 'GND', '1', 18, 'Black', 20.0, 'Standard', '', []))
    bom.add_wire(WireConnection('L-10-A', 'L3', '2', 'SW3', '1', 18, 'White', 30.0, 'Standard', '', []))
    bom.add_wire(WireConnection('P-1-A', 'BT1', '1', 'FH1', '1', 12, 'Red', 40.0, 'Standard', '', []))
    bom.add_wire(WireConnection('A-9-A', 'FH1', '2', 'LRU1', '1', 22, 'Blue', 50.0, 'Standard', '', []))
    bom.add_wire(WireConnection('L-2-B', 'SW1', '1', 'L2', '1', 18, 'White', 25.0, 'Standard', '', []))
    bom.add_wire(WireConnection('G-5-A', 'L1', '1', 'GND', '1', 18, 'Black', 15.0, 'Standard', '', []))

    # Sort the wires
    def parse_wire_label(label):
        """Parse wire label to extract system_code, circuit_num, segment_letter for sorting"""
        pattern = r'^([A-Z])-?(\d+)-?([A-Z])$'
        match = re.match(pattern, label)
        if match:
            system_code = match.group(1)
            circuit_num = int(match.group(2))
            segment_letter = match.group(3)
            return (system_code, circuit_num, segment_letter)
        return ('', 0, '')  # Fallback for invalid labels

    bom.wires.sort(key=lambda w: parse_wire_label(w.wire_label))

    # Verify sorted order
    assert len(bom.wires) == 6
    assert bom.wires[0].wire_label == 'A-9-A'  # A comes first
    assert bom.wires[1].wire_label == 'G-5-A'  # G, circuit 5
    assert bom.wires[2].wire_label == 'G-11-A' # G, circuit 11
    assert bom.wires[3].wire_label == 'L-2-B'  # L, circuit 2
    assert bom.wires[4].wire_label == 'L-10-A' # L, circuit 10
    assert bom.wires[5].wire_label == 'P-1-A'  # P comes last
