# ABOUTME: Tests for output_component_bom module
# ABOUTME: Verifies component BOM CSV generation with coordinates and metadata

import pytest
from pathlib import Path
import csv

from kicad2wireBOM.component import Component
from kicad2wireBOM.output_component_bom import write_component_bom


def test_write_component_bom_basic(tmp_path):
    """Test basic component BOM CSV writing"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0,
                  value='10A Breaker', desc='Circuit Breaker', datasheet='https://example.com/cb1.pdf'),
        Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0,
                  value='Toggle Switch', desc='SPST Switch'),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None,
                  value='Landing Light', desc='LED Landing Light'),
    ]

    output_file = tmp_path / "component_bom.csv"
    write_component_bom(components, str(output_file))

    # Verify file was created
    assert output_file.exists()

    # Read and verify contents
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3

    # Components should be sorted: CB1, LIGHT1, SW1

    # Check CB1
    assert rows[0]['Reference'] == 'CB1'
    assert rows[0]['Value'] == '10A Breaker'
    assert rows[0]['Description'] == 'Circuit Breaker'
    assert rows[0]['Datasheet'] == 'https://example.com/cb1.pdf'
    assert rows[0]['FS'] == '100.0'
    assert rows[0]['WL'] == '25.0'
    assert rows[0]['BL'] == '-5.0'

    # Check LIGHT1
    assert rows[1]['Reference'] == 'LIGHT1'
    assert rows[1]['Value'] == 'Landing Light'

    # Check SW1 (no datasheet)
    assert rows[2]['Reference'] == 'SW1'
    assert rows[2]['Datasheet'] == ''


def test_write_component_bom_sorted_by_reference(tmp_path):
    """Test that components are sorted by reference"""
    components = [
        Component(ref='SW2', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0),
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None),
    ]

    output_file = tmp_path / "component_bom.csv"
    write_component_bom(components, str(output_file))

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should be sorted: CB1, LIGHT1, SW2
    assert rows[0]['Reference'] == 'CB1'
    assert rows[1]['Reference'] == 'LIGHT1'
    assert rows[2]['Reference'] == 'SW2'


def test_write_component_bom_empty_list(tmp_path):
    """Test component BOM with empty component list"""
    components = []

    output_file = tmp_path / "component_bom.csv"
    write_component_bom(components, str(output_file))

    # Verify file was created with headers only
    assert output_file.exists()

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0  # No data rows


def test_write_component_bom_headers(tmp_path):
    """Test that CSV has correct headers"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
    ]

    output_file = tmp_path / "component_bom.csv"
    write_component_bom(components, str(output_file))

    with open(output_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)

    expected_headers = ['Reference', 'Value', 'Description', 'Datasheet', 'Type', 'Amps', 'FS', 'WL', 'BL']
    assert headers == expected_headers


def test_write_component_bom_type_and_amps(tmp_path):
    """Test that type and amps columns are populated correctly"""
    components = [
        Component(ref='CB1', fs=100.0, wl=25.0, bl=-5.0, load=None, rating=10.0),
        Component(ref='LIGHT1', fs=200.0, wl=35.0, bl=5.0, load=5.0, rating=None),
        Component(ref='BT1', fs=50.0, wl=20.0, bl=0.0, load=None, rating=None, source=40.0),
    ]

    output_file = tmp_path / "component_bom.csv"
    write_component_bom(components, str(output_file))

    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # CB1 is a rating (R) component
    assert rows[1]['Reference'] == 'CB1'
    assert rows[1]['Type'] == 'R'
    assert rows[1]['Amps'] == '10.0'

    # LIGHT1 is a load (L) component
    assert rows[2]['Reference'] == 'LIGHT1'
    assert rows[2]['Type'] == 'L'
    assert rows[2]['Amps'] == '5.0'

    # BT1 is a source (S) component
    assert rows[0]['Reference'] == 'BT1'
    assert rows[0]['Type'] == 'S'
    assert rows[0]['Amps'] == '40.0'
