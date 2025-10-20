# ABOUTME: Tests for graph building integration from schematic
# ABOUTME: Tests building complete connectivity graph with pins, junctions, and wires

import pytest
from pathlib import Path
from kicad2wireBOM.parser import parse_schematic_file
from kicad2wireBOM.graph_builder import build_connectivity_graph


def test_build_graph_simple_circuit():
    """Build graph for simple 2-component circuit (test_01_fixture)"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    graph = build_connectivity_graph(sexp)

    # Should have wires
    assert len(graph.wires) > 0

    # Should have nodes at wire endpoints
    assert len(graph.nodes) > 0

    # Should have component pins
    assert len(graph.component_pins) > 0


def test_build_graph_with_junction():
    """Build graph with junction (test_03A_fixture)"""
    fixture_path = Path("tests/fixtures/test_03A_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    graph = build_connectivity_graph(sexp)

    # Should have 2 junctions from test_03A
    assert len(graph.junctions) == 2

    # Junctions should be in nodes
    assert len([n for n in graph.nodes.values() if n.node_type == 'junction']) == 2

    # Should have component pins
    assert len(graph.component_pins) > 0

    # Should have wires
    assert len(graph.wires) > 0


def test_build_graph_pin_positions():
    """Component pins should have correct calculated positions"""
    fixture_path = Path("tests/fixtures/test_03A_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    graph = build_connectivity_graph(sexp)

    # Should have pins for SW1 and SW2 (each has 3 pins)
    # And J1 (has 2 pins)
    assert len(graph.component_pins) >= 8

    # Check that pin nodes exist
    component_pin_nodes = [n for n in graph.nodes.values() if n.node_type == 'component_pin']
    assert len(component_pin_nodes) >= 8


def test_build_graph_wires_connect_to_pins():
    """Wires should connect to component pin nodes"""
    fixture_path = Path("tests/fixtures/test_01_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    graph = build_connectivity_graph(sexp)

    # Find a component pin node
    pin_nodes = [n for n in graph.nodes.values() if n.node_type == 'component_pin']
    assert len(pin_nodes) > 0

    # At least one pin should have connected wires
    pins_with_wires = [n for n in pin_nodes if len(n.connected_wire_uuids) > 0]
    assert len(pins_with_wires) > 0


def test_build_graph_wires_connect_at_junction():
    """Multiple wires should connect at junction nodes"""
    fixture_path = Path("tests/fixtures/test_03A_fixture.kicad_sch")
    sexp = parse_schematic_file(fixture_path)

    graph = build_connectivity_graph(sexp)

    # Find junction nodes
    junction_nodes = [n for n in graph.nodes.values() if n.node_type == 'junction']
    assert len(junction_nodes) == 2

    # At least one junction should have multiple wires
    junctions_with_multiple_wires = [n for n in junction_nodes if len(n.connected_wire_uuids) >= 2]
    assert len(junctions_with_multiple_wires) > 0
