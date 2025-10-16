# System Code Detection Analysis: 657CZ Components

**Date:** 2025-10-16
**Purpose:** Analyze real 657CZ aircraft components to validate and expand system code detection keywords

## Executive Summary

The programmer implemented `detect_system_code()` with three keyword sets (Lighting, Power, Radio). Analysis of the 657CZ schematic (163 components) reveals **gaps in detection coverage** for major aircraft systems. This document categorizes all real components by their appropriate system codes and extracts the keywords needed for accurate detection.

---

## Current Implementation Status

### Programmer's Current Keywords (wire_calculator.py:122-124)

```python
lighting_keywords = ['LIGHT', 'LAMP', 'LED']
power_keywords = ['BAT', 'BATT', 'BATTERY', 'PWR', 'POWER']
radio_keywords = ['RADIO', 'NAV', 'COM', 'XPNDR']
```

### Detection Priority (wire_calculator.py:102-107)
1. Component description fields
2. Component value fields
3. Component reference designators (with special handling for load components)
4. Net name
5. Default → "U" (Unknown)

---

## Component Analysis by System Code

### **P - Power (DC Generation & Distribution)**

**MIL-W-5088L Definition:** DC Power - Generation, Distribution, Battery

#### Components (18 total):
- **A1, A2** - Alternator-Generic - "ALTERNATOR GENERIC ENGINE MOUNTED"
- **BT1** - Battery - "Multiple-cell battery"
- **BT2** - Battery - "Main Battery"
- **B1** - Breaker-Switch - "2A"
- **B2** - Breaker-Pullable - "2 A"
- **B3** - Breaker-Pullable - "5A"
- **B4, B9, B13** - Breaker-Switch
- **B5, B6, B7, B10, B11, B12, B14, B15, B16** - Breaker-Pullable - "TBDA"
- **B8, B17** - Breaker-Pullable - "4A"
- **C1, C2** - Contactor_4_Terminal
- **C3** - C_Polarized - "20-50kFd/15-40V"
- **C4** - Contactor_3_Terminal_w_Diode - "Starter Contactor"
- **CON1** - Receptacle_Gnd_Pwr - "Ground Power Receptacle"
- **F1** - Fuse-Inline - "10A"
- **F2** - Fuse-Inline - "30A"
- **F6** - Fuse-Inline
- **FH1** - Fuse_Holder_6x - "Main Battery Bus"
- **FH2** - Fuse_Holder_10x
- **FH3** - Fuse_Holder_20x - "Main Bus"
- **FH4, FH5** - Fuse_Holder_6x - "G3X System Bus"
- **M1** - Starter - "STARTER"
- **R1** - S704-1D - "Alt Feed Relay"
- **R2** - S704-1 - "Brownout Battery Relay"
- **R3** - S704-1_r
- **R4, R5** - Shunt - "50MV/10A"
- **RG1** - Voltage_Regulator_Ford - "Generic Ford Voltage Regulator"
- **SW1, SW2, SW3, SW4, SW7, SW8, SW9, SW10, SW11, SW12, SW14, SW15, SW16, SW17, SW19, SW20, SW21, SW22, SW23, SW24** - S700-2-10 - "ON-ON-ON"
- **SW5** - S700-2-3 - "BATT/ALT DC POWER"
- **W1, W2** - Shield_Connection

#### Keywords to Detect:
**Component Names/Types:**
- ALTERNATOR, ALT
- BREAKER, CB
- CONTACTOR
- STARTER
- RELAY
- REGULATOR, VOLTAGE_REGULATOR
- SHUNT
- FUSE, FUSE_HOLDER
- CAPACITOR (when in power context)
- RECEPTACLE (for ground power)
- SHIELD (connection)

**Values/Descriptions:**
- ALTERNATOR, ENGINE_MOUNTED
- BATTERY, MAIN_BATTERY
- GROUND_POWER
- STARTER_CONTACTOR
- RELAY (ALT_FEED, BROWNOUT, BATTERY)
- VOLTAGE_REGULATOR
- MAIN_BUS, BATTERY_BUS, SYSTEM_BUS

**Reference Prefixes:**
- A (Alternator)
- BT (Battery)
- B (Breaker)
- C (Contactor)
- F (Fuse)
- FH (Fuse Holder)
- M (Motor/Starter)
- RG (Regulator)
- CON (Connector - when power-related)

---

### **L - Lighting (Illumination)**

**MIL-W-5088L Definition:** Lighting - Illumination

#### Components (12 total):
- **L1, L2, L3, L4, L5, L6, L7, L8, L9, L10** - Lamp - "~"
- **D4, D5** - LED - "RED"

#### Keywords to Detect:
**Current keywords are GOOD:**
- LIGHT, LAMP, LED ✓

**Additional keywords:**
- ILLUMINATION
- BEACON
- STROBE
- NAV_LIGHT (may overlap with R - Radio/Nav)
- TAXI
- LANDING
- INSTRUMENT_LIGHT

**Reference Prefixes:**
- L (Lamp/Light)
- D (when LED context)

---

### **R - Radio (Navigation & Communication)**

**MIL-W-5088L Definition:** Radio - Navigational and Communication

#### Components (74 total):
- **LRU1 through LRU74** - LRU_2x - "Generic LRU, 2 Connections"

**Note:** LRU = Line Replaceable Unit (avionics term for radio/nav/com equipment)

**CRITICAL DETECTION REQUIREMENT:**
LRU components in the schematic use generic reference designators (LRU1, LRU2, etc.) and generic component names (LRU_2x). **System code detection CANNOT rely on the reference prefix "LRU" alone.** The programmer MUST examine the component's **description** and **value** fields to determine the actual device type (GPS, radio, transponder, etc.).

Tom will provide a list of actual LRU descriptions/values from the real schematic to inform keyword extraction.

#### Keywords to Detect:
**Current keywords are LIMITED:**
- RADIO, NAV, COM, XPNDR ✓

**Critical additions (to be expanded when Tom provides LRU data):**
- AVIONICS
- TRANSPONDER (full word, not just XPNDR)
- GPS
- COMM (alternative spelling)
- VHF, UHF
- ADS-B
- EFIS (Electronic Flight Information System)
- AUTOPILOT
- DME (Distance Measuring Equipment)
- AUDIO_PANEL
- INTERCOM
- G3X, G5 (Garmin avionics)
- GTN, GNC (Garmin GPS/Nav/Com)
- GMA (Garmin Audio Panel)
- AVIDYNE
- DYNON

**Reference Prefixes:**
- LRU (Line Replaceable Unit) - **NOTE: Cannot be used alone, must check desc/value**
- R (Radio)

---

### **E - Engine Instruments**

**MIL-W-5088L Definition:** Engine Instrument

#### Components (2 total):
- **R6, R7** - R_Variable_US - "Variable resistor, US symbol"

**Note:** These variable resistors are likely fuel level senders or temperature sensors

#### Keywords to Detect:
**NEW SYSTEM - No current implementation:**
- ENGINE_INSTRUMENT
- CHT (Cylinder Head Temperature)
- EGT (Exhaust Gas Temperature)
- OIL_PRESSURE, OIL_TEMP
- FUEL_FLOW, FUEL_PRESSURE
- TACH, TACHOMETER, RPM
- MANIFOLD_PRESSURE, MAP
- SENSOR (when engine context)
- SENDER (fuel, temp)

**Reference Prefixes:**
- E (Engine instrument)

---

### **F - Flight Instruments**

**MIL-W-5088L Definition:** Flight Instrument

#### Components (Likely 0 in current list):
- None explicitly identified in 657CZ BOM

**Note:** Flight instruments (airspeed, altitude, attitude) in modern GA aircraft are often electronic (EFIS) and might be categorized as LRUs (system R)

#### Keywords to Detect:
**NEW SYSTEM - No current implementation:**
- FLIGHT_INSTRUMENT
- AIRSPEED
- ALTIMETER, ALTITUDE
- ATTITUDE
- VSI (Vertical Speed Indicator)
- TURN_COORDINATOR
- HEADING
- G_METER
- AOA (Angle of Attack)
- EFIS, PFD, MFD (may overlap with R)

**Reference Prefixes:**
- F (Flight instrument)

---

### **K - Engine Control**

**MIL-W-5088L Definition:** Engine Control

#### Components (Likely 1 in current list):
- **M1** - Starter - "STARTER" (could be P or K depending on interpretation)

#### Keywords to Detect:
**NEW SYSTEM - No current implementation:**
- ENGINE_CONTROL
- IGNITION
- MAGNETO
- MIXTURE
- THROTTLE (when electric)
- PROP_CONTROL, PROPELLER
- COWL_FLAP
- ELECTRONIC_IGNITION

**Reference Prefixes:**
- K (Engine control)

---

### **W - Warning and Emergency**

**MIL-W-5088L Definition:** Warning and Emergency

#### Components (Likely 2 in current list):
- **D4, D5** - LED - "RED" (Warning LEDs)

**Note:** Warning LEDs could be L (Lighting) or W (Warning) depending on function

#### Keywords to Detect:
**NEW SYSTEM - No current implementation:**
- WARNING
- ALARM
- ANNUNCIATOR
- EMERGENCY
- CAUTION
- STALL_WARNING
- LOW_VOLTAGE
- LOW_FUEL

**Reference Prefixes:**
- W (Warning)

---

### **M - Miscellaneous (Electrical)**

**MIL-W-5088L Definition:** Miscellaneous - Electrical

#### Components (5+ total):
- **D1** - D_Small - "Diode, small symbol"
- **D2** - D_Small - "1N5400"
- **D3** - D - "NOTE 12"
- **GB1** - Ground_Block_24x - "Instrument Panel Ground Bus"
- **GB2** - Ground_DSUB_25x - "Avionics Ground Bus"
- **SW6, SW13, SW18** - S700-1-2 - "Heater" (OFF-none-ON)

#### Keywords to Detect:
**NEW SYSTEM - No current implementation:**
- DIODE (protection, flyback)
- GROUND_BUS, GROUND_BLOCK
- HEATER (electric heat)
- FAN, BLOWER
- PUMP (electric fuel pump)
- WIPER
- TRIM (electric trim)
- FLAP (electric flaps)

**Reference Prefixes:**
- D (Diode)
- GB (Ground Bus/Block)
- M (Miscellaneous)

---

### **U - Miscellaneous (Electronic)**

**MIL-W-5088L Definition:** Miscellaneous (Electronic) - Common leads, antenna, power circuits

#### Components:
- Default catch-all for unclassified circuits

---

## Critical Gaps in Current Implementation

### 1. **Missing System Codes**
The programmer only implemented 3 system codes (L, P, R). The 657CZ schematic requires at least:
- **E** - Engine Instruments (variable resistors/sensors)
- **F** - Flight Instruments (if electronic)
- **K** - Engine Control (ignition, starter)
- **W** - Warning/Emergency (annunciators)
- **M** - Miscellaneous Electrical (ground buses, heaters, diodes)

### 2. **Power System Detection Incomplete**
Missing critical keywords:
- ALTERNATOR, ALT
- BREAKER, CB
- CONTACTOR
- STARTER
- RELAY
- REGULATOR
- SHUNT
- FUSE

### 3. **Radio/Avionics Detection Too Narrow**
Missing keywords for 74 LRU components:
- AVIONICS
- TRANSPONDER (full word)
- GPS
- AUDIO_PANEL, AUDIO
- AUTOPILOT
- G3X, GTN, GNC, GMA (Garmin model numbers)
- AVIDYNE, DYNON (manufacturer names)

**Note:** These keywords will be found in LRU description/value fields, not reference designators.

### 4. **Reference Prefix Detection**
Current implementation checks load component ref prefixes but needs expansion:
- A → P (Alternator)
- B → P (Breaker)
- BT → P (Battery)
- C → P (Contactor)
- F, FH → P (Fuse)
- E → E (Engine instrument)
- K → K (Engine control)
- W → W (Warning)
- M → M (Miscellaneous)
- GB → M (Ground Bus)

**Note:** Do NOT add LRU → R mapping. LRU reference prefixes are generic and meaningless without checking description/value fields.

---

## Recommendations for Programmer

### Priority 1: Expand Radio/Avionics Keywords
**Impact:** 74 LRU components will currently be marked "U" (Unknown)

**IMPORTANT:** LRU detection must rely on description/value fields, NOT reference prefixes.

Add to `radio_keywords` (to be expanded after Tom provides LRU data):
```python
radio_keywords = ['RADIO', 'NAV', 'COM', 'XPNDR', 'TRANSPONDER',
                  'AVIONICS', 'GPS', 'COMM', 'VHF', 'UHF',
                  'AUDIO_PANEL', 'INTERCOM', 'AUTOPILOT', 'EFIS',
                  'ADS-B', 'DME', 'G3X', 'G5', 'GTN', 'GNC', 'GMA',
                  'AVIDYNE', 'DYNON']
```

**Note:** Do NOT add "LRU" as a standalone keyword. The programmer's implementation already checks description/value fields first (correct priority), so actual device names (GPS, TRANSPONDER, etc.) will be detected.

### Priority 2: Expand Power Keywords
**Impact:** Many power distribution components won't be detected

Add to `power_keywords`:
```python
power_keywords = ['BAT', 'BATT', 'BATTERY', 'PWR', 'POWER',
                  'ALTERNATOR', 'ALT', 'BREAKER', 'CB',
                  'CONTACTOR', 'STARTER', 'RELAY', 'REGULATOR',
                  'SHUNT', 'FUSE', 'BUS', 'VOLTAGE_REGULATOR',
                  'GROUND_POWER']
```

### Priority 3: Add New System Codes
**Impact:** Proper categorization of engine, warning, and misc systems

Add keyword sets for:
- **E** - Engine Instruments
- **M** - Miscellaneous Electrical
- **W** - Warning/Emergency
- **K** - Engine Control
- **F** - Flight Instruments (if needed)

### Priority 4: Expand Reference Prefix Detection
**Impact:** Better fallback detection when keywords not found

**WARNING:** Reference prefix detection is ONLY a fallback. It should NOT be relied upon for LRU components, as they use generic "LRU1", "LRU2" names without meaningful device information.

Current code only checks load component ref prefixes. Consider expanding to:
```python
# Reference prefix → System code mapping (fallback only)
ref_prefix_map = {
    'A': 'P',    # Alternator
    'B': 'P',    # Breaker
    'BT': 'P',   # Battery
    'C': 'P',    # Contactor
    'F': 'P',    # Fuse
    'FH': 'P',   # Fuse Holder
    'M': 'P',    # Motor/Starter (or 'M' if misc)
    'RG': 'P',   # Regulator
    'L': 'L',    # Lamp/Light
    'E': 'E',    # Engine instrument
    'K': 'K',    # Engine control
    'W': 'W',    # Warning
    'GB': 'M',   # Ground Bus
    'D': 'M'     # Diode (or 'L' if LED)
    # NOTE: Do NOT add 'LRU' → 'R' mapping
    # LRU refs are generic and must be detected via desc/value
}
```

**Recommendation:** Keep reference prefix detection as minimal fallback. Primary detection should ALWAYS be via description/value fields.

---

## Testing Strategy

### Test Fixture Requirements
Create test fixtures with components from each system:

1. **Power System Test** (Alternator, Battery, Breaker, Relay, Bus)
2. **Avionics/LRU Test** (Multiple LRUs on same net)
3. **Engine Instruments Test** (Sensors, senders)
4. **Warning System Test** (Annunciators, warning LEDs)
5. **Miscellaneous Test** (Ground bus, heater, diode)

### Expected Outcomes
After implementing recommendations:
- **74 LRU components** → System R (not U)
- **Alternators A1, A2** → System P (not U)
- **Breakers B1-B17** → System P
- **Variable resistors R6, R7** → System E (if engine sensors)
- **Ground buses GB1, GB2** → System M
- **Heater switches SW6, SW13, SW18** → System M

---

## Document Status
- **Status:** Draft - Awaiting Tom's Review
- **Next Steps:**
  1. Tom reviews and approves recommendations
  2. Architect creates updated keyword specification
  3. Programmer implements expanded detection
  4. Create test fixtures for each system code
  5. Validate against full 657CZ schematic
