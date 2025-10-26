# ABOUTME: Output directory management and stdout/stderr capture
# ABOUTME: Creates unified output directories and tees console output to files

import sys
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Optional


def create_output_directory(source_path: str, dest_dir: Optional[str], force: bool) -> Path:
    """
    Create output directory for kicad2wireBOM outputs.

    Args:
        source_path: Path to source .kicad_sch file
        dest_dir: Parent directory for output (None = current directory)
        force: If True, delete existing directory; if False, keep existing

    Returns:
        Path object to created output directory

    Examples:
        source_path="/path/to/myproject.kicad_sch", dest_dir=None
        → Creates "./myproject/" in current directory

        source_path="/path/to/myproject.kicad_sch", dest_dir="/output/"
        → Creates "/output/myproject/"
    """
    # Extract base name from source (e.g., "myproject.kicad_sch" → "myproject")
    source = Path(source_path)
    basename = source.stem

    # Determine parent directory for output
    if dest_dir is None:
        parent = Path.cwd()
    else:
        parent = Path(dest_dir)

    # Create output directory path
    output_dir = parent / basename

    # Handle existing directory
    if output_dir.exists():
        if force:
            # Delete existing directory and all contents
            shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True)
        # else: keep existing directory (don't prompt in non-interactive mode)
    else:
        # Create new directory
        output_dir.mkdir(parents=True)

    return output_dir


class TeeWriter:
    """
    Write to both a file and original stream (console).

    Used to capture stdout/stderr to files while still displaying to console.
    """

    def __init__(self, file_stream, original_stream):
        """
        Initialize TeeWriter.

        Args:
            file_stream: File object to write to
            original_stream: Original stream (sys.stdout or sys.stderr)
        """
        self.file_stream = file_stream
        self.original_stream = original_stream

    def write(self, text):
        """Write text to both file and original stream"""
        self.file_stream.write(text)
        self.original_stream.write(text)

    def flush(self):
        """Flush both streams"""
        self.file_stream.flush()
        self.original_stream.flush()


@contextmanager
def capture_output(output_dir: Path):
    """
    Context manager to capture stdout and stderr to files while displaying to console.

    Creates stdout.txt and stderr.txt in output_dir, replacing sys.stdout and
    sys.stderr with TeeWriter instances. Restores original streams on exit.

    Args:
        output_dir: Directory to write stdout.txt and stderr.txt

    Example:
        with capture_output(Path("/output/myproject/")):
            print("This goes to both console and stdout.txt")
    """
    # Save original streams
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Open output files
    stdout_file = open(output_dir / "stdout.txt", "w")
    stderr_file = open(output_dir / "stderr.txt", "w")

    try:
        # Replace sys.stdout and sys.stderr with TeeWriter instances
        sys.stdout = TeeWriter(stdout_file, original_stdout)
        sys.stderr = TeeWriter(stderr_file, original_stderr)

        yield

    finally:
        # Restore original streams
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        # Close files
        stdout_file.close()
        stderr_file.close()
