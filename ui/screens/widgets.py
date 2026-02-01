import pygame
import os
from typing import Dict, Tuple

from ui.sound_manager import sound

# Logical resolution for scaling
BASE_W: int = 1280
BASE_H: int = 720

_font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}

def get_font(size: int = 24, scale: float = 1.0, bold: bool = False) -> pygame.font.Font:
    """Return a scaled pygame font."""
    pixel_size = max(12, int(size * scale))
    key = (pixel_size, bold)

    if key not in _font_cache:
        font = pygame.font.Font(None, pixel_size)
        font.set_bold(bold)
        _font_cache[key] = font

    return _font_cache[key]


class Button:
    def __init__(self, logical_rect: Tuple[float, float, float, float], text: str, callback, font_size: int = 26):
        """
        logical_rect = (x, y, w, h) expressed in 1280×720 units.
        This button is full rectangle button (PLAY GAME, ABOUT)
        """
        self.logical_rect = pygame.Rect(logical_rect)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.hover = False
        self.actual_rect = self.logical_rect.copy()

    def _update_rect(self, surf):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        self.actual_rect = pygame.Rect(
            int(ox + self.logical_rect.x * scale),
            int(oy + self.logical_rect.y * scale),
            int(self.logical_rect.w * scale),
            int(self.logical_rect.h * scale)
        )
        return scale

    def handle_event(self, event):
        # Hover (mouse only)
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.actual_rect.collidepoint(event.pos)

        # Touch / pen
        if event.type == pygame.FINGERDOWN:
            sound.note_finger_event()
            surf = pygame.display.get_surface()
            if surf is None:
                return
            sw, sh = surf.get_size()
            pos = (int(event.x * sw), int(event.y * sh))
            if self.actual_rect.collidepoint(pos):
                sound.play_click(3000)
                self.callback()
            return

        # Mouse click (ignore duplicates immediately after touch)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if sound.should_ignore_mouse_after_finger():
                return
            if self.actual_rect.collidepoint(event.pos):
                sound.play_click(3000)
                self.callback()

    def draw(self, surf):
        scale = self._update_rect(surf)

        # Style
        bg_normal = (220, 220, 220)
        bg_hover = (180, 240, 200)

        color = bg_hover if self.hover else bg_normal

        pygame.draw.rect(surf, color, self.actual_rect, border_radius=12)
        pygame.draw.rect(surf, (0, 0, 0), self.actual_rect, 2, border_radius=12)

        font = get_font(self.font_size, scale)
        txt = font.render(self.text, True, (0, 0, 0))
        surf.blit(txt, txt.get_rect(center=self.actual_rect.center))


class Label:
    def __init__(self, logical_pos: Tuple[float, float], text: str, size: int = 24, color: Tuple[int, int, int] = (0, 0, 0), bold: bool = False):
        self.logical_pos = logical_pos
        self.text = text
        self.size = size
        self.color = color
        self.bold = bold

    def draw(self, surf, center=False):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        font = get_font(self.size, scale, bold=self.bold)
        txt = font.render(self.text, True, self.color)

        lx = ox + self.logical_pos[0] * scale
        ly = oy + self.logical_pos[1] * scale

        rect = txt.get_rect()

        if center:
            rect.center = (lx, ly)
        else:
            rect.topleft = (lx, ly)

        surf.blit(txt, rect)


class IconTextButton:
    """
    Minimalistic button: icon + text (for QUIT).
    Looks exactly like your screenshot “× QUIT”.
    """
    def __init__(self, logical_center_pos: Tuple[float, float], text: str, callback, font_size: int = 26):
        self.logical_center = logical_center_pos
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.hover = False
        self.actual_rect = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.actual_rect:
            self.hover = self.actual_rect.collidepoint(event.pos)

        if event.type == pygame.FINGERDOWN:
            sound.note_finger_event()
            if not self.actual_rect:
                return
            surf = pygame.display.get_surface()
            if surf is None:
                return
            sw, sh = surf.get_size()
            pos = (int(event.x * sw), int(event.y * sh))
            if self.actual_rect.collidepoint(pos):
                sound.play_click(3000)
                self.callback()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if sound.should_ignore_mouse_after_finger():
                return
            if self.actual_rect and self.actual_rect.collidepoint(event.pos):
                sound.play_click(3000)
                self.callback()

    def draw(self, surf):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        font = get_font(self.font_size, scale)
        color = (110, 120, 130) if not self.hover else (70, 80, 90)

        # Render icon + text
        icon = font.render("×", True, color)
        label = font.render(self.text, True, color)

        spacing = int(10 * scale)
        total_width = icon.get_width() + spacing + label.get_width()

        # Convert logical coordinates to scaled ones
        cx = ox + self.logical_center[0] * scale
        cy = oy + self.logical_center[1] * scale

        x = cx - total_width // 2
        y = cy

        icon_rect = icon.get_rect(topleft=(x, y))
        label_rect = label.get_rect(topleft=(x + icon.get_width() + spacing, y))

        surf.blit(icon, icon_rect)
        surf.blit(label, label_rect)

        # Clickable area covers both icon + label
        self.actual_rect = icon_rect.union(label_rect)


class ImageButton:
    def __init__(self, logical_rect, image_path, callback):
        """
        logical_rect = (x, y, w, h) expressed in 1280×720 units.
        This button uses an image instead of text.
        """
        self.logical_rect = pygame.Rect(logical_rect)
        self.image_path = image_path
        self.callback = callback
        self.hover = False
        self.actual_rect = self.logical_rect.copy()
        self.image = None
        self.load_image()

    def load_image(self):
        if os.path.exists(self.image_path):
            try:
                self.image = pygame.image.load(self.image_path).convert_alpha()
            except:
                self.image = None
        else:
            self.image = None

    def _update_rect(self, surf):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        self.actual_rect = pygame.Rect(
            int(ox + self.logical_rect.x * scale),
            int(oy + self.logical_rect.y * scale),
            int(self.logical_rect.w * scale),
            int(self.logical_rect.h * scale)
        )
        return scale

    def handle_event(self, event):
        # Hover (mouse only)
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.actual_rect.collidepoint(event.pos)

        # Touch / pen
        if event.type == pygame.FINGERDOWN:
            sound.note_finger_event()
            surf = pygame.display.get_surface()
            if surf is None:
                return
            sw, sh = surf.get_size()
            pos = (int(event.x * sw), int(event.y * sh))
            if self.actual_rect.collidepoint(pos):
                sound.play_click(3000)
                self.callback()
            return

        # Mouse click (ignore duplicates immediately after touch)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if sound.should_ignore_mouse_after_finger():
                return
            if self.actual_rect.collidepoint(event.pos):
                sound.play_click(3000)
                self.callback()

    def draw(self, surf):
        scale = self._update_rect(surf)

        # Style background if no image
        if self.image is None:
            bg_normal = (220, 220, 220)
            bg_hover = (180, 240, 200)
            color = bg_hover if self.hover else bg_normal
            pygame.draw.rect(surf, color, self.actual_rect, border_radius=12)
            pygame.draw.rect(surf, (0, 0, 0), self.actual_rect, 2, border_radius=12)
        else:
            # Draw image scaled to fit
            img_w, img_h = self.image.get_size()
            rect_w, rect_h = self.actual_rect.size
            img_scale = min(rect_w / img_w, rect_h / img_h)
            new_w = int(img_w * img_scale)
            new_h = int(img_h * img_scale)
            scaled_img = pygame.transform.smoothscale(self.image, (new_w, new_h))
            img_rect = scaled_img.get_rect(center=self.actual_rect.center)
            surf.blit(scaled_img, img_rect)

            # Optional border
            pygame.draw.rect(surf, (0, 0, 0), self.actual_rect, 2, border_radius=12)
