"""Graphics scene/view for the chip bonding diagram.

Draws, from the inside out:
  1. The die with its pads (colored by bonding target).
  2. The VSS ring (E-PAD ring) surrounding the die.
  3. The individual lead frame pins around the outside (LF.1 ... LF.n,
     numbered counterclockwise starting at the bottom-left corner, the
     convention used by the bonding data).
  4. Optional bond wires from each pad to its LF pin or to the VSS ring.

Coordinates in the Excel file are die coordinates in micrometres with the
origin at the bottom-left and Y increasing upward. Qt's Y axis points down,
so every die coordinate is flipped (scene_y = -die_y) when drawn.
"""

import re

from PyQt5.QtCore import QEvent, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (QBrush, QColor, QFont, QNativeGestureEvent, QPainter,
                         QPainterPath, QPen)
from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsPathItem,
                             QGraphicsRectItem, QGraphicsScene,
                             QGraphicsTextItem, QGraphicsView)

from models import ChipLayout, Pad

_LF_PATTERN = re.compile(r'^LF[._\s]*(\d+)$', re.IGNORECASE)
_DIE_PREFIXES = ('SOC.', 'PSRAM.', 'DDRA.', 'DDRB.', 'ROM.')

# Pad/pin fill colors
COLOR_NOT_BOND = QColor(33, 33, 33, 220)        # black
COLOR_VSS = QColor(41, 128, 185, 220)           # dark blue
COLOR_DIE_TO_DIE = QColor(80, 80, 80, 220)      # dark gray
COLOR_UNDEFINED = QColor(192, 57, 43, 220)      # dark red
COLOR_PIN_UNUSED = QColor(189, 195, 199, 180)   # light gray

# Palette for LF pin groups; a pin keeps the same color as the pads bonded
# to it (keyed by pin number, so LF.5 is always the same color).
LF_PALETTE = [
    QColor(46, 204, 113, 220),   # green
    QColor(52, 152, 219, 220),   # blue
    QColor(230, 126, 34, 220),   # orange
    QColor(155, 89, 182, 220),   # purple
    QColor(241, 196, 15, 220),   # yellow
    QColor(26, 188, 156, 220),   # teal
]


def classify_bonding(bonding: str):
    """Return (kind, detail) where kind is one of
    'not_bond' | 'vss_ring' | 'lf' | 'die' | 'unknown'.
    For 'lf', detail is the pin number (int)."""
    value = (bonding or "").strip()
    upper = value.upper()

    if upper in ("", "NOT BOND", "NOT_BOND"):
        return 'not_bond', None

    if "VSS" in upper and "RING" in upper:
        return 'vss_ring', None
    if "E-PAD" in upper or "E_PAD" in upper or "EPAD" in upper:
        return 'vss_ring', None

    match = _LF_PATTERN.match(value)
    if match:
        return 'lf', int(match.group(1))

    if upper.startswith(tuple(p.upper() for p in _DIE_PREFIXES)):
        return 'die', None

    return 'unknown', None


def lf_color(pin_number: int) -> QColor:
    return LF_PALETTE[pin_number % len(LF_PALETTE)]


def bonding_color(bonding: str) -> QColor:
    kind, detail = classify_bonding(bonding)
    if kind == 'not_bond':
        return COLOR_NOT_BOND
    if kind == 'vss_ring':
        return COLOR_VSS
    if kind == 'lf':
        return lf_color(detail)
    if kind == 'die':
        return COLOR_DIE_TO_DIE
    return COLOR_UNDEFINED


class PadGraphicsItem(QGraphicsRectItem):
    """A pad rectangle with its number centered inside."""

    def __init__(self, pad: Pad, rect: QRectF, fill_color: QColor):
        super().__init__(rect)
        self.pad = pad
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setAcceptHoverEvents(False)
        self.setZValue(10)

        self.setPen(QPen(QColor(41, 128, 185), 3))
        self.setBrush(QBrush(fill_color))

        self.text_item = self._make_label(rect)

    def _make_label(self, rect: QRectF) -> QGraphicsTextItem:
        label = self.pad.pad_id.split('.')[-1]
        min_dim = min(rect.width(), rect.height())
        # Longer numbers get a smaller starting font.
        divisor = {1: 1.8, 2: 2.5}.get(len(label), 3.5)
        font_size = max(6.0, min_dim / divisor)

        text_item = QGraphicsTextItem(label)
        text_item.setFont(QFont("Arial", int(font_size), QFont.Bold))
        text_item.setDefaultTextColor(QColor(255, 255, 255))
        text_item.setZValue(100)

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
        return text_item

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


class ChipScene(QGraphicsScene):
    pad_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chip_layout = ChipLayout()
        self.pad_items = {}       # pad_id -> PadGraphicsItem
        self.wire_items = {}      # pad_id -> QGraphicsLineItem
        self.pin_points = {}      # pin number -> QPointF (inner tip, scene coords)
        self.ring_centerline = None  # QRectF, scene coords
        self._frame_params = None
        self._wires_visible = True
        self._highlighted_wire = None
        self._die_rotation = 0       # degrees CCW, multiple of 90
        self._die_center = (0.0, 0.0)  # die coords, set during redraw
        self.pad_clicked.connect(self._on_pad_clicked)

    # --- public API ---------------------------------------------------

    def set_pads(self, pads, frame_params=None):
        self._frame_params = frame_params
        self.chip_layout.set_pads(pads)
        self._redraw()

    def refresh(self):
        """Redraw with the current pads (e.g. after an edit)."""
        self._redraw()

    def rotate_die(self, degrees):
        """Rotate the die and its pads by a multiple of 90 degrees (positive =
        counterclockwise). The VSS ring and lead frame pins stay fixed; bond
        wires re-route to the pads' new positions."""
        self._die_rotation = (self._die_rotation + degrees) % 360
        self._redraw()

    def set_wires_visible(self, visible: bool):
        self._wires_visible = visible
        for item in self.wire_items.values():
            item.setVisible(visible)

    # --- coordinate helpers ---------------------------------------------

    @staticmethod
    def _to_scene(x: float, y: float) -> QPointF:
        """Die coordinates (Y up) -> scene coordinates (Y down)."""
        return QPointF(x, -y)

    def _rotate_die_point(self, x: float, y: float):
        """Rotate a die-coordinate point (Y up) around the die center by the
        current die rotation. Returns die coordinates."""
        cx, cy = self._die_center
        dx, dy = x - cx, y - cy
        r = self._die_rotation % 360
        if r == 90:      # CCW: (x, y) -> (-y, x)
            dx, dy = -dy, dx
        elif r == 180:
            dx, dy = -dx, -dy
        elif r == 270:   # CW
            dx, dy = dy, -dx
        return cx + dx, cy + dy

    def _pad_scene_rect(self, pad_id: str) -> QRectF:
        x1, y1, x2, y2 = self.chip_layout.get_pad_rectangle(pad_id)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        half_w, half_h = (x2 - x1) / 2, (y2 - y1) / 2

        rcx, rcy = self._rotate_die_point(cx, cy)
        if self._die_rotation % 180 == 90:
            half_w, half_h = half_h, half_w  # pad turns with the die

        top_left = self._to_scene(rcx - half_w, rcy + half_h)
        bottom_right = self._to_scene(rcx + half_w, rcy - half_h)
        return QRectF(top_left, bottom_right).normalized()

    # --- drawing ----------------------------------------------------------

    def _redraw(self):
        self.clear()
        self.pad_items = {}
        self.wire_items = {}
        self.pin_points = {}
        self.ring_centerline = None
        self._highlighted_wire = None

        if not self.chip_layout.pads:
            return

        bounds = self.chip_layout.get_bounds()
        self._die_center = (bounds['min_x'] + bounds['width'] / 2,
                            bounds['min_y'] + bounds['height'] / 2)

        die_rect = self._compute_die_rect()
        pin_count = self._compute_pin_count()

        self._draw_die(die_rect)
        self._draw_vss_ring(die_rect)
        self._draw_lead_frame_pins(die_rect, pin_count)
        self._draw_bond_wires()
        self._draw_pads()

        bounds = self.itemsBoundingRect()
        margin = max(bounds.width(), bounds.height()) * 0.03
        self.setSceneRect(bounds.adjusted(-margin, -margin, margin, margin))

    def _compute_die_rect(self) -> QRectF:
        """Die outline in scene coordinates, centered on the pads."""
        bounds = self.chip_layout.get_bounds()
        center = self._to_scene(bounds['min_x'] + bounds['width'] / 2,
                                bounds['min_y'] + bounds['height'] / 2)

        params = self._frame_params or {}
        die_w = params.get('die_width') or bounds['width'] * 1.02
        die_h = params.get('die_height') or bounds['height'] * 1.02
        # Never draw the die smaller than its pads.
        die_w = max(die_w, bounds['width'])
        die_h = max(die_h, bounds['height'])

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

    def _draw_die(self, die_rect: QRectF):
        die_item = QGraphicsRectItem(die_rect)
        die_item.setPen(QPen(QColor(127, 140, 141), die_rect.width() * 0.003))
        die_item.setBrush(QBrush(QColor(236, 240, 241)))
        die_item.setZValue(-20)
        self.addItem(die_item)

        label = QGraphicsTextItem("DIE")
        label.setFont(QFont("Arial", int(die_rect.width() * 0.05)))
        label.setDefaultTextColor(QColor(189, 195, 199))
        bounds = label.boundingRect()
        label.setPos(die_rect.center().x() - bounds.width() / 2,
                     die_rect.center().y() - bounds.height() / 2)
        label.setZValue(-19)
        self.addItem(label)

    def _draw_vss_ring(self, die_rect: QRectF):
        scale = max(die_rect.width(), die_rect.height())
        gap = scale * 0.05
        thickness = scale * 0.04

        inner = die_rect.adjusted(-gap, -gap, gap, gap)
        outer = inner.adjusted(-thickness, -thickness, thickness, thickness)
        self.ring_centerline = inner.adjusted(-thickness / 2, -thickness / 2,
                                              thickness / 2, thickness / 2)

        path = QPainterPath()
        path.setFillRule(Qt.OddEvenFill)
        path.addRect(outer)
        path.addRect(inner)

        ring_item = QGraphicsPathItem(path)
        ring_item.setPen(QPen(QColor(31, 97, 141), scale * 0.002))
        ring_item.setBrush(QBrush(QColor(41, 128, 185, 180)))
        ring_item.setZValue(-15)
        self.addItem(ring_item)

        label = QGraphicsTextItem("VSS ring (E-PAD ring)")
        label.setFont(QFont("Arial", int(thickness * 0.55), QFont.Bold))
        label.setDefaultTextColor(QColor(255, 255, 255))
        bounds = label.boundingRect()
        # Centered on the bottom segment of the ring.
        label.setPos(outer.center().x() - bounds.width() / 2,
                     outer.bottom() - thickness / 2 - bounds.height() / 2)
        label.setZValue(-14)
        self.addItem(label)

    def _draw_lead_frame_pins(self, die_rect: QRectF, pin_count: int):
        """Individual pins around the package, numbered counterclockwise
        from the bottom-left corner (matching the bonding data):
        bottom left->right, right bottom->top, top right->left,
        left top->bottom."""
        if pin_count < 4:
            return

        scale = max(die_rect.width(), die_rect.height())
        ring_outer_offset = scale * 0.05 + scale * 0.04  # ring gap + thickness
        pin_gap = scale * 0.05
        pin_len = scale * 0.10
        corner_clear = scale * 0.04

        # Rectangle on which the pin inner tips sit.
        offset = ring_outer_offset + pin_gap
        pkg = die_rect.adjusted(-offset, -offset, offset, offset)

        # Which pin numbers are actually bonded (for coloring).
        used_pins = set()
        for pad in self.chip_layout.pads:
            kind, detail = classify_bonding(pad.bonding)
            if kind == 'lf':
                used_pins.add(detail)

        per_side = pin_count // 4
        remainder = pin_count % 4
        side_counts = [per_side + (1 if i < remainder else 0) for i in range(4)]

        pin_number = 1
        for side_index, count in enumerate(side_counts):
            if count == 0:
                continue
            if side_index in (0, 2):   # bottom, top
                span = pkg.width() - 2 * corner_clear
            else:                      # right, left
                span = pkg.height() - 2 * corner_clear
            pitch = span / count
            pin_w = min(pitch * 0.55, scale * 0.03)

            for i in range(count):
                step = (i + 0.5) * pitch
                if side_index == 0:    # bottom, left -> right
                    pos = pkg.left() + corner_clear + step
                    rect = QRectF(pos - pin_w / 2, pkg.bottom(), pin_w, pin_len)
                    tip = QPointF(pos, pkg.bottom())
                elif side_index == 1:  # right, bottom -> top
                    pos = pkg.bottom() - corner_clear - step
                    rect = QRectF(pkg.right(), pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.right(), pos)
                elif side_index == 2:  # top, right -> left
                    pos = pkg.right() - corner_clear - step
                    rect = QRectF(pos - pin_w / 2, pkg.top() - pin_len, pin_w, pin_len)
                    tip = QPointF(pos, pkg.top())
                else:                  # left, top -> bottom
                    pos = pkg.top() + corner_clear + step
                    rect = QRectF(pkg.left() - pin_len, pos - pin_w / 2, pin_len, pin_w)
                    tip = QPointF(pkg.left(), pos)

                fill = lf_color(pin_number) if pin_number in used_pins else COLOR_PIN_UNUSED
                pin_item = QGraphicsRectItem(rect)
                pin_item.setPen(QPen(QColor(52, 73, 94), scale * 0.0015))
                pin_item.setBrush(QBrush(fill))
                pin_item.setZValue(-10)
                pin_item.setToolTip(f"LF.{pin_number}")
                self.addItem(pin_item)

                self.pin_points[pin_number] = tip
                self._draw_pin_label(pin_number, rect, side_index, pin_w)
                pin_number += 1

    def _draw_pin_label(self, pin_number: int, pin_rect: QRectF, side_index: int, pin_w: float):
        label = QGraphicsTextItem(str(pin_number))
        label.setFont(QFont("Arial", max(1, int(pin_w * 0.75)), QFont.Bold))
        label.setDefaultTextColor(QColor(52, 73, 94))
        bounds = label.boundingRect()

        pad_off = pin_w * 0.2
        if side_index == 0:    # bottom: label below the pin
            label.setPos(pin_rect.center().x() - bounds.width() / 2,
                         pin_rect.bottom() + pad_off)
        elif side_index == 1:  # right: label right of the pin
            label.setPos(pin_rect.right() + pad_off,
                         pin_rect.center().y() - bounds.height() / 2)
        elif side_index == 2:  # top: label above the pin
            label.setPos(pin_rect.center().x() - bounds.width() / 2,
                         pin_rect.top() - bounds.height() - pad_off)
        else:                  # left: label left of the pin
            label.setPos(pin_rect.left() - bounds.width() - pad_off,
                         pin_rect.center().y() - bounds.height() / 2)
        label.setZValue(-9)
        self.addItem(label)

    def _nearest_ring_point(self, point: QPointF) -> QPointF:
        """Nearest point on the VSS ring centerline for a point inside it."""
        rect = self.ring_centerline
        distances = [
            (point.x() - rect.left(), QPointF(rect.left(), point.y())),
            (rect.right() - point.x(), QPointF(rect.right(), point.y())),
            (point.y() - rect.top(), QPointF(point.x(), rect.top())),
            (rect.bottom() - point.y(), QPointF(point.x(), rect.bottom())),
        ]
        return min(distances, key=lambda d: d[0])[1]

    def _draw_bond_wires(self):
        for pad in self.chip_layout.pads:
            kind, detail = classify_bonding(pad.bonding)

            source = self._pad_scene_rect(pad.pad_id).center()
            if kind == 'lf' and detail in self.pin_points:
                target = self.pin_points[detail]
                color = lf_color(detail)
            elif kind == 'vss_ring' and self.ring_centerline is not None:
                target = self._nearest_ring_point(source)
                color = COLOR_VSS
            else:
                continue  # Not Bond, die-to-die, or unresolvable target

            wire = QGraphicsLineItem(source.x(), source.y(), target.x(), target.y())
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 130), 1.2)
            pen.setCosmetic(True)  # constant width at any zoom level
            wire.setPen(pen)
            wire.setZValue(5)
            wire.setVisible(self._wires_visible)
            self.addItem(wire)
            self.wire_items[pad.pad_id] = wire

    def _draw_pads(self):
        for pad in self.chip_layout.pads:
            rect = self._pad_scene_rect(pad.pad_id)
            if rect.isEmpty():
                continue
            pad_item = PadGraphicsItem(pad, rect, bonding_color(pad.bonding))
            self.addItem(pad_item)
            self.addItem(pad_item.text_item)
            self.pad_items[pad.pad_id] = pad_item

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
            self._highlighted_wire = None

        wire = self.wire_items.get(pad_id)
        if wire is not None:
            pen = wire.pen()
            color = pen.color()
            color.setAlpha(255)
            pen.setColor(color)
            pen.setWidthF(3.0)
            wire.setPen(pen)
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
        # Zoom keeps the point under the cursor fixed.
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def viewportEvent(self, event):
        # macOS trackpad pinch arrives as a native "zoom" gesture, not a wheel
        # event; value() is the incremental scale change (e.g. 0.02 = +2%).
        if event.type() == QEvent.NativeGesture and isinstance(event, QNativeGestureEvent):
            if event.gestureType() == Qt.ZoomNativeGesture:
                self._zoom(1.0 + event.value())
                return True
        return super().viewportEvent(event)

    def wheelEvent(self, event):
        # A physical mouse wheel (angleDelta only) zooms; a trackpad two-finger
        # scroll (reports pixelDelta) pans through the default handler.
        if event.pixelDelta().isNull():
            self._zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)
        else:
            super().wheelEvent(event)

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
        if self.scene():
            rect = self.scene().sceneRect()
            if not rect.isNull():
                self.fitInView(rect, Qt.KeepAspectRatio)
