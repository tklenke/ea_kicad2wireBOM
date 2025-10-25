# ABOUTME: Tests for SVG routing diagram generation
# ABOUTME: Validates data structures, coordinate transformations, and SVG rendering

import pytest
from kicad2wireBOM.diagram_generator import (
    DiagramComponent,
    DiagramWireSegment,
    SystemDiagram,
)


def test_diagram_component_creation():
    """Test DiagramComponent stores ref, fs, bl correctly."""
    comp = DiagramComponent(ref="CB1", fs=10.0, bl=20.0)

    assert comp.ref == "CB1"
    assert comp.fs == 10.0
    assert comp.bl == 20.0


def test_manhattan_path_calculation():
    """Test manhattan_path property returns 3-point BL-first path."""
    # Test case 1: comp1=(10, 30), comp2=(50, 10)
    comp1 = DiagramComponent(ref="CB1", fs=10.0, bl=30.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, bl=10.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    path = segment.manhattan_path

    # Expected: [(10, 30), (10, 10), (50, 10)]
    # First move along BL axis (30→10), then along FS axis (10→50)
    assert len(path) == 3
    assert path[0] == (10.0, 30.0)  # Start at comp1
    assert path[1] == (10.0, 10.0)  # Corner (BL move)
    assert path[2] == (50.0, 10.0)  # End at comp2 (FS move)


def test_manhattan_path_calculation_case2():
    """Test manhattan_path with different coordinates."""
    # Test case 2: comp1=(0, 0), comp2=(100, 50)
    comp1 = DiagramComponent(ref="BT1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="BUS1", fs=100.0, bl=50.0)
    segment = DiagramWireSegment(label="P1A", comp1=comp1, comp2=comp2)

    path = segment.manhattan_path

    # Expected: [(0, 0), (0, 50), (100, 50)]
    assert len(path) == 3
    assert path[0] == (0.0, 0.0)
    assert path[1] == (0.0, 50.0)
    assert path[2] == (100.0, 50.0)


def test_system_diagram_creation():
    """Test SystemDiagram stores all required data."""
    comp1 = DiagramComponent(ref="CB1", fs=10.0, bl=20.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, bl=30.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=10.0,
        fs_max=50.0,
        bl_min=20.0,
        bl_max=30.0
    )

    assert diagram.system_code == "L"
    assert len(diagram.components) == 2
    assert len(diagram.wire_segments) == 1
    assert diagram.fs_min == 10.0
    assert diagram.fs_max == 50.0
    assert diagram.bl_min == 20.0
    assert diagram.bl_max == 30.0
