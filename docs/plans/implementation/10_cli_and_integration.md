# Work Package 10: CLI and Integration

## Overview

**Modules:** `kicad2wireBOM/__main__.py` and `kicad2wireBOM/schematic_help.py`

**Purpose:** Command-line interface and orchestration of all modules.

**Dependencies:** ALL other modules

**Estimated Effort:** 12-15 hours

**Important:** This package should be started AFTER all other packages are complete and tested.

---

## Module Interface Contracts

See `00_overview_and_contracts.md` section "Module 10"

**__main__.py Exports:**
- `main()` - CLI entry point
- `generate_output_filename(input_path, format, output_dir)` - REVnnn generation
- `load_config(config_path)` - Configuration file loading

**schematic_help.py Exports:**
- `print_schematic_requirements(config)` - Print requirements documentation

---

## Key Tasks

### Task 10.1: Implement Argument Parser (2 hours)

**CLI Specification (from design):**
```bash
python -m kicad2wireBOM [OPTIONS] SOURCE [DEST]

Required:
  SOURCE              KiCad netlist file (.net or .xml)

Optional:
  DEST                Output file (.csv or .md)

Flags:
  --help              Show help and exit
  --version           Show version and exit
  --schematic-requirements  Show required schematic fields and exit
  --permissive        Use defaults for missing fields (warnings instead of errors)
  --engineering       Enable engineering mode output (detailed calculations)

Options:
  --system-voltage VOLTS    System voltage (default: 12)
  --slack-length INCHES     Extra wire length (default: 24)
  --format {csv,md}         Output format (overrides extension)
  --config FILE             Configuration file path
```

**Tests:**
- Parse required argument (source)
- Parse optional argument (dest)
- Parse all flags
- Parse all options
- Default values work
- Invalid arguments show error

### Task 10.2: Implement generate_output_filename (2 hours)

**Functionality:**
- If no dest specified, generate from source filename
- Format: `<basename>_REV001.csv` (or .md)
- Find existing REVnnn files and increment
- REV001, REV002, REV003, etc.

**Tests:**
- No existing files → REV001
- REV001 exists → REV002
- REV005 exists → REV006
- Non-contiguous revisions handled
- Different formats (CSV vs MD) tracked separately

**Algorithm:**
```python
from pathlib import Path
import re

def generate_output_filename(input_path, format, output_dir):
    base = Path(input_path).stem  # e.g., "schematic"
    pattern = re.compile(rf"{base}_REV(\d+)\.{format}")

    # Find all existing revision files
    existing = []
    for file in Path(output_dir).glob(f"{base}_REV*{format}"):
        match = pattern.match(file.name)
        if match:
            existing.append(int(match.group(1)))

    # Next revision number
    next_rev = max(existing, default=0) + 1

    return Path(output_dir) / f"{base}_REV{next_rev:03d}.{format}"
```

### Task 10.3: Implement load_config (2 hours)

**Configuration File Search Order:**
1. Path specified by --config flag
2. Current working directory (`.kicad2wireBOM.yaml`)
3. Same directory as input netlist
4. User home directory

**Config File Format (YAML):**
```yaml
system_voltage: 14
slack_length: 30

wire_resistance:
  22: 0.016
  20: 0.010

wire_ampacity:
  22: 5
  20: 7.5

system_colors:
  L: White
  P: Red
```

**Tests:**
- Load valid YAML config
- Merge with defaults
- CLI args override config file
- Config file not found → use defaults
- Invalid config → error message

**Implementation:**
```python
import yaml
from pathlib import Path

def load_config(config_path: Optional[Path]) -> dict:
    """Load configuration from file and merge with defaults"""
    from kicad2wireBOM.reference_data import DEFAULT_CONFIG

    config = DEFAULT_CONFIG.copy()

    if config_path and config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f)
            if user_config:
                config.update(user_config)

    return config
```

### Task 10.4: Implement print_schematic_requirements (3 hours)

**Output Sections:**
1. Required Custom Fields (FS, WL, BL, Load/Rating)
2. Optional Custom Fields
3. Net Naming Convention
4. System Codes Table (from EAWMS)
5. Wire Color Mapping Table
6. Load vs Rating Explanation
7. Tool Assumptions (voltage drop, slack, etc.)
8. Complete Example Component
9. Field Export Verification Note

**Tests:**
- All sections present
- System codes from EAWMS included
- Color mapping from reference_data displayed
- Output is readable and well-formatted

### Task 10.5: Implement main() Orchestration (4 hours)

**Processing Flow:**
1. Parse arguments
2. Handle special commands (--help, --version, --schematic-requirements)
3. Load configuration file
4. Merge CLI args with config
5. Determine output format and filename
6. Parse netlist → components + nets
7. Build circuits from nets
8. For each circuit segment:
   - Calculate wire length
   - Determine wire gauge
   - Assign wire color
   - Generate wire label
   - Create WireConnection
9. Validate BOM
10. Sort BOM
11. Write output (CSV or Markdown, builder or engineering mode)
12. Print success message or errors
13. Return exit code (0=success, 1=error)

**Tests:**
- End-to-end with simple netlist
- End-to-end with complex netlist
- Error handling (file not found, parse errors)
- Exit codes correct
- Progress messages helpful
- Both output formats work
- Both output modes work

**Implementation Structure:**
```python
def main() -> int:
    """CLI entry point"""
    import sys
    import argparse
    from pathlib import Path

    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Handle special commands
        if args.schematic_requirements:
            print_schematic_requirements(config)
            return 0

        # Load config
        config = load_config(args.config)

        # Merge CLI args into config
        if args.system_voltage:
            config['system_voltage'] = args.system_voltage
        # ... etc for all CLI options

        # Determine output path and format
        if args.dest:
            output_path = Path(args.dest)
            output_format = args.format or output_path.suffix.lstrip('.')
        else:
            output_format = args.format or 'csv'
            output_path = generate_output_filename(
                args.source, output_format, Path.cwd()
            )

        # Parse netlist
        print(f"Parsing netlist: {args.source}")
        from kicad2wireBOM.parser import parse_netlist_file, extract_components, extract_nets
        parsed = parse_netlist_file(args.source)
        components = extract_components(parsed)
        nets = extract_nets(parsed)
        print(f"  Found {len(components)} components, {len(nets)} nets")

        # Build circuits
        print("Analyzing circuits...")
        from kicad2wireBOM.circuit import build_circuits
        circuits = build_circuits(nets, components)
        print(f"  Created {len(circuits)} circuits")

        # Generate BOM
        print("Calculating wire specifications...")
        from kicad2wireBOM.wire_bom import WireBOM, WireConnection
        from kicad2wireBOM.wire_calculator import (
            calculate_length, determine_min_gauge, assign_wire_color, generate_wire_label
        )
        from kicad2wireBOM.circuit import create_wire_segments

        bom = WireBOM()
        bom.config = config
        bom.components = components

        for circuit in circuits:
            segments = create_wire_segments(circuit)

            for i, segment in enumerate(segments):
                # Calculate wire specs
                length = calculate_length(
                    segment['from_comp'],
                    segment['to_comp'],
                    config['slack_length']
                )

                # Determine current (from load or rating)
                current = segment['to_comp'].load or segment['from_comp'].load or 0

                # Calculate minimum gauge
                awg, vdrop_v, vdrop_pct = determine_min_gauge(
                    current,
                    length,
                    config['system_voltage'],
                    config['slack_length']
                )

                # Assign color
                color = assign_wire_color(
                    circuit.system_code,
                    segment['from_comp'].wire_color
                )

                # Generate label
                label = generate_wire_label(
                    circuit.net_name,
                    circuit.circuit_id,
                    circuit.system_code,
                    segment['segment_letter']
                )

                # Create wire connection
                wire = WireConnection(
                    wire_label=label,
                    from_ref=f"{segment['from_comp'].ref}-{segment['from_pin']}",
                    to_ref=f"{segment['to_comp'].ref}-{segment['to_pin']}",
                    wire_gauge=f"{awg} AWG",
                    wire_color=color,
                    length=length,
                    wire_type=segment['from_comp'].wire_type or "M22759/16",
                    # Engineering fields
                    calculated_min_gauge=f"{awg} AWG",
                    voltage_drop_volts=vdrop_v,
                    voltage_drop_percent=vdrop_pct,
                    current=current,
                    from_coords=segment['from_comp'].coordinates,
                    to_coords=segment['to_comp'].coordinates,
                    calculated_length=length - config['slack_length']
                )

                bom.add_wire(wire)

        print(f"  Generated {len(bom.wires)} wire connections")

        # Validate
        print("Validating BOM...")
        from kicad2wireBOM.validator import collect_all_warnings
        warnings = collect_all_warnings(bom, circuits, components, args.permissive)
        if warnings:
            print(f"  {len(warnings)} validation issues found")

        # Sort BOM
        bom.sort_by_system_code()

        # Write output
        print(f"Writing output: {output_path}")
        if output_format == 'csv':
            if args.engineering:
                from kicad2wireBOM.output_csv import write_engineering_csv
                write_engineering_csv(bom, output_path)
            else:
                from kicad2wireBOM.output_csv import write_builder_csv
                write_builder_csv(bom, output_path)
        else:  # markdown
            if args.engineering:
                from kicad2wireBOM.output_markdown import write_engineering_markdown
                write_engineering_markdown(bom, output_path, components, config)
            else:
                from kicad2wireBOM.output_markdown import write_builder_markdown
                write_builder_markdown(bom, output_path)

        print("✓ Wire BOM generated successfully")
        if warnings:
            print(f"\n⚠ {len(warnings)} warnings - see output file for details")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

### Task 10.6: Integration Testing (2 hours)

**End-to-End Tests:**
- Process simple netlist → CSV
- Process simple netlist → Markdown
- Process complex netlist → Both formats
- Process with --engineering flag
- Process with --permissive flag
- Process with custom config file
- Auto-generate filename works
- REVnnn increments correctly
- Validate against hand-calculated example

**Test Fixtures:**
- Use netlists from tests/fixtures/
- Create expected output files
- Compare actual vs expected

---

## Testing Checklist

- [ ] Argument parser works
- [ ] All flags recognized
- [ ] Output filename generation works
- [ ] REVnnn increments correctly
- [ ] Config file loading works
- [ ] Schematic requirements prints
- [ ] End-to-end CSV generation works
- [ ] End-to-end Markdown generation works
- [ ] Engineering mode works
- [ ] Permissive mode works
- [ ] Error handling works
- [ ] Exit codes correct
- [ ] All tests pass

---

## Integration Notes

**Depends on:** ALL modules

**This is the final integration point.**

---

## Estimated Timeline

~14 hours total

---

## Completion Criteria

- CLI works end-to-end
- All output modes functional
- Real KiCad netlist processes successfully
- Integration tests pass
- Tool ready for use

---

## Final Steps

After completing this package:

1. Run complete test suite: `pytest -v`
2. Test with real KiCad schematic
3. Generate example outputs
4. Update main README with usage examples
5. Create final project documentation
6. Tag release v0.1.0
