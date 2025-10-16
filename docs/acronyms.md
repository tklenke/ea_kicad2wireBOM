# Acronyms

This document defines acronyms used throughout the ea_tools project.

## Project Acronyms

- **EA** - Experimental Aircraft
- **BOM** - Bill of Materials
- **KiCad** - Open-source electronics design automation suite
- **EAWMS** - Wire Marking Standard for EA.  file is ea_wire_marking_standard.md
- **OFI** - Opportunities For Improvement
- **AWG** - American Wire Gauge - wire sizing standard
- **TDD** - Test-Driven Development
- **YAGNI** - You Aren't Gonna Need It

## Aircraft Coordinate System

- **FS** - Fuselage Station - longitudinal aircraft coordinate (inches from datum, +forward/-aft)
- **WL** - Water Line - vertical aircraft coordinate (inches from datum, +above/-below)
- **BL** - Butt Line - lateral aircraft coordinate (inches from centerline, +right/-left)

## Domain-Specific Terms

- **Wire BOM** - Bill of Materials specifically for wire harness components and connections
- **Ampacity** - Current-carrying capacity of a wire (maximum safe amperage)
- **Load** - Current drawn by a consuming device (lights, radios, instruments, etc.)
- **Manhattan Distance** - Sum of absolute differences in each axis (taxicab metric) - used for wire length estimation
- **Net** - Electrical connection in a schematic connecting two or more component pins
- **Netlist** - File describing all connections in a schematic, exported from KiCad
- **Node** - Connection point (component pin) in a net
- **Rating** - Maximum current capacity of a pass-through device (switches, breakers, connectors)
- **Segment** - Individual physical wire run within a circuit (labeled A, B, C... in EAWMS format)
- **Signal Flow** - Direction of electrical current from source to load through a circuit
- **System Code** - Single-letter identifier for circuit function per MIL-W-5088L (L=Lighting, P=Power, R=Radio, etc.)
- **Topology** - Physical routing arrangement of wires in multi-node circuits (star, daisy-chain, etc.)
