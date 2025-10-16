# ABOUTME: Tests for the Component data model
# ABOUTME: Validates Component dataclass and its properties

import pytest
from kicad2wireBOM.component import Component


def test_component_creation():
    """Test creating a Component with all fields"""
    comp = Component(
        ref='J1',
        fs=100.0,
        wl=25.0,
        bl=0.0,
        load=None,
        rating=15.0
    )

    assert comp.ref == 'J1'
    assert comp.fs == 100.0
    assert comp.wl == 25.0
    assert comp.bl == 0.0
    assert comp.load is None
    assert comp.rating == 15.0


def test_component_coordinates_property():
    """Test coordinates property returns tuple of (fs, wl, bl)"""
    comp = Component(ref='SW1', fs=150.0, wl=30.0, bl=0.0, load=None, rating=20.0)

    coords = comp.coordinates
    assert coords == (150.0, 30.0, 0.0)
    assert isinstance(coords, tuple)


def test_component_is_load_property():
    """Test is_load property returns True when component has load value"""
    load_comp = Component(ref='LIGHT1', fs=0, wl=0, bl=0, load=5.0, rating=None)
    passthrough_comp = Component(ref='SW1', fs=0, wl=0, bl=0, load=None, rating=20.0)

    assert load_comp.is_load is True
    assert passthrough_comp.is_load is False


def test_component_is_passthrough_property():
    """Test is_passthrough property returns True when component has rating value"""
    passthrough_comp = Component(ref='SW1', fs=0, wl=0, bl=0, load=None, rating=20.0)
    load_comp = Component(ref='LIGHT1', fs=0, wl=0, bl=0, load=5.0, rating=None)

    assert passthrough_comp.is_passthrough is True
    assert load_comp.is_passthrough is False


def test_component_neither_load_nor_rating():
    """Test component can have neither load nor rating"""
    comp = Component(ref='UNKNOWN', fs=0, wl=0, bl=0, load=None, rating=None)

    assert comp.is_load is False
    assert comp.is_passthrough is False
