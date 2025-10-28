# ABOUTME: Tests for output_engineering_report module
# ABOUTME: Verifies engineering report text file generation with statistics and summary

import pytest
from pathlib import Path

from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.output_engineering_report import (
    write_engineering_report,
    _format_markdown_table,
    _generate_wire_purchasing_summary
)


def test_write_engineering_report_basic(tmp_path):
    """Test basic engineering report generation"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='CB2', fs=100.0, wl=25.0, bl=5.0, load=None, rating=15.0),
        Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None),
    ]

    wires = [
        WireConnection(wire_label='L1A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='22', wire_color='RED', length=50.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='L1B', from_component='LIGHT1', from_pin='2', to_component='GND', to_pin=None,
                       wire_gauge='22', wire_color='BLK', length=45.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='P1A', from_component='CB2', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='20', wire_color='RED', length=60.0, wire_type='Standard', notes='', warnings=[]),
    ]

    output_file = tmp_path / "engineering_report.txt"
    write_engineering_report(components, wires, str(output_file))

    # Verify file was created
    assert output_file.exists()

    # Read and verify contents
    content = output_file.read_text()

    # Check for key sections
    assert "ENGINEERING REPORT" in content
    assert "COMPONENT SUMMARY" in content
    assert "WIRE SUMMARY" in content
    assert "Total Components: 4" in content
    assert "Total Wires: 3" in content


def test_write_engineering_report_component_breakdown(tmp_path):
    """Test component type breakdown in report"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='CB2', fs=100.0, wl=25.0, bl=5.0, load=None, rating=15.0),
        Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None),
        Component(ref='LIGHT2', fs=200.0, wl=35.0, bl=-5.0, load=3.0, rating=None),
    ]

    wires = []

    output_file = tmp_path / "engineering_report.txt"
    write_engineering_report(components, wires, str(output_file))

    content = output_file.read_text()

    # Check component breakdown
    assert "Circuit Breakers (CB): 2" in content
    assert "Switches (SW): 1" in content
    assert "Lights (LIGHT): 2" in content


def test_write_engineering_report_wire_breakdown(tmp_path):
    """Test wire system breakdown in report"""
    components = []

    wires = [
        WireConnection(wire_label='L1A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='22', wire_color='RED', length=50.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='L2A', from_component='CB1', from_pin='2', to_component='LIGHT2', to_pin='1',
                       wire_gauge='22', wire_color='RED', length=45.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='P1A', from_component='CB2', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='20', wire_color='RED', length=60.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='P2A', from_component='CB3', from_pin='1', to_component='SW2', to_pin='1',
                       wire_gauge='20', wire_color='RED', length=55.0, wire_type='Standard', notes='', warnings=[]),
        WireConnection(wire_label='P3A', from_component='CB4', from_pin='1', to_component='SW3', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=65.0, wire_type='Standard', notes='', warnings=[]),
    ]

    output_file = tmp_path / "engineering_report.txt"
    write_engineering_report(components, wires, str(output_file))

    content = output_file.read_text()

    # Check wire system breakdown
    assert "Lighting (L): 2" in content
    assert "Power (P): 3" in content


def test_write_engineering_report_empty_lists(tmp_path):
    """Test report generation with empty components and wires"""
    components = []
    wires = []

    output_file = tmp_path / "engineering_report.txt"
    write_engineering_report(components, wires, str(output_file))

    assert output_file.exists()

    content = output_file.read_text()
    assert "Total Components: 0" in content
    assert "Total Wires: 0" in content


def test_format_markdown_table_left_aligned():
    """Test markdown table formatting with left alignment"""
    headers = ['Name', 'Age', 'City']
    rows = [
        ['Alice', '30', 'NYC'],
        ['Bob', '25', 'LA'],
    ]
    alignments = ['left', 'left', 'left']

    result = _format_markdown_table(headers, rows, alignments)

    expected = [
        '| Name  | Age | City |',
        '| ----- | --- | ---- |',
        '| Alice | 30  | NYC  |',
        '| Bob   | 25  | LA   |',
    ]

    assert result == expected


def test_format_markdown_table_mixed_alignment():
    """Test markdown table with mixed alignment (left, center, right)"""
    headers = ['Item', 'Count', 'Price']
    rows = [
        ['Apple', '5', '1.50'],
        ['Banana', '10', '0.75'],
    ]
    alignments = ['left', 'center', 'right']

    result = _format_markdown_table(headers, rows, alignments)

    # Note: Python's str.center() puts extra space on right for odd-width content
    expected = [
        '| Item   | Count | Price |',
        '| ------ | :---: | ----: |',
        '| Apple  |   5   |  1.50 |',
        '| Banana |   10  |  0.75 |',
    ]

    assert result == expected


def test_format_markdown_table_default_alignment():
    """Test markdown table with default (all left) alignment"""
    headers = ['Col1', 'Col2']
    rows = [
        ['Data1', 'Data2'],
    ]

    result = _format_markdown_table(headers, rows)

    expected = [
        '| Col1  | Col2  |',
        '| ----- | ----- |',
        '| Data1 | Data2 |',
    ]

    assert result == expected


def test_format_markdown_table_with_varying_widths():
    """Test markdown table handles varying column widths"""
    headers = ['Short', 'VeryLongHeader']
    rows = [
        ['X', 'Y'],
        ['LongData', 'Short'],
    ]
    alignments = ['left', 'right']

    result = _format_markdown_table(headers, rows, alignments)

    expected = [
        '| Short    | VeryLongHeader |',
        '| -------- | -------------: |',
        '| X        |              Y |',
        '| LongData |          Short |',
    ]

    assert result == expected


def test_generate_wire_purchasing_summary():
    """Test wire purchasing summary table generation"""
    wires = [
        WireConnection(wire_label='L1A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='L2A', from_component='CB1', from_pin='2', to_component='LIGHT2', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=45.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='P1A', from_component='CB2', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=60.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='P2A', from_component='CB3', from_pin='1', to_component='SW2', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=40.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    result = _generate_wire_purchasing_summary(wires)

    # Verify table structure
    assert isinstance(result, list)
    assert len(result) > 0

    # Should have header, separator, 2 data rows (AWG 12 and 18), and totals row
    assert len(result) == 5

    # Verify header
    assert 'Wire Gauge' in result[0]
    assert 'Wire Type' in result[0]
    assert 'Total Length (in)' in result[0]
    assert 'Total Length (ft)' in result[0]

    # Verify separator (markdown alignment syntax)
    assert '|' in result[1]
    assert '-' in result[1]

    # Verify data rows - AWG 12 should come first (sorted numerically)
    assert '12 AWG' in result[2]
    assert '100.0' in result[2]  # 60 + 40 inches
    assert '8.3' in result[2]     # 100/12 = 8.33... feet

    assert '18 AWG' in result[3]
    assert '95.0' in result[3]    # 50 + 45 inches
    assert '7.9' in result[3]     # 95/12 = 7.91... feet

    # Verify totals row
    assert 'Total' in result[4]
    assert '195.0' in result[4]   # 100 + 95 inches
    assert '16.2' in result[4]    # 195/12 = 16.25 feet (rounds to 16.2)


def test_generate_wire_purchasing_summary_multiple_types():
    """Test wire purchasing summary with different wire types"""
    wires = [
        WireConnection(wire_label='L1A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='L2A', from_component='CB1', from_pin='2', to_component='LIGHT2', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=45.0, wire_type='M22759/32', notes='', warnings=[]),
    ]

    result = _generate_wire_purchasing_summary(wires)

    # Should have header, separator, 2 data rows (same gauge, different types), and totals
    assert len(result) == 5

    # Both should be AWG 18 but different types
    assert '18 AWG' in result[2]
    assert '18 AWG' in result[3]

    # Check they're grouped separately
    assert ('M22759/16' in result[2] and 'M22759/32' in result[3]) or \
           ('M22759/32' in result[2] and 'M22759/16' in result[3])


def test_generate_wire_purchasing_summary_empty():
    """Test wire purchasing summary with no wires"""
    wires = []

    result = _generate_wire_purchasing_summary(wires)

    # Should still have header and separator, but no data rows
    assert len(result) >= 2
