# Chip Bonding Visualization

A PyQt5 desktop app for visualizing and editing the pad layout and bonding
relationships of a chip die: which pads are wire-bonded to lead frame pins,
which are down-bonded to the VSS ring (E-PAD ring), and which are not bonded.

## Running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Select an Excel bonding file (must contain a `connect` worksheet).
2. Check the die width/height; the lead frame pin count is auto-detected
   from the file and can be overridden. Optionally set the **VSS ring size**
   (outer side of the square ring); left empty, a spacious default is used.
3. Click **Start Visualization** to open the editor (one window; use
   **← Back to Upload** to return):
   - The **die** (with numbered pads) sits inside a fixed square **VSS ring**
     and the numbered black **lead frame pins** (LF.1 top of the left side,
     counting left↓ bottom→ right↑ top←).
   - **Move/rotate the die**: drag its body to move it, drag the round
     handle at its top-right corner to rotate it by any angle — or type the
     center position and angle in **Die placement** and press Apply. The
     ring and pins never move; bond wires re-route live.
   - The axes at the ring's bottom-left corner mark the **ring coordinate
     system** origin; each pad's position in it is shown in the side panel.
   - **Bond wires** connect each pad to its LF pin (gray) or the VSS ring
     (blue); toggle with "Show bond wires".
   - Click a pad to edit its name, net name or bonding target; saving
     updates the drawing immediately. **Revert** restores the original
     bonding value.
   - The **Show on pad** dropdown switches pad labels between the original
     number, the position number (rotation-aware), and the bond target code
     (LF pin number / V / E / N / O / U).
4. **Export Modified Excel** writes a new file to a location you choose;
   the current die move/rotation is baked into the exported coordinates and
   sizes, and the original file is never modified. Optionally renumber pads
   by position via the checkbox next to the export button.

## Excel format (`connect` sheet)

| Row | Content |
|-----|---------|
| 1 | Headers: Die Pad No, Pad name, X-coord, Y-coord, X open, Y open, Net Name, Bonding |
| 2 | Units / remarks |
| 3+ | Pad data (coordinates in µm, origin bottom-left, Y up) |

Bonding values: `LF.<n>` (lead frame pin), `VSS_ring` (E-PAD ring),
`Not Bond`, or `SOC.<n>` / `PSRAM.<n>` / `DDRA.<n>` / `DDRB.<n>` / `ROM.<n>`
(die-to-die).

## Project structure

```
main.py                        Entry point: single window (upload/editor pages)
models/
  pad.py                       Pad data model
  chip_layout.py               Pad list + rectangle geometry (die coords)
data_handlers/
  excel_handler.py             Reads the 'connect' sheet, pin auto-detect
  excel_exporter.py            Writes modified pads to a new workbook
ui/
  upload_section.py            File picker + package parameters
  format_description.py        File-format help box
  progress_control.py          Status label + start button
  chip_visualization.py        Scene/view: movable die, fixed ring/pins, wires
  pad_editor.py                Edit panel for one pad
  editor_window.py             Editor page (diagram + controls)
```
