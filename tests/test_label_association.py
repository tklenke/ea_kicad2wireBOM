# ABOUTME: Tests for label-to-wire association module
# ABOUTME: Validates proximity matching and circuit ID parsing

import math
from kicad2wireBOM.label_association import (
    point_to_segment_distance,
    associate_labels_with_wires,
    is_circuit_id,
    parse_circuit_id
)
from kicad2wireBOM.schematic import WireSegment, Label


def test_point_to_segment_distance_perpendicular():
    """Calculate perpendicular distance from point to line segment"""
    # Point at (0, 1), segment from (0, 0) to (2, 0) (horizontal)
    # Perpendicular distance should be 1.0
    dist = point_to_segment_distance(0, 1, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001


def test_point_to_segment_distance_midpoint():
    """Point perpendicular to segment midpoint"""
    # Point at (1, 1), segment from (0, 0) to (2, 0)
    # Perpendicular distance should be 1.0
    dist = point_to_segment_distance(1, 1, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001


def test_point_to_segment_distance_beyond_end():
    """Point beyond segment end uses endpoint distance"""
    # Point at (3, 0), segment from (0, 0) to (2, 0)
    # Distance should be 1.0 (to endpoint at x=2)
    dist = point_to_segment_distance(3, 0, 0, 0, 2, 0)
    assert abs(dist - 1.0) < 0.001


def test_point_to_segment_distance_on_segment():
    """Point exactly on segment has zero distance"""
    dist = point_to_segment_distance(1, 0, 0, 0, 2, 0)
    assert abs(dist) < 0.001


def test_is_circuit_id_valid():
    """Recognize valid circuit ID patterns"""
    assert is_circuit_id("P1A") is True
    assert is_circuit_id("L2B") is True
    assert is_circuit_id("G-1-A") is True
    assert is_circuit_id("R-105-C") is True


def test_is_circuit_id_invalid():
    """Reject invalid circuit ID patterns"""
    assert is_circuit_id("Note") is False
    assert is_circuit_id("TODO") is False
    assert is_circuit_id("POWER") is False
    assert is_circuit_id("12") is False


def test_associate_labels_with_wires():
    """Associate labels with nearest wire segments"""
    wires = [
        WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0)),
        WireSegment(uuid="w2", start_point=(0, 50), end_point=(100, 50))
    ]

    labels = [
        Label(text="P1A", position=(50, 5), uuid="l1"),   # Near wire 1
        Label(text="G1A", position=(50, 55), uuid="l2")   # Near wire 2
    ]

    associate_labels_with_wires(wires, labels, threshold=10.0)

    assert "P1A" in wires[0].labels
    assert "G1A" in wires[1].labels
    assert wires[0].circuit_id == "P1A"
    assert wires[1].circuit_id == "G1A"


def test_associate_labels_respects_threshold():
    """Labels beyond threshold are not associated"""
    wires = [
        WireSegment(uuid="w1", start_point=(0, 0), end_point=(100, 0))
    ]

    labels = [
        Label(text="P1A", position=(50, 20), uuid="l1")  # 20mm away
    ]

    # Threshold of 10mm should exclude this label
    associate_labels_with_wires(wires, labels, threshold=10.0)

    assert len(wires[0].labels) == 0
    assert wires[0].circuit_id is None


def test_parse_circuit_id_compact():
    """Parse compact circuit ID format: P1A"""
    wire = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 10))
    wire.circuit_id = "P1A"

    parse_circuit_id(wire)

    assert wire.system_code == "P"
    assert wire.circuit_num == "1"
    assert wire.segment_letter == "A"


def test_parse_circuit_id_dashed():
    """Parse dashed circuit ID format: L-105-B"""
    wire = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 10))
    wire.circuit_id = "L-105-B"

    parse_circuit_id(wire)

    assert wire.system_code == "L"
    assert wire.circuit_num == "105"
    assert wire.segment_letter == "B"


def test_parse_circuit_id_none():
    """Handle wire with no circuit ID"""
    wire = WireSegment(uuid="w1", start_point=(0, 0), end_point=(10, 10))
    wire.circuit_id = None

    parse_circuit_id(wire)  # Should not raise error

    assert wire.system_code is None
    assert wire.circuit_num is None
    assert wire.segment_letter is None
