"""Graphics scene/view for the chip bonding diagram.

A chip has one or more dies sharing a single VSS ring:
  1. Each die is a movable/rotatable unit (its pads move with it). Click a die
     to select it, then drag its body to move it or drag the round handle to
     rotate it (or use the numeric "Die placement" controls). Dies start
     arranged side by side, centered in the ring.
  2. The VSS ring (E-PAD ring): a fixed square band that does not move with the
     dies. Its coordinate system has its origin at the ring's bottom-left
     corner (X right, Y up) and is drawn as small axes; it is the shared frame.
  3. The lead frame pins around the outside (LF.1..LF.n), fixed like the ring.
  4. Bond wires: pad -> LF pin (gray), pad -> VSS ring (blue), and die-to-die
     pad -> pad on another die (purple). They re-route live as dies move.

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

from models import Die, Pad

_LF_PATTERN = re.compile(r'^LF[._\s]*(\d+)$', re.IGNORECASE)
_DIE_PREFIXES = ('SOC.', 'PSRAM.', 'DDRA.', 'DDRB.', 'ROM.')

# Pad/pin fill colors
COLOR_NOT_BOND = QColor(33, 33, 33, 220)        # black
COLOR_VSS = QColor(41, 128, 185, 220)           # dark blue
COLOR_DIE_TO_DIE = QColor(80, 80, 80, 220)      # dark gray
COLOR_UNDEFINED = QColor(192, 57, 43, 220)      # dark red
COLOR_PIN = QColor(20, 20, 20, 255)             # solid black (all lead frame pins)

# Bond wires: one uniform color per target type.
COLOR_LF_WIRE = QColor(127, 140, 141)           # to a lead frame pin
COLOR_RING_WIRE = QColor(41, 128, 185)          # to the VSS ring
COLOR_DIE_WIRE = QColor(142, 68, 173)           # die-to-die (pad -> pad)

# Ring geometry.
RING_THICKNESS_FACTOR = 0.04
RING_DEFAULT_FACTOR = 1.8   # ring size relative to the arranged dies' extent

# Bond wires draw above everything else so they are never hidden by a die.
WIRE_Z = 50

# Light palette for lead-frame pads (cycled by pin number). Excludes blue so
# these light colors never clash with the dark blue VSS ring.
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
    For 'lf', detail is the pin number (int). For 'die', detail is the target
    pad id string (e.g. 'ROM.5')."""
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
        return 'die', value

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
    """A pad rectangle with its number centered inside. Lives as a child of a
    die group, so it moves and rotates with its die."""

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
        rect = self.rect()
        min_dim = min(rect.width(), rect.height())
        divisor = {1: 1.8, 2: 2.5}.get(len(label), 3.5)
        font_size = max(6.0, min_dim / divisor)

        text_item = self.text_item
        text_item.setPlainText(label)
        text_item.setFont(QFont("Arial", int(font_size), QFont.Bold))

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
    """Round handle outside a die's top-right corner; drag it to rotate that
    die around its center by any angle."""

    def __init__(self, die_item, radius: float, pos: QPointF):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, die_item)
        self.setPos(pos)
        self.setBrush(QBrush(QColor(52, 152, 219)))
        self.setPen(QPen(QColor(255, 255, 255), radius * 0.3))
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag to rotate this die")
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
    """A die outline; its pads, labels, name label and rotation handle are its
    children, so the whole die moves/rotates as one unit. Drag the body to move
    it; click it to select it."""

    def __init__(self, chip_scene, index: int, rect: QRectF):
        super().__init__(rect)
        self._chip_scene = chip_scene
        self.die_index = index
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.SizeAllCursor)
        self.setTransformOriginPoint(rect.center())
        self.setBrush(QBrush(QColor(236, 240, 241)))
        self.setZValue(6)
        self.set_selected(False)

    def set_selected(self, selected: bool):
        scale = max(self.rect().width(), self.rect().height())
        if selected:
            self.setPen(QPen(QColor(243, 156, 18), scale * 0.008))  # orange
        else:
            self.setPen(QPen(QColor(127, 140, 141), scale * 0.003))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            self.notify_transform()
        return super().itemChange(change, value)

    def notify_transform(self):
        self._chip_scene._on_die_moved(self.die_index)

    def notify_interaction_end(self):
        self._chip_scene._on_die_interaction_end()

    def mousePressEvent(self, event):
        self._chip_scene.select_die(self.die_index)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.notify_interaction_end()


class ChipScene(QGraphicsScene):
    pad_clicked = pyqtSignal(object)
    # (die index, center_x, center_y, rotation) in RING coordinates.
    die_transform_changed = pyqtSignal(int, float, float, float)
    die_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dies = []               # list[Die]
        self._states = []            # per-die: dict(arranged, local_center, offset, rotation, group, handle)
        self.pad_items = {}          # pad_id -> PadGraphicsItem
        self.pad_die = {}            # pad_id -> die index
        self.wire_items = {}         # source pad_id -> QGraphicsLineItem
        self._wire_targets = {}      # source pad_id -> ('lf', n) | ('ring', None) | ('die', target_id)
        self._wire_by_pad = {}       # any pad_id -> its wire (for highlight)
        self.pin_points = {}         # pin number -> QPointF (scene)
        self.ring_outer = None       # QRectF (scene, fixed)
        self.ring_centerline = None  # QRectF (scene, fixed)
        self._frame_params = None
        self._wires_visible = True
        self._highlighted_wire = None
        self._display_mode = 'soc'
        self._position_numbers = {}
        self._selected_die = None
        self._building = False
        self._preserved_transforms = None  # set by refresh() to survive a redraw
        self._preserved_selected = None
        self._pad_names_visible = False
        self.pad_name_items = {}     # pad_id -> QGraphicsTextItem (name beside pad)
        self._die_priority = None    # list of die names, highest priority first
        self.pad_clicked.connect(self._on_pad_clicked)

    # --- public API ---------------------------------------------------

    def set_dies(self, dies, frame_params=None):
        self.dies = list(dies)
        self._frame_params = frame_params
        self._redraw()

    def refresh(self):
        """Redraw (e.g. after a pad edit) while keeping each die's current
        position/rotation and the current selection."""
        self._preserved_transforms = {
            self.dies[i].name: (st['offset'], st['rotation'])
            for i, st in enumerate(self._states)
        }
        self._preserved_selected = self._selected_die
        self._redraw()

    def die_names(self):
        return [d.name for d in self.dies]

    def selected_die(self):
        return self._selected_die

    def select_die(self, index: int):
        if index is None or not (0 <= index < len(self.dies)):
            return
        if index != self._selected_die:
            self._selected_die = index
            self._apply_selection_style()
            self.die_selected.emit(index)

    def set_display_mode(self, mode: str):
        if mode != self._display_mode:
            self._display_mode = mode
            self._redraw()

    def rotate_die(self, index, degrees):
        cx, cy, rotation = self.die_transform(index)
        self.set_die_transform(index, cx, cy, rotation + degrees)

    def set_die_transform(self, index, ring_x, ring_y, rotation_deg):
        """Place die `index`: its center goes to (ring_x, ring_y) in ring
        coordinates, rotated rotation_deg degrees CCW."""
        if not (0 <= index < len(self._states)):
            return
        st = self._states[index]
        target = self._ring_to_scene(ring_x, ring_y)
        st['offset'] = (target.x() - st['arranged'].x(),
                        target.y() - st['arranged'].y())
        st['rotation'] = self._normalize_angle(rotation_deg)
        self._apply_die_transform(index)
        self._after_die_transform(index, heavy=True)

    def die_transform(self, index):
        """(center_x, center_y, rotation) of die `index` in ring coordinates."""
        st = self._states[index]
        center = QPointF(st['arranged'].x() + st['offset'][0],
                         st['arranged'].y() + st['offset'][1])
        rx, ry = self._scene_to_ring(center)
        return rx, ry, st['rotation']

    def reset_die_transform(self, index):
        st = self._states[index]
        st['offset'] = (0.0, 0.0)
        st['rotation'] = 0.0
        self._apply_die_transform(index)
        self._after_die_transform(index, heavy=True)

    def set_wires_visible(self, visible: bool):
        self._wires_visible = visible
        for item in self.wire_items.values():
            item.setVisible(visible)

    def set_pad_names_visible(self, visible: bool):
        self._pad_names_visible = visible
        for item in self.pad_name_items.values():
            item.setVisible(visible)

    def set_die_priority(self, order):
        """Set die stacking priority. `order` is a list of die names, highest
        priority first; higher-priority dies are drawn on top of overlaps."""
        self._die_priority = list(order)
        self._apply_die_priority()

    def die_priority(self):
        """Current priority order (die names, highest first)."""
        if self._die_priority:
            names = self.die_names()
            return [n for n in self._die_priority if n in names]
        return self.die_names()

    def _apply_die_priority(self):
        order = self.die_priority()
        n = len(order)
        name_to_idx = {d.name: i for i, d in enumerate(self.dies)}
        for rank, name in enumerate(order):
            idx = name_to_idx.get(name)
            if idx is None:
                continue
            group = self._states[idx]['group']
            if group is not None:
                group.setZValue(6 + (n - 1 - rank))  # first = highest z

    def reset_view(self):
        self._display_mode = 'soc'
        self._wires_visible = True
        self._pad_names_visible = False
        self._selected_die = None
        self._die_priority = None

    # --- ring coordinate helpers -----------------------------------------

    @staticmethod
    def _to_scene(x, y):
        return QPointF(x, -y)

    @staticmethod
    def _normalize_angle(angle):
        normalized = (angle + 180.0) % 360.0 - 180.0
        return 180.0 if normalized == -180.0 else normalized

    def _ring_to_scene(self, rx, ry):
        return QPointF(self.ring_outer.left() + rx, self.ring_outer.bottom() - ry)

    def _scene_to_ring(self, p):
        return p.x() - self.ring_outer.left(), self.ring_outer.bottom() - p.y()

    def pad_scene_center(self, pad_id):
        item = self.pad_items[pad_id]
        return item.mapToScene(item.rect().center())

    def ring_coords(self, pad):
        if self.ring_outer is None or pad.pad_id not in self.pad_items:
            return None
        return self._scene_to_ring(self.pad_scene_center(pad.pad_id))

    def die_index_of(self, pad):
        return self.pad_die.get(pad.pad_id)

    def die_name_of(self, pad):
        idx = self.pad_die.get(pad.pad_id)
        return self.dies[idx].name if idx is not None else ""

    def rotated_geometry(self, pad):
        """Pad center in ring coordinates and its opening size after the die's
        rotation (axis-aligned bounding box for non-90° angles)."""
        idx = self.pad_die.get(pad.pad_id)
        if idx is None:
            return pad.x_coord, pad.y_coord, pad.x_open, pad.y_open
        rx, ry = self._scene_to_ring(self.pad_scene_center(pad.pad_id))
        theta = math.radians(self._states[idx]['rotation'])
        c, s = abs(math.cos(theta)), abs(math.sin(theta))
        x_open = pad.x_open * c + pad.y_open * s
        y_open = pad.x_open * s + pad.y_open * c
        return rx, ry, x_open, y_open

    def pads_for_export(self, renumber_by_position=False):
        """Clones of every pad (all dies) with ring coordinates and rotated
        openings baked in. Optionally renumbered by position."""
        result = []
        for idx, die in enumerate(self.dies):
            st = self._states[idx]
            moved = st['rotation'] != 0 or st['offset'] != (0.0, 0.0)
            for pad in die.pads:
                rx, ry, xo, yo = self.rotated_geometry(pad)
                clone = pad.clone()
                clone.x_coord, clone.y_coord = rx, ry
                clone.x_open, clone.y_open = xo, yo
                if pad.is_modified or moved:
                    clone.mark_as_modified()
                pos = self._position_numbers.get(pad.pad_id)
                if renumber_by_position and pos is not None:
                    prefix = pad.pad_id.split('.')[0]
                    clone.pad_id = f"{prefix}.{pos}" if '.' in pad.pad_id else str(pos)
                    clone.mark_as_modified()
                result.append((die.name, clone))
        return result

    # --- drawing ----------------------------------------------------------

    def _redraw(self):
        self._building = True
        self.clear()
        self.pad_items = {}
        self.pad_die = {}
        self.pad_name_items = {}
        self.wire_items = {}
        self._wire_targets = {}
        self._wire_by_pad = {}
        self.pin_points = {}
        self.ring_outer = None
        self.ring_centerline = None
        self._states = []
        self._highlighted_wire = None

        if not self.dies:
            self._building = False
            return

        self._arrange_dies()
        self._restore_preserved_transforms()
        ring_w, ring_h = self._ring_size()
        self._draw_vss_ring(ring_w, ring_h)
        pin_x, pin_y = self._compute_pin_counts()
        self._draw_lead_frame_pins(self._pin_reference_rect(ring_w, ring_h),
                                   pin_x, pin_y)
        self._position_numbers = self._compute_position_numbers()

        for idx in range(len(self.dies)):
            self._build_die_group(idx)
            self._apply_die_transform(idx)
        self._counter_rotate_labels()
        self._draw_bond_wires()
        self._apply_die_priority()

        if self._selected_die is None or self._selected_die >= len(self.dies):
            self._selected_die = 0
        self._apply_selection_style()

        item_bounds = self.itemsBoundingRect()
        margin = max(item_bounds.width(), item_bounds.height()) * 0.03
        self.setSceneRect(item_bounds.adjusted(-margin, -margin, margin, margin))
        self._building = False

    def _arrange_dies(self):
        """Lay the dies out side by side, centered at scene (0,0)."""
        widths = [d.width for d in self.dies]
        heights = [d.height for d in self.dies]
        gap = max(widths) * 0.15
        total_w = sum(widths) + gap * (len(self.dies) - 1)
        self._arranged_w = total_w
        self._arranged_h = max(heights)
        self._arranged_extent = max(total_w, max(heights))

        x = -total_w / 2
        for die, w in zip(self.dies, widths):
            cx = x + w / 2
            self._states.append({
                'arranged': QPointF(cx, 0.0),   # scene, vertically centered
                'local_center': die.center(),   # die-local
                'offset': (0.0, 0.0),
                'rotation': 0.0,
                'group': None,
                'handle': None,
            })
            x += w + gap

    def _restore_preserved_transforms(self):
        """Re-apply die placements saved by refresh() (by die name), so a
        redraw after editing a pad does not reset the dies."""
        preserved = getattr(self, '_preserved_transforms', None)
        if not preserved:
            return
        for i, die in enumerate(self.dies):
            if die.name in preserved:
                offset, rotation = preserved[die.name]
                self._states[i]['offset'] = offset
                self._states[i]['rotation'] = rotation
        selected = getattr(self, '_preserved_selected', None)
        if selected is not None and 0 <= selected < len(self.dies):
            self._selected_die = selected
        self._preserved_transforms = None
        self._preserved_selected = None

    def _ring_size(self):
        """Outer (width, height) of the VSS ring. User values (rectangle) are
        honored but never smaller than the arranged dies; otherwise a square
        default large enough to move the dies around."""
        params = self._frame_params or {}
        default = self._arranged_extent * RING_DEFAULT_FACTOR
        w = params.get('ring_w')
        h = params.get('ring_h')
        if w and w > 0 and h and h > 0:
            return (max(float(w), self._arranged_w * 1.1),
                    max(float(h), self._arranged_h * 1.1))
        return default, default

    def _pin_reference_rect(self, ring_w, ring_h):
        w, h = ring_w * 1.12, ring_h * 1.12
        return QRectF(-w / 2, -h / 2, w, h)

    def _compute_pin_counts(self):
        """(pins per horizontal edge, pins per vertical edge). User values are
        honored; otherwise a square split of the auto-detected total."""
        params = self._frame_params or {}
        pin_x = params.get('pin_x')
        pin_y = params.get('pin_y')
        if pin_x and pin_y:
            return int(pin_x), int(pin_y)
        max_pin = 0
        for pad in (p for d in self.dies for p in d.pads):
            kind, detail = classify_bonding(pad.bonding)
            if kind == 'lf':
                max_pin = max(max_pin, detail)
        total = ((max_pin + 3) // 4) * 4 if max_pin else 0
        per_edge = round(total / 4)
        return per_edge, per_edge

    def _die_base_scene(self, idx, x, y):
        """Die-local point -> base (unmoved) scene point for die idx."""
        st = self._states[idx]
        dcx, dcy = st['local_center']
        arranged = st['arranged']
        return QPointF(arranged.x() + (x - dcx), arranged.y() - (y - dcy))

    def _pad_base_rect(self, idx, pad_id):
        x1, y1, x2, y2 = self.dies[idx].get_pad_rectangle(pad_id)
        return QRectF(self._die_base_scene(idx, x1, y2),
                      self._die_base_scene(idx, x2, y1)).normalized()

    def _build_die_group(self, idx):
        die = self.dies[idx]
        st = self._states[idx]
        arranged = st['arranged']
        rect = QRectF(arranged.x() - die.width / 2, arranged.y() - die.height / 2,
                      die.width, die.height)
        group = DieGroupItem(self, idx, rect)
        self.addItem(group)
        st['group'] = group

        label = QGraphicsTextItem(die.name, group)
        label.setFont(QFont("Arial", max(1, int(min(die.width, die.height) * 0.12))))
        label.setDefaultTextColor(QColor(170, 178, 185))
        b = label.boundingRect()
        label.setPos(arranged.x() - b.width() / 2, arranged.y() - b.height() / 2)
        # Keep the name upright when the die rotates (counter-rotate about its center).
        label.setTransformOriginPoint(b.center())
        st['name_label'] = label

        handle_r = max(die.width, die.height) * 0.04
        st['handle'] = DieRotationHandle(
            group, handle_r,
            QPointF(rect.right() + handle_r * 2.0, rect.top() - handle_r * 2.0))

        for pad in die.pads:
            prect = self._pad_base_rect(idx, pad.pad_id)
            if prect.isEmpty():
                continue
            item = PadGraphicsItem(pad, prect, bonding_color(pad.bonding),
                                   self._pad_label(pad))
            item.setParentItem(group)
            item.text_item.setParentItem(group)
            self.pad_items[pad.pad_id] = item
            self.pad_die[pad.pad_id] = idx
            self._make_pad_name_label(idx, pad, prect, group)

    def _make_pad_name_label(self, idx, pad, prect, group):
        """A small, light pad-name label placed just outside the pad, oriented
        radially (perpendicular to the die edge the pad sits on)."""
        name = (pad.pad_name or "").strip()
        if not name:
            return
        arranged = self._states[idx]['arranged']
        c = prect.center()
        dx, dy = c.x() - arranged.x(), c.y() - arranged.y()
        horizontal = abs(dx) >= abs(dy)

        label = QGraphicsTextItem(name, group)
        font_size = max(1, int(min(prect.width(), prect.height()) * 0.5))
        label.setFont(QFont("Arial", font_size))
        label.setDefaultTextColor(QColor(120, 128, 135, 200))  # small & light
        b = label.boundingRect()
        gap = min(prect.width(), prect.height()) * 0.3

        if horizontal:
            if dx < 0:   # left edge: text to the left of the pad
                label.setPos(prect.left() - gap - b.width(), c.y() - b.height() / 2)
            else:        # right edge
                label.setPos(prect.right() + gap, c.y() - b.height() / 2)
        else:
            # top/bottom edges: rotate so the name runs outward
            label.setTransformOriginPoint(b.width() / 2, b.height() / 2)
            label.setRotation(-90)
            if dy < 0:   # top edge (smaller scene y): above the pad
                cy = prect.top() - gap - b.width() / 2
            else:        # bottom edge
                cy = prect.bottom() + gap + b.width() / 2
            label.setPos(c.x() - b.width() / 2, cy - b.height() / 2)

        label.setZValue(20)
        label.setVisible(self._pad_names_visible)
        self.pad_name_items[pad.pad_id] = label

    def _draw_vss_ring(self, width, height):
        side = min(width, height)   # thickness/labels scale with the smaller side
        thickness = side * RING_THICKNESS_FACTOR
        outer = QRectF(-width / 2, -height / 2, width, height)
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
        b = label.boundingRect()
        label.setPos(outer.center().x() - b.width() / 2,
                     outer.bottom() - thickness / 2 - b.height() / 2)
        label.setZValue(-14)
        self.addItem(label)

        self._draw_ring_axes(outer, side)

    def _draw_ring_axes(self, outer, side):
        color = QColor(31, 97, 141)
        gap = side * 0.015
        length = side * 0.10
        head = side * 0.02
        pen = QPen(color, side * 0.004)
        pen.setCapStyle(Qt.RoundCap)
        ox = outer.left() - gap
        oy = outer.bottom() + gap
        segments = [
            (ox, oy, ox + length, oy),
            (ox + length, oy, ox + length - head, oy - head * 0.6),
            (ox + length, oy, ox + length - head, oy + head * 0.6),
            (ox, oy, ox, oy - length),
            (ox, oy - length, ox - head * 0.6, oy - length + head),
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

    def _draw_lead_frame_pins(self, ref_rect, pin_x, pin_y):
        """pin_x = pins on each of the top/bottom edges, pin_y = pins on each
        of the left/right edges (the package may be rectangular)."""
        if pin_x < 1 and pin_y < 1:
            return
        scale = min(ref_rect.width(), ref_rect.height())
        pin_gap = scale * 0.04
        pin_len = scale * 0.09
        corner_clear = scale * 0.04
        pkg = ref_rect.adjusted(-pin_gap, -pin_gap, pin_gap, pin_gap)

        order = ['left', 'bottom', 'right', 'top']
        counts = {'left': pin_y, 'right': pin_y, 'top': pin_x, 'bottom': pin_x}

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
                if side == 'left':
                    pos = pkg.top() + corner_clear + step
                    rect = QRectF(pkg.left() - pin_len, pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.left(), pos)
                elif side == 'bottom':
                    pos = pkg.left() + corner_clear + step
                    rect = QRectF(pos - pin_w / 2, pkg.bottom(), pin_w, pin_len)
                    tip = QPointF(pos, pkg.bottom())
                elif side == 'right':
                    pos = pkg.bottom() - corner_clear - step
                    rect = QRectF(pkg.right(), pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.right(), pos)
                else:
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

    def _draw_pin_label(self, pin_number, pin_rect, side, pin_w):
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
            label.setTransformOriginPoint(bounds.width() / 2, bounds.height() / 2)
            label.setRotation(-90)
            px = pin_rect.center().x()
            if side == 'top':
                cy = pin_rect.top() - pad_off - bounds.width() / 2
            else:
                cy = pin_rect.bottom() + pad_off + bounds.width() / 2
            label.setPos(px - bounds.width() / 2, cy - bounds.height() / 2)
        label.setZValue(-9)
        self.addItem(label)

    def _nearest_ring_point(self, point):
        rect = self.ring_centerline
        x = min(max(point.x(), rect.left()), rect.right())
        y = min(max(point.y(), rect.top()), rect.bottom())
        if rect.left() < x < rect.right() and rect.top() < y < rect.bottom():
            distances = [
                (x - rect.left(), (rect.left(), y)),
                (rect.right() - x, (rect.right(), y)),
                (y - rect.top(), (x, rect.top())),
                (rect.bottom() - y, (x, rect.bottom())),
            ]
            _, (x, y) = min(distances, key=lambda d: d[0])
        return QPointF(x, y)

    def _draw_bond_wires(self):
        drawn_pairs = set()
        for pad in (p for d in self.dies for p in d.pads):
            if pad.pad_id not in self.pad_items:
                continue
            kind, detail = classify_bonding(pad.bonding)
            sid = pad.pad_id
            source = self.pad_scene_center(sid)

            if kind == 'lf' and detail in self.pin_points:
                target = self.pin_points[detail]
                color, info = COLOR_LF_WIRE, ('lf', detail)
                extra = None
            elif kind in ('vss_ring', 'epad') and self.ring_centerline is not None:
                target = self._nearest_ring_point(source)
                color, info = COLOR_RING_WIRE, ('ring', None)
                extra = None
            elif kind == 'die' and detail in self.pad_items and detail != sid:
                pair = frozenset({sid, detail})
                if pair in drawn_pairs:
                    continue
                drawn_pairs.add(pair)
                target = self.pad_scene_center(detail)
                color, info = COLOR_DIE_WIRE, ('die', detail)
                extra = detail
            else:
                continue

            wire = QGraphicsLineItem(source.x(), source.y(), target.x(), target.y())
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 150), 1.4)
            pen.setCosmetic(True)
            wire.setPen(pen)
            wire.setZValue(WIRE_Z)
            wire.setAcceptedMouseButtons(Qt.NoButton)
            wire.setVisible(self._wires_visible)
            self.addItem(wire)
            self.wire_items[sid] = wire
            self._wire_targets[sid] = info
            self._wire_by_pad[sid] = wire
            if extra is not None:
                self._wire_by_pad[extra] = wire

    # --- die transform plumbing --------------------------------------------

    def _apply_die_transform(self, idx):
        st = self._states[idx]
        group = st['group']
        if group is None:
            return
        was = self._building
        self._building = True
        dx, dy = st['offset']
        group.setPos(dx, dy)
        group.setRotation(-st['rotation'])
        self._building = was

    def _on_die_moved(self, idx):
        if self._building:
            return
        st = self._states[idx]
        group = st['group']
        st['offset'] = (group.pos().x(), group.pos().y())
        st['rotation'] = self._normalize_angle(-group.rotation())
        self.select_die(idx)
        self._after_die_transform(idx, heavy=False)

    def _after_die_transform(self, idx, heavy):
        self._counter_rotate_labels(idx)
        self._update_wires()
        if heavy:
            self._refresh_position_numbers()
        rx, ry, rot = self.die_transform(idx)
        self.die_transform_changed.emit(idx, rx, ry, rot)

    def _on_die_interaction_end(self):
        self._refresh_position_numbers()
        self.setSceneRect(self.sceneRect().united(self.itemsBoundingRect()))

    def _counter_rotate_labels(self, idx=None):
        indices = [idx] if idx is not None else range(len(self.dies))
        for i in indices:
            rot = self._states[i]['rotation']
            name_label = self._states[i].get('name_label')
            if name_label is not None:
                name_label.setRotation(rot)  # keep the die name upright
            for pad in self.dies[i].pads:
                item = self.pad_items.get(pad.pad_id)
                if item is not None:
                    item.text_item.setRotation(rot)

    def _update_wires(self):
        for sid, wire in self.wire_items.items():
            info = self._wire_targets.get(sid)
            if sid not in self.pad_items or info is None:
                continue
            source = self.pad_scene_center(sid)
            kind, detail = info
            if kind == 'lf':
                target = self.pin_points.get(detail)
            elif kind == 'die':
                target = self.pad_scene_center(detail) if detail in self.pad_items else None
            else:
                target = self._nearest_ring_point(source)
            if target is None:
                continue
            wire.setLine(source.x(), source.y(), target.x(), target.y())

    def _apply_selection_style(self):
        for i, st in enumerate(self._states):
            selected = (i == self._selected_die)
            if st['group'] is not None:
                st['group'].set_selected(selected)
            if st['handle'] is not None:
                st['handle'].setVisible(selected)

    # --- position numbering ------------------------------------------------

    def _compute_position_numbers(self):
        """Number each die's pads 1..k around that die's perimeter (using the
        die's current rotation), independently per die."""
        numbers = {}
        for idx, die in enumerate(self.dies):
            numbers.update(self._die_position_numbers(idx, die))
        return numbers

    def _die_position_numbers(self, idx, die):
        cx, cy = self._states[idx]['local_center']
        bounds = die.get_bounds()
        half_w = max(bounds['width'] / 2, 1e-6)
        half_h = max(bounds['height'] / 2, 1e-6)
        rot = self._states[idx]['rotation']
        if 45 < abs(rot) % 180 < 135:
            half_w, half_h = half_h, half_w

        left, bottom, right, top = [], [], [], []
        theta = math.radians(rot)
        c, s = math.cos(theta), math.sin(theta)
        for pad in die.pads:
            dx, dy = pad.x_coord - cx, pad.y_coord - cy
            rx, ry = dx * c - dy * s, dx * s + dy * c   # rotate about die center
            nx, ny = rx / half_w, ry / half_h
            if abs(nx) >= abs(ny):
                (left if nx < 0 else right).append((rx, ry, pad.pad_id))
            else:
                (bottom if ny < 0 else top).append((rx, ry, pad.pad_id))
        left.sort(key=lambda p: -p[1])
        bottom.sort(key=lambda p: p[0])
        right.sort(key=lambda p: p[1])
        top.sort(key=lambda p: -p[0])
        numbers = {}
        for i, (_, _, pad_id) in enumerate(left + bottom + right + top, 1):
            numbers[pad_id] = i
        return numbers

    def _refresh_position_numbers(self):
        self._position_numbers = self._compute_position_numbers()
        if self._display_mode == 'position':
            for pad in (p for d in self.dies for p in d.pads):
                item = self.pad_items.get(pad.pad_id)
                if item is not None:
                    item.update_label(self._pad_label(pad))
            self._counter_rotate_labels()

    def _pad_label(self, pad):
        if self._display_mode == 'position':
            return str(self._position_numbers.get(pad.pad_id, '?'))
        if self._display_mode == 'bond':
            return bond_code(pad.bonding)
        return pad.pad_id.split('.')[-1]

    # --- interaction ------------------------------------------------------

    def _on_pad_clicked(self, pad):
        idx = self.pad_die.get(pad.pad_id)
        if idx is not None:
            self.select_die(idx)
        self._highlight_wire(pad.pad_id)

    def _highlight_wire(self, pad_id):
        if self._highlighted_wire is not None:
            pen = self._highlighted_wire.pen()
            color = pen.color()
            color.setAlpha(150)
            pen.setColor(color)
            pen.setWidthF(1.4)
            self._highlighted_wire.setPen(pen)
            self._highlighted_wire.setZValue(WIRE_Z)
            self._highlighted_wire = None

        wire = self._wire_by_pad.get(pad_id)
        if wire is not None:
            pen = wire.pen()
            color = pen.color()
            color.setAlpha(255)
            pen.setColor(color)
            pen.setWidthF(3.0)
            wire.setPen(pen)
            wire.setZValue(WIRE_Z + 1)
            wire.setVisible(True)
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
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._auto_fit = True

    def viewportEvent(self, event):
        if event.type() == QEvent.NativeGesture and isinstance(event, QNativeGestureEvent):
            if event.gestureType() == Qt.ZoomNativeGesture:
                self._auto_fit = False
                self._zoom(1.0 + event.value())
                return True
        return super().viewportEvent(event)

    def wheelEvent(self, event):
        if event.pixelDelta().isNull():
            self._auto_fit = False
            self._zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
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
