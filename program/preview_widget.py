import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor

class AnimationPreview(QWidget):
    zoomChanged = pyqtSignal(int)
    dataChanged = pyqtSignal()

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.pixmap = None
        self.current_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.show_direction = 0 
        self.zoom = 2
        
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse_pos = None

        self.is_hitbox_mode = False 
        self.hover_state = None
        self.is_dragging = False
        
        # --- NEW: Store the loaded image path ---
        self.image_path = ""

        self.bg_color = QColor(80, 80, 80)
        self.grid_color = QColor(60, 60, 60)
        
        self.setMouseTracking(True)
        self.setMinimumSize(400, 400)
        self.update_timer()

    def set_hitbox_mode(self, enabled):
        self.is_hitbox_mode = enabled
        self.update()

    def set_zoom(self, value):
        self.zoom = value
        self.update()

    def load_image(self):
        # Reset path before trying to load
        self.image_path = ""
        self.pixmap = None

        if not self.data.filepath: 
            self.update()
            return
        
        base = os.path.splitext(self.data.filepath)[0]
        for ext in ['.png', '.gif', '.bmp']:
            path = base + ext
            if os.path.exists(path):
                # --- NEW: Store the path ---
                self.image_path = path 
                self.pixmap = QPixmap(self.image_path)
                break # Found one, stop looking
        
        self.update()

    # (The rest of preview_widget.py remains the same)
    def update_timer(self):
        speed = self.data.standard_params.get('framespeed', 8)
        if speed is None: speed = 8
        if speed < 1: speed = 1
        ms = int(speed * (1000 / 64))
        self.timer.start(ms)

    def next_frame(self):
        total_frames = self.data.standard_params.get('frames', 1)
        if total_frames is None: total_frames = 1
        if total_frames < 1: total_frames = 1
        self.current_frame = (self.current_frame + 1) % total_frames
        self.update()

    def get_logical_pos(self, screen_pos):
        cx, cy = self.width() // 2, self.height() // 2
        lx = (screen_pos.x() - cx - self.pan_x) / self.zoom
        ly = (screen_pos.y() - cy - self.pan_y) / self.zoom
        p = self.data.standard_params
        style = int(p.get('framestyle', 0) or 0)
        if style == 0 and self.show_direction == 1:
            lx = -lx
        return lx, ly

    def get_active_rect(self):
        p = self.data.standard_params
        if self.is_hitbox_mode:
            w = int(p.get('width', 32) or 32)
            h = int(p.get('height', 32) or 32)
            return QRectF(-w/2, -h/2, w, h)
        else:
            fw = int(p.get('gfxwidth', 32) or 32)
            fh = int(p.get('gfxheight', 32) or 32)
            ox = int(p.get('gfxoffsetx', 0) or 0)
            oy = int(p.get('gfxoffsety', 0) or 0)
            ph = int(p.get('height', 32) or 32)
            style = int(p.get('framestyle', 0) or 0)
            if style >= 1 and self.show_direction == 1:
                ox = -ox
            x = -fw / 2 + ox
            y = (ph / 2) - fh + oy
            return QRectF(x, y, fw, fh)

    def check_hover_edge(self, lx, ly):
        rect = self.get_active_rect()
        if not rect: return None
        tol = 6 / self.zoom
        if tol < 1: tol = 1
        l, r = rect.left(), rect.right()
        t, b = rect.top(), rect.bottom()
        if t - tol <= ly <= b + tol:
            if abs(lx - l) < tol: return 'L'
            if abs(lx - r) < tol: return 'R'
        if l - tol <= lx <= r + tol:
            if abs(ly - t) < tol: return 'T'
            if abs(ly - b) < tol: return 'B'
        if l < lx < r and t < ly < b:
            return 'MOVE'
        return None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        new_zoom = self.zoom + (1 if delta > 0 else -1)
        new_zoom = max(1, min(8, new_zoom))
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self.update()
            self.zoomChanged.emit(self.zoom)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.hover_state:
                self.is_dragging = True

    def mouseReleaseEvent(self, event):
        self.is_panning = False
        self.is_dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        lx, ly = self.get_logical_pos(event.pos())
        if self.is_panning:
            delta = event.pos() - self.last_mouse_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()
            return

        if self.is_dragging:
            delta_screen = event.pos() - self.last_mouse_pos
            dx = int(delta_screen.x() / self.zoom)
            dy = int(delta_screen.y() / self.zoom)
            if dx == 0 and dy == 0: return
            p = self.data.standard_params
            style = int(p.get('framestyle', 0) or 0)
            if style == 0 and self.show_direction == 1:
                dx = -dx
            visual_offset_inverted = (style >= 1 and self.show_direction == 1)
            if self.hover_state == 'MOVE':
                if not self.is_hitbox_mode:
                    if visual_offset_inverted:
                        p['gfxoffsetx'] -= dx
                    else:
                        p['gfxoffsetx'] += dx
                    p['gfxoffsety'] += dy
            elif self.is_hitbox_mode:
                if self.hover_state == 'R': p['width'] += dx
                elif self.hover_state == 'L': p['width'] -= dx
                elif self.hover_state == 'B': p['height'] += dy
                elif self.hover_state == 'T': p['height'] -= dy
            else:
                if self.hover_state == 'R': p['gfxwidth'] += dx
                elif self.hover_state == 'L': p['gfxwidth'] -= dx
                elif self.hover_state == 'B': p['gfxheight'] += dy
                elif self.hover_state == 'T': p['gfxheight'] -= dy
            p['width'] = max(1, p['width'])
            p['height'] = max(1, p['height'])
            p['gfxwidth'] = max(1, p['gfxwidth'])
            p['gfxheight'] = max(1, p['gfxheight'])
            self.last_mouse_pos = event.pos()
            self.dataChanged.emit()
            self.update()
            return

        state = self.check_hover_edge(lx, ly)
        self.hover_state = state
        if state in ['L', 'R']: self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif state in ['T', 'B']: self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif state == 'MOVE':
            self.setCursor(Qt.CursorShape.ArrowCursor if self.is_hitbox_mode else Qt.CursorShape.SizeAllCursor)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        cx, cy = self.width() // 2, self.height() // 2
        painter.save()
        painter.translate(cx, cy)
        painter.translate(self.pan_x, self.pan_y)
        painter.scale(self.zoom, self.zoom)
        grid_size = 16
        steps_x = int((self.width() / self.zoom) / 2 / grid_size) + 2
        steps_y = int((self.height() / self.zoom) / 2 / grid_size) + 2
        painter.setPen(QPen(self.grid_color, 0))
        for i in range(-steps_x, steps_x + 1):
            x = i * grid_size
            painter.drawLine(x, -steps_y * grid_size, x, steps_y * grid_size)
        for i in range(-steps_y, steps_y + 1):
            y = i * grid_size
            painter.drawLine(-steps_x * grid_size, y, steps_x * grid_size, y)
        p = self.data.standard_params
        fw = int(p.get('gfxwidth', 32) or 32)
        fh = int(p.get('gfxheight', 32) or 32)
        frames = int(p.get('frames', 1) or 1)
        style = int(p.get('framestyle', 0) or 0)
        ox = int(p.get('gfxoffsetx', 0) or 0)
        oy = int(p.get('gfxoffsety', 0) or 0)
        pw = int(p.get('width', 32) or 32)
        ph = int(p.get('height', 32) or 32)
        hitbox_rect = QRectF(-pw / 2, -ph / 2, pw, ph)
        pen = QPen(QColor(0, 255, 0), 2) if self.is_hitbox_mode else QPen(QColor(0, 255, 0, 100), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(hitbox_rect)
        if self.pixmap:
            painter.save()
            row_offset = 0
            is_facing_right = (self.show_direction == 1)
            if style == 0:
                if is_facing_right:
                    painter.scale(-1, 1)
            elif style >= 1:
                if is_facing_right:
                    row_offset = frames
                    ox = -ox
            src_y = (row_offset + self.current_frame) * fh
            src_rect = QRect(0, src_y, fw, fh)
            dest_x = -fw / 2 + ox
            dest_y = (ph / 2) - fh + oy
            dest_rect = QRectF(dest_x, dest_y, fw, fh)
            painter.drawPixmap(dest_rect.toRect(), self.pixmap, src_rect)
            pen = QPen(QColor(255, 50, 50), 2, Qt.PenStyle.SolidLine) if not self.is_hitbox_mode else QPen(QColor(255, 50, 50, 100), 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawRect(dest_rect)
            painter.restore()
        painter.restore()
        painter.setPen(Qt.GlobalColor.white)
        mode_text = "[HITBOX MODE]" if self.is_hitbox_mode else "[GRAPHIC MODE]"
        info = f"{mode_text} | Frame: {self.current_frame + 1}/{frames} | Zoom: {self.zoom}x"
        painter.drawText(10, self.height() - 10, info)