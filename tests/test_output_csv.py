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

    # Check headers (new 4-column format)
    assert reader.fieldnames == ['Wire Label', 'From Component', 'From Pin', 'To Component', 'To Pin', 'Wire Gauge', 'Wire Color', 'Length', 'Wire Type', 'Warnings']

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

    wire1 = WireConnection('L-105-A', 'J1', '1', 'SW1', '3', 20, 'White', 79.0, 'Standard', [])
    wire2 = WireConnection('P-12-A', 'BAT1', '1', 'SW2', '2', 12, 'Red', 50.0, 'Standard', [])
    wire3 = WireConnection('L-105-B', 'SW1', '3', 'LIGHT1', '1', 18, 'White', 45.0, 'Standard', [])

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
