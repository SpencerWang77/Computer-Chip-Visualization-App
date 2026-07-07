# Chip Bonding Visualization

A PyQt5 desktop app for visualizing and editing the pad layout and bonding
relationships of one or more chip dies: which pads are wire-bonded to lead
frame pins, which are down-bonded to the VSS ring (E-PAD ring), which bond to
a pad on another die, and which are not bonded.

## Running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Select an Excel bonding file. Die sizes and pin count are read from the
   file. Optionally override the **lead frame pins** as *per top/bottom edge ×
   per left/right edge* (a rectangular package can differ), and the **VSS ring
   size** as *width × height* µm. Leave a field empty for a square / spacious
   default large enough to move all dies around.
2. Click **Start Visualization** to open the editor (one window; use
   **← Back to Upload** to return):
   - Each **die** (with numbered pads) sits inside a fixed **VSS ring**,
     surrounded by numbered black **lead frame pins** (LF.1 top of the left
     side, counting left↓ bottom→ right↑ top←). Multiple dies start arranged
     side by side.
   - **Move/rotate a die**: click a die to select it (orange border), then
     drag its body to move it, drag the round handle to rotate it by any
     angle — or pick the die in the **Die placement** dropdown and type its
     center position and angle. Each die moves independently; the ring and
     pins never move; bond wires re-route live.
   - **VSS ring size** can be changed live in the side panel (W × H µm); the
     dies stay in place as the ring resizes.
   - The axes at the ring's bottom-left corner mark the shared **ring
     coordinate system** origin; each pad's position in it is shown in the
     side panel.
   - **Bond wires**: gray = to a lead frame pin, blue = to the VSS ring
     (drawn radially — continuing the line from the die center through the
     pad out to the ring), purple = die-to-die (pad → pad on another die).
     Toggle with "Show bond wires". **Show pad names** labels each pad beside
     it; **Priority** (drag to reorder the dies) sets which die is drawn on
     top when dies overlap.
   - Click a pad to edit its name, net name or bonding target; saving
     updates the drawing immediately. **Revert** restores the original
     bonding value.
   - The **Show on pad** dropdown switches pad labels between the original
     number, the position number (rotation-aware, per die), and the bond
     target code (LF pin number / V / E / N / O / U).
3. **Export Modified Excel** writes a new file to a location you choose: one
   `Die Netlist(<name>)` tab per die (pad coordinates in each die's own local
   frame, mirroring the input), plus a `Basic information` sheet recording the
   VSS ring size and every die's position and angle. Reopening that file
   restores the ring size and drops every die back exactly where you left it.
   The original file is never modified.

## Excel format

**Multi-die**: one sheet per die named `Die Netlist(<name>)` (e.g.
`Die Netlist(SOC)`), plus an optional `Basic information` sheet giving each
die's size and the pin count. **Legacy single-die**: a sheet named `connect`.

Each die sheet:

| Row | Content |
|-----|---------|
| 1 | Headers: Die Pad No, Pad name, X-coord, Y-coord, X open, Y open, Net Name, Bonding |
| 2 | Units / remarks |
| 3+ | Pad data (coordinates in µm, each die's own origin bottom-left, Y up) |

Bonding values: `LF.<n>` (lead frame pin), `VSS_ring` (E-PAD ring),
`Not Bond`, or `SOC.<n>` / `ROM.<n>` / … (die-to-die — a wire to that pad on
the named die).

## Project structure

```
main.py                        Entry point: single window (upload/editor pages)
models/
  pad.py                       Pad data model
  chip_layout.py               Pad list + rectangle geometry (one die's coords)
  die.py                       A named die: pads + size + geometry
data_handlers/
  excel_handler.py             Reads die tabs + Basic information; pin auto-detect
  excel_exporter.py            Writes all pads to one combined sheet
ui/
  upload_section.py            File picker + package parameters
  format_description.py        File-format help box
  progress_control.py          Status label + start button
  chip_visualization.py        Scene/view: movable dies, fixed ring/pins, wires
  pad_editor.py                Edit panel for one pad
  editor_window.py             Editor page (diagram + controls)
```
