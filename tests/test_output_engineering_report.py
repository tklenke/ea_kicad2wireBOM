# ABOUTME: Tests for output_engineering_report module
# ABOUTME: Verifies engineering report text file generation with statistics and summary

import pytest
from pathlib import Path

from kicad2wireBOM.component import Component
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.output_engineering_report import (
    write_engineering_report,
    _format_markdown_table,
    _generate_wire_purchasing_summary,
    _generate_component_purchasing_summary,
    _calculate_circuit_currents,
    _generate_wire_engineering_analysis,
    _generate_engineering_summary,
    _generate_wire_bom_table,
    _generate_component_bom_table
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


def test_generate_component_purchasing_summary():
    """Test component purchasing summary table generation"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0, value='10A', datasheet='CB-10A.pdf'),
        Component(ref='CB2', fs=100.0, wl=25.0, bl=5.0, load=None, rating=10.0, value='10A', datasheet='CB-10A.pdf'),
        Component(ref='CB3', fs=150.0, wl=30.0, bl=0.0, load=None, rating=15.0, value='15A', datasheet='CB-15A.pdf'),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None, value='LED', datasheet='LED-W.pdf'),
        Component(ref='LIGHT2', fs=200.0, wl=35.0, bl=-5.0, load=5.0, rating=None, value='LED', datasheet='LED-W.pdf'),
    ]

    result = _generate_component_purchasing_summary(components)

    # Verify table structure
    assert isinstance(result, list)
    assert len(result) > 0

    # Should have header, separator, 3 data rows (2 LED, 2 CB 10A, 1 CB 15A), and totals
    assert len(result) == 6

    # Verify header
    assert 'Value' in result[0]
    assert 'Datasheet' in result[0]
    assert 'Quantity' in result[0]
    assert 'Example Refs' in result[0]

    # Verify data rows (sorted by value, then datasheet)
    # Should contain both 10A and 15A
    data_content = '\n'.join(result[2:5])  # Skip header and separator
    assert '10A' in data_content
    assert '15A' in data_content
    assert 'LED' in data_content

    # Verify quantities
    assert '2' in result[2] or '2' in result[3] or '2' in result[4]  # Two LEDs or two CB 10A

    # Verify example refs
    assert 'CB1' in data_content or 'CB2' in data_content  # At least one CB ref
    assert 'LIGHT1' in data_content or 'LIGHT2' in data_content  # At least one LIGHT ref

    # Verify totals row
    assert 'Total' in result[5]
    assert '5' in result[5]  # Total 5 components


def test_generate_component_purchasing_summary_with_many_refs():
    """Test component purchasing summary with >5 refs shows ellipsis"""
    components = [
        Component(ref=f'R{i}', fs=100.0, wl=25.0, bl=0.0, load=None, rating=None, value='1K', datasheet='resistor.pdf')
        for i in range(1, 8)  # 7 resistors
    ]

    result = _generate_component_purchasing_summary(components)

    # Should show first 5 refs + ellipsis
    data_row = result[2]  # First data row after header and separator
    assert 'R1' in data_row
    assert '...' in data_row or '7' in data_row  # Either ellipsis or total count
    assert '7' in data_row  # Quantity should be 7


def test_generate_component_purchasing_summary_empty():
    """Test component purchasing summary with no components"""
    components = []

    result = _generate_component_purchasing_summary(components)

    # Should still have header and separator
    assert len(result) >= 2


def test_calculate_circuit_currents():
    """Test circuit current calculation from wires and components"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None),  # 5A load
        Component(ref='LIGHT2', fs=200.0, wl=35.0, bl=-5.0, load=3.0, rating=None), # 3A load
        Component(ref='GND1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=None),
    ]

    wires = [
        # L1 circuit with LIGHT1 (5A)
        WireConnection(wire_label='L-1-A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='L-1-B', from_component='LIGHT1', from_pin='2', to_component='GND1', to_pin='1',
                       wire_gauge='18', wire_color='BLK', length=45.0, wire_type='M22759/16', notes='', warnings=[]),
        # L2 circuit with LIGHT2 (3A)
        WireConnection(wire_label='L-2-A', from_component='CB1', from_pin='2', to_component='LIGHT2', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=55.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='L-2-B', from_component='LIGHT2', from_pin='2', to_component='GND1', to_pin='1',
                       wire_gauge='18', wire_color='BLK', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    result = _calculate_circuit_currents(wires, components)

    # Should be a dict mapping circuit_id to current
    assert isinstance(result, dict)

    # Should have L1 and L2 circuits
    assert 'L1' in result
    assert 'L2' in result

    # L1 should have 5A (LIGHT1 load)
    assert result['L1'] == 5.0

    # L2 should have 3A (LIGHT2 load)
    assert result['L2'] == 3.0


def test_calculate_circuit_currents_missing_data():
    """Test circuit current calculation handles missing load data"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0),  # No load
    ]

    wires = [
        WireConnection(wire_label='P-1-A', from_component='CB1', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    result = _calculate_circuit_currents(wires, components)

    # Should have P1 circuit
    assert 'P1' in result

    # P1 should have -99 (sentinel for missing data)
    assert result['P1'] == -99


def test_generate_wire_engineering_analysis():
    """Test wire engineering analysis table with electrical calculations"""
    wires = [
        WireConnection(wire_label='L-1-A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    circuit_currents = {
        'L1': 5.0  # 5A current in L1 circuit
    }

    result = _generate_wire_engineering_analysis(wires, circuit_currents)

    # Verify table structure
    assert isinstance(result, list)
    assert len(result) > 0

    # Should have header, separator, 1 data row, and totals row
    assert len(result) == 4

    # Verify header columns
    assert 'Wire Label' in result[0]
    assert 'Current (A)' in result[0]
    assert 'Gauge' in result[0]
    assert 'Length (in)' in result[0]
    assert 'Voltage Drop (V)' in result[0]
    assert 'Vdrop %' in result[0]
    assert 'Ampacity (A)' in result[0]
    assert 'Utilization %' in result[0]
    assert 'Resistance' in result[0]
    assert 'Power Loss (W)' in result[0]

    # Verify data row contains expected values
    data_row = result[2]
    assert 'L-1-A' in data_row
    assert '5.0' in data_row  # Current
    assert '18' in data_row    # Gauge
    assert '50.0' in data_row  # Length

    # Verify totals row
    assert 'Total' in result[3]
    assert '50.0' in result[3]  # Total length


def test_generate_wire_engineering_analysis_multiple_wires():
    """Test wire engineering analysis with multiple wires and circuits"""
    wires = [
        WireConnection(wire_label='L-1-A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='L-1-B', from_component='LIGHT1', from_pin='2', to_component='GND1', to_pin='1',
                       wire_gauge='18', wire_color='BLK', length=45.0, wire_type='M22759/16', notes='', warnings=[]),
        WireConnection(wire_label='P-1-A', from_component='CB2', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=60.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    circuit_currents = {
        'L1': 5.0,   # 5A in L1 circuit
        'P1': 20.0,  # 20A in P1 circuit
    }

    result = _generate_wire_engineering_analysis(wires, circuit_currents)

    # Should have header, separator, 3 data rows, totals
    assert len(result) == 6

    # Verify all wire labels present
    all_data = '\n'.join(result)
    assert 'L-1-A' in all_data
    assert 'L-1-B' in all_data
    assert 'P-1-A' in all_data

    # Verify totals row
    assert '155.0' in result[5]  # Total length (50 + 45 + 60)


def test_generate_engineering_summary_with_warnings():
    """Test engineering summary with overload and high voltage drop warnings"""
    wires = [
        # Overloaded wire: 18 AWG (10A ampacity) with 15A current = 150% utilization
        WireConnection(wire_label='L-1-A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=50.0, wire_type='M22759/16', notes='', warnings=[]),
        # High voltage drop wire: 18 AWG, 300 inches, 5A = ~5.7% vdrop
        WireConnection(wire_label='L-2-A', from_component='CB2', from_pin='1', to_component='LIGHT2', to_pin='1',
                       wire_gauge='18', wire_color='RED', length=300.0, wire_type='M22759/16', notes='', warnings=[]),
        # Normal wire: 12 AWG, 60 inches, 10A = normal
        WireConnection(wire_label='P-1-A', from_component='CB3', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=60.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    circuit_currents = {
        'L1': 15.0,  # Overload condition
        'L2': 5.0,   # High voltage drop
        'P1': 10.0,  # Normal
    }

    result = _generate_engineering_summary(wires, circuit_currents)

    # Verify result is list of strings
    assert isinstance(result, list)
    assert len(result) > 0

    # Convert to single string for easier checking
    summary_text = '\n'.join(result)

    # Verify summary section markers
    assert '**Summary**:' in summary_text or 'Summary' in summary_text

    # Verify total power loss is reported
    assert 'Total Power Loss' in summary_text or 'Power Loss' in summary_text

    # Verify worst voltage drop is reported
    assert 'Voltage Drop' in summary_text or 'Vdrop' in summary_text

    # Verify warnings for overloaded wire
    assert 'overload' in summary_text.lower() or 'ampacity' in summary_text.lower()
    assert 'L-1-A' in summary_text  # The overloaded wire label

    # Verify warnings for high voltage drop
    assert 'L-2-A' in summary_text  # The high vdrop wire label

    # Verify notes section exists
    assert 'Notes' in summary_text or 'notes' in summary_text


def test_generate_engineering_summary_no_warnings():
    """Test engineering summary with no safety warnings"""
    wires = [
        # Normal wire: 12 AWG, 60 inches, 10A = normal
        WireConnection(wire_label='P-1-A', from_component='CB1', from_pin='1', to_component='SW1', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=60.0, wire_type='M22759/16', notes='', warnings=[]),
    ]

    circuit_currents = {
        'P1': 10.0,  # Normal (12 AWG has 22A ampacity)
    }

    result = _generate_engineering_summary(wires, circuit_currents)

    # Verify result is list of strings
    assert isinstance(result, list)
    assert len(result) > 0

    # Convert to single string for easier checking
    summary_text = '\n'.join(result)

    # Verify summary section exists
    assert '**Summary**:' in summary_text or 'Summary' in summary_text

    # Verify no warnings reported (or explicitly states no warnings)
    # Should either have "0 wires" or "No wires" or similar
    assert '0 wire' in summary_text.lower() or 'no wire' in summary_text.lower() or 'none' in summary_text.lower()


def test_generate_wire_bom_table():
    """Test wire BOM table generation with all wire fields"""
    wires = [
        WireConnection(wire_label='L-1-A', from_component='CB1', from_pin='1', to_component='LIGHT1', to_pin='1',
                       wire_gauge='18', wire_color='WHITE', length=50.0, wire_type='M22759/16', notes='Test note', warnings=[]),
        WireConnection(wire_label='P-1-A', from_component='BT1', from_pin='1', to_component='CB1', to_pin='1',
                       wire_gauge='12', wire_color='RED', length=60.0, wire_type='M22759/16', notes='', warnings=['Warning: test']),
    ]

    result = _generate_wire_bom_table(wires)

    # Verify result is list of strings
    assert isinstance(result, list)
    assert len(result) > 0

    # Should have header, separator, 2 data rows (sorted by wire label)
    assert len(result) == 4

    # Verify header columns (11 total from design spec)
    header = result[0]
    assert 'Wire Label' in header
    assert 'From Component' in header
    assert 'From Pin' in header
    assert 'To Component' in header
    assert 'To Pin' in header
    assert 'Gauge' in header
    assert 'Color' in header
    assert 'Length (in)' in header
    assert 'Type' in header
    assert 'Notes' in header
    assert 'Warnings' in header

    # Verify separator has alignment markers
    assert '|' in result[1]
    assert '-' in result[1]

    # Verify data rows contain wire data (sorted by label: L-1-A, P-1-A)
    data_rows = '\n'.join(result[2:])
    assert 'L-1-A' in data_rows
    assert 'P-1-A' in data_rows
    assert 'CB1' in data_rows
    assert 'LIGHT1' in data_rows
    assert 'BT1' in data_rows
    assert '50.0' in data_rows
    assert '60.0' in data_rows
    assert 'M22759/16' in data_rows


def test_generate_wire_bom_table_empty():
    """Test wire BOM table with no wires"""
    wires = []

    result = _generate_wire_bom_table(wires)

    # Should still have header and separator
    assert len(result) >= 2
    assert 'Wire Label' in result[0]


def test_generate_component_bom_table():
    """Test component BOM table generation with all component fields"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0, value='10A',
                  desc='Circuit Breaker', datasheet='CB-10A.pdf'),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None, value='LED',
                  desc='LED Light', datasheet='LED-W.pdf'),
        Component(ref='BT1', fs=0.0, wl=0.0, bl=0.0, load=None, rating=None, value='Battery',
                  desc='12V Battery', datasheet='', source=40.0),
    ]

    result = _generate_component_bom_table(components)

    # Verify result is list of strings
    assert isinstance(result, list)
    assert len(result) > 0

    # Should have header, separator, 3 data rows (sorted by ref: BT1, CB1, LIGHT1)
    assert len(result) == 5

    # Verify header columns (9 total from design spec)
    header = result[0]
    assert 'Reference' in header
    assert 'Value' in header
    assert 'Description' in header
    assert 'Datasheet' in header
    assert 'Type' in header
    assert 'Amps' in header
    assert 'FS' in header
    assert 'WL' in header
    assert 'BL' in header

    # Verify separator has alignment markers
    assert '|' in result[1]
    assert '-' in result[1]

    # Verify data rows contain component data (sorted by ref: BT1, CB1, LIGHT1)
    data_rows = '\n'.join(result[2:])
    assert 'BT1' in data_rows
    assert 'CB1' in data_rows
    assert 'LIGHT1' in data_rows
    assert '10A' in data_rows
    assert 'LED' in data_rows
    assert 'Battery' in data_rows
    assert '100.0' in data_rows  # CB1 FS
    assert '200.0' in data_rows  # LIGHT1 FS
    assert '5.0' in data_rows    # LIGHT1 load


def test_generate_component_bom_table_empty():
    """Test component BOM table with no components"""
    components = []

    result = _generate_component_bom_table(components)

    # Should still have header and separator
    assert len(result) >= 2
    assert 'Reference' in result[0]
