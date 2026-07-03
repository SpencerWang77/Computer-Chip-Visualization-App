class Pad:
    """A single die pad: position/size on the die plus its bonding target.

    Bonding values found in the Excel data:
      - "LF.<n>"    -> wire bonded to lead frame pin n
      - "VSS_ring"  -> wire bonded down to the VSS ring (E-PAD ring)
      - "Not Bond"  -> no wire
      - "<DIE>.<n>" -> die-to-die bond (SOC/PSRAM/DDRA/DDRB/ROM)
    """

    def __init__(self, pad_id, pad_name, x_coord, y_coord, x_open, y_open, net_name, bonding):
        self.pad_id = str(pad_id) if pad_id is not None else ""
        self.pad_name = str(pad_name) if pad_name is not None else ""
        self.x_coord = float(x_coord) if x_coord else 0.0
        self.y_coord = float(y_coord) if y_coord else 0.0
        self.x_open = float(x_open) if x_open else 0.0
        self.y_open = float(y_open) if y_open else 0.0
        self.net_name = str(net_name) if net_name is not None else ""
        self.bonding = str(bonding).strip() if bonding is not None else ""

        self._modified = False
        self._marked_for_deletion = False

    @property
    def is_modified(self):
        return self._modified

    @property
    def is_marked_for_deletion(self):
        return self._marked_for_deletion

    def mark_as_modified(self):
        self._modified = True

    def reset_modified_status(self):
        self._modified = False

    def mark_for_deletion(self):
        self._marked_for_deletion = True

    def unmark_for_deletion(self):
        self._marked_for_deletion = False

    def update_position(self, x_coord=None, y_coord=None):
        if x_coord is not None:
            self.x_coord = float(x_coord)
        if y_coord is not None:
            self.y_coord = float(y_coord)
        self.mark_as_modified()

    def update_size(self, x_open=None, y_open=None):
        if x_open is not None:
            self.x_open = float(x_open)
        if y_open is not None:
            self.y_open = float(y_open)
        self.mark_as_modified()

    def update_info(self, pad_name=None, net_name=None, bonding=None):
        if pad_name is not None:
            self.pad_name = pad_name
        if net_name is not None:
            self.net_name = net_name
        if bonding is not None:
            self.bonding = str(bonding).strip()
        self.mark_as_modified()

    def clone(self):
        return Pad(
            self.pad_id,
            self.pad_name,
            self.x_coord,
            self.y_coord,
            self.x_open,
            self.y_open,
            self.net_name,
            self.bonding,
        )

    def __repr__(self):
        return (f"Pad(id={self.pad_id}, name={self.pad_name}, "
                f"coords=({self.x_coord}, {self.y_coord}), "
                f"open=({self.x_open}, {self.y_open}), "
                f"net={self.net_name}, bonding={self.bonding})")

    def to_dict(self):
        return {
            'pad_id': self.pad_id,
            'pad_name': self.pad_name,
            'x_coord': self.x_coord,
            'y_coord': self.y_coord,
            'x_open': self.x_open,
            'y_open': self.y_open,
            'net_name': self.net_name,
            'bonding': self.bonding,
            'is_modified': self._modified,
            'is_marked_for_deletion': self._marked_for_deletion,
        }

    @classmethod
    def from_dict(cls, data):
        pad = cls(
            data.get('pad_id', ''),
            data.get('pad_name', ''),
            data.get('x_coord', 0.0),
            data.get('y_coord', 0.0),
            data.get('x_open', 0.0),
            data.get('y_open', 0.0),
            data.get('net_name', ''),
            data.get('bonding', ''),
        )
        if data.get('is_modified', False):
            pad._modified = True
        if data.get('is_marked_for_deletion', False):
            pad._marked_for_deletion = True
        return pad
