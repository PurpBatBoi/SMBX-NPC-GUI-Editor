import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor

class AnimationPreview(QWidget):
    zoomChanged = pyqtSignal(int)
    # New signal to tell UI to update SpinBoxes when we drag visually
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
        
        # Panning
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse_pos = None

        # Editing / Dragging
        self.is_hitbox_mode = False # False = Graphics, True = Hitbox
        self.hover_edge = None # 'L', 'R', 'T', 'B'
        self.is_resizing = False
        
        # Colors
        self.bg_color = QColor(80, 80, 80)
        self.grid_color = QColor(60, 60, 60)
        
        self.setMouseTracking(True) # Required to see hover cursor changes
        self.update_timer()

    def set_hitbox_mode(self, enabled):
        self.is_hitbox_mode = enabled
        self.update()

    def set_zoom(self, value):
        self.zoom = value
        self.update()

    def load_image(self):
        if not self.data.filepath: return
        base = os.path.splitext(self.data.filepath)[0]
        for ext in ['.png', '.gif', '.bmp']:
            if os.path.exists(base + ext):
                self.pixmap = QPixmap(base + ext)
                self.update()
                return
        self.pixmap = None
        self.update()

    def update_timer(self):
        speed = self.data.params['framespeed']
        if speed < 1: speed = 1
        ms = int(speed * (1000 / 64))
        self.timer.start(ms)

    def next_frame(self):
        total_frames = self.data.params['frames']
        if total_frames < 1: total_frames = 1
        self.current_frame = (self.current_frame + 1) % total_frames
        self.update()

    # --- COORDINATE HELPERS ---
    def get_logical_pos(self, screen_pos):
        """Convert screen pixel to logical game pixel."""
        cx, cy = self.width() // 2, self.height() // 2
        # Reverse the paint transformation
        # x_screen = (x_logical * zoom) + cx + pan_x
        # x_logical = (x_screen - cx - pan_x) / zoom
        lx = (screen_pos.x() - cx - self.pan_x) / self.zoom
        ly = (screen_pos.y() - cy - self.pan_y) / self.zoom
        return lx, ly

    def get_active_rect(self):
        """Returns the logical QRectF of the currently editable box."""
        p = self.data.params
        
        if self.is_hitbox_mode:
            # Hitbox is centered at 0,0 relative to our logic
            w, h = p['width'], p['height']
            return QRectF(-w/2, -h/2, w, h)
        else:
            # Graphics Rect
            fw, fh = p['gfxwidth'], p['gfxheight']
            ox, oy = p['gfxoffsetx'], p['gfxoffsety']
            ph = p['height']
            
            # Logic from paintEvent:
            # y = (hitbox_y + ph) - fh + oy
            # Since hitbox_y is -ph/2
            # y = (-ph/2 + ph) - fh + oy = ph/2 - fh + oy
            
            x = -fw / 2 + ox
            y = (ph / 2) - fh + oy
            return QRectF(x, y, fw, fh)

    def check_hover_edge(self, lx, ly):
        """Determines if mouse is near an edge of the active rect."""
        rect = self.get_active_rect()
        if not rect: return None
        
        tol = 6 / self.zoom # Tolerance in logical pixels (approx 6 screen pixels)
        if tol < 1: tol = 1

        l, r = rect.left(), rect.right()
        t, b = rect.top(), rect.bottom()
        
        # Check Vertical Edges
        if t - tol <= ly <= b + tol:
            if abs(lx - l) < tol: return 'L'
            if abs(lx - r) < tol: return 'R'
            
        # Check Horizontal Edges
        if l - tol <= lx <= r + tol:
            if abs(ly - t) < tol: return 'T'
            if abs(ly - b) < tol: return 'B'
            
        return None

    # --- INPUT EVENTS ---
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
            if self.hover_edge:
                self.is_resizing = True
            else:
                pass # Clicked empty space

    def mouseReleaseEvent(self, event):
        self.is_panning = False
        self.is_resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # Re-check hover to set correct cursor immediately
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        lx, ly = self.get_logical_pos(event.pos())

        # 1. HANDLE PANNING
        if self.is_panning:
            delta = event.pos() - self.last_mouse_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()
            return

        # 2. HANDLE RESIZING
        if self.is_resizing:
            delta_screen = event.pos() - self.last_mouse_pos
            # Convert screen delta to logical delta (rounding to nearest int for pixel art feel)
            dx = int(delta_screen.x() / self.zoom)
            dy = int(delta_screen.y() / self.zoom)
            
            p = self.data.params
            
            # Prevent ultra-fast updates if zoom is high but mouse moved little
            if dx == 0 and dy == 0: return 

            if self.is_hitbox_mode:
                # HITBOX EDITING (Symmetric)
                # Hitbox is center-anchored. Growing 'Right' adds to width. 
                # Since it stays centered, it effectively grows both sides visually.
                if self.hover_edge == 'R': p['width'] += dx
                elif self.hover_edge == 'L': p['width'] -= dx
                elif self.hover_edge == 'B': p['height'] += dy
                elif self.hover_edge == 'T': p['height'] -= dy
            else:
                # GRAPHICS EDITING
                if self.hover_edge == 'R': 
                    p['gfxwidth'] += dx
                    # Optional: Compensate offset if you want it to grow one-sided?
                    # For now, changing width expands from center of sprite logic
                elif self.hover_edge == 'L':
                    p['gfxwidth'] -= dx
                elif self.hover_edge == 'B':
                    p['gfxheight'] += dy
                elif self.hover_edge == 'T':
                    p['gfxheight'] -= dy
            
            # Clamp values to prevent crash or negative sizes
            p['width'] = max(1, p['width'])
            p['height'] = max(1, p['height'])
            p['gfxwidth'] = max(1, p['gfxwidth'])
            p['gfxheight'] = max(1, p['gfxheight'])

            self.last_mouse_pos = event.pos()
            self.dataChanged.emit() # Update UI
            self.update()
            return

        # 3. HANDLE HOVER (Set Cursor)
        edge = self.check_hover_edge(lx, ly)
        self.hover_edge = edge
        
        if edge in ['L', 'R']:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in ['T', 'B']:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        cx, cy = self.width() // 2, self.height() // 2

        painter.save()
        painter.translate(cx, cy)
        painter.translate(self.pan_x, self.pan_y) # Apply Pan BEFORE Scale
        painter.scale(self.zoom, self.zoom)
        
        # Draw Grid
        grid_size = 16 
        steps_x = int((self.width() / self.zoom) / 2 / grid_size) + 2
        steps_y = int((self.height() / self.zoom) / 2 / grid_size) + 2
        painter.setPen(QPen(self.grid_color, 0))
        
        for i in range(-steps_x, steps_x + 1):
            x = i * grid_size
            painter.drawLine(x, -steps_y*grid_size, x, steps_y*grid_size)
        for i in range(-steps_y, steps_y + 1):
            y = i * grid_size
            painter.drawLine(-steps_x*grid_size, y, steps_x*grid_size, y)

        # Params
        p = self.data.params
        fw, fh = p['gfxwidth'], p['gfxheight']
        frames = p['frames']
        style = p['framestyle']
        ox, oy = p['gfxoffsetx'], p['gfxoffsety']
        pw, ph = p['width'], p['height']

        # 1. Draw Hitbox
        # Hitbox is always centered at (0,0) in logical space
        hitbox_rect = QRectF(-pw/2, -ph/2, pw, ph)
        
        # Style based on mode
        if self.is_hitbox_mode:
            pen = QPen(QColor(0, 255, 0), 2) # Thick Green
            pen.setCosmetic(True) # Keeps thickness constant on screen (doesn't scale with zoom)
            painter.setPen(pen)
        else:
            pen = QPen(QColor(0, 255, 0, 100), 1) # Thin Faint Green
            pen.setCosmetic(True)
            painter.setPen(pen)
            
        painter.drawRect(hitbox_rect)

        # 2. Draw Sprite
        if self.pixmap:
            row_offset = 0
            if style == 1 and self.show_direction == 1: row_offset = frames
            elif style == 2 and self.show_direction == 1: row_offset = frames
            
            src_y = (row_offset + self.current_frame) * fh
            src_rect = QRect(0, src_y, fw, fh)

            # Logic: y = (ph/2) - fh + oy
            dest_x = -fw/2 + ox
            dest_y = (ph/2) - fh + oy
            dest_rect = QRectF(dest_x, dest_y, fw, fh)

            painter.drawPixmap(dest_rect.toRect(), self.pixmap, src_rect)
            
            # GFX Border
            if not self.is_hitbox_mode:
                pen = QPen(QColor(255, 50, 50), 2, Qt.PenStyle.SolidLine) # Thick Red
                pen.setCosmetic(True)
                painter.setPen(pen)
            else:
                pen = QPen(QColor(255, 50, 50, 100), 1, Qt.PenStyle.DashLine) # Faint Red
                pen.setCosmetic(True)
                painter.setPen(pen)
                
            painter.drawRect(dest_rect)

        painter.restore()

        # Text Overlay
        painter.setPen(Qt.GlobalColor.white)
        mode_text = "[HITBOX MODE]" if self.is_hitbox_mode else "[GRAPHIC MODE]"
        info = f"{mode_text} | Frame: {self.current_frame+1}/{frames} | Zoom: {self.zoom}x"
        painter.drawText(10, self.height() - 10, info)