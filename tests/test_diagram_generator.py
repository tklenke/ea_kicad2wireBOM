# ABOUTME: Tests for SVG routing diagram generation
# ABOUTME: Validates data structures, coordinate transformations, and SVG rendering

import pytest
import math
from kicad2wireBOM.diagram_generator import (
    DiagramComponent,
    DiagramWireSegment,
    SystemDiagram,
    group_wires_by_system,
    calculate_bounds,
    calculate_scale,
    transform_to_svg,
    calculate_wire_label_position,
    build_system_diagram,
    generate_svg,
    scale_bl_nonlinear,
    project_3d_to_2d,
)
from kicad2wireBOM.reference_data import DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.component import Component
from pathlib import Path
import tempfile


def test_diagram_component_creation():
    """Test DiagramComponent stores ref, fs, wl, bl correctly."""
    comp = DiagramComponent(ref="CB1", fs=10.0, wl=5.0, bl=20.0)

    assert comp.ref == "CB1"
    assert comp.fs == 10.0
    assert comp.wl == 5.0
    assert comp.bl == 20.0


def test_manhattan_path_calculation():
    """Test manhattan_path property returns 5-point 3D path with BL→FS→WL routing."""
    # Test case 1: comp1=(FS=10, WL=0, BL=30), comp2=(FS=50, WL=0, BL=10)
    comp1 = DiagramComponent(ref="CB1", fs=10.0, wl=0.0, bl=30.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=0.0, bl=10.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    path = segment.manhattan_path

    # Expected: 5 3D points with BL→FS→WL routing
    assert len(path) == 5
    assert path[0] == (10.0, 0.0, 30.0)  # Start at comp1
    assert path[1] == (10.0, 0.0, 10.0)  # BL move
    assert path[2] == (50.0, 0.0, 10.0)  # FS move
    assert path[3] == (50.0, 0.0, 10.0)  # WL move (no change since WL1=WL2=0)
    assert path[4] == (50.0, 0.0, 10.0)  # End at comp2


def test_manhattan_path_calculation_case2():
    """Test manhattan_path with different coordinates."""
    # Test case 2: comp1=(FS=0, WL=0, BL=0), comp2=(FS=100, WL=0, BL=50)
    comp1 = DiagramComponent(ref="BT1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="BUS1", fs=100.0, wl=0.0, bl=50.0)
    segment = DiagramWireSegment(label="P1A", comp1=comp1, comp2=comp2)

    path = segment.manhattan_path

    # Expected: 5 3D points with BL→FS→WL routing
    assert len(path) == 5
    assert path[0] == (0.0, 0.0, 0.0)    # Start at comp1
    assert path[1] == (0.0, 0.0, 50.0)   # BL move
    assert path[2] == (100.0, 0.0, 50.0) # FS move
    assert path[3] == (100.0, 0.0, 50.0) # WL move (no change since WL1=WL2=0)
    assert path[4] == (100.0, 0.0, 50.0) # End at comp2


def test_system_diagram_creation():
    """Test SystemDiagram stores all required data."""
    comp1 = DiagramComponent(ref="CB1", fs=10.0, wl=0.0, bl=20.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=0.0, bl=30.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=10.0,
        fs_max=50.0,
        bl_min_scaled=scale_bl_nonlinear(20.0),
        bl_max_scaled=scale_bl_nonlinear(30.0),
        fs_min_original=10.0,
        fs_max_original=50.0,
        bl_min_original=20.0,
        bl_max_original=30.0
    )

    assert diagram.system_code == "L"
    assert len(diagram.components) == 2
    assert len(diagram.wire_segments) == 1
    assert diagram.fs_min == 10.0
    assert diagram.fs_max == 50.0
    assert diagram.bl_min_original == 20.0
    assert diagram.bl_max_original == 30.0


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
    comp1 = DiagramComponent(ref="C1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="C2", fs=100.0, wl=0.0, bl=50.0)
    comp3 = DiagramComponent(ref="C3", fs=50.0, wl=0.0, bl=25.0)

    components = [comp1, comp2, comp3]
    fs_min, fs_max, bl_scaled_min, bl_scaled_max = calculate_bounds(components)

    assert fs_min == 0.0
    assert fs_max == 100.0
    # BL bounds are scaled now
    assert bl_scaled_min == scale_bl_nonlinear(0.0)  # 0.0
    assert bl_scaled_max == pytest.approx(scale_bl_nonlinear(50.0))


def test_calculate_bounds_negative_coords():
    """Test bounds calculation with negative coordinates."""
    comp1 = DiagramComponent(ref="C1", fs=-10.0, wl=0.0, bl=-20.0)
    comp2 = DiagramComponent(ref="C2", fs=30.0, wl=0.0, bl=40.0)

    components = [comp1, comp2]
    fs_min, fs_max, bl_scaled_min, bl_scaled_max = calculate_bounds(components)

    assert fs_min == -10.0
    assert fs_max == 30.0
    # BL bounds are scaled now
    assert bl_scaled_min == pytest.approx(scale_bl_nonlinear(-20.0))
    assert bl_scaled_max == pytest.approx(scale_bl_nonlinear(40.0))


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
    # New orientation: BL->X (right), FS->Y (up, flipped)
    # BL is scaled non-linearly: scale_bl_nonlinear(0) = 0
    svg_x, svg_y = transform_to_svg(
        fs=0.0, bl=0.0,
        fs_min=0.0, fs_max=100.0, bl_scaled_min=0.0,
        scale_x=2.0, scale_y=2.0, margin=10.0
    )

    # X = (0 - 0) * 2 + 10 = 10
    # Y = (100 - 0) * 2 + 10 = 210 (FS=0 is at bottom, maps to high Y)
    assert svg_x == 10.0
    assert svg_y == 210.0


def test_transform_to_svg_max_coords():
    """Test transforming max coordinates to SVG."""
    # Transform (100, 50) with bounds (0, 100, 0, 50), scale=2, margin=10
    # New orientation: BL->X (right), FS->Y (up, flipped)
    # BL is scaled: scale_bl_nonlinear(50) ≈ 40.5
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear
    bl_scaled = scale_bl_nonlinear(50.0)

    svg_x, svg_y = transform_to_svg(
        fs=100.0, bl=50.0,
        fs_min=0.0, fs_max=100.0, bl_scaled_min=0.0,
        scale_x=2.0, scale_y=2.0, margin=10.0
    )

    # X = (bl_scaled - 0) * 2 + 10
    # Y = (100 - 100) * 2 + 10 = 10 (FS=100 is at top, maps to low Y)
    expected_x = bl_scaled * 2.0 + 10.0
    assert svg_x == pytest.approx(expected_x)
    assert svg_y == 10.0


def test_transform_to_svg_negative_coords():
    """Test transforming negative coordinates to SVG."""
    # Transform (-10, -20) with bounds (-10, 30, -20, 40), scale=2, margin=10
    # New orientation: BL->X (right), FS->Y (up, flipped)
    # BL is scaled: scale_bl_nonlinear(-20) and scale_bl_nonlinear(-20) for min
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear
    bl_scaled_min = scale_bl_nonlinear(-20.0)
    bl_scaled = scale_bl_nonlinear(-20.0)

    svg_x, svg_y = transform_to_svg(
        fs=-10.0, bl=-20.0,
        fs_min=-10.0, fs_max=30.0, bl_scaled_min=bl_scaled_min,
        scale_x=2.0, scale_y=2.0, margin=10.0
    )

    # X = (bl_scaled - bl_scaled_min) * 2 + 10 = 0 * 2 + 10 = 10
    # Y = (30 - (-10)) * 2 + 10 = 40 * 2 + 10 = 90
    assert svg_x == 10.0
    assert svg_y == 90.0


def test_transform_to_svg_v2_origin():
    """Test that FS=0, BL=0 maps to origin position (v2 transform)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2

    # Origin at (550, 200) in SVG coordinates
    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    svg_x, svg_y = transform_to_svg_v2(
        fs=0.0, bl=0.0,
        origin_svg_x=origin_x, origin_svg_y=origin_y,
        scale_x=scale_x, scale_y=scale_y
    )

    # BL=0, FS=0 should map to origin
    assert svg_x == origin_x
    assert svg_y == origin_y


def test_transform_to_svg_v2_fs_positive():
    """Test that FS+ renders below origin (higher svg_y) (v2 transform)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2

    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    svg_x, svg_y = transform_to_svg_v2(
        fs=50.0, bl=0.0,
        origin_svg_x=origin_x, origin_svg_y=origin_y,
        scale_x=scale_x, scale_y=scale_y
    )

    # FS+ should move down (svg_y increases) - rear down
    assert svg_x == origin_x  # BL=0, no horizontal movement
    assert svg_y == origin_y + (50.0 * scale_y)  # 200 + 100 = 300


def test_transform_to_svg_v2_fs_negative():
    """Test that FS- renders above origin (lower svg_y) (v2 transform)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2

    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    svg_x, svg_y = transform_to_svg_v2(
        fs=-50.0, bl=0.0,
        origin_svg_x=origin_x, origin_svg_y=origin_y,
        scale_x=scale_x, scale_y=scale_y
    )

    # FS- should move up (svg_y decreases) - nose up
    assert svg_x == origin_x  # BL=0, no horizontal movement
    assert svg_y == origin_y + (-50.0 * scale_y)  # 200 + (-100) = 100


def test_transform_to_svg_v2_bl_positive():
    """Test that BL+ renders right of origin (v2 transform)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2, scale_bl_nonlinear_v2

    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    svg_x, svg_y = transform_to_svg_v2(
        fs=0.0, bl=20.0,
        origin_svg_x=origin_x, origin_svg_y=origin_y,
        scale_x=scale_x, scale_y=scale_y
    )

    # BL+ should move right (svg_x increases)
    # BL=20 scaled with v2: 20 * 3.0 = 60
    bl_scaled = scale_bl_nonlinear_v2(20.0)
    assert svg_x == origin_x + (bl_scaled * scale_x)  # 550 + (60 * 2) = 670
    assert svg_y == origin_y  # FS=0, no vertical movement


def test_transform_to_svg_v2_bl_negative():
    """Test that BL- renders left of origin (v2 transform)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2, scale_bl_nonlinear_v2

    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    svg_x, svg_y = transform_to_svg_v2(
        fs=0.0, bl=-20.0,
        origin_svg_x=origin_x, origin_svg_y=origin_y,
        scale_x=scale_x, scale_y=scale_y
    )

    # BL- should move left (svg_x decreases)
    # BL=-20 scaled with v2: -20 * 3.0 = -60
    bl_scaled = scale_bl_nonlinear_v2(-20.0)
    assert svg_x == origin_x + (bl_scaled * scale_x)  # 550 + (-60 * 2) = 430
    assert svg_y == origin_y  # FS=0, no vertical movement


def test_label_position_longer_horizontal():
    """Test label position when FS segment is longer."""
    # Path: 5 3D points representing BL→FS→WL routing
    # Segment 1 (BL): 30 to 10 = 20 inches
    # Segment 2 (FS): 10 to 50 = 40 inches (longest)
    # Segment 3 (WL): 0 to 0 = 0 inches
    # FS segment is longest, so label should be at its midpoint
    path = [(10.0, 0.0, 30.0), (10.0, 0.0, 10.0), (50.0, 0.0, 10.0),
            (50.0, 0.0, 10.0), (50.0, 0.0, 10.0)]
    label_fs, label_wl, label_bl, axis = calculate_wire_label_position(path)

    # Midpoint of FS segment: ((10 + 50) / 2, 0, 10) = (30, 0, 10)
    assert label_fs == 30.0
    assert label_wl == 0.0
    assert label_bl == 10.0
    assert axis == 'FS'


def test_label_position_longer_vertical():
    """Test label position when BL segment is longer."""
    # Path: 5 3D points representing BL→FS→WL routing
    # Segment 1 (BL): 30 to 5 = 25 inches (longest)
    # Segment 2 (FS): 10 to 20 = 10 inches
    # Segment 3 (WL): 0 to 0 = 0 inches
    # BL segment is longest, so label should be at its midpoint
    path = [(10.0, 0.0, 30.0), (10.0, 0.0, 5.0), (20.0, 0.0, 5.0),
            (20.0, 0.0, 5.0), (20.0, 0.0, 5.0)]
    label_fs, label_wl, label_bl, axis = calculate_wire_label_position(path)

    # Midpoint of BL segment: (10, 0, (30 + 5) / 2) = (10, 0, 17.5)
    assert label_fs == 10.0
    assert label_wl == 0.0
    assert label_bl == 17.5
    assert axis == 'BL'


def test_label_position_longer_wl():
    """Test label position when WL segment is longer."""
    # Path: 5 3D points representing BL→FS→WL routing
    # Segment 1 (BL): 30 to 10 = 20 inches
    # Segment 2 (FS): 10 to 30 = 20 inches
    # Segment 3 (WL): 5 to 35 = 30 inches (longest)
    # WL segment is longest, so label should be at its midpoint
    path = [(10.0, 5.0, 30.0), (10.0, 5.0, 10.0), (30.0, 5.0, 10.0),
            (30.0, 35.0, 10.0), (30.0, 35.0, 10.0)]
    label_fs, label_wl, label_bl, axis = calculate_wire_label_position(path)

    # Midpoint of WL segment: (30, (5 + 35) / 2, 10) = (30, 20, 10)
    assert label_fs == 30.0
    assert label_wl == 20.0
    assert label_bl == 10.0
    assert axis == 'WL'


def test_label_position_invalid_path():
    """Test that invalid path raises ValueError."""
    # Path with only 2 points (not a valid 5-point 3D Manhattan path)
    path = [(10.0, 0.0, 30.0), (50.0, 0.0, 10.0)]

    with pytest.raises(ValueError, match="Manhattan path must have exactly 5 points"):
        calculate_wire_label_position(path)


def test_build_system_diagram_single_wire():
    """Test building diagram from single wire connection."""
    # Create components
    cb1 = Component(ref="CB1", fs=10.0, wl=0.0, bl=20.0, load=None, rating=10.0)
    sw1 = Component(ref="SW1", fs=50.0, wl=0.0, bl=30.0, load=None, rating=10.0)
    components = {"CB1": cb1, "SW1": sw1}

    # Create wire
    wire_l1a = WireConnection(
        wire_label="L1A",
        from_component="CB1", from_pin="1",
        to_component="SW1", to_pin="2",
        wire_gauge=20, wire_color="white", length=10.0,
        wire_type="Standard", notes="", warnings=[]
    )

    diagram = build_system_diagram("L", [wire_l1a], components)

    assert diagram.system_code == "L"
    assert len(diagram.components) == 2
    assert len(diagram.wire_segments) == 1
    assert diagram.fs_min == 10.0
    assert diagram.fs_max == 50.0
    assert diagram.bl_min_original == 20.0
    assert diagram.bl_max_original == 30.0


def test_build_system_diagram_multiple_wires():
    """Test building diagram with multiple wires and shared components."""
    # Create components
    cb1 = Component(ref="CB1", fs=10.0, wl=0.0, bl=20.0, load=None, rating=10.0)
    sw1 = Component(ref="SW1", fs=50.0, wl=0.0, bl=30.0, load=None, rating=10.0)
    l1 = Component(ref="L1", fs=80.0, wl=0.0, bl=25.0, load=2.0, rating=None)
    components = {"CB1": cb1, "SW1": sw1, "L1": l1}

    # Create wires
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

    diagram = build_system_diagram("L", [wire_l1a, wire_l1b], components)

    assert diagram.system_code == "L"
    assert len(diagram.components) == 3  # CB1, SW1, L1 (unique components)
    assert len(diagram.wire_segments) == 2  # L1A, L1B
    assert diagram.fs_min == 10.0
    assert diagram.fs_max == 80.0
    assert diagram.bl_min_original == 20.0
    assert diagram.bl_max_original == 30.0


def test_generate_svg_creates_file():
    """Test that generate_svg creates an SVG file."""
    # Create a simple diagram
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, wl=0.0, bl=50.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0),
        fs_min_original=0.0,
        fs_max_original=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0
    )

    # Generate SVG to temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_diagram.svg"
        generate_svg(diagram, output_path)

        # Verify file was created
        assert output_path.exists()

        # Read and verify content
        content = output_path.read_text()
        assert '<svg' in content
        assert '</svg>' in content


def test_generate_svg_dimensions():
    """Test that SVG has correct dimensions."""
    # Create diagram with known bounds
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, wl=0.0, bl=50.0)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0),
        fs_min_original=0.0,
        fs_max_original=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_diagram.svg"
        generate_svg(diagram, output_path)

        content = output_path.read_text()
        # Verify SVG tag exists with width and height
        assert 'width=' in content
        assert 'height=' in content
        # Should have white background
        assert 'fill="white"' in content or "fill='white'" in content


def test_wire_labels_offset_from_lines():
    """Test that wire labels are offset to the right from wire lines."""
    # Create diagram with a wire segment
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, wl=0.0, bl=50.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0),
        fs_min_original=0.0,
        fs_max_original=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_diagram.svg"
        generate_svg(diagram, output_path)

        content = output_path.read_text()
        # Wire labels should have dx offset (to the right)
        # Look for wire label text element with dx attribute
        assert 'dx="' in content
        # Should also still have dy for vertical adjustment
        assert 'dy=' in content


def test_scale_bl_nonlinear_zero():
    """Test that zero BL remains zero."""
    result = scale_bl_nonlinear(0.0)
    assert result == 0.0


def test_scale_bl_nonlinear_small_values():
    """Test that small BL values are mostly unchanged."""
    # For small values (less than compression factor), scaling should be approximately linear
    # Using default compression_factor=25.0
    result = scale_bl_nonlinear(10.0)
    # log(1 + 10/25) = log(1.4) ≈ 0.336, scaled: 25 * 0.336 ≈ 8.4
    # Should be close to original but slightly compressed
    assert 7.0 < result < 10.0
    assert result < 10.0  # Should be slightly compressed


def test_scale_bl_nonlinear_large_values():
    """Test that large BL values are significantly compressed."""
    # For large values (much larger than compression factor), compression should be significant
    # Using default compression_factor=25.0
    result = scale_bl_nonlinear(200.0)
    # log(1 + 200/25) = log(9) ≈ 2.197, scaled: 25 * 2.197 ≈ 54.9
    # Should be significantly less than original 200
    assert 50.0 < result < 60.0
    assert result < 100.0  # Should be much less than original


def test_scale_bl_nonlinear_preserves_sign():
    """Test that negative BL values remain negative."""
    # Using default compression_factor=25.0
    result_positive = scale_bl_nonlinear(100.0)
    result_negative = scale_bl_nonlinear(-100.0)

    assert result_positive > 0
    assert result_negative < 0
    assert abs(result_positive) == pytest.approx(abs(result_negative))


def test_scale_bl_nonlinear_v2_zero():
    """Test that zero BL remains zero (v2 scaling)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2
    result = scale_bl_nonlinear_v2(0.0)
    assert result == 0.0


def test_scale_bl_nonlinear_v2_expansion():
    """Test that small BL values are expanded (v2 scaling)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2
    # BL < 30" should be expanded by 3x
    result = scale_bl_nonlinear_v2(10.0)
    assert result == pytest.approx(30.0)  # 10 * 3.0 = 30


def test_scale_bl_nonlinear_v2_threshold():
    """Test that threshold BL (30") maps correctly (v2 scaling)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2
    # BL = 30" should be at the threshold: 30 * 3.0 = 90
    result = scale_bl_nonlinear_v2(30.0)
    assert result == pytest.approx(90.0)


def test_scale_bl_nonlinear_v2_compression():
    """Test that large BL values are compressed (v2 scaling)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2
    import math
    # BL = 200" should be heavily compressed
    # base = 30 * 3.0 = 90
    # excess = 200 - 30 = 170
    # compressed_excess = 10.0 * log(1 + 170/10.0) = 10.0 * log(18) ≈ 10.0 * 2.89 ≈ 28.9
    # result = 90 + 28.9 ≈ 118.9
    result = scale_bl_nonlinear_v2(200.0)
    expected = 90.0 + 10.0 * math.log(1 + 170.0 / 10.0)
    assert result == pytest.approx(expected, abs=0.1)
    # Should be significantly less than 200 but more than threshold
    assert 90.0 < result < 140.0


def test_scale_bl_nonlinear_v2_preserves_sign():
    """Test that negative BL values remain negative (v2 scaling)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2
    result_positive = scale_bl_nonlinear_v2(10.0)
    result_negative = scale_bl_nonlinear_v2(-10.0)

    assert result_positive > 0
    assert result_negative < 0
    assert result_positive == pytest.approx(30.0)  # 10 * 3.0
    assert result_negative == pytest.approx(-30.0)  # -10 * 3.0


def test_scale_calculation_v2():
    """Test that scale calculations work correctly with v2 BL scaling (Phase 13.3)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2

    # Create components spanning a range within centerline (< 30" for 3x expansion)
    # FS: 0 to 100 inches
    # BL: -20 to +20 inches (will be scaled with v2, within centerline threshold)

    # With v2 scaling (centerline expansion):
    # BL -20 → -60 (3x expansion at center)
    # BL +20 → +60 (3x expansion at center)
    # Range: 120 scaled inches

    fs_min, fs_max = 0.0, 100.0
    bl_min_scaled = scale_bl_nonlinear_v2(-20.0)
    bl_max_scaled = scale_bl_nonlinear_v2(20.0)

    # Verify v2 scaling expands centerline
    assert bl_min_scaled == pytest.approx(-60.0)  # -20 * 3.0
    assert bl_max_scaled == pytest.approx(60.0)   # +20 * 3.0

    # Calculate scale factors as done in generate_svg()
    # Assume 1100x700 landscape, 40px margins, 80px title, 100px origin offset
    available_width = 1100 - 2 * 40  # 1020px
    available_height = 700 - 80 - 100 - 40  # 480px

    fs_range = fs_max - fs_min  # 100 inches
    bl_scaled_range = bl_max_scaled - bl_min_scaled  # 120 scaled inches

    scale_x = available_width / bl_scaled_range  # 1020 / 120 = 8.5 px/inch
    scale_y = available_height / fs_range  # 480 / 100 = 4.8 px/inch

    # Verify scales are reasonable (positive, not too extreme)
    assert scale_x > 0
    assert scale_y > 0
    assert 1.0 < scale_x < 20.0  # Reasonable range
    assert 1.0 < scale_y < 20.0  # Reasonable range

    # Verify independent scaling allows different X/Y ratios
    # (This is a key feature of Phase 13)
    assert scale_x != scale_y  # Should be different for this test case


def test_3d_projection_constants_exist():
    """Test that 3D projection constants are defined with correct values."""
    assert DEFAULT_WL_SCALE == 1.5
    assert DEFAULT_PROJECTION_ANGLE == 30


def test_project_3d_to_2d_origin():
    """Test 3D projection of origin point."""
    # Origin (0, 0, 0) should project to (0, 0)
    screen_x, screen_y = project_3d_to_2d(0.0, 0.0, 0.0, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)

    assert screen_x == pytest.approx(0.0)
    assert screen_y == pytest.approx(0.0)


def test_project_3d_to_2d_fs_only():
    """Test projection of point with only FS coordinate."""
    # Point at (100, 0, 0) - FS forward, no WL/BL
    # screen_x = 100 + (0 × 3) × cos(30°) = 100
    # screen_y = 0 + (0 × 3) × sin(30°) = 0
    screen_x, screen_y = project_3d_to_2d(100.0, 0.0, 0.0, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)

    assert screen_x == pytest.approx(100.0)
    assert screen_y == pytest.approx(0.0)


def test_project_3d_to_2d_wl_only():
    """Test projection of point with only WL coordinate."""
    # Point at (0, 10, 0) - WL up, no FS/BL
    # screen_x = 0 + (10 × 3) × cos(30°) = 30 × 0.866... ≈ 25.98
    # screen_y = 0 + (10 × 3) × sin(30°) = 30 × 0.5 = 15.0
    screen_x, screen_y = project_3d_to_2d(0.0, 10.0, 0.0, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)

    angle_rad = math.radians(DEFAULT_PROJECTION_ANGLE)
    expected_x = (10.0 * DEFAULT_WL_SCALE) * math.cos(angle_rad)
    expected_y = (10.0 * DEFAULT_WL_SCALE) * math.sin(angle_rad)

    assert screen_x == pytest.approx(expected_x)
    assert screen_y == pytest.approx(expected_y)


def test_project_3d_to_2d_bl_only():
    """Test projection of point with only BL coordinate."""
    # Point at (0, 0, 50) - BL starboard, no FS/WL
    # screen_x = 0 + (0 × 3) × cos(30°) = 0
    # screen_y = 50 + (0 × 3) × sin(30°) = 50
    screen_x, screen_y = project_3d_to_2d(0.0, 0.0, 50.0, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)

    assert screen_x == pytest.approx(0.0)
    assert screen_y == pytest.approx(50.0)


def test_project_3d_to_2d_all_coordinates():
    """Test projection of point with all three coordinates."""
    # Point at (100, 10, 50)
    # screen_x = 100 + (10 × 3) × cos(30°)
    # screen_y = 50 + (10 × 3) × sin(30°)
    screen_x, screen_y = project_3d_to_2d(100.0, 10.0, 50.0, DEFAULT_WL_SCALE, DEFAULT_PROJECTION_ANGLE)

    angle_rad = math.radians(DEFAULT_PROJECTION_ANGLE)
    wl_scaled = 10.0 * DEFAULT_WL_SCALE
    expected_x = 100.0 + wl_scaled * math.cos(angle_rad)
    expected_y = 50.0 + wl_scaled * math.sin(angle_rad)

    assert screen_x == pytest.approx(expected_x)
    assert screen_y == pytest.approx(expected_y)


def test_project_3d_to_2d_custom_scale():
    """Test projection with custom WL scale factor."""
    # Point at (0, 10, 0) with wl_scale=5.0
    # screen_x = 0 + (10 × 5) × cos(30°) = 50 × 0.866... ≈ 43.3
    # screen_y = 0 + (10 × 5) × sin(30°) = 50 × 0.5 = 25.0
    screen_x, screen_y = project_3d_to_2d(0.0, 10.0, 0.0, 5.0, DEFAULT_PROJECTION_ANGLE)

    angle_rad = math.radians(DEFAULT_PROJECTION_ANGLE)
    expected_x = (10.0 * 5.0) * math.cos(angle_rad)
    expected_y = (10.0 * 5.0) * math.sin(angle_rad)

    assert screen_x == pytest.approx(expected_x)
    assert screen_y == pytest.approx(expected_y)


def test_project_3d_to_2d_custom_angle():
    """Test projection with custom projection angle."""
    # Point at (0, 10, 0) with angle=45°
    # screen_x = 0 + (10 × 3) × cos(45°) = 30 × 0.707... ≈ 21.21
    # screen_y = 0 + (10 × 3) × sin(45°) = 30 × 0.707... ≈ 21.21
    screen_x, screen_y = project_3d_to_2d(0.0, 10.0, 0.0, DEFAULT_WL_SCALE, 45.0)

    angle_rad = math.radians(45.0)
    wl_scaled = 10.0 * DEFAULT_WL_SCALE
    expected_x = wl_scaled * math.cos(angle_rad)
    expected_y = wl_scaled * math.sin(angle_rad)

    assert screen_x == pytest.approx(expected_x)
    assert screen_y == pytest.approx(expected_y)


def test_build_component_circuits_map():
    """Test building component-to-circuits mapping (Phase 13.4.1)."""
    # Create components and wire segments
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=0.0, bl=20.0)
    comp3 = DiagramComponent(ref="L1", fs=100.0, wl=0.0, bl=10.0)

    seg1 = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)
    seg2 = DiagramWireSegment(label="L1B", comp1=comp2, comp2=comp3)
    seg3 = DiagramWireSegment(label="L2A", comp1=comp1, comp2=comp3)

    # Build mapping as done in generate_svg()
    component_circuits = {}
    for segment in [seg1, seg2, seg3]:
        # Add to comp1
        if segment.comp1.ref not in component_circuits:
            component_circuits[segment.comp1.ref] = []
        component_circuits[segment.comp1.ref].append(segment.label)

        # Add to comp2
        if segment.comp2.ref not in component_circuits:
            component_circuits[segment.comp2.ref] = []
        component_circuits[segment.comp2.ref].append(segment.label)

    # Sort and deduplicate
    for ref in component_circuits:
        component_circuits[ref] = sorted(set(component_circuits[ref]))

    # Verify mapping
    assert "CB1" in component_circuits
    assert "SW1" in component_circuits
    assert "L1" in component_circuits

    # CB1 connects to L1A and L2A
    assert component_circuits["CB1"] == ["L1A", "L2A"]

    # SW1 connects to L1A and L1B
    assert component_circuits["SW1"] == ["L1A", "L1B"]

    # L1 connects to L1B and L2A
    assert component_circuits["L1"] == ["L1B", "L2A"]


def test_diagram_landscape_orientation(tmp_path):
    """Test that Phase 13 diagrams use landscape orientation (Phase 13.5.2)."""
    from kicad2wireBOM.diagram_generator import SystemDiagram, generate_svg

    # Create simple diagram
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=0.0, bl=20.0)
    seg = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[seg],
        fs_min=0.0, fs_max=50.0,
        bl_min_scaled=-40.0, bl_max_scaled=40.0,
        bl_min_original=-20.0, bl_max_original=20.0,
        fs_min_original=0.0, fs_max_original=50.0
    )

    output_file = tmp_path / "test_landscape.svg"
    generate_svg(diagram, output_file, use_2d=True)

    # Read SVG and verify landscape dimensions
    svg_content = output_file.read_text()
    assert 'width="1100"' in svg_content
    assert 'height="700"' in svg_content
    # Verify width > height (landscape)
    assert 1100 > 700


def test_diagram_origin_centered(tmp_path):
    """Test that FS=0,BL=0 appears at expected origin position (Phase 13.5.2)."""
    from kicad2wireBOM.diagram_generator import SystemDiagram, generate_svg, transform_to_svg_v2
    from kicad2wireBOM.reference_data import DIAGRAM_CONFIG

    # Origin should be at (svg_width/2, title_height + origin_offset_y)
    expected_origin_x = 1100 / 2  # 550
    expected_origin_y = DIAGRAM_CONFIG['title_height'] + DIAGRAM_CONFIG['origin_offset_y']  # 80 + 100 = 180

    # Verify transform_to_svg_v2 maps (0,0) to origin
    svg_x, svg_y = transform_to_svg_v2(
        fs=0.0, bl=0.0,
        origin_svg_x=expected_origin_x,
        origin_svg_y=expected_origin_y,
        scale_x=2.0, scale_y=2.0
    )

    assert svg_x == expected_origin_x
    assert svg_y == expected_origin_y


def test_diagram_fs_axis_direction(tmp_path):
    """Test that FS+ renders below FS- (nose up, rear down) (Phase 13.5.2)."""
    from kicad2wireBOM.diagram_generator import transform_to_svg_v2

    origin_x, origin_y = 550.0, 200.0
    scale_x, scale_y = 2.0, 2.0

    # FS+ (rear) should be below origin (higher svg_y)
    svg_x_plus, svg_y_plus = transform_to_svg_v2(50.0, 0.0, origin_x, origin_y, scale_x, scale_y)

    # FS- (nose) should be above origin (lower svg_y)
    svg_x_minus, svg_y_minus = transform_to_svg_v2(-50.0, 0.0, origin_x, origin_y, scale_x, scale_y)

    # Verify FS+ has higher Y (below) than FS- (above)
    assert svg_y_plus > origin_y  # FS+ below origin
    assert svg_y_minus < origin_y  # FS- above origin
    assert svg_y_plus > svg_y_minus  # Rear below nose


def test_diagram_bl_expansion_at_center(tmp_path):
    """Test that centerline BL values are expanded 3x (Phase 13.5.2)."""
    from kicad2wireBOM.diagram_generator import scale_bl_nonlinear_v2

    # BL values < 30" should be expanded by 3x
    bl_10 = scale_bl_nonlinear_v2(10.0)
    bl_20 = scale_bl_nonlinear_v2(20.0)
    bl_30 = scale_bl_nonlinear_v2(30.0)

    # Verify 3x expansion in centerline region
    assert bl_10 == pytest.approx(30.0)  # 10 * 3.0
    assert bl_20 == pytest.approx(60.0)  # 20 * 3.0
    assert bl_30 == pytest.approx(90.0)  # 30 * 3.0 (threshold)


def test_circuit_labels_under_components(tmp_path):
    """Test that circuit labels render in boxes under components (Phase 13.5.2)."""
    from kicad2wireBOM.diagram_generator import SystemDiagram, generate_svg

    # Create diagram with labeled wires
    comp1 = DiagramComponent(ref="CB1", fs=0.0, wl=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=0.0, bl=20.0)
    comp3 = DiagramComponent(ref="L1", fs=100.0, wl=0.0, bl=10.0)

    seg1 = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)
    seg2 = DiagramWireSegment(label="L1B", comp1=comp2, comp2=comp3)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2, comp3],
        wire_segments=[seg1, seg2],
        fs_min=0.0, fs_max=100.0,
        bl_min_scaled=0.0, bl_max_scaled=60.0,
        bl_min_original=0.0, bl_max_original=20.0,
        fs_min_original=0.0, fs_max_original=100.0
    )

    output_file = tmp_path / "test_circuit_labels.svg"
    generate_svg(diagram, output_file, use_2d=True)

    # Read SVG and verify circuit label boxes exist
    svg_content = output_file.read_text()

    # Verify component-circuits group exists
    assert '<g id="component-circuits"' in svg_content

    # Verify boxes with white fill and navy stroke
    assert 'fill="white"' in svg_content
    assert 'stroke="navy"' in svg_content

    # Verify circuit labels appear
    assert 'L1A' in svg_content
    assert 'L1B' in svg_content


def test_calculate_star_layout_single_neighbor():
    """Test star layout with 1 neighbor positioned at 0° (Phase 13.6.1)."""
    from kicad2wireBOM.diagram_generator import calculate_star_layout
    import math

    center_x, center_y = 400.0, 400.0
    radius = 250.0
    neighbor_refs = ["SW1"]

    layout = calculate_star_layout(center_x, center_y, neighbor_refs, radius)

    # Single neighbor should be at 0° (right side)
    assert "SW1" in layout
    x, y = layout["SW1"]
    # 0° = right side: x = center_x + radius, y = center_y
    assert x == pytest.approx(center_x + radius)
    assert y == pytest.approx(center_y)


def test_calculate_star_layout_two_neighbors():
    """Test star layout with 2 neighbors at 0° and 180° (Phase 13.6.1)."""
    from kicad2wireBOM.diagram_generator import calculate_star_layout
    import math

    center_x, center_y = 400.0, 400.0
    radius = 250.0
    neighbor_refs = ["SW1", "L1"]

    layout = calculate_star_layout(center_x, center_y, neighbor_refs, radius)

    # Two neighbors: 0° and 180°
    assert "SW1" in layout
    assert "L1" in layout

    x1, y1 = layout["SW1"]
    x2, y2 = layout["L1"]

    # 0° = right: (center_x + radius, center_y)
    # 180° = left: (center_x - radius, center_y)
    assert x1 == pytest.approx(center_x + radius)
    assert y1 == pytest.approx(center_y)
    assert x2 == pytest.approx(center_x - radius)
    assert y2 == pytest.approx(center_y)


def test_calculate_star_layout_four_neighbors():
    """Test star layout with 4 neighbors at 0°, 90°, 180°, 270° (Phase 13.6.1)."""
    from kicad2wireBOM.diagram_generator import calculate_star_layout
    import math

    center_x, center_y = 400.0, 400.0
    radius = 250.0
    neighbor_refs = ["N1", "N2", "N3", "N4"]

    layout = calculate_star_layout(center_x, center_y, neighbor_refs, radius)

    # Four neighbors at cardinal directions
    assert len(layout) == 4

    x1, y1 = layout["N1"]  # 0° = right
    x2, y2 = layout["N2"]  # 90° = down
    x3, y3 = layout["N3"]  # 180° = left
    x4, y4 = layout["N4"]  # 270° = up

    # Verify positions (SVG: Y increases downward)
    assert x1 == pytest.approx(center_x + radius)  # Right
    assert y1 == pytest.approx(center_y)

    assert x2 == pytest.approx(center_x)  # Down
    assert y2 == pytest.approx(center_y + radius)

    assert x3 == pytest.approx(center_x - radius)  # Left
    assert y3 == pytest.approx(center_y)

    assert x4 == pytest.approx(center_x)  # Up
    assert y4 == pytest.approx(center_y - radius)


def test_wrap_text():
    """Test text wrapping for long component descriptions (Phase 13.6.2)."""
    from kicad2wireBOM.diagram_generator import wrap_text

    # Short text - no wrapping needed
    result = wrap_text("Short", max_width=50)
    assert result == ["Short"]

    # Medium text - fits in one line
    result = wrap_text("Circuit Breaker", max_width=50)
    assert result == ["Circuit Breaker"]

    # Long text - needs wrapping
    result = wrap_text("This is a very long component description that should wrap", max_width=30)
    assert len(result) > 1
    # Each line should be shorter than max_width
    for line in result:
        assert len(line) <= 30

    # Empty text
    result = wrap_text("", max_width=50)
    assert result == [""]


def test_calculate_circle_radius_short_text():
    """Test circle radius calculation with short text returns minimum (Phase 13.6.2)."""
    from kicad2wireBOM.diagram_generator import calculate_circle_radius

    # Short text should return minimum radius
    text_lines = ["CB1", "5A", "Breaker"]
    radius = calculate_circle_radius(text_lines, font_size=10)

    # Minimum radius is 40px
    assert radius == 40.0


def test_calculate_circle_radius_long_text():
    """Test circle radius calculation with long text returns larger radius (Phase 13.6.2)."""
    from kicad2wireBOM.diagram_generator import calculate_circle_radius

    # Longer text should return larger radius
    text_lines = ["SWITCH1", "SPDT Toggle", "Main Power Switch"]
    radius = calculate_circle_radius(text_lines, font_size=10)

    # Should be larger than minimum but less than max
    assert 40.0 < radius <= 80.0


def test_calculate_circle_radius_very_long_text():
    """Test circle radius calculation with very long text returns max + wrapping (Phase 13.6.2)."""
    from kicad2wireBOM.diagram_generator import calculate_circle_radius

    # Very long text should return maximum radius
    text_lines = [
        "CB-MASTER-CONTROL-1",
        "50A Circuit Breaker",
        "This is a very long description that exceeds normal component text length"
    ]
    radius = calculate_circle_radius(text_lines, font_size=10)

    # Maximum radius is 80px
    assert radius == 80.0


def test_build_component_star_diagram():
    """Test building star diagram data structures (Phase 13.6.3)."""
    from kicad2wireBOM.diagram_generator import (
        StarDiagramComponent,
        StarDiagramWire,
        ComponentStarDiagram
    )

    # Create center component
    center = StarDiagramComponent(
        ref="CB1",
        value="5A",
        desc="Circuit Breaker",
        x=400.0,
        y=400.0,
        radius=50.0
    )

    # Create neighbor components
    neighbor1 = StarDiagramComponent(
        ref="SW1",
        value="SPDT",
        desc="Power Switch",
        x=600.0,
        y=400.0,
        radius=45.0
    )
    neighbor2 = StarDiagramComponent(
        ref="L1",
        value="LED",
        desc="Indicator",
        x=400.0,
        y=600.0,
        radius=40.0
    )

    # Create wire connections
    wire1 = StarDiagramWire(circuit_id="L1A", from_ref="CB1", to_ref="SW1")
    wire2 = StarDiagramWire(circuit_id="L2A", from_ref="CB1", to_ref="L1")

    # Create star diagram
    diagram = ComponentStarDiagram(
        center=center,
        neighbors=[neighbor1, neighbor2],
        wires=[wire1, wire2]
    )

    # Verify structure
    assert diagram.center.ref == "CB1"
    assert len(diagram.neighbors) == 2
    assert len(diagram.wires) == 2
    assert diagram.neighbors[0].ref == "SW1"
    assert diagram.neighbors[1].ref == "L1"
    assert diagram.wires[0].circuit_id == "L1A"
    assert diagram.wires[1].circuit_id == "L2A"


def test_generate_star_svg(tmp_path):
    """Test star SVG generation creates correct file structure (Phase 13.6.4)."""
    from kicad2wireBOM.diagram_generator import (
        StarDiagramComponent,
        StarDiagramWire,
        ComponentStarDiagram,
        generate_star_svg
    )

    # Create center component
    center = StarDiagramComponent(
        ref="CB1",
        value="5A",
        desc="Circuit Breaker",
        x=375.0,
        y=475.0,
        radius=50.0
    )

    # Create neighbor components
    neighbor1 = StarDiagramComponent(
        ref="SW1",
        value="SPDT",
        desc="Power Switch",
        x=625.0,
        y=475.0,
        radius=45.0
    )
    neighbor2 = StarDiagramComponent(
        ref="L1",
        value="LED",
        desc="Indicator",
        x=375.0,
        y=675.0,
        radius=40.0
    )

    # Create wire connections
    wire1 = StarDiagramWire(circuit_id="L1A", from_ref="CB1", to_ref="SW1")
    wire2 = StarDiagramWire(circuit_id="L2A", from_ref="CB1", to_ref="L1")

    # Create star diagram
    diagram = ComponentStarDiagram(
        center=center,
        neighbors=[neighbor1, neighbor2],
        wires=[wire1, wire2]
    )

    # Generate SVG
    output_file = tmp_path / "test_star.svg"
    generate_star_svg(diagram, output_file)

    # Verify file exists
    assert output_file.exists()

    # Read and verify content
    content = output_file.read_text()

    # Verify SVG structure
    assert '<svg' in content
    assert 'width="750"' in content
    assert 'height="950"' in content

    # Verify title block
    assert 'CB1' in content
    assert '5A' in content
    assert 'Circuit Breaker' in content

    # Verify circles (3 total: 1 center + 2 neighbors)
    assert content.count('<circle') == 3

    # Verify wires (lines between center and neighbors)
    assert content.count('<line') == 2

    # Verify wire labels
    assert 'L1A' in content
    assert 'L2A' in content


def test_manhattan_path_3d_routing():
    """Test 3D Manhattan routing returns 5 points with BL→FS→WL order."""
    # Component 1: (FS1=10, WL1=5, BL1=30)
    # Component 2: (FS2=50, WL2=15, BL2=10)
    comp1 = DiagramComponent(ref="CB1", fs=10.0, wl=5.0, bl=30.0)
    comp2 = DiagramComponent(ref="SW1", fs=50.0, wl=15.0, bl=10.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    path = segment.manhattan_path

    # Expected 5 points with BL → FS → WL routing:
    # Point 1: (FS1, WL1, BL1) - start at C1
    # Point 2: (FS1, WL1, BL2) - BL move, horizontal at C1's WL
    # Point 3: (FS2, WL1, BL2) - FS move, still horizontal at C1's WL
    # Point 4: (FS2, WL2, BL2) - WL move, vertical at C2's location
    # Point 5: (FS2, WL2, BL2) - end at C2 (same as point 4)

    assert len(path) == 5
    assert path[0] == (10.0, 5.0, 30.0)   # Start at C1
    assert path[1] == (10.0, 5.0, 10.0)   # BL move (30→10), horizontal at WL1=5
    assert path[2] == (50.0, 5.0, 10.0)   # FS move (10→50), still at WL1=5
    assert path[3] == (50.0, 15.0, 10.0)  # WL move (5→15), vertical at C2's FS/BL
    assert path[4] == (50.0, 15.0, 10.0)  # End at C2 (same as point 3)
