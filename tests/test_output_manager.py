# ABOUTME: Tests for output_manager module
# ABOUTME: Verifies directory creation, force overwrite, and TeeWriter functionality

import pytest
import shutil
import sys
from pathlib import Path
from io import StringIO

from kicad2wireBOM.output_manager import create_output_directory, TeeWriter, capture_output


def test_create_output_directory_basic(tmp_path):
    """Test basic directory creation from source path"""
    source = tmp_path / "myproject.kicad_sch"
    source.touch()

    output_dir = create_output_directory(str(source), str(tmp_path), force=False)

    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.name == "myproject"
    assert output_dir.parent == tmp_path


def test_create_output_directory_default_dest(tmp_path):
    """Test directory creation with no dest specified (uses current directory)"""
    source = tmp_path / "aircraft.kicad_sch"
    source.touch()

    # Pass None for dest to use current directory
    output_dir = create_output_directory(str(source), None, force=False)

    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.name == "aircraft"


def test_create_output_directory_with_dest_dir(tmp_path):
    """Test directory creation with explicit dest directory"""
    source = tmp_path / "myproject.kicad_sch"
    source.touch()

    dest_parent = tmp_path / "output"
    dest_parent.mkdir()

    output_dir = create_output_directory(str(source), str(dest_parent), force=False)

    assert output_dir.exists()
    assert output_dir == dest_parent / "myproject"


def test_create_output_directory_force_overwrites_existing(tmp_path):
    """Test that force=True deletes and recreates existing directory"""
    source = tmp_path / "myproject.kicad_sch"
    source.touch()

    # Create existing directory with a file
    existing_dir = tmp_path / "myproject"
    existing_dir.mkdir()
    existing_file = existing_dir / "oldfile.txt"
    existing_file.write_text("old content")

    # Call with force=True
    output_dir = create_output_directory(str(source), str(tmp_path), force=True)

    # Directory should exist but old file should be gone
    assert output_dir.exists()
    assert not existing_file.exists()


def test_create_output_directory_no_force_keeps_existing(tmp_path):
    """Test that force=False keeps existing directory without prompting in tests"""
    source = tmp_path / "myproject.kicad_sch"
    source.touch()

    # Create existing directory with a file
    existing_dir = tmp_path / "myproject"
    existing_dir.mkdir()
    existing_file = existing_dir / "oldfile.txt"
    existing_file.write_text("old content")

    # Call with force=False (should not prompt in non-interactive test)
    output_dir = create_output_directory(str(source), str(tmp_path), force=False)

    # Directory and file should still exist
    assert output_dir.exists()
    assert existing_file.exists()
    assert existing_file.read_text() == "old content"


def test_tee_writer_writes_to_both_streams():
    """Test that TeeWriter writes to both file and original stream"""
    original_stream = StringIO()
    file_stream = StringIO()

    tee = TeeWriter(file_stream, original_stream)

    tee.write("Hello, world!")
    tee.flush()

    # Should be written to both streams
    assert file_stream.getvalue() == "Hello, world!"
    assert original_stream.getvalue() == "Hello, world!"


def test_tee_writer_multiple_writes():
    """Test that TeeWriter handles multiple writes correctly"""
    original_stream = StringIO()
    file_stream = StringIO()

    tee = TeeWriter(file_stream, original_stream)

    tee.write("Line 1\n")
    tee.write("Line 2\n")
    tee.flush()

    expected = "Line 1\nLine 2\n"
    assert file_stream.getvalue() == expected
    assert original_stream.getvalue() == expected


def test_capture_output_context_manager(tmp_path):
    """Test that capture_output context manager captures stdout and stderr"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Use context manager to capture output
    with capture_output(output_dir):
        print("This goes to stdout")
        print("This goes to stderr", file=sys.stderr)

    # Check files were created and contain expected content
    stdout_file = output_dir / "stdout.txt"
    stderr_file = output_dir / "stderr.txt"

    assert stdout_file.exists()
    assert stderr_file.exists()

    assert "This goes to stdout" in stdout_file.read_text()
    assert "This goes to stderr" in stderr_file.read_text()


def test_capture_output_restores_original_streams(tmp_path):
    """Test that capture_output restores original sys.stdout and sys.stderr"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    with capture_output(output_dir):
        # Inside context, streams should be different
        assert sys.stdout != original_stdout
        assert sys.stderr != original_stderr

    # After context, streams should be restored
    assert sys.stdout == original_stdout
    assert sys.stderr == original_stderr
