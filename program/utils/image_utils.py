from PyQt6.QtGui import QImage, QPixmap, QColor

def load_legacy_sprite(img_path: str, mask_path: str) -> QPixmap:
    """
    Combines a source image and mask using the Moondust/PGE logic.
    Simulates legacy BitBlt SRCAND / SRCPAINT rendering.
    """
    # Load images and ensure they are in a manipulatable 32-bit format
    front = QImage(img_path).convertToFormat(QImage.Format.Format_ARGB32)
    mask = QImage(mask_path).convertToFormat(QImage.Format.Format_ARGB32)
    
    img_w, img_h = front.width(), front.height()
    mask_w, mask_h = mask.width(), mask.height()

    # SMBX typically assumes a white background during the blit simulation 
    bg_r, bg_g, bg_b = 255, 255, 255

    # Process per pixel
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
            res_r = (m_r & bg_r) | f_r
            res_g = (m_g & bg_g) | f_g
            res_b = (m_b & bg_b) | f_b

            # 4. Calculate Alpha
            m_avg = (m_r + m_g + m_b) // 3
            new_alpha = 255 - m_avg

            # Moondust Threshold: Almost white mask becomes fully transparent
            if m_r > 240 and m_g > 240 and m_b > 240:
                new_alpha = 0

            # 5. Enhance Alpha based on Source brightness 
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
