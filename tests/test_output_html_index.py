# ABOUTME: Tests for output_html_index module
# ABOUTME: Verifies HTML index page generation with links to all outputs

import pytest
from pathlib import Path

from kicad2wireBOM.output_html_index import write_html_index


def test_write_html_index_basic(tmp_path):
    """Test basic HTML index generation"""
    # Create some output files to reference
    (tmp_path / "wire_bom.csv").touch()
    (tmp_path / "component_bom.csv").touch()
    (tmp_path / "engineering_report.md").touch()
    (tmp_path / "L_System.svg").touch()
    (tmp_path / "P_System.svg").touch()
    (tmp_path / "CB1_Component.svg").touch()
    (tmp_path / "SW1_Component.svg").touch()

    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    # Verify file was created
    assert output_file.exists()

    # Read and verify contents
    content = output_file.read_text()

    # Check for HTML structure
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "</html>" in content
    assert "<head>" in content
    assert "</head>" in content
    assert "<body>" in content
    assert "</body>" in content

    # Check for title
    assert "<title>" in content
    assert "kicad2wireBOM Output" in content

    # Check for links to outputs
    assert 'href="wire_bom.csv"' in content
    assert 'href="component_bom.csv"' in content
    assert 'href="engineering_report.md"' in content
    assert 'href="L_System.svg"' in content
    assert 'href="P_System.svg"' in content
    assert 'href="CB1_Component.svg"' in content
    assert 'href="SW1_Component.svg"' in content


def test_write_html_index_sections(tmp_path):
    """Test that HTML index has proper sections"""
    (tmp_path / "wire_bom.csv").touch()
    (tmp_path / "engineering_report.txt").touch()
    (tmp_path / "L_System.svg").touch()

    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    content = output_file.read_text()

    # Check for section headings
    assert "Bill of Materials" in content or "BOMs" in content
    assert "System Diagrams" in content or "Diagrams" in content
    assert "Engineering Report" in content or "Reports" in content


def test_write_html_index_no_outputs(tmp_path):
    """Test HTML index generation when no output files exist"""
    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    # Should still create a valid HTML file
    assert output_file.exists()

    content = output_file.read_text()
    assert "<!DOCTYPE html>" in content
    assert "<html" in content


def test_write_html_index_only_system_diagrams(tmp_path):
    """Test HTML index with only system diagrams"""
    (tmp_path / "L_System.svg").touch()
    (tmp_path / "P_System.svg").touch()
    (tmp_path / "G_System.svg").touch()

    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    content = output_file.read_text()

    # Should have links to all system diagrams
    assert 'href="L_System.svg"' in content
    assert 'href="P_System.svg"' in content
    assert 'href="G_System.svg"' in content


def test_write_html_index_only_component_diagrams(tmp_path):
    """Test HTML index with only component diagrams"""
    (tmp_path / "CB1_Component.svg").touch()
    (tmp_path / "CB2_Component.svg").touch()
    (tmp_path / "SW1_Component.svg").touch()

    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    content = output_file.read_text()

    # Should have links to all component diagrams
    assert 'href="CB1_Component.svg"' in content
    assert 'href="CB2_Component.svg"' in content
    assert 'href="SW1_Component.svg"' in content


def test_write_html_index_with_star_diagrams(tmp_path):
    """Test HTML index includes star diagrams section"""
    # Create some star diagram files
    (tmp_path / "CB1_Star.svg").touch()
    (tmp_path / "CB2_Star.svg").touch()
    (tmp_path / "SW1_Star.svg").touch()

    output_file = tmp_path / "index.html"
    write_html_index(tmp_path, str(output_file))

    content = output_file.read_text()

    # Should have Star Diagrams section
    assert "Star Diagrams" in content

    # Should have links to all star diagrams
    assert 'href="CB1_Star.svg"' in content
    assert 'href="CB2_Star.svg"' in content
    assert 'href="SW1_Star.svg"' in content
