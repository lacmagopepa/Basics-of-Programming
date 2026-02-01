import os
import pygame
from typing import Tuple, Any

from ui.screens.widgets import Button, Label, IconTextButton, BASE_W, BASE_H


def _fit_image(img: pygame.Surface, target_size: Tuple[int, int], mode: str = "cover") -> Tuple[pygame.Surface, pygame.Rect]:
    """Scale an image to fit target_size while keeping aspect ratio.

    mode:
      - "cover": fill the target completely (may crop edges)
      - "contain": fully visible (may letterbox)

    Returns: (scaled_surface, rect_centered_in_target)
    """
    tw: int
    th: int
    tw, th = target_size
    iw: int
    ih: int
    iw, ih = img.get_size()
    if iw <= 0 or ih <= 0:
        rect = img.get_rect(center=(tw // 2, th // 2))
        return img, rect

    sx: float = tw / iw
    sy: float = th / ih
    scale: float = max(sx, sy) if mode == "cover" else min(sx, sy)

    new_w: int = max(1, int(iw * scale))
    new_h: int = max(1, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
    rect = scaled.get_rect(center=(tw // 2, th // 2))
    return scaled, rect


class LoginScreen:
    def __init__(self, ui: Any):
        self.ui = ui
        self.screen = ui.screen

        # -----------------------------
        # Optional full-screen background image
        # Put your image in assets/ (recommended filename: start_bg.png)
        # -----------------------------
        self.bg_original = None
        for path in [
            "assets/start_bg.png",
            "assets/login_bg.png",
            "assets/login_bg.jpg",
            "assets/start_bg.jpg",
            "assets/beer_bg.jpg",
            "assets/background.png",
            "./assets/start_bg.png",
            "./assets/login_bg.png",
            "./assets/login_bg.jpg",
        ]:
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    self.bg_original = img.convert_alpha() if img.get_alpha() else img.convert()
                except Exception:
                    self.bg_original = None
                break

        # cache to avoid re-scaling every frame
        self._bg_cache_size = None
        self._bg_scaled = None
        self._bg_rect = None
        self.bg_mode = "cover"  # change to "contain" if you don't want cropping

        # -----------------------------
        # Load cup icon
        # -----------------------------
        self.icon_original = None
        for path in ["assets/cup.png", "./assets/cup.png", "../assets/cup.png"]:
            if os.path.exists(path):
                try:
                    self.icon_original = pygame.image.load(path).convert_alpha()
                except:
                    self.icon_original = None
                break

        # -----------------------------
        # Title (centered)
        # -----------------------------
        self.title_label = Label(
            (BASE_W / 2, 120),
            "BEER GAME 2.0",
            size=64,
            bold=True
        )

        # -----------------------------
        # Buttons (logical positions)
        # -----------------------------
        self.play_button = Button(
            (BASE_W / 2 - 180, BASE_H / 2 + 140, 360, 70),
            "PLAY GAME",
            self.go_to_login,
            font_size=32
        )

        self.about_button = Button(
            (BASE_W / 2 - 180, BASE_H / 2 + 240, 360, 70),
            "ABOUT",
            self.go_to_about,
            font_size=32
        )

        # Modern QUIT (icon + text)
        self.quit_button = IconTextButton(
            (BASE_W / 2, BASE_H - 30),
            "QUIT",
            self.quit_game,
            font_size=22
        )

        # Sound toggle button (bottom right)
        self.sound_button = Button(
            (BASE_W - 120, BASE_H - 80, 100, 50),
            self.get_sound_text(),
            self.toggle_sound,
            font_size=24
        )

    # -----------------------------
    # Navigation
    # -----------------------------
    def go_to_login(self):
        self.ui.change_state("LOGIN_AUTH")

    def go_to_about(self):
        self.ui.change_state("ABOUT")

    def quit_game(self):
        pygame.quit()
        exit()
    def get_sound_text(self):
        return "MUTE" if self.ui.sound.muted else "SOUND"

    def toggle_sound(self):
        self.ui.sound.toggle_mute()
        self.sound_button.text = self.get_sound_text()
    # -----------------------------
    # Event Handling
    # -----------------------------
    def handle_event(self, event):
        self.play_button.handle_event(event)
        self.about_button.handle_event(event)
        self.quit_button.handle_event(event)
        self.sound_button.handle_event(event)

    def update(self):
        pass

    # -----------------------------
    # Draw everything
    # -----------------------------
    def draw(self, surface):
        # Background
        if self.bg_original is not None:
            size = surface.get_size()
            if self._bg_cache_size != size or self._bg_scaled is None:
                self._bg_scaled, self._bg_rect = _fit_image(self.bg_original, size, mode=self.bg_mode)
                self._bg_cache_size = size
            surface.blit(self._bg_scaled, self._bg_rect)
        else:
            surface.fill((245, 248, 248))

        w, h = surface.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        # Title
        self.title_label.draw(surface, center=True)

        # Cup circle (kept as foreground element)
        cx = ox + (BASE_W / 2) * scale
        cy = oy + (BASE_H / 2 - 60) * scale

        pygame.draw.circle(surface, (200, 240, 240), (int(cx), int(cy)), int(130 * scale))
        pygame.draw.circle(surface, (180, 50, 50), (int(cx), int(cy)), int(115 * scale))


        # Draw cup icon (fill the circle completely + clip to circle)
        if self.icon_original:
            inner_r = int(115 * scale)          # same radius you used for the red circle
            diam = max(1, inner_r * 2)

            iw, ih = self.icon_original.get_size()

            # "cover" scale => fills the circle, may crop
            s = max(diam / iw, diam / ih)
            new_w = max(1, int(iw * s))
            new_h = max(1, int(ih * s))
            icon = pygame.transform.smoothscale(self.icon_original, (new_w, new_h))

            # canvas exactly the circle size
            circle_img = pygame.Surface((diam, diam), pygame.SRCALPHA)

            # center the scaled icon on that canvas (cropping happens automatically)
            x = (diam - new_w) // 2
            y = (diam - new_h) // 2
            circle_img.blit(icon, (x, y))

            # circular alpha mask
            mask = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (inner_r, inner_r), inner_r)
            circle_img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # draw onto main surface centered in the circle
            surface.blit(circle_img, circle_img.get_rect(center=(int(cx), int(cy))))



        # Buttons
        self.play_button.draw(surface)
        self.about_button.draw(surface)

        # QUIT (icon + text)
        self.quit_button.draw(surface)

        # Sound button
        self.sound_button.draw(surface)
