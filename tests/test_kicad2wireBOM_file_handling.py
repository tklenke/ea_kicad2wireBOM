# ABOUTME: Tests for kicad2wireBOM file handling behavior
# ABOUTME: Validates source file checks, destination overwrite protection, and force flag

import subprocess
import sys
import tempfile
import os
from pathlib import Path


def test_missing_source_file_fails_gracefully():
    """Test that missing source file produces clear error message"""
    with tempfile.TemporaryDirectory() as tmpdir:
        strNonexistentFile = os.path.join(tmpdir, "nonexistent.net")
        strOutputFile = os.path.join(tmpdir, "output.csv")

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strNonexistentFile, strOutputFile],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()
        assert strNonexistentFile in result.stderr


def test_existing_destination_prompts_for_confirmation():
    """Test that existing destination file prompts user before overwriting"""
    with tempfile.TemporaryDirectory() as tmpdir:
        strSourceFile = os.path.join(tmpdir, "source.net")
        strDestFile = os.path.join(tmpdir, "output.csv")

        # Create both files
        Path(strSourceFile).write_text("dummy netlist content")
        Path(strDestFile).write_text("existing output")

        # Run with 'n' (no) response to overwrite prompt
        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strSourceFile, strDestFile],
            input="n\n",
            capture_output=True,
            text=True
        )

        # Should ask about overwrite
        assert "overwrite" in result.stdout.lower() or "exists" in result.stdout.lower()
        # Should not overwrite (exit with error or success but no change)
        assert result.returncode != 0 or Path(strDestFile).read_text() == "existing output"


def test_force_flag_skips_overwrite_confirmation():
    """Test that -f flag overwrites without prompting"""
    with tempfile.TemporaryDirectory() as tmpdir:
        strSourceFile = os.path.join(tmpdir, "source.net")
        strDestFile = os.path.join(tmpdir, "output.csv")

        # Create both files
        Path(strSourceFile).write_text("dummy netlist content")
        Path(strDestFile).write_text("existing output")

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", "-f", strSourceFile, strDestFile],
            capture_output=True,
            text=True
        )

        # Should not prompt (stdout should not mention overwrite)
        assert "overwrite" not in result.stdout.lower()


def test_successful_processing_with_new_destination():
    """Test that processing succeeds with non-existent destination file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        strSourceFile = os.path.join(tmpdir, "source.net")
        strDestFile = os.path.join(tmpdir, "output.csv")

        # Create only source file
        Path(strSourceFile).write_text("dummy netlist content")

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strSourceFile, strDestFile],
            capture_output=True,
            text=True
        )

        # Should succeed (for now, even with dummy content)
        assert result.returncode == 0
