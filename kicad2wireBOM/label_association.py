# ABOUTME: Label-to-wire association using proximity matching
# ABOUTME: Implements geometric algorithms for distance calculation and label assignment

import math
import re
from typing import List
from kicad2wireBOM.schematic import WireSegment, Label


def point_to_segment_distance(px: float, py: float,
                              x1: float, y1: float,
                              x2: float, y2: float) -> float:
    """
    Calculate perpendicular distance from point to line segment.

    Uses vector projection to find the closest point on the segment,
    then computes Euclidean distance.

    Args:
        px, py: Point coordinates
        x1, y1: Segment start coordinates
        x2, y2: Segment end coordinates

    Returns:
        Minimum distance from point to segment (float)
    """
    # Vector from segment start to point
    dx = px - x1
    dy = py - y1

    # Vector along segment
    sx = x2 - x1
    sy = y2 - y1

    # Segment length squared
    segment_length_sq = sx * sx + sy * sy

    if segment_length_sq == 0:
        # Segment is a point
        return math.sqrt(dx * dx + dy * dy)

    # Parameter t = projection of point onto segment (0 to 1)
    # 0 = at start, 1 = at end, between = on segment
    t = max(0, min(1, (dx * sx + dy * sy) / segment_length_sq))

    # Closest point on segment
    closest_x = x1 + t * sx
    closest_y = y1 + t * sy

    # Distance from point to closest point
    dist_x = px - closest_x
    dist_y = py - closest_y

    return math.sqrt(dist_x * dist_x + dist_y * dist_y)


def is_circuit_id(text: str) -> bool:
    """
    Check if text matches circuit ID pattern.

    Valid patterns:
    - Compact: P1A, L2B, G1C
    - Dashed: P-1-A, L-105-B, G-2-C

    Pattern: Letter, optional dash, digits, optional dash, letter

    Args:
        text: Text to check

    Returns:
        True if text matches circuit ID pattern
    """
    # Pattern: ([A-Z])-?(\d+)-?([A-Z])
    pattern = r'^[A-Z]-?\d+-?[A-Z]$'
    return re.match(pattern, text) is not None


def parse_circuit_ids(label_text: str) -> List[str]:
    """
    Parse circuit IDs from label text, supporting pipe notation.

    Handles labels with multiple circuit IDs separated by pipe characters.
    Filters out invalid parts that don't match circuit ID pattern.

    Examples:
    - "L3B|L10A" -> ["L3B", "L10A"]
    - "L2B" -> ["L2B"]
    - "L3B|NOTES" -> ["L3B"]
    - "" -> []

    Args:
        label_text: Label text potentially containing pipe-separated circuit IDs

    Returns:
        List of valid circuit IDs found in the label text
    """
    if not label_text:
        return []

    parts = label_text.split('|')
    circuit_ids = [part.strip() for part in parts if is_circuit_id(part.strip())]
    return circuit_ids


def parse_circuit_id(wire: WireSegment) -> None:
    """
    Parse wire.circuit_id into system_code, circuit_num, segment_letter.

    Modifies the wire object in place.

    Args:
        wire: WireSegment object with circuit_id set
    """
    if not wire.circuit_id:
        return

    # Pattern: ([A-Z])-?(\d+)-?([A-Z])
    pattern = r'^([A-Z])-?(\d+)-?([A-Z])$'
    match = re.match(pattern, wire.circuit_id)

    if match:
        wire.system_code = match.group(1)
        wire.circuit_num = match.group(2)
        wire.segment_letter = match.group(3)


def associate_labels_with_wires(wires: List[WireSegment],
                                labels: List[Label],
                                threshold: float = 10.0) -> None:
    """
    Associate labels with nearest wire segments using proximity matching.

    For each label, finds the nearest wire segment and associates the label
    with that wire if the distance is within the threshold.

    Circuit ID labels (matching pattern [A-Z]-?\\d+-?[A-Z]) are stored in
    wire.circuit_id and parsed into components. Labels with pipe notation
    (e.g., "L3B|L10A") are parsed into multiple circuit IDs stored in
    wire.circuit_ids. Non-circuit labels are stored in wire.notes.

    Modifies wire objects in place, updating:
    - wire.labels (appends all label text)
    - wire.circuit_id (sets to first circuit ID)
    - wire.circuit_ids (list of all circuit IDs from pipe notation)
    - wire.notes (appends non-circuit label text)
    - wire.system_code, circuit_num, segment_letter (parsed from first circuit_id)

    Args:
        wires: List of WireSegment objects
        labels: List of Label objects
        threshold: Maximum distance (mm) for association (default: 10.0mm)
                  This value is configurable and can be adjusted if needed.
    """
    for label in labels:
        # Find nearest wire
        min_distance = float('inf')
        nearest_wire = None

        for wire in wires:
            dist = point_to_segment_distance(
                label.position[0], label.position[1],
                wire.start_point[0], wire.start_point[1],
                wire.end_point[0], wire.end_point[1]
            )

            if dist < min_distance:
                min_distance = dist
                nearest_wire = wire

        # Associate if within threshold
        if min_distance <= threshold and nearest_wire:
            # Parse circuit IDs from label text (handles pipe notation)
            circuit_ids = parse_circuit_ids(label.text)

            if circuit_ids:
                # Label contains valid circuit ID(s)
                nearest_wire.labels.append(label.text)
                nearest_wire.circuit_id = circuit_ids[0]  # First ID for backward compatibility
                nearest_wire.circuit_ids = circuit_ids  # All IDs
                # Parse first circuit ID into components
                parse_circuit_id(nearest_wire)
            else:
                # Non-circuit label - add to notes
                nearest_wire.notes.append(label.text)
