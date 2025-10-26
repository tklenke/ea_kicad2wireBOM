# ABOUTME: Tests for kicad2wireBOM file handling behavior
# ABOUTME: Validates source file checks, directory overwrite protection, and force flag

import subprocess
import sys
import tempfile
import os
import shutil
from pathlib import Path


def test_missing_source_file_fails_gracefully():
    """Test that missing source file produces clear error message"""
    with tempfile.TemporaryDirectory() as tmpdir:
        strNonexistentFile = os.path.join(tmpdir, "nonexistent.kicad_sch")
        strOutputDir = tmpdir

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strNonexistentFile, strOutputDir],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()
        assert strNonexistentFile in result.stderr


def test_existing_destination_directory_kept_without_force():
    """Test that existing destination directory is kept when force flag not provided"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use real test fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_01_fixture.kicad_sch"
        strSourceFile = os.path.join(tmpdir, "source.kicad_sch")

        # Copy fixture
        shutil.copy(fixture_path, strSourceFile)

        # Create existing output directory with a marker file
        existing_dir = Path(tmpdir) / "source"
        existing_dir.mkdir()
        marker_file = existing_dir / "existing_marker.txt"
        marker_file.write_text("existing content")

        # Run without force flag
        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strSourceFile, tmpdir],
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0
        # Existing marker file should still exist (directory not deleted)
        assert marker_file.exists()
        # New outputs should also exist
        assert (existing_dir / "wire_bom.csv").exists()


def test_force_flag_deletes_existing_directory():
    """Test that -f flag deletes and recreates existing directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use real test fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_01_fixture.kicad_sch"
        strSourceFile = os.path.join(tmpdir, "source.kicad_sch")

        # Copy fixture
        shutil.copy(fixture_path, strSourceFile)

        # Create existing output directory with a marker file
        existing_dir = Path(tmpdir) / "source"
        existing_dir.mkdir()
        marker_file = existing_dir / "existing_marker.txt"
        marker_file.write_text("existing content")

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", "-f", strSourceFile, tmpdir],
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0
        # Existing marker file should be gone (directory was deleted and recreated)
        assert not marker_file.exists()
        # New outputs should exist
        assert (existing_dir / "wire_bom.csv").exists()


def test_successful_processing_with_new_destination():
    """Test that processing succeeds and creates output directory with files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use real test fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_01_fixture.kicad_sch"
        strSourceFile = os.path.join(tmpdir, "source.kicad_sch")

        # Copy fixture to temp location
        shutil.copy(fixture_path, strSourceFile)

        result = subprocess.run(
            [sys.executable, "-m", "kicad2wireBOM", strSourceFile, tmpdir],
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Verify output directory was created
        output_dir = Path(tmpdir) / "source"
        assert output_dir.exists()
        assert output_dir.is_dir()

        # Verify expected output files were created
        assert (output_dir / "wire_bom.csv").exists()
        assert (output_dir / "stdout.txt").exists()
        assert (output_dir / "stderr.txt").exists()
        # Routing diagrams should also exist
        svg_files = list(output_dir.glob("*.svg"))
        assert len(svg_files) > 0  # At least one diagram should be created
