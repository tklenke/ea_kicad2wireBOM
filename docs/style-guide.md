# Code Style Guide

This document outlines the coding standards and naming conventions for the ea_tools project.

## Naming Conventions

### Variables
- **Style**: camelCase (first letter lowercase)
- **Hungarian notation**: Use type prefixes
- **Examples**:
  - `strAircraftName` - string variable
  - `intAltitude` - integer variable
  - `fSpeed` - float variable
  - `bIsVfrConditions` - boolean variable
  - `lstWaypoints` - list variable
  - `dctConfig` - dictionary variable

### Functions
- **Style**: lowercase with underscores (snake_case)
- **Examples**:
  - `calculate_airspeed()`
  - `convert_knots_to_mph()`
  - `get_aircraft_weight()`
  - `is_within_envelope()`

### Classes
- **Style**: PascalCase (first letter uppercase)
- **Examples**:
  - `Aircraft`
  - `FlightPlan`
  - `WeightAndBalance`
  - `PerformanceCalculator`

### Modules
- **Style**: PascalCase (first letter uppercase)
- **Examples**:
  - `AircraftPerformance.py`
  - `WeightBalance.py`
  - `NavigationTools.py`

## General Guidelines

### Indentation
- Use 4 spaces per indentation level (no tabs)

### Line Length
- Maximum line length: 100 characters
- Break long lines at logical points

### Imports
- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Separate each group with a blank line

### Documentation
- Use docstrings for all modules, classes, and functions
- Format: Google-style or NumPy-style docstrings

### Comments
- Write clear, concise comments explaining *why*, not *what*
- Keep comments up-to-date with code changes
