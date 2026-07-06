"""Graphics scene/view for the chip bonding diagram.

Draws, from the inside out:
  1. The die with its pads (colored by bonding target). The die and its pads
     form one movable unit: drag the die body to move it, drag the round
     handle at its top-right corner to rotate it by any angle (or use the
     numeric "Die placement" controls in the editor panel).
  2. The VSS ring (E-PAD ring): a fixed square band that does not move or
     rotate with the die. Its own coordinate system has its origin at the
     ring's bottom-left corner (X right, Y up) and is drawn as small axes.
  3. The individual lead frame pins around the outside (LF.1 ... LF.n,
     numbered: left side top->down, bottom left->right, right bottom->up,
     top right->left). Pins are fixed, like the ring.
  4. Optional bond wires from each pad to its LF pin or to the VSS ring;
     they re-route live while the die is dragged or rotated.

Coordinates in the Excel file are die coordinates in micrometres with the
origin at the bottom-left and Y increasing upward. Qt's Y axis points down,
so every die coordinate is flipped (scene_y = -die_y) when drawn.
"""

import math
import re

from PyQt5.QtCore import QEvent, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (QBrush, QColor, QFont, QNativeGestureEvent, QPainter,
                         QPainterPath, QPen)
from PyQt5.QtWidgets import (QGraphicsEllipseItem, QGraphicsLineItem,
                             QGraphicsPathItem, QGraphicsRectItem,
                             QGraphicsScene, QGraphicsTextItem, QGraphicsView)

from models import ChipLayout, Pad

_LF_PATTERN = re.compile(r'^LF[._\s]*(\d+)$', re.IGNORECASE)
_DIE_PREFIXES = ('SOC.', 'PSRAM.', 'DDRA.', 'DDRB.', 'ROM.')

# Pad/pin fill colors
COLOR_NOT_BOND = QColor(33, 33, 33, 220)        # black
COLOR_VSS = QColor(41, 128, 185, 220)           # dark blue
COLOR_DIE_TO_DIE = QColor(80, 80, 80, 220)      # dark gray
COLOR_UNDEFINED = QColor(192, 57, 43, 220)      # dark red
COLOR_PIN = QColor(20, 20, 20, 255)             # solid black (all lead frame pins)

# Bond wires are drawn in one uniform color per target type (for a clean look).
COLOR_LF_WIRE = QColor(127, 140, 141)           # all lead-frame bond wires
COLOR_RING_WIRE = QColor(41, 128, 185)          # all VSS-ring bond wires

# Ring geometry: band thickness and the default size factor used when the
# user does not enter a ring size (relative to the larger die dimension).
RING_THICKNESS_FACTOR = 0.04
RING_DEFAULT_FACTOR = 1.35

# Bond wires draw above everything else (die, pads, pins) so they are never
# hidden by the die rectangle.
WIRE_Z = 50

# Light palette for lead-frame pads (cycled by pin number). Deliberately
# excludes blue so these light colors never clash with the dark blue VSS ring.
LF_PALETTE = [
    QColor(46, 204, 113, 230),   # green
    QColor(241, 196, 15, 230),   # amber
    QColor(230, 126, 34, 230),   # orange
    QColor(155, 89, 182, 230),   # purple
    QColor(72, 219, 191, 230),   # aqua
    QColor(255, 105, 180, 230),  # pink
]


def classify_bonding(bonding: str):
    """Return (kind, detail) where kind is one of
    'not_bond' | 'vss_ring' | 'epad' | 'lf' | 'die' | 'unknown'.
    For 'lf', detail is the pin number (int). 'vss_ring' and 'epad' share the
    same color but carry different display codes (V vs E)."""
    value = (bonding or "").strip()
    upper = value.upper()

    if upper in ("", "NOT BOND", "NOT_BOND"):
        return 'not_bond', None

    if "E-PAD" in upper or "E_PAD" in upper or "EPAD" in upper:
        return 'epad', None
    if "VSS" in upper and "RING" in upper:
        return 'vss_ring', None

    match = _LF_PATTERN.match(value)
    if match:
        return 'lf', int(match.group(1))

    if upper.startswith(tuple(p.upper() for p in _DIE_PREFIXES)):
        return 'die', None

    return 'unknown', None


def bond_code(bonding: str) -> str:
    """Short code shown on a pad in the 'bond target' display mode:
    the LF pin number, or V / E / N / O / U."""
    kind, detail = classify_bonding(bonding)
    if kind == 'lf':
        return str(detail)
    return {
        'vss_ring': 'V',
        'epad': 'E',
        'not_bond': 'N',
        'die': 'O',
        'unknown': 'U',
    }.get(kind, 'U')


def lf_color(pin_number: int) -> QColor:
    return LF_PALETTE[pin_number % len(LF_PALETTE)]


def bonding_color(bonding: str) -> QColor:
    kind, detail = classify_bonding(bonding)
    if kind == 'not_bond':
        return COLOR_NOT_BOND
    if kind in ('vss_ring', 'epad'):
        return COLOR_VSS
    if kind == 'lf':
        return lf_color(detail)
    if kind == 'die':
        return COLOR_DIE_TO_DIE
    return COLOR_UNDEFINED


class PadGraphicsItem(QGraphicsRectItem):
    """A pad rectangle with its number centered inside. Lives as a child of
    the die group, so it moves and rotates with the die."""

    def __init__(self, pad: Pad, rect: QRectF, fill_color: QColor, label: str):
        super().__init__(rect)
        self.pad = pad
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setAcceptHoverEvents(False)
        self.setZValue(10)

        self.setPen(QPen(QColor(41, 128, 185), 3))
        self.setBrush(QBrush(fill_color))

        self.text_item = QGraphicsTextItem()
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setZValue(100)
        self.update_label(label)

    def update_label(self, label: str):
        """Set (or replace) the pad's label, fitted and centered in the pad."""
        rect = self.rect()
        min_dim = min(rect.width(), rect.height())
        divisor = {1: 1.8, 2: 2.5}.get(len(label), 3.5)
        font_size = max(6.0, min_dim / divisor)

        text_item = self.text_item
        text_item.setPlainText(label)
        text_item.setFont(QFont("Arial", int(font_size), QFont.Bold))

        # Shrink until the label fits inside the pad.
        for _ in range(4):
            bounds = text_item.boundingRect()
            if bounds.width() <= rect.width() * 0.95 and bounds.height() <= rect.height() * 0.95:
                break
            font = text_item.font()
            font.setPointSize(max(4, int(font.pointSize() * 0.8)))
            text_item.setFont(font)

        bounds = text_item.boundingRect()
        text_item.setPos(rect.x() + (rect.width() - bounds.width()) / 2,
                         rect.y() + (rect.height() - bounds.height()) / 2)
        # Origin at the text center so a counter-rotation keeps it in place.
        text_item.setTransformOriginPoint(bounds.center())

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(QColor(243, 156, 18), 5))  # orange when selected
            else:
                self.setPen(QPen(QColor(41, 128, 185), 3))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.scene():
            for item in self.scene().selectedItems():
                if item is not self:
                    item.setSelected(False)
        self.setSelected(True)
        if self.scene() and hasattr(self.scene(), 'pad_clicked'):
            self.scene().pad_clicked.emit(self.pad)
        super().mousePressEvent(event)


class DieRotationHandle(QGraphicsEllipseItem):
    """Round handle outside the die's top-right corner; drag it to rotate the
    die around its center by any angle."""

    def __init__(self, die_item, radius: float, pos: QPointF):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, die_item)
        self.setPos(pos)
        self.setBrush(QBrush(QColor(52, 152, 219)))
        self.setPen(QPen(QColor(255, 255, 255), radius * 0.3))
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag to rotate the die")
        self._start_angle = 0.0
        self._start_rotation = 0.0

    def _cursor_angle(self, event) -> float:
        die = self.parentItem()
        center = die.mapToScene(die.transformOriginPoint())
        pos = event.scenePos()
        return math.degrees(math.atan2(pos.y() - center.y(), pos.x() - center.x()))

    def mousePressEvent(self, event):
        self._start_angle = self._cursor_angle(event)
        self._start_rotation = self.parentItem().rotation()
        self.setCursor(Qt.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        delta = self._cursor_angle(event) - self._start_angle
        die = self.parentItem()
        die.setRotation(self._start_rotation + delta)
        die.notify_transform()
        event.accept()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        self.parentItem().notify_interaction_end()
        event.accept()


class DieGroupItem(QGraphicsRectItem):
    """The die outline; the pads, their labels, the DIE label and the rotation
    handle are its children, so the whole die moves/rotates as one unit.
    Drag the die body (not a pad) to move it."""

    def __init__(self, chip_scene, rect: QRectF):
        super().__init__(rect)
        self._chip_scene = chip_scene
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.SizeAllCursor)
        self.setTransformOriginPoint(rect.center())
        self.setPen(QPen(QColor(127, 140, 141), rect.width() * 0.003))
        self.setBrush(QBrush(QColor(236, 240, 241)))
        # Above the ring/pins; the bond wires (WIRE_Z) draw above the die.
        self.setZValue(6)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            self.notify_transform()
        return super().itemChange(change, value)

    def notify_transform(self):
        self._chip_scene._on_die_transform_changed()

    def notify_interaction_end(self):
        self._chip_scene._on_die_interaction_end()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.notify_interaction_end()


class ChipScene(QGraphicsScene):
    pad_clicked = pyqtSignal(object)
    # Emitted whenever the die is moved/rotated (by hand or numerically):
    # (die center x, die center y, rotation in degrees CCW), die coordinates.
    die_transform_changed = pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chip_layout = ChipLayout()
        self.pad_items = {}       # pad_id -> PadGraphicsItem
        self.wire_items = {}      # pad_id -> QGraphicsLineItem
        self._wire_targets = {}   # pad_id -> ('lf', pin_no) | ('ring', None)
        self.pin_points = {}      # pin number -> QPointF (inner tip, scene coords)
        self.ring_outer = None       # QRectF, fixed, scene coords
        self.ring_centerline = None  # QRectF, fixed, scene coords
        self.die_group = None        # DieGroupItem
        self._frame_params = None
        self._wires_visible = True
        self._highlighted_wire = None
        self._die_center = (0.0, 0.0)   # original die center, die coords
        self._die_rotation = 0.0        # degrees CCW (any angle)
        self._die_offset = (0.0, 0.0)   # translation, die coords
        self._display_mode = 'soc'      # 'soc' | 'position' | 'bond'
        self._position_numbers = {}     # pad_id -> positional index (int)
        self._building = False
        self.pad_clicked.connect(self._on_pad_clicked)

    # --- public API ---------------------------------------------------

    def set_pads(self, pads, frame_params=None):
        self._frame_params = frame_params
        self.chip_layout.set_pads(pads)
        self._redraw()

    def refresh(self):
        """Redraw with the current pads (e.g. after an edit)."""
        self._redraw()

    def set_display_mode(self, mode: str):
        """Choose what each pad shows: 'soc' (original number),
        'position' (positional number for the current rotation), or
        'bond' (LF pin number / V / E / N / O / U)."""
        if mode != self._display_mode:
            self._display_mode = mode
            self._redraw()

    def rotate_die(self, degrees):
        """Rotate the die by the given angle (positive = counterclockwise)
        around its center, keeping its current position."""
        cx, cy, rotation = self.die_transform()
        self.set_die_transform(cx, cy, rotation + degrees)

    def set_die_transform(self, center_x: float, center_y: float, rotation_deg: float):
        """Place the die: its center goes to (center_x, center_y) in die
        coordinates, rotated rotation_deg degrees CCW. Ring and pins stay."""
        cx0, cy0 = self._die_center
        self._die_offset = (center_x - cx0, center_y - cy0)
        self._die_rotation = self._normalize_angle(rotation_deg)
        self._apply_die_transform()
        self._after_die_transform(refresh_labels=True)

    def die_transform(self):
        """Current die placement: (center_x, center_y, rotation_deg CCW)."""
        cx0, cy0 = self._die_center
        dx, dy = self._die_offset
        return cx0 + dx, cy0 + dy, self._die_rotation

    def reset_die_transform(self):
        cx0, cy0 = self._die_center
        self.set_die_transform(cx0, cy0, 0.0)

    def set_wires_visible(self, visible: bool):
        self._wires_visible = visible
        for item in self.wire_items.values():
            item.setVisible(visible)

    def reset_view(self):
        """Reset die placement / display mode / wire visibility to defaults
        (used when a new file is loaded). Does not redraw on its own."""
        self._die_rotation = 0.0
        self._die_offset = (0.0, 0.0)
        self._display_mode = 'soc'
        self._wires_visible = True

    @property
    def die_rotation(self) -> float:
        return self._die_rotation

    def rotated_geometry(self, pad: Pad):
        """(x_coord, y_coord, x_open, y_open) for a pad after the current die
        move/rotation, in die coordinates. At the default placement this
        equals the pad's stored values. For non-axis-aligned angles the
        openings are the axis-aligned bounding box of the rotated pad."""
        rx, ry = self._transform_die_point(pad.x_coord, pad.y_coord)
        theta = math.radians(self._die_rotation)
        c, s = abs(math.cos(theta)), abs(math.sin(theta))
        x_open = pad.x_open * c + pad.y_open * s
        y_open = pad.x_open * s + pad.y_open * c
        return rx, ry, x_open, y_open

    def ring_coords(self, pad: Pad):
        """Pad center in the ring coordinate system: origin at the ring's
        bottom-left (outer) corner, X right, Y up. None if nothing is drawn."""
        if self.ring_outer is None or pad.pad_id not in self.pad_items:
            return None
        p = self.pad_scene_center(pad.pad_id)
        return p.x() - self.ring_outer.left(), self.ring_outer.bottom() - p.y()

    def pads_with_rotation_applied(self, renumber_by_position=False):
        """Clones of the current pads with the die move/rotation baked into
        their coordinates and sizes (used when exporting).

        If renumber_by_position is True, each pad's number is replaced with its
        position number (keeping any prefix, e.g. 'SOC.1' -> 'SOC.<pos>') and
        the pads are returned sorted by that position."""
        moved = (self._die_rotation != 0 or self._die_offset != (0.0, 0.0))
        result = []
        for pad in self.chip_layout.pads:
            rx, ry, x_open, y_open = self.rotated_geometry(pad)
            clone = pad.clone()
            clone.x_coord, clone.y_coord = rx, ry
            clone.x_open, clone.y_open = x_open, y_open
            if pad.is_modified or moved:
                clone.mark_as_modified()

            pos = self._position_numbers.get(pad.pad_id)
            if renumber_by_position and pos is not None:
                prefix = pad.pad_id.split('.')[0]
                clone.pad_id = f"{prefix}.{pos}" if '.' in pad.pad_id else str(pos)
                clone.mark_as_modified()
            result.append((pos if pos is not None else 0, clone))

        if renumber_by_position:
            result.sort(key=lambda item: item[0])
        return [clone for _, clone in result]

    # --- coordinate helpers ---------------------------------------------

    @staticmethod
    def _to_scene(x: float, y: float) -> QPointF:
        """Die coordinates (Y up) -> scene coordinates (Y down)."""
        return QPointF(x, -y)

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize to (-180, 180], so a half turn reads as 180, not -180."""
        normalized = (angle + 180.0) % 360.0 - 180.0
        return 180.0 if normalized == -180.0 else normalized

    def _rotate_die_point(self, x: float, y: float):
        """Rotate a die-coordinate point around the die center by the current
        die rotation (no translation). Returns die coordinates."""
        cx, cy = self._die_center
        theta = math.radians(self._die_rotation)
        c, s = math.cos(theta), math.sin(theta)
        dx, dy = x - cx, y - cy
        return cx + dx * c - dy * s, cy + dx * s + dy * c

    def _transform_die_point(self, x: float, y: float):
        """Full die transform (rotation + translation) in die coordinates."""
        rx, ry = self._rotate_die_point(x, y)
        return rx + self._die_offset[0], ry + self._die_offset[1]

    def _pad_base_rect(self, pad_id: str) -> QRectF:
        """Pad rectangle in the die group's local coordinates (= unmoved
        scene coordinates)."""
        x1, y1, x2, y2 = self.chip_layout.get_pad_rectangle(pad_id)
        return QRectF(self._to_scene(x1, y2), self._to_scene(x2, y1)).normalized()

    def pad_scene_center(self, pad_id: str) -> QPointF:
        """Pad center in scene coordinates, honoring the die transform."""
        item = self.pad_items[pad_id]
        return item.mapToScene(item.rect().center())

    def _compute_position_numbers(self):
        """Number pads 1..N by their position around the die, using the same
        convention as the lead frame pins: left side top->down, bottom side
        left->right, right side bottom->up, top side right->left. Uses the
        pads' current rotation (translation does not matter)."""
        cx, cy = self._die_center
        bounds = self.chip_layout.get_bounds()
        half_w = max(bounds['width'] / 2, 1e-6)
        half_h = max(bounds['height'] / 2, 1e-6)
        if abs(self._die_rotation) % 180 > 45 and abs(self._die_rotation) % 180 < 135:
            half_w, half_h = half_h, half_w  # die is closer to portrait

        left, bottom, right, top = [], [], [], []
        for pad in self.chip_layout.pads:
            rx, ry = self._rotate_die_point(pad.x_coord, pad.y_coord)
            nx, ny = (rx - cx) / half_w, (ry - cy) / half_h  # die coords, Y up
            if abs(nx) >= abs(ny):
                (left if nx < 0 else right).append((rx, ry, pad.pad_id))
            else:
                (bottom if ny < 0 else top).append((rx, ry, pad.pad_id))

        left.sort(key=lambda p: -p[1])    # top -> down  (Y up: high y first)
        bottom.sort(key=lambda p: p[0])   # left -> right
        right.sort(key=lambda p: p[1])    # bottom -> up
        top.sort(key=lambda p: -p[0])     # right -> left

        numbers = {}
        for i, (_, _, pad_id) in enumerate(left + bottom + right + top, 1):
            numbers[pad_id] = i
        return numbers

    def _pad_label(self, pad: Pad) -> str:
        if self._display_mode == 'position':
            return str(self._position_numbers.get(pad.pad_id, '?'))
        if self._display_mode == 'bond':
            return bond_code(pad.bonding)
        return pad.pad_id.split('.')[-1]  # 'soc'

    # --- drawing ----------------------------------------------------------

    def _redraw(self):
        self._building = True
        self.clear()
        self.pad_items = {}
        self.wire_items = {}
        self._wire_targets = {}
        self.pin_points = {}
        self.ring_outer = None
        self.ring_centerline = None
        self.die_group = None
        self._highlighted_wire = None

        if not self.chip_layout.pads:
            self._building = False
            return

        bounds = self.chip_layout.get_bounds()
        self._die_center = (bounds['min_x'] + bounds['width'] / 2,
                            bounds['min_y'] + bounds['height'] / 2)
        self._position_numbers = self._compute_position_numbers()

        ring_side = self._ring_side()
        self._draw_vss_ring(ring_side)
        self._draw_lead_frame_pins(self._pin_reference_square(ring_side),
                                   self._compute_pin_count())
        self._build_die_group()
        self._apply_die_transform()
        self._counter_rotate_pad_labels()
        self._draw_bond_wires()

        item_bounds = self.itemsBoundingRect()
        margin = max(item_bounds.width(), item_bounds.height()) * 0.03
        self.setSceneRect(item_bounds.adjusted(-margin, -margin, margin, margin))
        self._building = False

    def _base_die_dims(self):
        """Die (width, height) in the unrotated orientation, at least large
        enough to contain the pads."""
        bounds = self.chip_layout.get_bounds()
        params = self._frame_params or {}
        die_w = params.get('die_width') or bounds['width'] * 1.02
        die_h = params.get('die_height') or bounds['height'] * 1.02
        die_w = max(die_w, bounds['width'])
        die_h = max(die_h, bounds['height'])
        return die_w, die_h

    def _ring_side(self) -> float:
        """Outer side length of the fixed VSS ring square: the user's value
        from the upload form, or a default with generous die-to-ring space."""
        params = self._frame_params or {}
        user_size = params.get('ring_size')
        if user_size and user_size > 0:
            return float(user_size)
        return max(self._base_die_dims()) * RING_DEFAULT_FACTOR

    def _pin_reference_square(self, ring_side: float) -> QRectF:
        """Fixed square the lead frame pins are placed around (just outside
        the ring, never smaller than the die)."""
        side = max(ring_side, max(self._base_die_dims()) * 1.18)
        center = self._to_scene(*self._die_center)
        return QRectF(center.x() - side / 2, center.y() - side / 2, side, side)

    def _compute_die_rect(self) -> QRectF:
        """Die outline in unmoved scene coordinates (the die group's local
        frame); the interactive transform moves/rotates it afterwards."""
        center = self._to_scene(*self._die_center)
        die_w, die_h = self._base_die_dims()
        return QRectF(center.x() - die_w / 2, center.y() - die_h / 2, die_w, die_h)

    def _compute_pin_count(self) -> int:
        params = self._frame_params or {}
        if params.get('pin_count'):
            return int(params['pin_count'])
        # Fall back to the highest LF.<n> in the data, rounded up to x4.
        max_pin = 0
        for pad in self.chip_layout.pads:
            kind, detail = classify_bonding(pad.bonding)
            if kind == 'lf':
                max_pin = max(max_pin, detail)
        return ((max_pin + 3) // 4) * 4 if max_pin else 0

    def _build_die_group(self):
        die_rect = self._compute_die_rect()
        group = DieGroupItem(self, die_rect)
        self.addItem(group)
        self.die_group = group

        label = QGraphicsTextItem("DIE", group)
        label.setFont(QFont("Arial", int(die_rect.width() * 0.05)))
        label.setDefaultTextColor(QColor(189, 195, 199))
        bounds = label.boundingRect()
        label.setPos(die_rect.center().x() - bounds.width() / 2,
                     die_rect.center().y() - bounds.height() / 2)

        handle_r = max(die_rect.width(), die_rect.height()) * 0.03
        DieRotationHandle(group, handle_r,
                          QPointF(die_rect.right() + handle_r * 2.5,
                                  die_rect.top() - handle_r * 2.5))

        for pad in self.chip_layout.pads:
            rect = self._pad_base_rect(pad.pad_id)
            if rect.isEmpty():
                continue
            pad_item = PadGraphicsItem(pad, rect, bonding_color(pad.bonding),
                                       self._pad_label(pad))
            pad_item.setParentItem(group)
            pad_item.text_item.setParentItem(group)
            self.pad_items[pad.pad_id] = pad_item

    def _draw_vss_ring(self, side: float):
        """The VSS ring: a fixed square band centered on the die's original
        position. It never moves or rotates with the die."""
        thickness = side * RING_THICKNESS_FACTOR
        center = self._to_scene(*self._die_center)
        outer = QRectF(center.x() - side / 2, center.y() - side / 2, side, side)
        inner = outer.adjusted(thickness, thickness, -thickness, -thickness)
        self.ring_outer = outer
        self.ring_centerline = outer.adjusted(thickness / 2, thickness / 2,
                                              -thickness / 2, -thickness / 2)

        path = QPainterPath()
        path.setFillRule(Qt.OddEvenFill)
        path.addRect(outer)
        path.addRect(inner)

        ring_item = QGraphicsPathItem(path)
        ring_item.setPen(QPen(QColor(31, 97, 141), side * 0.002))
        ring_item.setBrush(QBrush(QColor(41, 128, 185, 180)))
        ring_item.setZValue(-15)
        self.addItem(ring_item)

        label = QGraphicsTextItem("VSS ring (E-PAD ring)")
        label.setFont(QFont("Arial", int(thickness * 0.55), QFont.Bold))
        label.setDefaultTextColor(QColor(255, 255, 255))
        bounds = label.boundingRect()
        label.setPos(outer.center().x() - bounds.width() / 2,
                     outer.bottom() - thickness / 2 - bounds.height() / 2)
        label.setZValue(-14)
        self.addItem(label)

        self._draw_ring_axes(outer, side)

    def _draw_ring_axes(self, outer: QRectF, side: float):
        """Small coordinate axes at the ring's bottom-left corner: the origin
        of the ring coordinate system (X right, Y up)."""
        color = QColor(31, 97, 141)
        gap = side * 0.015
        length = side * 0.10
        head = side * 0.02
        pen = QPen(color, side * 0.004)
        pen.setCapStyle(Qt.RoundCap)

        ox = outer.left() - gap    # origin, nudged outside the band
        oy = outer.bottom() + gap

        segments = [
            (ox, oy, ox + length, oy),                                  # X axis
            (ox + length, oy, ox + length - head, oy - head * 0.6),     # X head
            (ox + length, oy, ox + length - head, oy + head * 0.6),
            (ox, oy, ox, oy - length),                                  # Y axis
            (ox, oy - length, ox - head * 0.6, oy - length + head),     # Y head
            (ox, oy - length, ox + head * 0.6, oy - length + head),
        ]
        for x1, y1, x2, y2 in segments:
            line = QGraphicsLineItem(x1, y1, x2, y2)
            line.setPen(pen)
            line.setZValue(-13)
            self.addItem(line)

        dot = QGraphicsEllipseItem(ox - side * 0.006, oy - side * 0.006,
                                   side * 0.012, side * 0.012)
        dot.setBrush(QBrush(color))
        dot.setPen(QPen(Qt.NoPen))
        dot.setZValue(-13)
        self.addItem(dot)

        font = QFont("Arial", max(1, int(side * 0.022)), QFont.Bold)
        for text, x, y in (("X", ox + length + gap, oy - side * 0.02),
                           ("Y", ox - side * 0.015, oy - length - side * 0.045),
                           ("Ring (0,0)", ox - side * 0.02, oy + head)):
            t = QGraphicsTextItem(text)
            t.setFont(font)
            t.setDefaultTextColor(color)
            t.setPos(x, y)
            t.setZValue(-13)
            self.addItem(t)

    def _draw_lead_frame_pins(self, ref_square: QRectF, pin_count: int):
        """Individual pins around the package, all drawn solid black and
        labeled 'LF.<n>'. Numbering: left side top->down, bottom side
        left->right, right side bottom->up, top side right->left.
        The reference square is fixed, so pins never move."""
        if pin_count < 4:
            return

        scale = ref_square.width()
        pin_gap = scale * 0.04
        pin_len = scale * 0.09
        corner_clear = scale * 0.04

        # Rectangle on which the pin inner tips sit.
        pkg = ref_square.adjusted(-pin_gap, -pin_gap, pin_gap, pin_gap)

        order = ['left', 'bottom', 'right', 'top']
        per_side = pin_count // 4
        remainder = pin_count % 4
        counts = {side: per_side + (1 if i < remainder else 0)
                  for i, side in enumerate(order)}

        pin_number = 1
        for side in order:
            count = counts[side]
            if count == 0:
                continue
            vertical = side in ('left', 'right')
            span = (pkg.height() if vertical else pkg.width()) - 2 * corner_clear
            pitch = span / count
            pin_w = min(pitch * 0.55, scale * 0.03)

            for i in range(count):
                step = (i + 0.5) * pitch
                if side == 'left':      # top -> down
                    pos = pkg.top() + corner_clear + step
                    rect = QRectF(pkg.left() - pin_len, pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.left(), pos)
                elif side == 'bottom':  # left -> right
                    pos = pkg.left() + corner_clear + step
                    rect = QRectF(pos - pin_w / 2, pkg.bottom(), pin_w, pin_len)
                    tip = QPointF(pos, pkg.bottom())
                elif side == 'right':   # bottom -> up
                    pos = pkg.bottom() - corner_clear - step
                    rect = QRectF(pkg.right(), pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.right(), pos)
                else:                   # top: right -> left
                    pos = pkg.right() - corner_clear - step
                    rect = QRectF(pos - pin_w / 2, pkg.top() - pin_len, pin_w, pin_len)
                    tip = QPointF(pos, pkg.top())

                pin_item = QGraphicsRectItem(rect)
                pin_item.setPen(QPen(QColor(0, 0, 0), scale * 0.0015))
                pin_item.setBrush(QBrush(COLOR_PIN))
                pin_item.setZValue(-10)
                pin_item.setToolTip(f"LF.{pin_number}")
                self.addItem(pin_item)

                self.pin_points[pin_number] = tip
                self._draw_pin_label(pin_number, rect, side, pin_w)
                pin_number += 1

    def _draw_pin_label(self, pin_number: int, pin_rect: QRectF, side: str, pin_w: float):
        label = QGraphicsTextItem(f"LF.{pin_number}")
        label.setFont(QFont("Arial", max(1, int(pin_w * 0.7)), QFont.Bold))
        label.setDefaultTextColor(QColor(20, 20, 20))
        bounds = label.boundingRect()
        pad_off = pin_w * 0.3

        if side == 'left':
            label.setPos(pin_rect.left() - bounds.width() - pad_off,
                         pin_rect.center().y() - bounds.height() / 2)
        elif side == 'right':
            label.setPos(pin_rect.right() + pad_off,
                         pin_rect.center().y() - bounds.height() / 2)
        else:
            # Top/bottom labels run perpendicular to the edge so long "LF.<n>"
            # labels don't overlap their neighbors.
            label.setTransformOriginPoint(bounds.width() / 2, bounds.height() / 2)
            label.setRotation(-90)
            px = pin_rect.center().x()
            if side == 'top':
                cy = pin_rect.top() - pad_off - bounds.width() / 2
            else:  # bottom
                cy = pin_rect.bottom() + pad_off + bounds.width() / 2
            label.setPos(px - bounds.width() / 2, cy - bounds.height() / 2)
        label.setZValue(-9)
        self.addItem(label)

    def _nearest_ring_point(self, point: QPointF) -> QPointF:
        """Nearest point on the VSS ring centerline for any point (inside or
        outside the ring)."""
        rect = self.ring_centerline
        x = min(max(point.x(), rect.left()), rect.right())
        y = min(max(point.y(), rect.top()), rect.bottom())
        if rect.left() < x < rect.right() and rect.top() < y < rect.bottom():
            # Inside the ring: project to the nearest edge.
            distances = [
                (x - rect.left(), (rect.left(), y)),
                (rect.right() - x, (rect.right(), y)),
                (y - rect.top(), (x, rect.top())),
                (rect.bottom() - y, (x, rect.bottom())),
            ]
            _, (x, y) = min(distances, key=lambda d: d[0])
        return QPointF(x, y)

    def _draw_bond_wires(self):
        for pad in self.chip_layout.pads:
            kind, detail = classify_bonding(pad.bonding)
            if pad.pad_id not in self.pad_items:
                continue

            source = self.pad_scene_center(pad.pad_id)
            if kind == 'lf' and detail in self.pin_points:
                target = self.pin_points[detail]
                color = COLOR_LF_WIRE   # uniform for all lead-frame wires
                self._wire_targets[pad.pad_id] = ('lf', detail)
            elif kind in ('vss_ring', 'epad') and self.ring_centerline is not None:
                target = self._nearest_ring_point(source)
                color = COLOR_RING_WIRE  # uniform for all ring wires
                self._wire_targets[pad.pad_id] = ('ring', None)
            else:
                continue  # Not Bond, die-to-die, or unresolvable target

            wire = QGraphicsLineItem(source.x(), source.y(), target.x(), target.y())
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 130), 1.2)
            pen.setCosmetic(True)  # constant width at any zoom level
            wire.setPen(pen)
            wire.setZValue(WIRE_Z)  # above the die so wires are never hidden
            wire.setAcceptedMouseButtons(Qt.NoButton)  # let clicks reach the pads
            wire.setVisible(self._wires_visible)
            self.addItem(wire)
            self.wire_items[pad.pad_id] = wire

    # --- die transform plumbing --------------------------------------------

    def _apply_die_transform(self):
        """Push the stored offset/rotation onto the die group item."""
        if self.die_group is None:
            return
        was_building = self._building
        self._building = True
        dx, dy = self._die_offset
        self.die_group.setPos(dx, -dy)
        self.die_group.setRotation(-self._die_rotation)
        self._building = was_building

    def _on_die_transform_changed(self):
        """Called live while the die is dragged or hand-rotated."""
        if self._building or self.die_group is None:
            return
        pos = self.die_group.pos()
        self._die_offset = (pos.x(), -pos.y())
        self._die_rotation = self._normalize_angle(-self.die_group.rotation())
        self._after_die_transform(refresh_labels=False)

    def _after_die_transform(self, refresh_labels: bool):
        self._counter_rotate_pad_labels()
        self._update_wires()
        if refresh_labels:
            self._refresh_position_numbers()
        cx, cy, rotation = self.die_transform()
        self.die_transform_changed.emit(cx, cy, rotation)

    def _on_die_interaction_end(self):
        """Called when a drag/hand-rotation finishes: do the heavier updates."""
        self._refresh_position_numbers()
        # Keep the moved die reachable when panning.
        self.setSceneRect(self.sceneRect().united(self.itemsBoundingRect()))

    def _counter_rotate_pad_labels(self):
        """Keep pad numbers upright while the die underneath them rotates."""
        for item in self.pad_items.values():
            item.text_item.setRotation(self._die_rotation)

    def _update_wires(self):
        for pad_id, wire in self.wire_items.items():
            item = self.pad_items.get(pad_id)
            target_info = self._wire_targets.get(pad_id)
            if item is None or target_info is None:
                continue
            source = item.mapToScene(item.rect().center())
            kind, detail = target_info
            if kind == 'lf':
                target = self.pin_points.get(detail)
            else:
                target = self._nearest_ring_point(source)
            if target is None:
                continue
            wire.setLine(source.x(), source.y(), target.x(), target.y())

    def _refresh_position_numbers(self):
        self._position_numbers = self._compute_position_numbers()
        if self._display_mode == 'position':
            for pad in self.chip_layout.pads:
                item = self.pad_items.get(pad.pad_id)
                if item is not None:
                    item.update_label(self._pad_label(pad))
            self._counter_rotate_pad_labels()

    # --- interaction ------------------------------------------------------

    def _on_pad_clicked(self, pad: Pad):
        self._highlight_wire(pad.pad_id)

    def _highlight_wire(self, pad_id: str):
        if self._highlighted_wire is not None:
            pen = self._highlighted_wire.pen()
            color = pen.color()
            color.setAlpha(130)
            pen.setColor(color)
            pen.setWidthF(1.2)
            self._highlighted_wire.setPen(pen)
            self._highlighted_wire.setZValue(WIRE_Z)
            self._highlighted_wire = None

        wire = self.wire_items.get(pad_id)
        if wire is not None:
            pen = wire.pen()
            color = pen.color()
            color.setAlpha(255)
            pen.setColor(color)
            pen.setWidthF(3.0)
            wire.setPen(pen)
            wire.setZValue(WIRE_Z + 1)  # highlighted wire above the others
            wire.setVisible(True)  # show even when wires are toggled off
            self._highlighted_wire = wire


class ChipVisualizationView(QGraphicsView):
    MIN_SCALE = 0.02
    MAX_SCALE = 200.0

    def __init__(self, scene: ChipScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setAlignment(Qt.AlignCenter)
        # Zoom keeps the point under the cursor fixed.
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # Keep the diagram fitted & centered until the user zooms manually.
        self._auto_fit = True

    def viewportEvent(self, event):
        # macOS trackpad pinch arrives as a native "zoom" gesture, not a wheel
        # event; value() is the incremental scale change (e.g. 0.02 = +2%).
        if event.type() == QEvent.NativeGesture and isinstance(event, QNativeGestureEvent):
            if event.gestureType() == Qt.ZoomNativeGesture:
                self._auto_fit = False
                self._zoom(1.0 + event.value())
                return True
        return super().viewportEvent(event)

    def wheelEvent(self, event):
        # A physical mouse wheel (angleDelta only) zooms; a trackpad two-finger
        # scroll (reports pixelDelta) pans through the default handler.
        if event.pixelDelta().isNull():
            self._auto_fit = False
            self._zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-center/fit when the window is resized (e.g. maximized after load),
        # until the user takes over with a manual zoom.
        if self._auto_fit:
            self.fit_in_view()

    def _zoom(self, factor):
        if factor <= 0:
            return
        current = self.transform().m11()
        new_scale = current * factor
        if new_scale < self.MIN_SCALE:
            factor = self.MIN_SCALE / current
        elif new_scale > self.MAX_SCALE:
            factor = self.MAX_SCALE / current
        self.scale(factor, factor)

    def fit_in_view(self):
        self._auto_fit = True
        if self.scene():
            rect = self.scene().sceneRect()
            if not rect.isNull():
                self.fitInView(rect, Qt.KeepAspectRatio)
