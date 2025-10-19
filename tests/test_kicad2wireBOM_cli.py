# ABOUTME: Tests for kicad2wireBOM command line interface
# ABOUTME: Validates CLI argument parsing and help text output

import subprocess
import sys


def test_help_option_displays_description():
    """Test that --help displays program description and usage"""
    result = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "KiCad" in result.stdout
    assert "schematic" in result.stdout.lower()
    assert "wire" in result.stdout.lower()
    assert "BOM" in result.stdout or "bom" in result.stdout.lower()
    assert "CSV" in result.stdout or "csv" in result.stdout.lower()


def test_help_option_shows_input_file_argument():
    """Test that --help shows input file argument"""
    result = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "input" in result.stdout.lower() or "file" in result.stdout.lower()


def test_help_option_shows_output_file_argument():
    """Test that --help shows output file argument"""
    result = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "output" in result.stdout.lower()
