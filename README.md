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
   from the file and can be overridden.
3. Click **Start Visualization** to open the editor:
   - The **die** (with numbered pads), the **VSS ring** around it, and the
     numbered **lead frame pins** are drawn to scale.
   - **Bond wires** connect each pad to its LF pin or the VSS ring
     (toggle with the "Show bond wires" checkbox).
   - Pads, wires and pins bonded together share the same color.
   - Click a pad to edit its name, net name or bonding target; saving
     updates the drawing immediately.
4. **Export Modified Excel** writes a new file (default: `exports/`);
   the original file is never modified.

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
main.py                        Entry point: upload window
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
  chip_visualization.py        Scene/view: die, VSS ring, LF pins, wires
  pad_editor.py                Edit panel for one pad
  editor_window.py             Main editor window
```
