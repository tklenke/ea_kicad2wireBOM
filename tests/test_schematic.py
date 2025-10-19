# ABOUTME: Tests for schematic data models
# ABOUTME: Validates WireSegment and Label dataclasses

from kicad2wireBOM.schematic import WireSegment, Label


def test_wire_segment_creation():
    """Verify WireSegment dataclass works"""
    wire = WireSegment(
        uuid="test-uuid-123",
        start_point=(10.0, 20.0),
        end_point=(30.0, 40.0)
    )

    assert wire.uuid == "test-uuid-123"
    assert wire.start_point == (10.0, 20.0)
    assert wire.end_point == (30.0, 40.0)
    assert wire.circuit_id is None
    assert wire.labels == []


def test_wire_segment_with_label():
    """Verify WireSegment can store label information"""
    wire = WireSegment(
        uuid="test-uuid",
        start_point=(0, 0),
        end_point=(100, 0),
        circuit_id="P1A",
        labels=["P1A"]
    )

    assert wire.circuit_id == "P1A"
    assert "P1A" in wire.labels


def test_label_creation():
    """Verify Label dataclass works"""
    label = Label(
        text="P1A",
        position=(50.0, 60.0),
        uuid="label-uuid-123"
    )

    assert label.text == "P1A"
    assert label.position == (50.0, 60.0)
    assert label.uuid == "label-uuid-123"
    assert label.rotation == 0.0


def test_label_with_rotation():
    """Verify Label can store rotation"""
    label = Label(
        text="G1A",
        position=(100.0, 50.0),
        uuid="label-uuid",
        rotation=90.0
    )

    assert label.rotation == 90.0
