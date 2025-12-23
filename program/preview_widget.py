import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor, QImage
from .ui.styles import AppColors
from .utils.image_utils import load_legacy_sprite

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
        self.zoom = 6  # CHANGE: Start at 6x

        self.is_paused = False # NEW: Track manual pause state
        
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse_pos = None

        self.is_hitbox_mode = False 
        self.hover_state = None
        self.is_dragging = False

        # --- THEME COLORS ---
        self.bg_color = AppColors.BACKGROUND
        self.grid_color = AppColors.GRID
        
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
                        self.pixmap = load_legacy_sprite(img_path, mask_path)
                    else:
                        # Fallback: No mask found, just load as is
                        self.pixmap = QPixmap(img_path)
                    break
                    
        self.update()

    def update_timer(self):
        """Starts/Stops the timer based on frame count and pause state"""
        p = self.data.standard_params
        frames = int(p.get('frames') or 1)
        
        # Logic: Stop timer if only 1 frame OR if manually paused
        if frames <= 1 or self.is_paused:
            self.timer.stop()
            if frames <= 1: self.current_frame = 0
            self.update()
            return

        speed = p.get('framespeed') or 8
        if speed < 1: speed = 1
        ms = int(speed * (1000 / 65))
        self.timer.start(ms)

    def toggle_pause(self, paused):
        """External hook to pause/play animation"""
        self.is_paused = paused
        self.update_timer()
    
    def manual_step_frame(self):
        """Manually advance to the next frame (for step-through button)"""
        self.advance_frame(auto=False)

    def next_frame(self):
        """Automatically advance frame (called by timer)"""
        self.advance_frame(auto=True)
        
    def advance_frame(self, auto=False):
        total_frames = int(self.data.standard_params.get('frames') or 1)
        if total_frames <= 1:
            self.current_frame = 0
            if auto: self.timer.stop()
        else:
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

    def get_view_limits(self):
        rect = self.get_active_rect()
        margin = 100
        
        # Expand limits to include lighting if active
        p = self.data.standard_params
        lr = int(p.get('lightradius') or 0)
        
        if not rect:
            l, r, t, b = 0, 0, 0, 0
        else:
            l, r, t, b = rect.left(), rect.right(), rect.top(), rect.bottom()
            
        if lr > 0:
            # Circle at cx,cy with radius lr
            cx, cy = self.get_light_center()
            l = min(l, cx - lr)
            r = max(r, cx + lr)
            t = min(t, cy - lr)
            b = max(b, cy + lr)
            
        return (l - margin, r + margin, t - margin, b + margin)

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
            
            new_px = self.pan_x + delta.x()
            new_py = self.pan_y + delta.y()

            # Logical limits
            l, r, t, b = self.get_view_limits()
            
            # Convert logical limits to pan limits (screen pixels)
            # Center (logical) = -pan / zoom
            # l <= -pan/zoom <= r  =>  -r*zoom <= pan <= -l*zoom
            
            min_px = -r * self.zoom
            max_px = -l * self.zoom
            min_py = -b * self.zoom
            max_py = -t * self.zoom
            
            self.pan_x = max(min_px, min(max_px, new_px))
            self.pan_y = max(min_py, min(max_py, new_py))

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
            elif self.hover_state == 'LIGHT':
                # Calculate new radius based on distance from center
                lx, ly = self.get_logical_pos(event.pos())
                cx, cy = self.get_light_center()
                import math
                dx = lx - cx
                dy = ly - cy
                new_radius = int(math.sqrt(dx*dx + dy*dy))
                p['lightradius'] = max(0, new_radius)
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
        elif state == 'LIGHT':
            self.setCursor(Qt.CursorShape.SizeAllCursor) # Or a diagonal cursor?
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def get_light_center(self):
        p = self.data.standard_params
        
        # Offsets
        lox = int(p.get('lightoffsetx') or 0)
        loy = int(p.get('lightoffsety') or 0)
        
        # Start at Hitbox Center (0, 0)
        cx = -lox
        cy = loy
        
        # Handle Direction (Mirroring)
        # If facing right (1), everything mirrors around X=0
        if self.show_direction == 1:
            cx = -cx
            
        return cx, cy

    def check_hover_edge(self, lx, ly):
        p = self.data.standard_params
        
        # Check Lighting Circle First (Outer layer)
        light_radius = int(p.get('lightradius') or 0)
        if light_radius > 0:
            cx, cy = self.get_light_center()
            import math
            # Distance from Light Center
            dx = lx - cx
            dy = ly - cy
            dist = math.sqrt(dx*dx + dy*dy)
            tol = 8 / self.zoom
            if tol < 2: tol = 2
            
            # Allow grabbing if close to radius
            if abs(dist - light_radius) < tol:
                return 'LIGHT'

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
        
        limit_l, limit_r, limit_t, limit_b = self.get_view_limits()
        
        draw_l = max(view_l, limit_l)
        draw_r = min(view_r, limit_r)
        draw_t = max(view_t, limit_t)
        draw_b = min(view_b, limit_b)

        grid_size = 16
        start_x = int(draw_l // grid_size) * grid_size
        end_x = int(draw_r // grid_size + 1) * grid_size
        start_y = int(draw_t // grid_size) * grid_size
        end_y = int(draw_b // grid_size + 1) * grid_size

        painter.setPen(QPen(self.grid_color, 0))
        for x in range(start_x, end_x + 1, grid_size):
            if x >= draw_l and x <= draw_r:
                painter.drawLine(x, int(draw_t), x, int(draw_b))
        for y in range(start_y, end_y + 1, grid_size):
            if y >= draw_t and y <= draw_b:
                painter.drawLine(int(draw_l), y, int(draw_r), y)

        # Origin Crosshair (Subtle Grey)
        painter.setPen(QPen(AppColors.GRID_CENTER, 0))
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
            painter.fillRect(hitbox_rect, AppColors.HITBOX_FILL)
        pen = QPen(AppColors.HITBOX_BORDER, 1) if self.is_hitbox_mode else QPen(AppColors.HITBOX_BORDER_DIM, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(hitbox_rect)

        # Lighting Circle
        light_radius = int(p.get('lightradius') or 0)
        if light_radius > 0:
            cx, cy = self.get_light_center()
            
            # Determine color
            c_str = p.get('lightcolor')
            fill_color = AppColors.LIGHT_FILL
            border_color = AppColors.LIGHT_BORDER
            
            if c_str:
                c_str = str(c_str).strip()
                # Parse customized color
                try:
                    if c_str.startswith("0x") and len(c_str) == 8:
                        r = int(c_str[2:4], 16)
                        g = int(c_str[4:6], 16)
                        b = int(c_str[6:8], 16)
                        # Create colors (Fill is semi-transparent)
                        fill_color = QColor(r, g, b, 100) 
                        border_color = QColor(r, g, b, 255)
                    elif c_str.startswith("#") or QColor.isValidColor(c_str):
                        c = QColor(c_str)
                        if c.isValid():
                            fill_color = QColor(c.red(), c.green(), c.blue(), 100)
                            border_color = c
                except:
                    # Fallback on error
                    pass

            painter.setBrush(fill_color)
            painter.setPen(QPen(border_color, 2 if self.hover_state == 'LIGHT' else 1))
            # Draw ellipse centered at cx, cy
            painter.drawEllipse(QRectF(cx - light_radius, cy - light_radius, light_radius*2, light_radius*2))
            painter.setBrush(Qt.BrushStyle.NoBrush) # Reset brush

        # Sprite
        if self.pixmap:
            painter.save()
            is_facing_right = (self.show_direction == 1)
            row_offset = 0
            if style == 0:
                # Style 0: Base is Left. Flip for Right.
                if is_facing_right: painter.scale(-1, 1)
            elif style >= 1:
                # Style >= 1: Top = Left, Bottom = Right (Standard SMBX)
                if is_facing_right:
                    row_offset = frames
                
                # Invert offset for Right facing
                if is_facing_right:
                    ox = -ox

            src_y = (row_offset + self.current_frame) * fh
            src_rect = QRect(0, src_y, fw, fh)
            
            dest_x = -fw / 2 + ox
            dest_y = (ph / 2) - fh + oy
            dest_rect = QRectF(dest_x, dest_y, fw, fh)

            painter.drawPixmap(dest_rect.toRect(), self.pixmap, src_rect)
            
            # GFX Box (Red)
            pen = QPen(AppColors.GFX_BORDER, 1) if not self.is_hitbox_mode else QPen(AppColors.GFX_BORDER_DIM, 1, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawRect(dest_rect)
            
            painter.restore()

        painter.restore()
        
        if self.pixmap:
            painter.save()
            painter.setOpacity(0.5)
            mw, mh = 300, 300
            scaled = self.pixmap.scaled(mw, mh, Qt.AspectRatioMode.KeepAspectRatio)
            x = self.width() - scaled.width() - 10
            y = 10
            painter.drawPixmap(x, y, scaled)
            painter.restore()

        # Info HUD
        painter.setPen(AppColors.TEXT_PRIMARY)
        mode_text = "[HITBOX MODE]" if self.is_hitbox_mode else "[GRAPHIC MODE]"
        info = f"{mode_text} | Frame: {self.current_frame + 1}/{frames} | Zoom: {self.zoom}x"
        painter.drawText(10, self.height() - 10, info)