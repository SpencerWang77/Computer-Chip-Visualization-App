import os
from datetime import datetime

import openpyxl


class ExcelExporter:
    """Writes the (possibly modified) pad data to a new Excel file.

    The original workbook is never modified; the caller chooses the output
    path. Multi-die exports go into one combined sheet whose coordinates are
    in the shared ring coordinate system (origin at the ring's bottom-left).
    """

    HEADERS = ["Die Pad No", "Pad name", "X-coord", "Y-coord",
               "X open", "Y open", "Net Name", "Bonding"]
    UNITS = ["", "", "(ring frame)", "(ring frame)",
             "(after rotation)", "(after rotation)", "", "relationship"]

    def __init__(self, source_file=None):
        self.source_file = source_file

    def export_by_die(self, rows, output_path):
        """Export one 'Die Netlist(<name>)' tab per die (mirroring the input).

        `rows` is a list of (die_name, Pad) with coordinates already baked into
        the shared ring frame. Returns (success, saved_path).
        """
        try:
            if not output_path:
                raise ValueError("No output path given")
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Group pads by die, preserving first-seen die order.
            by_die = {}
            for die_name, pad in rows:
                by_die.setdefault(die_name, []).append(pad)

            workbook = openpyxl.Workbook()
            workbook.remove(workbook.active)  # drop the default empty sheet
            for die_name, pads in by_die.items():
                sheet = workbook.create_sheet(title=self._sheet_title(die_name))
                for col, value in enumerate(self.HEADERS, 1):
                    sheet.cell(row=1, column=col, value=value)
                for col, value in enumerate(self.UNITS, 1):
                    sheet.cell(row=2, column=col, value=value)
                for row_idx, pad in enumerate(pads, 3):
                    sheet.cell(row=row_idx, column=1, value=pad.pad_id)
                    sheet.cell(row=row_idx, column=2, value=pad.pad_name)
                    sheet.cell(row=row_idx, column=3, value=pad.x_coord)
                    sheet.cell(row=row_idx, column=4, value=pad.y_coord)
                    sheet.cell(row=row_idx, column=5, value=pad.x_open)
                    sheet.cell(row=row_idx, column=6, value=pad.y_open)
                    sheet.cell(row=row_idx, column=7, value=pad.net_name)
                    sheet.cell(row=row_idx, column=8, value=pad.bonding)

            workbook.save(output_path)
            return True, output_path

        except Exception as e:
            print(f"Excel export failed: {e}")
            return False, None

    @staticmethod
    def _sheet_title(die_name):
        # Excel sheet titles are capped at 31 chars.
        return f"Die Netlist({die_name})"[:31]

    def get_export_summary(self, pads):
        return {
            'total_pads': len(pads),
            'modified_pads': len([p for p in pads if p.is_modified]),
            'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
