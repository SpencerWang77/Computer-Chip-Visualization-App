from typing import List, Optional, Tuple

from models import Pad


class ChipLayout:
    """Holds the pad list and computes pad rectangles in die coordinates.

    Die coordinates come straight from the Excel file (micrometres, origin
    bottom-left, Y increasing upward). The view layer is responsible for
    flipping Y when drawing.
    """

    def __init__(self):
        self.pads: List[Pad] = []
        self.pad_rectangles = {}  # pad_id -> (x1, y1, x2, y2) in die coords

    def set_pads(self, pads: List[Pad]):
        self.pads = [pad for pad in pads if not pad.is_marked_for_deletion]
        self._calculate_layout()

    def _calculate_layout(self):
        self.pad_rectangles = {}
        for pad in self.pads:
            half_w = pad.x_open / 2
            half_h = pad.y_open / 2
            self.pad_rectangles[pad.pad_id] = (
                pad.x_coord - half_w,
                pad.y_coord - half_h,
                pad.x_coord + half_w,
                pad.y_coord + half_h,
            )

    # --- CRUD -------------------------------------------------------------

    def add_pad(self, pad: Pad) -> bool:
        if any(p.pad_id == pad.pad_id for p in self.pads):
            return False
        self.pads.append(pad)
        self._calculate_layout()
        return True

    def remove_pad(self, pad_id: str) -> bool:
        for i, pad in enumerate(self.pads):
            if pad.pad_id == pad_id:
                self.pads.pop(i)
                self._calculate_layout()
                return True
        return False

    def update_pad(self, pad_id: str, **kwargs) -> bool:
        pad = self.get_pad_by_id(pad_id)
        if pad is None:
            return False
        if 'pad_name' in kwargs:
            pad.pad_name = kwargs['pad_name']
        if 'x_coord' in kwargs:
            pad.x_coord = float(kwargs['x_coord'])
        if 'y_coord' in kwargs:
            pad.y_coord = float(kwargs['y_coord'])
        if 'x_open' in kwargs:
            pad.x_open = float(kwargs['x_open'])
        if 'y_open' in kwargs:
            pad.y_open = float(kwargs['y_open'])
        if 'net_name' in kwargs:
            pad.net_name = kwargs['net_name']
        if 'bonding' in kwargs:
            pad.bonding = kwargs['bonding']
        pad.mark_as_modified()
        self._calculate_layout()
        return True

    def get_pad_by_id(self, pad_id: str) -> Optional[Pad]:
        for pad in self.pads:
            if pad.pad_id == pad_id:
                return pad
        return None

    def get_all_pads(self) -> List[Pad]:
        return self.pads.copy()

    def get_modified_pads(self) -> List[Pad]:
        return [pad for pad in self.pads if pad.is_modified]

    # --- Geometry ---------------------------------------------------------

    def get_pad_rectangle(self, pad_id: str) -> Tuple[float, float, float, float]:
        return self.pad_rectangles.get(pad_id, (0, 0, 0, 0))

    def get_pad_at_position(self, x: float, y: float) -> Optional[Pad]:
        for pad in self.pads:
            rect = self.pad_rectangles.get(pad.pad_id)
            if rect:
                x1, y1, x2, y2 = rect
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return pad
        return None

    def get_bounds(self):
        """Bounding box of all pad rectangles in die coordinates."""
        if not self.pad_rectangles:
            return {'min_x': 0, 'max_x': 800, 'min_y': 0, 'max_y': 500,
                    'width': 800, 'height': 500}

        rects = self.pad_rectangles.values()
        min_x = min(r[0] for r in rects)
        min_y = min(r[1] for r in rects)
        max_x = max(r[2] for r in rects)
        max_y = max(r[3] for r in rects)
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y,
        }
