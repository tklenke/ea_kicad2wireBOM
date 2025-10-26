# ABOUTME: Comprehensive integration tests for Phase 11 unified output
# ABOUTME: Verifies end-to-end Phase 11 functionality with all outputs

import pytest
import subprocess
import sys
from pathlib import Path


def test_phase_11_complete_integration(tmp_path):
    """
    Comprehensive test verifying all Phase 11 outputs are generated correctly.

    Tests the complete Phase 11 unified output directory structure:
    - Directory named after source file
    - Wire BOM CSV
    - Component BOM CSV
    - Engineering report
    - HTML index
    - System diagrams
    - Component diagrams
    - Console logs
    """
    # Use test fixture
    fixture_path = Path(__file__).parent / "fixtures" / "test_01_fixture.kicad_sch"
    source_file = tmp_path / "test_project.kicad_sch"

    # Copy fixture
    import shutil
    shutil.copy(fixture_path, source_file)

    # Run kicad2wireBOM
    result = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", str(source_file), str(tmp_path)],
        capture_output=True,
        text=True
    )

    # Should succeed
    assert result.returncode == 0, f"Process failed: {result.stderr}"

    # Verify output directory created with correct name
    output_dir = tmp_path / "test_project"
    assert output_dir.exists(), "Output directory not created"
    assert output_dir.is_dir(), "Output path is not a directory"

    # Verify wire BOM
    wire_bom = output_dir / "wire_bom.csv"
    assert wire_bom.exists(), "Wire BOM not created"
    wire_bom_content = wire_bom.read_text()
    assert "Wire Label" in wire_bom_content, "Wire BOM missing header"
    assert len(wire_bom_content) > 100, "Wire BOM appears empty"

    # Verify component BOM
    component_bom = output_dir / "component_bom.csv"
    assert component_bom.exists(), "Component BOM not created"
    component_bom_content = component_bom.read_text()
    assert "Reference" in component_bom_content, "Component BOM missing header"
    assert "FS" in component_bom_content, "Component BOM missing FS column"
    assert "WL" in component_bom_content, "Component BOM missing WL column"
    assert "BL" in component_bom_content, "Component BOM missing BL column"

    # Verify engineering report
    eng_report = output_dir / "engineering_report.txt"
    assert eng_report.exists(), "Engineering report not created"
    eng_report_content = eng_report.read_text()
    assert "ENGINEERING REPORT" in eng_report_content, "Report missing title"
    assert "Total Components:" in eng_report_content, "Report missing component count"
    assert "Total Wires:" in eng_report_content, "Report missing wire count"
    assert "COMPONENT SUMMARY" in eng_report_content, "Report missing component summary"
    assert "WIRE SUMMARY" in eng_report_content, "Report missing wire summary"

    # Verify HTML index
    html_index = output_dir / "index.html"
    assert html_index.exists(), "HTML index not created"
    html_index_content = html_index.read_text()
    assert "<!DOCTYPE html>" in html_index_content, "HTML missing DOCTYPE"
    assert "<html" in html_index_content, "HTML missing html tag"
    assert "kicad2wireBOM Output" in html_index_content, "HTML missing title"
    assert 'href="wire_bom.csv"' in html_index_content, "HTML missing wire BOM link"
    assert 'href="component_bom.csv"' in html_index_content, "HTML missing component BOM link"
    assert 'href="engineering_report.txt"' in html_index_content, "HTML missing report link"

    # Verify system diagrams exist
    system_diagrams = list(output_dir.glob("*_System.svg"))
    assert len(system_diagrams) > 0, "No system diagrams generated"
    for diagram in system_diagrams:
        assert diagram.stat().st_size > 0, f"System diagram {diagram.name} is empty"
        # Verify it's referenced in HTML index
        assert f'href="{diagram.name}"' in html_index_content, f"System diagram {diagram.name} not in HTML index"

    # Verify component diagrams exist
    component_diagrams = list(output_dir.glob("*_Component.svg"))
    assert len(component_diagrams) > 0, "No component diagrams generated"
    for diagram in component_diagrams:
        assert diagram.stat().st_size > 0, f"Component diagram {diagram.name} is empty"
        # Verify it's referenced in HTML index
        assert f'href="{diagram.name}"' in html_index_content, f"Component diagram {diagram.name} not in HTML index"

    # Verify console logs
    stdout_log = output_dir / "stdout.txt"
    assert stdout_log.exists(), "stdout.txt not created"
    stdout_content = stdout_log.read_text()
    assert "Processing" in stdout_content, "stdout missing processing messages"
    assert "Generated" in stdout_content or "Generating" in stdout_content, "stdout missing generation messages"

    stderr_log = output_dir / "stderr.txt"
    assert stderr_log.exists(), "stderr.txt not created"
    # stderr may be empty or have warnings - that's okay

    # Verify logs are referenced in HTML
    assert 'href="stdout.txt"' in html_index_content, "HTML missing stdout link"
    assert 'href="stderr.txt"' in html_index_content, "HTML missing stderr link"

    print(f"\n✅ Phase 11 integration test PASSED")
    print(f"   Output directory: {output_dir}")
    print(f"   Wire BOM: {wire_bom.stat().st_size} bytes")
    print(f"   Component BOM: {component_bom.stat().st_size} bytes")
    print(f"   Engineering report: {eng_report.stat().st_size} bytes")
    print(f"   HTML index: {html_index.stat().st_size} bytes")
    print(f"   System diagrams: {len(system_diagrams)}")
    print(f"   Component diagrams: {len(component_diagrams)}")


def test_phase_11_force_flag_integration(tmp_path):
    """
    Test Phase 11 with force flag - verify directory is deleted and recreated.
    """
    # Use test fixture
    fixture_path = Path(__file__).parent / "fixtures" / "test_01_fixture.kicad_sch"
    source_file = tmp_path / "test_project.kicad_sch"

    # Copy fixture
    import shutil
    shutil.copy(fixture_path, source_file)

    # Run once to create outputs
    result1 = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", str(source_file), str(tmp_path)],
        capture_output=True,
        text=True
    )
    assert result1.returncode == 0

    output_dir = tmp_path / "test_project"

    # Create a marker file
    marker = output_dir / "marker.txt"
    marker.write_text("original run")
    assert marker.exists()

    # Run again with force flag
    result2 = subprocess.run(
        [sys.executable, "-m", "kicad2wireBOM", "-f", str(source_file), str(tmp_path)],
        capture_output=True,
        text=True
    )
    assert result2.returncode == 0

    # Marker should be gone (directory was deleted and recreated)
    assert not marker.exists(), "Force flag did not delete existing directory"

    # But new outputs should exist
    assert (output_dir / "wire_bom.csv").exists()
    assert (output_dir / "index.html").exists()
