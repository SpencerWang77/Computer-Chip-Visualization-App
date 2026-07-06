from typing import List, Optional

from models.chip_layout import ChipLayout
from models.pad import Pad


class Die:
    """One die on the chip: a named group of pads with its own coordinate
    system (origin bottom-left, Y up, micrometres) and physical size.

    A chip may hold several dies (e.g. SOC and ROM) sharing one VSS ring.
    Geometry of the pads is delegated to a ChipLayout in the die's own frame.
    """

    def __init__(self, name: str, pads: List[Pad], width: float = None,
                 height: float = None):
        self.name = name
        self.layout = ChipLayout()
        self.layout.set_pads(pads)

        bounds = self.layout.get_bounds()
        # Physical die size; fall back to the pad bounding box (+2%).
        self.width = float(width) if width else bounds['width'] * 1.02
        self.height = float(height) if height else bounds['height'] * 1.02
        # Never smaller than the pads.
        self.width = max(self.width, bounds['width'])
        self.height = max(self.height, bounds['height'])

    # --- convenience delegators ------------------------------------------

    @property
    def pads(self) -> List[Pad]:
        return self.layout.pads

    def get_pad_by_id(self, pad_id: str) -> Optional[Pad]:
        return self.layout.get_pad_by_id(pad_id)

    def get_pad_rectangle(self, pad_id: str):
        return self.layout.get_pad_rectangle(pad_id)

    def get_bounds(self):
        return self.layout.get_bounds()

    def center(self):
        """Center of the pad bounding box, in die coordinates."""
        b = self.layout.get_bounds()
        return b['min_x'] + b['width'] / 2, b['min_y'] + b['height'] / 2

    def __repr__(self):
        return f"Die(name={self.name}, pads={len(self.pads)}, size={self.width:.1f}x{self.height:.1f})"
