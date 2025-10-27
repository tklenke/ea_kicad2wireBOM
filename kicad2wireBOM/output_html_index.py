# ABOUTME: HTML index page generation
# ABOUTME: Creates index.html with links to all output files

from pathlib import Path
from typing import List, Dict


def write_html_index(output_dir: Path, output_path: str, title_block: Dict[str, str] = None) -> None:
    """
    Write HTML index page with links to all outputs.

    Args:
        output_dir: Directory containing output files
        output_path: Path to output HTML file
        title_block: Optional dict with title, date, rev from schematic title_block

    HTML includes:
        - Project title block information
        - Links to wire and component BOMs
        - Links to system diagrams
        - Links to component diagrams
        - Links to star diagrams
        - Link to engineering report
        - Link to stdout/stderr logs
    """
    # Scan output directory for files
    wire_bom = "wire_bom.csv" if (output_dir / "wire_bom.csv").exists() else None
    component_bom = "component_bom.csv" if (output_dir / "component_bom.csv").exists() else None
    engineering_report = "engineering_report.txt" if (output_dir / "engineering_report.txt").exists() else None
    stdout_log = "stdout.txt" if (output_dir / "stdout.txt").exists() else None
    stderr_log = "stderr.txt" if (output_dir / "stderr.txt").exists() else None

    # Find system diagrams (*_System.svg)
    system_diagrams = sorted([f.name for f in output_dir.glob("*_System.svg")])

    # Find component diagrams (*_Component.svg)
    component_diagrams = sorted([f.name for f in output_dir.glob("*_Component.svg")])

    # Find star diagrams (*_Star.svg)
    star_diagrams = sorted([f.name for f in output_dir.glob("*_Star.svg")])

    # Build HTML
    html_lines = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append("<html lang=\"en\">")
    html_lines.append("<head>")
    html_lines.append("    <meta charset=\"UTF-8\">")
    html_lines.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    html_lines.append("    <title>kicad2wireBOM Output Index</title>")
    html_lines.append("    <style>")
    html_lines.append("        body { font-family: Arial, sans-serif; margin: 40px; }")
    html_lines.append("        h1 { color: #333; }")
    html_lines.append("        h2 { color: #666; margin-top: 30px; }")
    html_lines.append("        ul { list-style-type: none; padding: 0; }")
    html_lines.append("        li { margin: 8px 0; }")
    html_lines.append("        a { color: #0066cc; text-decoration: none; }")
    html_lines.append("        a:hover { text-decoration: underline; }")
    html_lines.append("        .section { margin-bottom: 30px; }")
    html_lines.append("    </style>")
    html_lines.append("</head>")
    html_lines.append("<body>")
    html_lines.append("    <h1>kicad2wireBOM Output Index</h1>")

    # Project information section
    if title_block:
        html_lines.append("    <div class=\"section\">")
        html_lines.append("        <h2>Project Information</h2>")
        html_lines.append("        <ul>")
        if 'title' in title_block:
            html_lines.append(f"            <li><strong>Project:</strong> {title_block['title']}</li>")
        if 'rev' in title_block:
            html_lines.append(f"            <li><strong>Revision:</strong> {title_block['rev']}</li>")
        if 'date' in title_block:
            html_lines.append(f"            <li><strong>Issue Date:</strong> {title_block['date']}</li>")
        if 'company' in title_block:
            html_lines.append(f"            <li><strong>Company:</strong> {title_block['company']}</li>")
        html_lines.append("        </ul>")
        html_lines.append("    </div>")

    # Bill of Materials section
    html_lines.append("    <div class=\"section\">")
    html_lines.append("        <h2>Bill of Materials</h2>")
    html_lines.append("        <ul>")
    if wire_bom:
        html_lines.append(f"            <li><a href=\"{wire_bom}\">Wire BOM (CSV)</a></li>")
    if component_bom:
        html_lines.append(f"            <li><a href=\"{component_bom}\">Component BOM (CSV)</a></li>")
    if not wire_bom and not component_bom:
        html_lines.append("            <li>No BOMs generated</li>")
    html_lines.append("        </ul>")
    html_lines.append("    </div>")

    # System Diagrams section
    if system_diagrams:
        html_lines.append("    <div class=\"section\">")
        html_lines.append("        <h2>System Diagrams</h2>")
        html_lines.append("        <ul>")
        for diagram in system_diagrams:
            # Extract system code from filename (e.g., "L_System.svg" -> "L")
            system_code = diagram.split('_')[0]
            html_lines.append(f"            <li><a href=\"{diagram}\">System {system_code}</a></li>")
        html_lines.append("        </ul>")
        html_lines.append("    </div>")

    # Component Diagrams section
    if component_diagrams:
        html_lines.append("    <div class=\"section\">")
        html_lines.append("        <h2>Component Diagrams</h2>")
        html_lines.append("        <ul>")
        for diagram in component_diagrams:
            # Extract component ref from filename (e.g., "CB1_Component.svg" -> "CB1")
            comp_ref = diagram.split('_')[0]
            html_lines.append(f"            <li><a href=\"{diagram}\">{comp_ref}</a></li>")
        html_lines.append("        </ul>")
        html_lines.append("    </div>")

    # Star Diagrams section
    if star_diagrams:
        html_lines.append("    <div class=\"section\">")
        html_lines.append("        <h2>Star Diagrams</h2>")
        html_lines.append("        <ul>")
        for diagram in star_diagrams:
            # Extract component ref from filename (e.g., "CB1_Star.svg" -> "CB1")
            comp_ref = diagram.split('_')[0]
            html_lines.append(f"            <li><a href=\"{diagram}\">{comp_ref}</a></li>")
        html_lines.append("        </ul>")
        html_lines.append("    </div>")

    # Reports section
    html_lines.append("    <div class=\"section\">")
    html_lines.append("        <h2>Reports and Logs</h2>")
    html_lines.append("        <ul>")
    if engineering_report:
        html_lines.append(f"            <li><a href=\"{engineering_report}\">Engineering Report</a></li>")
    if stdout_log:
        html_lines.append(f"            <li><a href=\"{stdout_log}\">Console Output (stdout)</a></li>")
    if stderr_log:
        html_lines.append(f"            <li><a href=\"{stderr_log}\">Error Output (stderr)</a></li>")
    if not engineering_report and not stdout_log and not stderr_log:
        html_lines.append("            <li>No reports generated</li>")
    html_lines.append("        </ul>")
    html_lines.append("    </div>")

    html_lines.append("</body>")
    html_lines.append("</html>")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(html_lines))
