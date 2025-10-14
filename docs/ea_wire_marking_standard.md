## Simplified Wire Marking System for Piston GA Aircraft (Revised)

This simplified wire marking system is designed for piston general aviation (GA) aircraft to provide clear, traceable, and standardized identification for maintenance and troubleshooting, with a focus on maximizing information density in a compact format.

### 1. Standard Marking Format

The primary wire marker label uses a compact, three-part structure to identify the wire's **system, specific circuit/function, and physical segment**.

| **Segment** | **Description** | **Length** | **Example** |
| :--- | :--- | :--- | :--- |
| **System Code** | Identifies the major system or zone the wire belongs to. | 1 Character | `A` |
| **Circuit ID** | The unique number or name of the electrical circuit (e.g., matching a schematic line number). | 3-5 Characters | `105` |
| **Segment ID** | A sequential letter for wire segments (A, B, C...) connecting multiple components within the same circuit net. | 1 Character (Optional) | `A` |

**Full Format Example:** `L-105-A`

* **L:** Lighting System
* **105:** Circuit 105 (e.g., Landing Light Power net)
* **A:** First physical segment of that net run

#### Complete Wire Marking Example

Consider a landing light circuit that runs from the main bus through a circuit breaker, to a switch, and finally to the landing light:

**Circuit Net 105: Landing Light**

| Wire Segment | Label | Description | Endpoints |
| :--- | :--- | :--- | :--- |
| Bus to Circuit Breaker | `L-105-A` | First segment of lighting circuit 105 | Main Bus → CB-105 |
| Circuit Breaker to Switch | `L-105-B` | Second segment after circuit protection | CB-105 → SW-105 |
| Switch to Landing Light | `L-105-C` | Final segment to load | SW-105 → Landing Light |
| Landing Light to Ground | `L-105-D` | Ground return path | Landing Light → Ground Point |

**Practical Marking (per Aeroelectric Connection 8:1021-1024):**
- Mark each wire segment at both termination points
- Use adhesive number tape (e.g., Digi-Key digit tape) or heat-shrink sleeves with printed markings
- Ensure markings are visible and readable after installation

***

### 2. System and Circuit Identification Codes

#### Single-Character System Codes

See MIL-W-5088L Appendix B for complete circuit function letters (A-Z). Common examples for piston GA aircraft:

- **A** - Armament (not applicable to most GA aircraft)
- **E** - Engine Instrument
- **F** - Flight Instrument
- **K** - Engine Control
- **L** - Lighting (Illumination)
- **M** - Miscellaneous (Electrical)
- **P** - DC Power (Generation, Distribution, Battery)
- **R** - Radio (Navigational and Communication)
- **U** - Miscellaneous (Electronic) - Common leads, antenna, power circuits
- **V** - AC Power
- **W** - Warning and Emergency

#### Circuit ID and Segment ID

* **Circuit ID (e.g., `105`):** Should directly correspond to a unique net name or line number on the master schematic. This links the physical wire back to the design document.
* **Segment ID (e.g., `A`):** Differentiates physical wires that belong to the same electrical net (Circuit ID). For example, a net that runs from the bus, through a fuse, to a component would use `...A` for the bus-to-fuse segment and `...B` for the fuse-to-component segment.

***

### 3. Wire Characteristics (Notes)

The wire's physical properties are not included in the main code but must be recorded in the accompanying wiring notes/log.

| Characteristic | Note Location | Example |
| :--- | :--- | :--- |
| **Wire Gauge** | Wiring Log / Schematic Notes | **20 AWG** (must be noted for proper current rating) |
| **Insulation Type** | Wiring Log / Installation Standard | e.g., **Teflon/Tefzel (MIL-W-22759)** |
| **Primary Wire Color** | Visual Inspection / Schematic | Red (often used for main power) |
| **Endpoints** | Derived from Schematic | **Main Bus** to **ANL Fuse** (for segment A) |

***

## References

The principles used in this system are derived from established industry and military practices to ensure traceability and reliability.

| Document | Description | Relevance to Marking |
| :--- | :--- | :--- |
| **MIL-STD-681E** | *Identification Coding and Application of Hookup and Lead Wire.* Systems III and IV apply to this standard. | Defines differentiation/functional coding by printed markings (System III) and coding of interconnecting wiring (System IV). |
| **MIL-W-5088L** | *Wiring, Aerospace Vehicle.* Appendix B defines circuit function letters. | Master aerospace wiring specification covering wire selection, installation, and identification. |
| **FAA Advisory Circular (AC) 43.13-1B** | *Acceptable Methods, Techniques, and Practices - Aircraft Inspection and Repair.* (Specifically Chapter 11, Electrical Systems) | Provides FAA-approved methods for wiring, including routing, clamping, and identification. |