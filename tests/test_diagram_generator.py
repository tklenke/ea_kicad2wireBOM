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
    calculate_wire_label_position,
    build_system_diagram,
    generate_svg,
    scale_bl_nonlinear,
)
from kicad2wireBOM.wire_bom import WireConnection
from kicad2wireBOM.component import Component
from pathlib import Path
import tempfile


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
        bl_min_original=20.0,
        bl_max_original=30.0,
        bl_min_scaled=scale_bl_nonlinear(20.0),
        bl_max_scaled=scale_bl_nonlinear(30.0)
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
    comp1 = DiagramComponent(ref="C1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="C2", fs=100.0, bl=50.0)
    comp3 = DiagramComponent(ref="C3", fs=50.0, bl=25.0)

    components = [comp1, comp2, comp3]
    fs_min, fs_max, bl_scaled_min, bl_scaled_max = calculate_bounds(components)

    assert fs_min == 0.0
    assert fs_max == 100.0
    # BL bounds are scaled now
    assert bl_scaled_min == scale_bl_nonlinear(0.0)  # 0.0
    assert bl_scaled_max == pytest.approx(scale_bl_nonlinear(50.0))


def test_calculate_bounds_negative_coords():
    """Test bounds calculation with negative coordinates."""
    comp1 = DiagramComponent(ref="C1", fs=-10.0, bl=-20.0)
    comp2 = DiagramComponent(ref="C2", fs=30.0, bl=40.0)

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
        scale=2.0, margin=10.0
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
        scale=2.0, margin=10.0
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
        scale=2.0, margin=10.0
    )

    # X = (bl_scaled - bl_scaled_min) * 2 + 10 = 0 * 2 + 10 = 10
    # Y = (30 - (-10)) * 2 + 10 = 40 * 2 + 10 = 90
    assert svg_x == 10.0
    assert svg_y == 90.0


def test_label_position_longer_horizontal():
    """Test label position when horizontal segment is longer."""
    # Path: [(10, 30), (10, 10), (50, 10)]
    # Vertical segment (BL): 30 to 10 = 20 inches
    # Horizontal segment (FS): 10 to 50 = 40 inches
    # Horizontal is longer, so label should be at midpoint of horizontal segment
    path = [(10.0, 30.0), (10.0, 10.0), (50.0, 10.0)]
    label_fs, label_bl = calculate_wire_label_position(path)

    # Midpoint of horizontal segment: ((10 + 50) / 2, 10) = (30, 10)
    assert label_fs == 30.0
    assert label_bl == 10.0


def test_label_position_longer_vertical():
    """Test label position when vertical segment is longer."""
    # Path: [(10, 30), (10, 5), (20, 5)]
    # Vertical segment (BL): 30 to 5 = 25 inches
    # Horizontal segment (FS): 10 to 20 = 10 inches
    # Vertical is longer, so label should be at midpoint of vertical segment
    path = [(10.0, 30.0), (10.0, 5.0), (20.0, 5.0)]
    label_fs, label_bl = calculate_wire_label_position(path)

    # Midpoint of vertical segment: (10, (30 + 5) / 2) = (10, 17.5)
    assert label_fs == 10.0
    assert label_bl == 17.5


def test_label_position_invalid_path():
    """Test that invalid path raises ValueError."""
    # Path with only 2 points (not a Manhattan 3-point path)
    path = [(10.0, 30.0), (50.0, 10.0)]

    with pytest.raises(ValueError, match="Manhattan path must have exactly 3 points"):
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
    comp1 = DiagramComponent(ref="CB1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, bl=50.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0)
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
    comp1 = DiagramComponent(ref="CB1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, bl=50.0)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0)
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
    comp1 = DiagramComponent(ref="CB1", fs=0.0, bl=0.0)
    comp2 = DiagramComponent(ref="SW1", fs=100.0, bl=50.0)
    segment = DiagramWireSegment(label="L1A", comp1=comp1, comp2=comp2)

    diagram = SystemDiagram(
        system_code="L",
        components=[comp1, comp2],
        wire_segments=[segment],
        fs_min=0.0,
        fs_max=100.0,
        bl_min_original=0.0,
        bl_max_original=50.0,
        bl_min_scaled=0.0,
        bl_max_scaled=scale_bl_nonlinear(50.0)
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
