import os
import pygame
from ui.screens.widgets import Label, Button, get_font, BASE_W, BASE_H


def _fit_image(img: pygame.Surface, target_size, mode: str = "cover"):
    """Scale an image to fit target_size while keeping aspect ratio.

    mode:
      - "cover": fill the target completely (may crop edges)
      - "contain": fully visible (may letterbox)

    Returns: (scaled_surface, rect_centered_in_target)
    """
    tw, th = target_size
    iw, ih = img.get_size()
    if iw <= 0 or ih <= 0:
        rect = img.get_rect(center=(tw // 2, th // 2))
        return img, rect

    sx = tw / iw
    sy = th / ih
    scale = max(sx, sy) if mode == "cover" else min(sx, sy)

    new_w = max(1, int(iw * scale))
    new_h = max(1, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
    rect = scaled.get_rect(center=(tw // 2, th // 2))
    return scaled, rect


class AuthScreen:
    def __init__(self, ui):
        self.ui = ui
        self.screen = ui.screen

        pygame.mouse.set_visible(True)  # ensure mouse cursor is visible

        # -----------------------------
        # Optional full-screen background image for the AUTH (login) screen
        # Put your image in assets/ (recommended filename: auth_bg.png)
        # -----------------------------
        self.bg_original = None
        for path in [
            "assets/auth_bg.png",
            "./assets/auth_bg.png",
            "assets/login_bg.png",
            "assets/login_bg.jpg",
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

        # Text input data
        self.username = ""
        self.password = ""
        self.active = None   # "user", "pass", or None

        # Logical coordinates (responsive)
        self.user_rect_log = pygame.Rect(BASE_W / 2 - 200, 250, 400, 60)
        self.pass_rect_log = pygame.Rect(BASE_W / 2 - 200, 360, 400, 60)

        self.error = ""

        self.login_button = Button(
            (BASE_W / 2 - 120, 480, 240, 65),
            "Login",
            self.try_login,
            font_size=32
        )

        self.back_button = Button(
            (30, 30, 120, 50),
            "Back",
            self.go_back,
            font_size=24
        )

    # ---------------------------------------------------
    # Scale logical rectangles into real window rectangles
    # ---------------------------------------------------
    def _scaled_rects(self, surface):
        w, h = surface.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        user_r = pygame.Rect(
            int(ox + self.user_rect_log.x * scale),
            int(oy + self.user_rect_log.y * scale),
            int(self.user_rect_log.w * scale),
            int(self.user_rect_log.h * scale)
        )

        pass_r = pygame.Rect(
            int(ox + self.pass_rect_log.x * scale),
            int(oy + self.pass_rect_log.y * scale),
            int(self.pass_rect_log.w * scale),
            int(self.pass_rect_log.h * scale)
        )

        return user_r, pass_r, scale

    # ---------------------------------------------------
    # Login attempt
    # ---------------------------------------------------
    def try_login(self):
        if self.username == "beer" and self.password == "beer":
            print("[DEBUG] Login success → switching to CONFIG")
            try:
                self.ui.change_state("CONFIG")
            except Exception as e:
                print("[ERROR] Failed to switch to CONFIG:", e)
        else:
            self.error = "Incorrect username or password"

    def go_back(self):
        self.ui.change_state("START")
    # ---------------------------------------------------
    # Handle typing and clicking
    # ---------------------------------------------------
    def handle_event(self, event):
        # Input boxes
        user_r, pass_r, scale = self._scaled_rects(self.screen)

        self.login_button.handle_event(event)
        self.back_button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if user_r.collidepoint(event.pos):
                self.active = "user"
            elif pass_r.collidepoint(event.pos):
                self.active = "pass"
            else:
                self.active = None

        if event.type == pygame.KEYDOWN:

            # -------------------------
            # TAB KEY → Switch focus
            # -------------------------
            if event.key == pygame.K_TAB:
                if self.active == "user":
                    self.active = "pass"
                elif self.active == "pass":
                    self.active = None  # optional: press tab again to leave fields
                else:
                    self.active = "user"
                return  # do not insert tab character

            # -------------------------
            # Typing inside active field
            # -------------------------
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    if self.active == "user":
                        self.username = self.username[:-1]
                    else:
                        self.password = self.password[:-1]

                elif event.key == pygame.K_RETURN:
                    self.try_login()

                elif event.unicode.isprintable():
                    if self.active == "user":
                        self.username += event.unicode
                    else:
                        self.password += event.unicode



        # Login button
        self.login_button.handle_event(event)

    def update(self):
        pass

    # ---------------------------------------------------
    # Draw the whole login screen
    # ---------------------------------------------------
    def draw(self, surface):
        # Background
        if self.bg_original is not None:
            size = surface.get_size()
            if self._bg_cache_size != size or self._bg_scaled is None:
                self._bg_scaled, self._bg_rect = _fit_image(self.bg_original, size, mode=self.bg_mode)
                self._bg_cache_size = size
            surface.blit(self._bg_scaled, self._bg_rect)

            # Slight white veil so the form remains readable on busy images
            veil = pygame.Surface(size, pygame.SRCALPHA)
            veil.fill((255, 255, 255, 70))
            surface.blit(veil, (0, 0))
        else:
            surface.fill((235, 235, 235))

        w, h = surface.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2

        # Optional semi-transparent card behind the login UI
        card_log = pygame.Rect(BASE_W / 2 - 290, 175, 580, 420)
        card = pygame.Rect(
            int(ox + card_log.x * scale),
            int(oy + card_log.y * scale),
            int(card_log.w * scale),
            int(card_log.h * scale),
        )
        card_surf = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
        card_surf.fill((255, 255, 255, 220))
        surface.blit(card_surf, card.topleft)
        pygame.draw.rect(surface, (210, 216, 222), card, width=max(1, int(2 * scale)), border_radius=max(10, int(16 * scale)))

        # Title
        title = Label((BASE_W / 2, 120), "Login", size=60, bold=True)
        title.draw(surface, center=True)

        # Get scaled rectangles
        user_r, pass_r, scale = self._scaled_rects(surface)

        # Fonts
        label_font = get_font(30, scale, bold=False)
        text_font = get_font(28, scale)

        # ----------------------------
        # USERNAME FIELD
 
        label_surface = label_font.render("Username:", True, (0, 0, 0))
        surface.blit(label_surface, (user_r.x, user_r.y - int(40 * scale)))

        pygame.draw.rect(surface, (255, 255, 255), user_r, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0), user_r, 2, border_radius=12)

        # Draw input text
        text_surface = text_font.render(self.username, True, (0, 0, 0))
        surface.blit(text_surface, (user_r.x + int(12 * scale), user_r.y + int(15 * scale)))

        # Blinking cursor
        if self.active == "user":
            cursor_x = user_r.x + int(12 * scale) + text_surface.get_width()
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, (0, 0, 0),
                                 (cursor_x, user_r.y + int(12 * scale)),
                                 (cursor_x, user_r.y + user_r.height - int(12 * scale)),
                                 max(1, int(2 * scale)))

        # ----------------------------
        # PASSWORD FIELD
    
        label_surface = label_font.render("Password:", True, (0, 0, 0))
        surface.blit(label_surface, (pass_r.x, pass_r.y - int(40 * scale)))

        pygame.draw.rect(surface, (255, 255, 255), pass_r, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0), pass_r, 2, border_radius=12)

        masked = "*" * len(self.password)
        text_surface = text_font.render(masked, True, (0, 0, 0))
        surface.blit(text_surface, (pass_r.x + int(12 * scale), pass_r.y + int(15 * scale)))

        if self.active == "pass":
            cursor_x = pass_r.x + int(12 * scale) + text_surface.get_width()
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                pygame.draw.line(surface, (0, 0, 0),
                                 (cursor_x, pass_r.y + int(12 * scale)),
                                 (cursor_x, pass_r.y + pass_r.height - int(12 * scale)),
                                 max(1, int(2 * scale)))

        # ----------------------------
        # ERROR MESSAGE
        if self.error:
            err_font = get_font(26, scale, bold=True)
            err_surface = err_font.render(self.error, True, (180, 0, 0))
            surface.blit(err_surface, (w // 2 - err_surface.get_width() // 2, pass_r.y + int(80 * scale)))

        # ----------------------------
        # LOGIN BUTTON
  
        self.login_button.draw(surface)

        # ----------------------------
        # BACK BUTTON
        self.back_button.draw(surface)
