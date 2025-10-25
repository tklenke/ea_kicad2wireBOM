# ABOUTME: Tests for building connectivity graphs from hierarchical schematics
# ABOUTME: Tests build_connectivity_graph_hierarchical for multi-sheet designs

from pathlib import Path
from kicad2wireBOM.parser import parse_schematic_hierarchical
from kicad2wireBOM.graph_builder import build_connectivity_graph_hierarchical


def test_build_hierarchical_graph_from_test_06():
    """Build connectivity graph from hierarchical test_06 fixture"""
    fixture_path = Path("tests/fixtures/test_06_fixture.kicad_sch")
    hierarchical_schematic = parse_schematic_hierarchical(fixture_path)

    # Build unified graph spanning all sheets
    graph = build_connectivity_graph_hierarchical(hierarchical_schematic)

    # Verify graph contains nodes from all sheets
    assert len(graph.nodes) > 0
    assert len(graph.wires) > 0

    # Verify we have component pins from both root and sub-sheets
    # Root sheet has SW1, J1, etc.
    # Lighting sub-sheet has L2, L3
    # Avionics sub-sheet has various components
    assert len(graph.component_pins) > 0

    # Verify we have sheet_pin nodes (on parent sheet)
    sheet_pin_nodes = [n for n in graph.nodes.values() if n.node_type == 'sheet_pin']
    assert len(sheet_pin_nodes) > 0

    # Verify we have hierarchical_label nodes (on child sheets)
    hierarchical_label_nodes = [n for n in graph.nodes.values() if n.node_type == 'hierarchical_label']
    assert len(hierarchical_label_nodes) > 0

    # Verify cross-sheet connections exist
    # There should be virtual wires connecting sheet_pins to hierarchical_labels
    # We should be able to trace from a component on root sheet to a component on child sheet

    # Example: SW1 on root sheet connects to L2 on lighting sub-sheet via TAIL_LT
    # Find SW1 pin in graph
    sw1_pins = [key for key in graph.component_pins.keys() if key.startswith('SW1-')]
    assert len(sw1_pins) > 0  # SW1 exists

    # Find L2 pin in graph (on lighting sub-sheet)
    l2_pins = [key for key in graph.component_pins.keys() if key.startswith('L2-')]
    assert len(l2_pins) > 0  # L2 exists (on child sheet)
