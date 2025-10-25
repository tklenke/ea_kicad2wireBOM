# ABOUTME: Tests for SVG routing diagram generation
# ABOUTME: Validates data structures, coordinate transformations, and SVG rendering

import pytest
from kicad2wireBOM.diagram_generator import (
    DiagramComponent,
    DiagramWireSegment,
    SystemDiagram,
    group_wires_by_system,
    calculate_bounds,
    calculate_scale,
    transform_to_svg,
)
from kicad2wireBOM.wire_bom import WireConnection


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


def test_group_wires_by_system():
    """Test wire connections are grouped correctly by system code."""
    # Create mock WireConnections with different system codes
    wire_l1a = WireConnection(
        wire_label="L1A",
        from_component="CB1", from_pin="1",
        to_component="SW1", to_pin="2",
        wire_gauge=20, wire_color="white", length=10.0,
        wire_type="Standard", notes="", warnings=[]
    )
    wire_l1b = WireConnection(
        wire_label="L1B",
        from_component="SW1", from_pin="3",
        to_component="L1", to_pin="1",
        wire_gauge=20, wire_color="white", length=15.0,
        wire_type="Standard", notes="", warnings=[]
    )
    wire_l2a = WireConnection(
        wire_label="L2A",
        from_component="CB2", from_pin="1",
        to_component="L2", to_pin="1",
        wire_gauge=20, wire_color="white", length=20.0,
        wire_type="Standard", notes="", warnings=[]
    )
    wire_p1a = WireConnection(
        wire_label="P1A",
        from_component="BT1", from_pin="1",
        to_component="BUS1", to_pin="1",
        wire_gauge=10, wire_color="red", length=5.0,
        wire_type="Standard", notes="", warnings=[]
    )
    wire_g1a = WireConnection(
        wire_label="G1A",
        from_component="BUS1", from_pin="2",
        to_component="GND1", to_pin="1",
        wire_gauge=10, wire_color="black", length=8.0,
        wire_type="Standard", notes="", warnings=[]
    )

    wires = [wire_l1a, wire_l1b, wire_l2a, wire_p1a, wire_g1a]
    groups = group_wires_by_system(wires)

    # Verify correct grouping
    assert "L" in groups
    assert "P" in groups
    assert "G" in groups

    assert len(groups["L"]) == 3
    assert wire_l1a in groups["L"]
    assert wire_l1b in groups["L"]
    assert wire_l2a in groups["L"]

    assert len(groups["P"]) == 1
    assert wire_p1a in groups["P"]

    assert len(groups["G"]) == 1
    assert wire_g1a in groups["G"]


def test_group_wires_skips_unparseable():
    """Test that wires with unparseable labels are skipped."""
    wire_l1a = WireConnection(
        wire_label="L1A",
        from_component="CB1", from_pin="1",
        to_component="SW1", to_pin="2",
        wire_gauge=20, wire_color="white", length=10.0,
        wire_type="Standard", notes="", warnings=[]
    )
    wire_invalid = WireConnection(
        wire_label="INVALID",
        from_component="X1", from_pin="1",
        to_component="X2", to_pin="1",
        wire_gauge=20, wire_color="white", length=10.0,
        wire_type="Standard", notes="", warnings=[]
    )

    wires = [wire_l1a, wire_invalid]
    groups = group_wires_by_system(wires)

    # Only L group should exist
    assert "L" in groups
    assert len(groups) == 1
    assert len(groups["L"]) == 1
    assert wire_l1a in groups["L"]
    # wire_invalid should not be in any group


def test_calculate_bounds_normal():
    """Test bounds calculation with normal coordinates."""
    comp1 = DiagramComponent(ref="C1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="C2", fs=100.0, bl=50.0)
    comp3 = DiagramComponent(ref="C3", fs=50.0, bl=25.0)

    components = [comp1, comp2, comp3]
    fs_min, fs_max, bl_min, bl_max = calculate_bounds(components)

    assert fs_min == 0.0
    assert fs_max == 100.0
    assert bl_min == 0.0
    assert bl_max == 50.0


def test_calculate_bounds_negative_coords():
    """Test bounds calculation with negative coordinates."""
    comp1 = DiagramComponent(ref="C1", fs=-10.0, bl=-20.0)
    comp2 = DiagramComponent(ref="C2", fs=30.0, bl=40.0)

    components = [comp1, comp2]
    fs_min, fs_max, bl_min, bl_max = calculate_bounds(components)

    assert fs_min == -10.0
    assert fs_max == 30.0
    assert bl_min == -20.0
    assert bl_max == 40.0


def test_calculate_bounds_empty_raises():
    """Test that empty component list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot calculate bounds for empty component list"):
        calculate_bounds([])


def test_calculate_scale_normal():
    """Test scale calculation with normal range."""
    # Range 100 inches, target 800px, margin 50px
    # Available = 800 - 100 = 700px
    # Scale = 700 / 100 = 7.0
    fs_range = 100.0
    bl_range = 100.0
    scale = calculate_scale(fs_range, bl_range, target_width=800, margin=50)

    assert scale == 7.0


def test_calculate_scale_large_range():
    """Test that scale is clamped to MIN_SCALE for large ranges."""
    # Range 500 inches, target 800px, margin 50px
    # Available = 700px
    # Raw scale = 700 / 500 = 1.4
    # Should be clamped to MIN_SCALE (2.0)
    fs_range = 500.0
    bl_range = 100.0
    scale = calculate_scale(fs_range, bl_range, target_width=800, margin=50)

    assert scale == 2.0


def test_calculate_scale_small_range():
    """Test that scale is clamped to MAX_SCALE for small ranges."""
    # Range 10 inches, target 800px, margin 50px
    # Available = 700px
    # Raw scale = 700 / 10 = 70.0
    # Should be clamped to MAX_SCALE (10.0)
    fs_range = 10.0
    bl_range = 5.0
    scale = calculate_scale(fs_range, bl_range, target_width=800, margin=50)

    assert scale == 10.0


def test_calculate_scale_zero_range():
    """Test that zero range returns MIN_SCALE."""
    # All components at same location
    fs_range = 0.0
    bl_range = 0.0
    scale = calculate_scale(fs_range, bl_range, target_width=800, margin=50)

    assert scale == 2.0


def test_transform_to_svg_origin():
    """Test transforming origin coordinates to SVG."""
    # Transform (0, 0) with bounds (0, 100, 0, 50), scale=2, margin=10
    svg_x, svg_y = transform_to_svg(
        fs=0.0, bl=0.0,
        fs_min=0.0, bl_min=0.0, bl_max=50.0,
        scale=2.0, margin=10.0
    )

    # X = (0 - 0) * 2 + 10 = 10
    # Y = (50 - 0) * 2 + 10 = 110
    assert svg_x == 10.0
    assert svg_y == 110.0


def test_transform_to_svg_max_coords():
    """Test transforming max coordinates to SVG."""
    # Transform (100, 50) with bounds (0, 100, 0, 50), scale=2, margin=10
    svg_x, svg_y = transform_to_svg(
        fs=100.0, bl=50.0,
        fs_min=0.0, bl_min=0.0, bl_max=50.0,
        scale=2.0, margin=10.0
    )

    # X = (100 - 0) * 2 + 10 = 210
    # Y = (50 - 50) * 2 + 10 = 10
    assert svg_x == 210.0
    assert svg_y == 10.0


def test_transform_to_svg_negative_coords():
    """Test transforming negative coordinates to SVG."""
    # Transform (-10, -20) with bounds (-10, 30, -20, 40), scale=2, margin=10
    svg_x, svg_y = transform_to_svg(
        fs=-10.0, bl=-20.0,
        fs_min=-10.0, bl_min=-20.0, bl_max=40.0,
        scale=2.0, margin=10.0
    )

    # X = (-10 - (-10)) * 2 + 10 = 0 * 2 + 10 = 10
    # Y = (40 - (-20)) * 2 + 10 = 60 * 2 + 10 = 130
    assert svg_x == 10.0
    assert svg_y == 130.0
