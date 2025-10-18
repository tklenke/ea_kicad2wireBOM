# kicad2wireBOM: Programmer Implementation Checklist **[REVISED - 2025-10-17]**

## Purpose

This document tracks implementation progress for kicad2wireBOM following the incremental, fixture-driven approach documented in `incremental_implementation_plan.md`.

**Important:** When assuming the Programmer role, read this document to understand what's been completed and what needs to be done next.

---

## **DESIGN REVISION NOTICE - READ FIRST!**

**Date**: 2025-10-17
**What Changed**: Net name parsing approach (simpler, more reliable)

**WHY**: Analysis of real KiCad netlist revealed that Schematic Designer (SD) embeds complete wire codes in net names (e.g., `/L1A`). This is more reliable than inferring system codes from component analysis.

**KEY CHANGES FOR PROGRAMMER**:
1. **Primary detection**: Parse system code/circuit/segment from net name (regex)
2. **Secondary validation**: Use component analysis to validate SD's choices
3. **Simpler implementation**: Less complex inference, more straightforward validation
4. **New validation checks**: Net name format, duplicate labels, multi-node nets, system code validation

**AFFECTED TASKS**:
- Phase 1 Task 1.4 - System code detection (now parsing + validation)
- Phase 1 Task 1.5 - Wire label generation (now extraction from net name)
- Phase 6 Task 6.2 - Enhanced system code detection (now for validation, not primary detection)
- Phase 6.5 - Still valuable for validation quality checks

**See**: `docs/plans/kicad2wireBOM_design.md` Section 2.3 and Design Revision History for full details

---

## Progress Tracking

**Status Codes:**
- `[ ]` - Not started
- `[~]` - In progress
- `[x]` - Complete

---

## Phase 0: Initial Spike (Validate Foundation) **[REVISED - 2025-10-17]**

**Goal:** Prove we can extract data from KiCad netlists with footprint encoding AND net name parsing

**Test Fixture:** `tests/fixtures/test_01_minimal_two_component.net` (needs revision - see below)

**IMPORTANT:** The existing `test_01_minimal_two_component.net` in `tests/fixtures/` was created before the design revision. It uses old-style net names (`Net-P12`). You must remove or replace it with a new version that uses SD-defined net names (`/P1A`). See `docs/plans/required_from_tom.md` for updated test fixture requirements.

### Tasks

- `[x]` **0.0: Remove old test fixture** **[NEW - 2025-10-17]**
  - Old fixture files did not exist (codebase was ahead of documentation)
  - Tom provided new fixtures: `test_fixture_01.net` and `test_fixture_02.net` with proper net names

- `[x]` **0.1: Project setup**
  - Project structure already existed from previous work
  - All directories, dependencies, and configurations in place

- `[x]` **0.2: Minimal netlist parser** **[REVISED - 2025-10-17]**
  - ✓ `parser.py` exists with ABOUTME comments
  - ✓ `parse_netlist_file()` implemented
  - ✓ `extract_nets()` implemented with net class support
  - ✓ Tests passing in `tests/test_parser.py`

- `[x]` **0.3: Component extraction**
  - ✓ `extract_components()` implemented in `parser.py`
  - ✓ Tests passing

- `[x]` **0.4: Footprint encoding parser** **[UPDATED - 2025-10-18]**
  - ✓ `parse_footprint_encoding()` implemented
  - ✓ **Added 'S' type support for Source** (was only L|R, now L|R|S)
  - ✓ Parses coordinates (FS, WL, BL) as floats
  - ✓ Parses type letter (L, R, or S)
  - ✓ Parses amperage value as float
  - ✓ Tests passing including 'S' type test

- `[x]` **0.5: Component data model** **[UPDATED - 2025-10-18]**
  - ✓ `component.py` exists with ABOUTME comments
  - ✓ Component dataclass defined
  - ✓ **Added `source` field for Source components**
  - ✓ **Updated `is_source` property to check source field** (not just J prefix + rating)
  - ✓ Properties: `coordinates`, `is_load`, `is_passthrough`, `is_source`
  - ✓ Tests passing in `tests/test_component.py`

- `[x]` **0.6: Spike integration test** **[UPDATED - 2025-10-18]**
  - ✓ `tests/test_spike.py` exists and passing
  - ✓ Parses `test_fixture_01.net` with new net names (`/P1A`, `/G1A`)
  - ✓ Extracts and verifies all data
  - ✓ Verifies Source type components (BT1 with S40)
  - ✓ Manual verification complete

**Acceptance Criteria:**
- Can parse KiCad netlist ✓
- Can extract net names following `/[SYSTEM][CIRCUIT][SEGMENT]` pattern ✓
- Can extract net codes ✓
- Can extract footprint encoding ✓
- Can parse coordinates and load/rating ✓

**Commit:** "Initial spike: Parse KiCad netlist with net name pattern extraction"

---

## Phase 1: Test Fixture 01 - Minimal Two-Component Circuit **[REVISED - 2025-10-17]**

**Goal:** Generate simple CSV with basic wire calculations using net name parsing

**Test Fixture:** `tests/fixtures/test_01_minimal_two_component.net` (MUST use new version with `/P1A` net name)

**REMINDER:** Do NOT proceed with Phase 1 until Tom provides the revised test fixture with SD-defined net names. The old fixture will cause tests to fail.

### Tasks

- `[ ]` **1.1: Reference data (stub)**
  - Create `kicad2wireBOM/reference_data.py` with ABOUTME comments
  - Define WIRE_RESISTANCE dict (stub with 3-4 AWG sizes)
  - Define WIRE_AMPACITY dict (stub with 3-4 AWG sizes)
  - Define STANDARD_AWG_SIZES list
  - Define DEFAULT_CONFIG dict (system_voltage, slack_length, voltage_drop_percent)
  - Write test: `tests/test_reference_data.py`

- `[ ]` **1.2: Wire length calculation**
  - Create `kicad2wireBOM/wire_calculator.py` with ABOUTME comments
  - Write function: `calculate_length(component1, component2, slack)` → float (inches)
  - Manhattan distance: |FS₁-FS₂| + |WL₁-WL₂| + |BL₁-BL₂| + slack
  - Write test: `tests/test_wire_calculator.py` (length calculation)

- `[ ]` **1.3: Wire gauge calculation**
  - In `wire_calculator.py`, add function: `calculate_voltage_drop(current, awg_size, length)` → float (volts)
  - Add function: `determine_min_gauge(current, length, system_voltage)` → int (AWG)
  - Use reference data for resistance and ampacity
  - Check both voltage drop (5%) and ampacity constraints
  - Write tests for gauge calculation

- `[x]` **1.4: Net name parsing and system code extraction** **[COMPLETED - 2025-10-18]**
  - ✓ `parse_net_name()` implemented in `wire_calculator.py`
  - ✓ Regex pattern: `/([A-Z])-?(\d+)-?([A-Z])/`
  - ✓ Handles: `/L1A`, `/L-1-A`, `/L001A`, `/L-001-A`, `/P1A`, `/G1A`
  - ✓ Returns: `{'system': 'L', 'circuit': '1', 'segment': 'A'}` or None
  - ✓ `infer_system_code_from_components()` implemented for validation
  - ✓ Basic inference patterns: "LIGHT" → "L", "BAT" → "P", "GND" → "G", etc.
  - ✓ `detect_system_code()` updated to use net name parsing as PRIMARY method
  - ✓ Component inference as FALLBACK if net name parsing fails
  - ✓ Comprehensive tests passing (7 new tests added)

- `[ ]` **1.5: Wire label generation** **[REVISED - 2025-10-17]**
  - In `wire_calculator.py`, add function: `format_wire_label(system_code, circuit_id, segment_letter, format='compact')` → str
  - Format options:
    - `compact`: `L1A` (default)
    - `dashes`: `L-1-A`
  - Write tests for both formats

- `[ ]` **1.6: Wire BOM data model** **[REVISED - 2025-10-17]**
  - Create `kicad2wireBOM/wire_bom.py` with ABOUTME comments
  - Define WireConnection dataclass with fields:
    - wire_label, from_ref, to_ref, wire_gauge, wire_color, length
    - wire_type, net_class **[NEW]**, net_name, warnings
  - Define WireBOM class with: wires list, config dict
  - Add method: `add_wire(wire)`
  - Write test: `tests/test_wire_bom.py`

- `[ ]` **1.7: CSV output (basic)**
  - Create `kicad2wireBOM/output_csv.py` with ABOUTME comments
  - Write function: `write_builder_csv(bom, output_path)`
  - Headers: Wire Label, From, To, Wire Gauge, Wire Color, Length, Wire Type, Warnings
  - Write test: `tests/test_output_csv.py`

- `[ ]` **1.8: Integration test for fixture 01**
  - Create `tests/test_fixture_01.py`
  - Parse netlist
  - Calculate wire specs
  - Generate CSV output
  - Verify output contents (one wire, correct values)
  - Test passes ✓

**Acceptance Criteria:**
- Produces valid CSV with one wire entry
- Wire length = Manhattan distance + 24"
- Wire gauge meets voltage drop constraint
- Wire label follows EAWMS format (e.g., "P-12-A")

**Commit:** "Complete Phase 1: Basic two-component circuit with CSV output"

---

## Phase 2: Test Fixture 02 - Simple Load Circuit with Shielded Wire **[REVISED - 2025-10-17]**

**Goal:** Multi-segment circuits with load calculations and shielded wire handling

**Test Fixture:** `tests/fixtures/test_02_simple_load.net` (use `docs/input/input_01_simple_lamp.net`)

**Special Feature:** Net `/L1B` has class "Shielded,Default" - must parse and apply shielded wire type

### Tasks

- `[ ]` **2.1: Circuit analysis module**
  - Create `kicad2wireBOM/circuit.py` with ABOUTME comments
  - Define Circuit dataclass: net_code, net_name, system_code, components, segments
  - Write function: `build_circuits(nets, components)` → list of Circuit objects
  - Write test: `tests/test_circuit.py`

- `[ ]` **2.2: Signal flow ordering**
  - In `circuit.py`, add function: `determine_signal_flow(circuit)` → ordered list of components
  - Identify source (has ref starting with "J", "BAT", "GEN")
  - Identify load (has load value)
  - Order: source → passthrough → load
  - Write test for signal flow ordering

- `[ ]` **2.3: Wire segmentation**
  - In `circuit.py`, add function: `create_wire_segments(circuit)` → list of segment defs
  - Create segments between adjacent components in signal flow order
  - Assign segment letters: A, B, C...
  - Write test for segmentation

- `[ ]` **2.4: Load vs Rating logic**
  - In `component.py`, add property: `is_source` (based on ref prefix)
  - In `wire_calculator.py`, update gauge calculation to use load current
  - Write test for load-based gauge calculation

- `[ ]` **2.5: Net class wire type handling** **[NEW - 2025-10-17]**
  - In `wire_calculator.py`, add function: `determine_wire_type(net_class: str, config)` → str
  - Check if net_class contains "Shielded" → return "M22759/16 (Shielded)"
  - Check config for custom class mappings (future extensibility)
  - Default: return "M22759/16"
  - Write test for shielded and non-shielded wires

- `[ ]` **2.6: Enhanced system code inference** **[REVISED - 2025-10-17]**
  - In `wire_calculator.py`, expand `infer_system_code_from_components()`:
    - Add component patterns: "LAMP" → "L", "BATTERY" → "P"
    - Net name analysis: "GND", "GROUND" → "G"
    - Make extensible (will load from `data/system_code_keywords.yaml` in Phase 6)
  - Write tests for inference (used for validation)

- `[ ]` **2.7: Integration test for fixture 02** **[REVISED - 2025-10-17]**
  - Create `tests/test_fixture_02.py`
  - Parse netlist with 3 components (BT1, SW1, L1)
  - Verify 3 nets/wires created: `/L1A`, `/L1B`, `/G1A`
  - Verify segment labels parsed from net names (L1A, L1B, G1A)
  - Verify `/L1B` has wire_type = "M22759/16 (Shielded)"
  - Verify `/L1A` and `/G1A` have wire_type = "M22759/16"
  - Verify load current (3.5A) used for L1A and L1B gauge calculation
  - Test passes ✓

**Acceptance Criteria:**
- CSV output has three rows (L1A, L1B, G1A)
- Segments labeled from net names correctly
- `/L1B` shows as shielded wire
- Load current used for lighting segments
- System codes parsed from net names (L, G)

**Commit:** "Complete Phase 2: Multi-segment circuit with shielded wire and ground return"

---

## Phase 3: Test Fixture 03 - Multi-Node Star Topology

**Goal:** Star topology detection and hub identification

**Test Fixture:** `tests/fixtures/test_03_multi_node_star.net`

### Tasks

- `[ ]` **3.1: Multi-node detection**
  - In `circuit.py`, add function: `is_multi_node(circuit)` → bool
  - Return True if 3+ components
  - Write test

- `[ ]` **3.2: Hub identification**
  - In `circuit.py`, add function: `identify_hub(circuit)` → Component
  - Implement priority algorithm:
    - Tier 1: BUS, BUSS, BAT, GND (substring match, case-insensitive)
    - Tier 2: FUSE, CB, PANEL
    - Tier 3: J/CONN with Rating ≥ 20A
    - Tier 4: Highest rating, closest to origin
  - Return hub component
  - Write test with various hub scenarios

- `[ ]` **3.3: Star topology wire creation**
  - In `circuit.py`, add function: `create_star_segments(hub, spokes)` → list of segments
  - Create hub→spoke segments for each spoke
  - Order spokes by distance from hub
  - Assign segment letters A, B, C...
  - Write test

- `[ ]` **3.4: Integration test for fixture 03**
  - Create `tests/test_fixture_03.py`
  - Parse 4-component star topology netlist
  - Verify hub identified correctly (J1)
  - Verify 3 segments created (one per spoke)
  - Verify all segments originate from hub
  - Test passes ✓

**Acceptance Criteria:**
- CSV has 3 rows (one per spoke)
- Hub correctly identified
- All segments connect hub to spokes

**Commit:** "Complete Phase 3: Multi-node star topology with hub detection"

---

## Phase 4: Test Fixture 06 - Missing Data (Permissive Mode) **[REVISED - 2025-10-17]**

**Goal:** Validation modes (strict and permissive) including net name validation

**Test Fixture:** `tests/fixtures/test_06_missing_data.net`

### Tasks

- `[ ]` **4.1: Validator module**
  - Create `kicad2wireBOM/validator.py` with ABOUTME comments
  - Define ValidationResult dataclass: component_ref, net_name, severity, message, suggestion
  - Write function: `validate_required_fields(components, permissive)` → list of ValidationResult
  - Write test: `tests/test_validator.py`

- `[ ]` **4.2: Net name format validation** **[NEW - 2025-10-17]**
  - In `validator.py`, add function: `validate_net_name_format(nets, permissive)` → list of ValidationResult
  - Check net names match pattern `/[SYSTEM][CIRCUIT][SEGMENT]`
  - Strict mode: Error if no match
  - Permissive mode: Warning if no match
  - Write test for net name validation

- `[ ]` **4.3: Duplicate label detection** **[NEW - 2025-10-17]**
  - In `validator.py`, add function: `validate_unique_labels(wires, permissive)` → list of ValidationResult
  - Check for duplicate wire labels
  - Strict mode: Error if duplicates found
  - Permissive mode: Warning + append suffix to make unique
  - Write test for duplicate detection

- `[ ]` **4.4: Multi-node net validation** **[NEW - 2025-10-17]**
  - In `validator.py`, add function: `validate_node_count(nets)` → list of ValidationResult
  - Check for nets with 3+ components
  - Always warn (both modes): "Net connects 3+ components, consider splitting into segments"
  - Write test for multi-node detection

- `[ ]` **4.5: System code validation** **[NEW - 2025-10-17]**
  - In `validator.py`, add function: `validate_system_codes(nets, components)` → list of ValidationResult
  - Compare parsed system code vs inferred system code
  - Always warn on mismatch (both modes): "Net system code doesn't match component analysis"
  - Write test for system code validation

- `[ ]` **4.6: Strict mode validation**
  - In `validator.py`, implement strict mode checks:
    - Error on missing FS/WL/BL
    - Error on missing Load/Rating
    - Error if both Load AND Rating present
  - Return error ValidationResults
  - Write test for strict mode errors

- `[ ]` **4.7: Permissive mode defaults**
  - In `parser.py`, add function: `apply_permissive_defaults(components)`
  - Default missing coordinates to (-9, -9, -9)
  - Default missing Load/Rating to 0.0
  - Generate warnings for applied defaults
  - Write test for permissive defaults

- `[ ]` **4.8: Warning system**
  - In `wire_bom.py`, add `warnings` field to WireConnection
  - In `validator.py`, add function: `collect_warnings(bom)` → list of warnings
  - Include warnings in CSV output (Warnings column)
  - Write test for warning collection

- `[ ]` **4.9: Integration test for fixture 06**
  - Create `tests/test_fixture_06.py`
  - Test strict mode: Verify errors and no output
  - Test permissive mode: Verify BOM generated with warnings
  - Verify default coordinates (-9, -9, -9)
  - Test net name validation
  - Test duplicate label handling
  - Test passes ✓

**Acceptance Criteria:**
- Strict mode fails with clear error messages
- Permissive mode produces BOM with warnings
- Missing coords default to (-9, -9, -9)
- Warnings appear in CSV output
- Net name format validated
- Duplicate labels detected
- Multi-node nets flagged
- System code mismatches warned

**Commit:** "Complete Phase 4: Strict and permissive modes with comprehensive validation"

---

## Phase 5: Test Fixture 07 - Negative Coordinates

**Goal:** Handle negative coordinates correctly

**Test Fixture:** `tests/fixtures/test_07_negative_coords.net`

### Tasks

- `[ ]` **5.1: Verify negative coordinate parsing**
  - Ensure `parse_footprint_encoding()` handles negative values
  - Update regex if needed: `([-\d.]+)` should already handle negatives
  - Write test with negative coordinates

- `[ ]` **5.2: Verify Manhattan distance with negatives**
  - `calculate_length()` already uses absolute values
  - Test with negative BL values
  - Write test: `tests/test_fixture_07.py`

- `[ ]` **5.3: Integration test for fixture 07**
  - Parse netlist with negative BL coordinates
  - Verify wire lengths calculated correctly
  - Test passes ✓

**Acceptance Criteria:**
- Negative coordinates parse correctly
- Wire lengths calculated correctly (absolute differences)

**Commit:** "Complete Phase 5: Negative coordinate handling"

---

## Phase 6: Test Fixture 05 - Multiple Independent Circuits **[REVISED - 2025-10-17]**

**Goal:** Complete wire color assignment and system code inference (for validation)

**Test Fixture:** `tests/fixtures/test_05_multiple_circuits.net`

### Tasks

- `[ ]` **6.1: Complete reference data extraction**
  - Update `reference_data.py` with complete data:
    - Full WIRE_RESISTANCE table (AWG 2-22)
    - Full WIRE_AMPACITY table (AWG 2-22)
    - SYSTEM_COLOR_MAP dict (L→White, P→Red, G→Black, R→Gray, A→Blue)
  - Source: Extract from `docs/references/aeroelectric_connection/` and `docs/ea_wire_marking_standard.md`
  - Write test verifying all data present

- `[ ]` **6.2: Enhanced system code inference (for validation)** **[REVISED - 2025-10-17]**
  - In `wire_calculator.py`, expand `infer_system_code_from_components()`:
    - Add component patterns: "RADIO", "NAV", "COM", "XPNDR" → "R"
    - Add: "GPS", "EFIS", "EMS", "AHRS" → "A"
    - Add: "FUEL", "OIL", "CHT", "EGT" → "E"
    - Net name analysis: "GND", "GROUND" → "G", "PWR", "POWER" → "P"
    - Pass-through analysis: Parse switch/fuse refs for keywords
    - Make extensible (configurable patterns in reference_data)
  - **PURPOSE**: Validation comparison, not primary detection
  - Write comprehensive tests for all patterns

- `[ ]` **6.3: Wire color assignment** **[REVISED - 2025-10-17]**
  - In `wire_calculator.py`, add function: `assign_wire_color(system_code)` → str
  - Look up system_code (parsed from net name) in SYSTEM_COLOR_MAP
  - Default to "White" if not found, with warning
  - Write test for color assignment

- `[ ]` **6.4: Output sorting**
  - In `wire_bom.py`, add method: `sort_wires()`
  - Sort by: system_code (alpha), circuit_id (numeric), segment_letter (alpha)
  - Write test for sorting

- `[ ]` **6.5: Update CSV output**
  - In `output_csv.py`, ensure Wire Color column populated
  - Ensure wires sorted before output
  - Write test

- `[ ]` **6.6: Integration test for fixture 05**
  - Create `tests/test_fixture_05.py`
  - Parse netlist with multiple systems (L, R, G)
  - Verify all system codes detected correctly
  - Verify wire colors assigned correctly
  - Verify output sorted by system/circuit/segment
  - Test passes ✓

**Acceptance Criteria:**
- All system codes (L, R, G) detected correctly
- Wire colors assigned per system
- CSV output sorted properly

**Commit:** "Complete Phase 6: Multiple circuits with system detection and colors"

---

## Phase 6.5: Comprehensive System Code Detection Enhancement **[REVISED - 2025-10-17]**

**Goal:** Implement comprehensive system code inference for high-quality validation

**Reference Documents:**
- `docs/plans/system_code_analysis.md` - Initial analysis and component categorization
- `docs/plans/keyword_extraction_from_657CZ.md` - Complete keyword lists extracted from real 657CZ schematic (163 components)

**Background:**
The Architect analyzed Tom's real 657CZ aircraft schematic and discovered that the current implementation will misclassify ~95% of components. The analysis identified 74 LRU (avionics) components and categorized all 163 components into 6 system codes.

**DESIGN REVISION NOTE:**
After the 2025-10-17 design revision, system code detection is NO LONGER the primary method for wire labeling. Instead:
- **Primary**: Parse system codes from net names (SD-provided)
- **Secondary**: Infer system codes from components for validation comparison

**WHY THIS PHASE IS STILL VALUABLE:**
The comprehensive keywords enable high-quality validation warnings. When the SD makes a mistake in net naming (e.g., labels a Radio net as Lighting), the inference engine will catch it and warn them. This helps the SD learn system codes and catch errors early.

### Tasks

- `[ ]` **6.5.1: Expand System R (Radio/Avionics) Keywords**
  - **Priority:** CRITICAL - 74 LRU components currently undetected
  - In `wire_calculator.py`, expand `radio_keywords` list:
    - Add Garmin model patterns: G5, G3X, GAD, GDU, GEA, GMA, GMC, GMU, GNX, GSA, GSU, GTR
    - Add device types: ADAHRS, AUDIO_PANEL, AUDIO, AUTOPILOT, SERVO, EIS, ELT, HSI, MAGNETOMETER, NAV_INTERFACE, NAV_INTRFCE, PFD, TRANSPONDER, XPONDER, VHF, COMM, COMMUNICATION
    - Add manufacturers: ARTEX, GARMIN, AVIONICS
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System R" section
  - Write comprehensive tests for all new keywords
  - **Expected Result:** 74 LRU components → System R (not U)

- `[ ]` **6.5.2: Expand System P (Power) Keywords**
  - **Priority:** HIGH - ~45 power components need better detection
  - In `wire_calculator.py`, expand `power_keywords` list:
    - Power generation: ALTERNATOR, ALT
    - Protection/distribution: BREAKER, CB, CONTACTOR, FUSE, FUSELINK, FUSE_LINK, FUSE_HOLDER, BUS, BATTERY_BUS, MAIN_BUS, SYSTEM_BUS, ENDURANCE_BUS
    - Components: STARTER, RELAY, SPDT, REGULATOR, VOLTAGE_REGULATOR, SHUNT, LOADMETER, OVERVOLTAGE, CROWBAR, CURRENT_LIMITER, ANL
    - Ground power: GROUND_POWER, GND_PWR, RECEPTACLE
    - Descriptors: BROWNOUT, AUX_ALT, ALT_FLD, ALT_FEED
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System P" section
  - Write tests for each keyword category
  - **Expected Result:** Alternators, breakers, relays, buses → System P

- `[ ]` **6.5.3: Add System K (Engine Control) Detection**
  - **Priority:** MEDIUM - New system code for ignition, fuel systems
  - In `wire_calculator.py`, add `engine_control_keywords` list:
    - IGNITION, ELEC_IGNITION, ELECTRONIC_IGNITION
    - MAGNETO, IMPULSE, NON_IMPULSE
    - PRIME_VALVE, PRIMER, BOOST_PUMP, FUEL_PUMP
    - ENGINE_CONTROL
  - Add System K to detection logic (search desc → value → ref → net name)
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System K" section
  - Write tests for engine control components
  - **Expected Result:** Ignition, magneto, fuel pumps → System K

- `[ ]` **6.5.4: Add System M (Miscellaneous Electrical) Detection**
  - **Priority:** MEDIUM - New system code for actuators, fans, ground buses
  - In `wire_calculator.py`, add `misc_electrical_keywords` list:
    - Ground: GROUND_BUS, GROUND_BLOCK, GB, GROUNDING, DSUB
    - Diodes: DIODE, 1N4005, 1N5400
    - Comfort/utility: HEATER, CABIN_HEATER, FAN, BLOWER, CASE_FAN, PANEL_FAN
    - Actuators: ACTUATOR, LINEAR_ACTUATOR, CANOPY, LANDING_BRAKE, BRAKE, NOSE_GEAR, GEAR
    - Sensors: PITOT_PROBE, PITOT
    - Shielding: SHIELD, SHIELD_CONNECTION
  - Add System M to detection logic
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System M" section
  - Write tests for miscellaneous components
  - **Expected Result:** Ground buses, actuators, heaters → System M

- `[ ]` **6.5.5: Add System E (Engine Instruments) Detection**
  - **Priority:** MEDIUM - New system code for fuel probes, sensors
  - In `wire_calculator.py`, add `engine_instrument_keywords` list:
    - FUEL_PROBE, FUEL_SENDER, POTENTIOMETER, POT
    - CHT, EGT, OIL_PRESSURE, OIL_TEMP, OIL_SENSOR
    - FUEL_FLOW, FUEL_PRESSURE, TACH, TACHOMETER, RPM
    - MANIFOLD_PRESSURE, MAP, SENSOR, SENDER
  - Add System E to detection logic
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System E" section
  - Write tests for engine instrument components
  - **Expected Result:** Fuel probes, sensors → System E

- `[ ]` **6.5.6: Expand System L (Lighting) Keywords**
  - **Priority:** LOW - Current detection is good, but add specific light types
  - In `wire_calculator.py`, expand `lighting_keywords` list:
    - Specific types: INTERIOR_LIGHT, INTERIOR, LANDING_LIGHT, LANDING, NAV_LIGHT, NAVIGATION_LIGHT, STROBE, TAXI_LIGHT, TAXI, ILLUMINATION
  - Reference: `docs/plans/keyword_extraction_from_657CZ.md` - "System L" section
  - Write tests for specific light types
  - **Expected Result:** Landing lights, strobes, nav lights → System L

- `[ ]` **6.5.7: Update System Color Map**
  - In `reference_data.py`, expand `SYSTEM_COLOR_MAP`:
    - Add: E → TBD (Engine Instruments)
    - Add: K → TBD (Engine Control)
    - Add: M → TBD (Miscellaneous)
  - **Note:** Colors for new systems need Tom's input
  - Write test for expanded color map

- `[ ]` **6.5.8: Comprehensive System Code Tests**
  - Create `tests/test_system_code_detection_comprehensive.py`
  - Test all 6 system codes with real 657CZ component examples
  - Test keyword priority (description → value → ref → net name)
  - Test edge cases and conflicts (NAV_LIGHT vs NAV)
  - Verify detection coverage: ~95%+ of 657CZ components correctly categorized
  - **Acceptance:** All tests pass with real component data

**Acceptance Criteria:**
- 6 system codes implemented (L, P, R, E, K, M)
- ~95%+ detection coverage for 657CZ components (163 total)
- 74 LRU components correctly identified as System R
- Power components (alternators, breakers, relays) correctly identified as System P
- Engine control/instruments correctly categorized
- All tests pass with real component examples

**Commit:** "Implement comprehensive system code detection based on 657CZ analysis"

**Reference for Next Phase:**
After completing this phase, the Programmer should review `docs/plans/keyword_extraction_from_657CZ.md` for implementation notes about:
- Keyword normalization (handling hyphens, underscores, spaces)
- Detection priority order
- Special cases and conflicts

---

## Phase 7: Test Fixture 08 - Realistic Complex System

**Goal:** Full end-to-end integration with CLI

**Test Fixture:** `tests/fixtures/test_08_realistic_system.net`

### Tasks

- `[ ]` **7.1: CLI module basics**
  - Create `kicad2wireBOM/__main__.py` with ABOUTME comments
  - Implement argument parser (argparse):
    - Positional: source (required), dest (optional)
    - Flags: --help, --permissive, --engineering, --version
    - Options: --system-voltage, --slack-length, --format
  - Write function: `main()` - CLI entry point
  - Write test: `tests/test_cli.py`

- `[ ]` **7.2: Auto-generate output filename**
  - In `__main__.py`, add function: `generate_output_filename(input_path, format)`
  - Parse input filename, find existing REVnnn files
  - Increment to next revision number
  - Format: `{base}_REV{nnn}.{ext}`
  - Write test for filename generation

- `[ ]` **7.3: Engineering mode CSV**
  - In `output_csv.py`, add function: `write_engineering_csv(bom, output_path)`
  - Additional columns: Calculated Min Gauge, Current, Vdrop (V), Vdrop (%), From Coords, To Coords, Calc Length
  - Populate from WireConnection engineering fields
  - Write test

- `[ ]` **7.4: Markdown output module**
  - Create `kicad2wireBOM/output_markdown.py` with ABOUTME comments
  - Write function: `write_builder_markdown(bom, output_path)`
    - Summary section (total wires, purchasing summary)
    - Wire list tables grouped by system
    - Warnings section
  - Write function: `write_engineering_markdown(bom, output_path)`
    - All builder sections plus detailed calculations
  - Write test: `tests/test_output_markdown.py`

- `[ ]` **7.5: Orchestration in main**
  - In `__main__.py`, implement full workflow:
    - Parse arguments
    - Load netlist
    - Extract components and nets
    - Build circuits
    - Calculate wire specs
    - Validate (strict/permissive)
    - Generate output (CSV or Markdown, builder or engineering)
    - Handle errors and exit codes
  - Write integration test

- `[ ]` **7.6: Integration test for fixture 08**
  - Create `tests/test_fixture_08.py`
  - Parse realistic netlist (10-15 components, 8-12 circuits)
  - Verify complete BOM generated
  - Test both CSV and Markdown output
  - Test both builder and engineering modes
  - Verify all features work together
  - Test passes ✓

- `[ ]` **7.7: CLI end-to-end test**
  - Test CLI invocation from command line:
    ```bash
    python -m kicad2wireBOM tests/fixtures/test_08_realistic_system.net output.csv
    python -m kicad2wireBOM --engineering tests/fixtures/test_08_realistic_system.net output.md
    python -m kicad2wireBOM tests/fixtures/test_08_realistic_system.net  # Auto-generate filename
    ```
  - Verify all work correctly
  - Manual verification of output files

**Acceptance Criteria:**
- Processes realistic netlist successfully
- Produces accurate, complete BOM
- Both output formats work (CSV, Markdown)
- Both output modes work (builder, engineering)
- CLI interface functional with all flags

**Commit:** "Complete Phase 7: Realistic system with full CLI and output formats"

---

## Phase 8: Remaining Features and Polish

**Goal:** Complete validation, documentation, and final touches

### 8.1 Validation Enhancements

- `[ ]` **8.1.1: Rating vs Load validation**
  - In `validator.py`, add function: `validate_rating_vs_load(circuit)` → list of ValidationResult
  - Trace circuit path from source to load
  - Check load doesn't exceed any rating in path
  - Generate warnings for violations
  - Write test

- `[ ]` **8.1.2: Gauge progression validation**
  - In `validator.py`, add function: `validate_gauge_progression(circuit)` → list of ValidationResult
  - Check that wire gauge doesn't decrease along path
  - Warn if downstream wire heavier than upstream
  - Write test

- `[ ]` **8.1.3: Component validation report (engineering mode)**
  - In `output_markdown.py`, add component validation table
  - List all components with coordinates, load/rating
  - Flag missing data
  - Write test

### 8.2 CLI Completion

- `[ ]` **8.2.1: --version flag**
  - In `__main__.py`, implement --version
  - Display tool version and exit
  - Version number from package metadata or constant
  - Write test

- `[ ]` **8.2.2: --schematic-requirements flag**
  - Create `kicad2wireBOM/schematic_help.py` with ABOUTME comments
  - Write function: `print_schematic_requirements(config)`
  - Output complete documentation for schematic designers:
    - Required fields (FS/WL/BL, Load/Rating)
    - Footprint encoding format
    - System codes table
    - Wire color mapping
    - Examples
  - Write test

- `[ ]` **8.2.3: --system-voltage and --slack-length flags**
  - In `__main__.py`, implement these options
  - Override DEFAULT_CONFIG values
  - Pass to calculation functions
  - Write test

- `[ ]` **8.2.4: Error messages and exit codes**
  - Ensure helpful error messages throughout
  - Include component refs in error messages
  - Provide suggestions for correction
  - Exit code 0 = success, 1 = error
  - Write test for error handling

### 8.3 Output Enhancements

- `[ ]` **8.3.1: Purchasing summary (Markdown)**
  - In `wire_bom.py`, add method: `get_wire_summary()` → dict
  - Group by (gauge, color): total length
  - In `output_markdown.py`, add purchasing summary section
  - Write test

- `[ ]` **8.3.2: Engineering mode detailed calculations**
  - In `output_markdown.py`, add sections:
    - Detailed calculations (voltage drop analysis)
    - Circuit analysis (power budget per system)
    - Assumptions documentation
  - Write test

- `[ ]` **8.3.3: Net name and net type in notes**
  - In `parser.py`, capture net_name and net_type from netlist
  - Add to Wire BOM (notes field or separate column)
  - Skip net_type if value is "DEFAULT"
  - Write test

### 8.4 Documentation

- `[ ]` **8.4.1: README.md**
  - Write comprehensive README:
    - Project description
    - Installation instructions
    - Quick start guide
    - Usage examples
    - Links to design docs

- `[ ]` **8.4.2: Module docstrings**
  - Verify all modules have ABOUTME comments
  - Verify all public functions have docstrings
  - Add any missing documentation

- `[ ]` **8.4.3: Example output**
  - Generate example CSV and Markdown outputs
  - Save to `docs/examples/` directory
  - Reference in README

### 8.5 Module Refactoring and Polish

- `[ ]` **8.5.1: Code review**
  - Review all modules for:
    - CLAUDE.md compliance
    - No temporal names
    - DRY (no duplication)
    - Type hints present
    - Tests comprehensive

- `[ ]` **8.5.2: Test coverage check**
  - Run: `pytest --cov=kicad2wireBOM --cov-report=term-missing`
  - Aim for >90% coverage
  - Add tests for any gaps

- `[ ]` **8.5.3: Performance check**
  - Test with large netlist (20+ circuits, 50+ components)
  - Ensure reasonable performance (<5 seconds)
  - Profile if needed

**Commit:** "Complete Phase 8: Validation, documentation, and polish"

---

## Final Verification

- `[ ]` **Run complete test suite**
  ```bash
  pytest -v
  ```
  All tests pass ✓

- `[ ]` **Run with all test fixtures**
  ```bash
  python -m kicad2wireBOM tests/fixtures/test_01_minimal_two_component.net
  python -m kicad2wireBOM tests/fixtures/test_02_simple_load.net
  python -m kicad2wireBOM tests/fixtures/test_03_multi_node_star.net
  python -m kicad2wireBOM tests/fixtures/test_06_missing_data.net --permissive
  python -m kicad2wireBOM tests/fixtures/test_07_negative_coords.net
  python -m kicad2wireBOM tests/fixtures/test_05_multiple_circuits.net
  python -m kicad2wireBOM tests/fixtures/test_08_realistic_system.net --engineering
  ```
  All produce valid output ✓

- `[ ]` **Manual verification**
  - Review generated BOMs for correctness
  - Check calculations by hand for one circuit
  - Verify output formats look professional
  - Test edge cases

**Final Commit:** "kicad2wireBOM v1.0: Complete implementation"

---

## Project Complete! 🎉

All phases complete, all tests pass, ready for real-world use.

**Next Steps:**
- Create GitHub release (v1.0.0)
- Add to PyPI (optional)
- Test with Tom's real aircraft schematics
- Collect feedback and iterate
