import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor, QImage

class AnimationPreview(QWidget):
    zoomChanged = pyqtSignal(int)
    dataChanged = pyqtSignal()      # For real-time UI syncing
    dragStarted = pyqtSignal()      # Fired when user clicks to start a drag
    dragFinished = pyqtSignal()     # Fired when user releases mouse

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.pixmap = None
        self.image_path = ""
        
        self.current_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.show_direction = 0 # 0=Left, 1=Right
        self.zoom = 2
        
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse_pos = None

        self.is_hitbox_mode = False 
        self.hover_state = None
        self.is_dragging = False

        # --- THEME COLORS ---
        self.bg_color = QColor(30, 30, 30)   # Clean Dark Grey
        self.grid_color = QColor(50, 50, 50) # Subtle Grid
        
        self.setMouseTracking(True)
        self.setMinimumSize(400, 400)
        self.update_timer()

    def set_hitbox_mode(self, enabled):
        self.is_hitbox_mode = enabled
        self.update()

    def load_image(self):
        self.image_path = ""
        self.mask_path = "" # Track mask for the file watcher
        self.pixmap = None
        
        if not self.data.filepath: 
            self.update()
            return
        
        base = os.path.splitext(self.data.filepath)[0]
        png_path = base + ".png"
        
        # 1. Try modern PNG first
        if os.path.exists(png_path):
            self.image_path = png_path
            self.pixmap = QPixmap(self.image_path)
        else:
            # 2. Look for legacy GIF/BMP + Mask
            for ext in ['.gif', '.bmp']:
                img_path = base + ext
                if os.path.exists(img_path):
                    self.image_path = img_path
                    # Check for mask (e.g., npc-6.gif -> npc-6m.gif)
                    mask_path = base + "m" + ext
                    if os.path.exists(mask_path):
                        self.mask_path = mask_path
                        self.pixmap = self._load_legacy_sprite(img_path, mask_path)
                    else:
                        # Fallback: No mask found, just load as is
                        self.pixmap = QPixmap(img_path)
                    break
                    
        self.update()

    def _load_legacy_sprite(self, img_path, mask_path):
        """
        Combines a source image and mask using the Moondust/PGE logic.
        Simulates legacy BitBlt SRCAND / SRCPAINT rendering.
        """
        # Load images and ensure they are in a manipulatable 32-bit format
        # Note: We use Format_ARGB32 so we can directly access alpha
        front = QImage(img_path).convertToFormat(QImage.Format.Format_ARGB32)
        mask = QImage(mask_path).convertToFormat(QImage.Format.Format_ARGB32)
        
        img_w, img_h = front.width(), front.height()
        mask_w, mask_h = mask.width(), mask.height()

        # SMBX typically assumes a white background during the blit simulation 
        # for texture generation to ensure colors are preserved correctly.
        bg_r, bg_g, bg_b = 255, 255, 255

        # Process per pixel (following Moondust bitmask_to_rgba logic)
        for y in range(img_h):
            for x in range(img_w):
                # 1. Get Source Pixel
                f_pixel = front.pixelColor(x, y)
                f_r, f_g, f_b = f_pixel.red(), f_pixel.green(), f_pixel.blue()

                # 2. Get Mask Pixel (or assume white if out of mask bounds)
                if x < mask_w and y < mask_h:
                    m_pixel = mask.pixelColor(x, y)
                    m_r, m_g, m_b = m_pixel.red(), m_pixel.green(), m_pixel.blue()
                else:
                    m_r, m_g, m_b = 255, 255, 255

                # 3. Calculate RGB (Simulate (Mask & BG) | Front)
                # This ensures the sprite "cuts" into the background correctly
                res_r = (m_r & bg_r) | f_r
                res_g = (m_g & bg_g) | f_g
                res_b = (m_b & bg_b) | f_b

                # 4. Calculate Alpha
                # Initial: 255 - average(mask)
                m_avg = (m_r + m_g + m_b) // 3
                new_alpha = 255 - m_avg

                # Moondust Threshold: Almost white mask becomes fully transparent
                if m_r > 240 and m_g > 240 and m_b > 240:
                    new_alpha = 0

                # 5. Enhance Alpha based on Source brightness 
                # (Standard legacy rendering "glow" or lightness compensation)
                f_avg = (f_r + f_g + f_b) // 3
                new_alpha += f_avg

                # Clamp alpha
                if new_alpha > 255:
                    new_alpha = 255
                elif new_alpha < 0:
                    new_alpha = 0

                # 6. Apply back to front image
                front.setPixelColor(x, y, QColor(res_r, res_g, res_b, new_alpha))

        return QPixmap.fromImage(front)

    def update_timer(self):
        speed = self.data.standard_params.get('framespeed') or 8
        if speed < 1: speed = 1
        ms = int(speed * (1000 / 65))
        self.timer.start(ms)

    def next_frame(self):
        total_frames = self.data.standard_params.get('frames') or 1
        if total_frames < 1: total_frames = 1
        self.current_frame = (self.current_frame + 1) % total_frames
        self.update()

    def get_logical_pos(self, screen_pos):
        cx, cy = self.width() // 2, self.height() // 2
        lx = (screen_pos.x() - cx - self.pan_x) / self.zoom
        ly = (screen_pos.y() - cy - self.pan_y) / self.zoom
        
        p = self.data.standard_params
        style = int(p.get('framestyle') or 0)
        if style == 0 and self.show_direction == 1:
            lx = -lx
        return lx, ly

    def get_active_rect(self):
        p = self.data.standard_params
        if self.is_hitbox_mode:
            w = int(p.get('width') or 32)
            h = int(p.get('height') or 32)
            return QRectF(-w/2, -h/2, w, h)
        else:
            fw = int(p.get('gfxwidth') or 32)
            fh = int(p.get('gfxheight') or 32)
            ox = int(p.get('gfxoffsetx') or 0)
            oy = int(p.get('gfxoffsety') or 0)
            
            style = int(p.get('framestyle') or 0)
            if style >= 1 and self.show_direction == 1:
                ox = -ox
            
            ph = int(p.get('height') or 32)
            x = -fw / 2 + ox
            y = (ph / 2) - fh + oy 
            return QRectF(x, y, fw, fh)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        new_zoom = self.zoom + (1 if delta > 0 else -1)
        self.zoom = max(1, min(16, new_zoom))
        self.zoomChanged.emit(self.zoom)
        self.update()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            lx, ly = self.get_logical_pos(event.pos())
            state = self.check_hover_edge(lx, ly)
            if state:
                self.hover_state = state
                self.is_dragging = True
                self.dragStarted.emit() # Notify MainWindow to snapshot values

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.dragFinished.emit() # Notify MainWindow to push the final Undo command
        
        self.is_panning = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
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
            style = int(p.get('framestyle') or 0)
            if style == 0 and self.show_direction == 1:
                dx = -dx

            visual_offset_inverted = (style >= 1 and self.show_direction == 1)

            if self.hover_state == 'MOVE':
                if not self.is_hitbox_mode:
                    if visual_offset_inverted:
                        p['gfxoffsetx'] = (p.get('gfxoffsetx') or 0) - dx
                    else:
                        p['gfxoffsetx'] = (p.get('gfxoffsetx') or 0) + dx
                    p['gfxoffsety'] = (p.get('gfxoffsety') or 0) + dy
            elif self.is_hitbox_mode:
                w = p.get('width') or 32
                h = p.get('height') or 32
                if self.hover_state == 'R': p['width'] = w + dx * 2
                elif self.hover_state == 'L': p['width'] = w - dx * 2
                elif self.hover_state == 'B': p['height'] = h + dy * 2
                elif self.hover_state == 'T': p['height'] = h - dy * 2
            else:
                w = p.get('gfxwidth') or 32
                h = p.get('gfxheight') or 32
                if self.hover_state == 'R': p['gfxwidth'] = w + dx * 2
                elif self.hover_state == 'L': p['gfxwidth'] = w - dx * 2
                elif self.hover_state == 'B': p['gfxheight'] = h + dy * 2
                elif self.hover_state == 'T': p['gfxheight'] = h - dy * 2

            for k in ['width', 'height', 'gfxwidth', 'gfxheight']:
                if p.get(k) is not None and p[k] < 1: p[k] = 1

            self.last_mouse_pos = event.pos()
            # This triggers the UI sync in editor_window, but NOT the undo command
            self.dataChanged.emit() 
            self.update()
            return

        lx, ly = self.get_logical_pos(event.pos())
        state = self.check_hover_edge(lx, ly)
        self.hover_state = state
        
        if state in ['L', 'R']: self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif state in ['T', 'B']: self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif state == 'MOVE':
            self.setCursor(Qt.CursorShape.ArrowCursor if self.is_hitbox_mode else Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def check_hover_edge(self, lx, ly):
        rect = self.get_active_rect()
        if not rect: return None
        tol = 8 / self.zoom
        if tol < 2: tol = 2
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        cx, cy = self.width() // 2, self.height() // 2
        painter.save()
        painter.translate(cx, cy)
        painter.translate(self.pan_x, self.pan_y)
        painter.scale(self.zoom, self.zoom)
        
        # Grid
        inv_zoom = 1.0 / self.zoom
        view_l = (-cx - self.pan_x) * inv_zoom
        view_r = (self.width() - cx - self.pan_x) * inv_zoom
        view_t = (-cy - self.pan_y) * inv_zoom
        view_b = (self.height() - cy - self.pan_y) * inv_zoom
        grid_size = 32
        start_x = int(view_l // grid_size) * grid_size
        end_x = int(view_r // grid_size + 1) * grid_size
        start_y = int(view_t // grid_size) * grid_size
        end_y = int(view_b // grid_size + 1) * grid_size

        painter.setPen(QPen(self.grid_color, 0))
        for x in range(start_x, end_x + 1, grid_size):
            painter.drawLine(x, int(view_t), x, int(view_b))
        for y in range(start_y, end_y + 1, grid_size):
            painter.drawLine(int(view_l), y, int(view_r), y)

        # Origin Crosshair (Subtle Grey)
        painter.setPen(QPen(QColor(100, 100, 100), 0))
        painter.drawLine(-8, 0, 8, 0)
        painter.drawLine(0, -8, 0, 8)

        p = self.data.standard_params
        fw = int(p.get('gfxwidth') or 32)
        fh = int(p.get('gfxheight') or 32)
        pw = int(p.get('width') or 32)
        ph = int(p.get('height') or 32)
        ox = int(p.get('gfxoffsetx') or 0)
        oy = int(p.get('gfxoffsety') or 0)
        frames = int(p.get('frames') or 1)
        style = int(p.get('framestyle') or 0)

        # Hitbox (Green)
        hitbox_rect = QRectF(-pw / 2, -ph / 2, pw, ph)
        if self.is_hitbox_mode:
            painter.fillRect(hitbox_rect, QColor(0, 255, 0, 30))
        pen = QPen(QColor(0, 255, 0), 1) if self.is_hitbox_mode else QPen(QColor(0, 255, 0, 80), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(hitbox_rect)

        # Sprite
        if self.pixmap:
            painter.save()
            is_facing_right = (self.show_direction == 1)
            row_offset = 0
            if style == 0:
                if is_facing_right: painter.scale(-1, 1)
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
            
            # GFX Box (Red)
            pen = QPen(QColor(255, 50, 50), 1) if not self.is_hitbox_mode else QPen(QColor(255, 50, 50, 80), 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawRect(dest_rect)
            
            painter.restore()

        painter.restore()
        
        # Info HUD
        painter.setPen(QColor(200, 200, 200))
        mode_text = "[HITBOX MODE]" if self.is_hitbox_mode else "[GRAPHIC MODE]"
        info = f"{mode_text} | Frame: {self.current_frame + 1}/{frames} | Zoom: {self.zoom}x"
        painter.drawText(10, self.height() - 10, info)