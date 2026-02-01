# ui/screens/game_screen.py
from __future__ import annotations

import os
import pygame

from config import ROLES
from ui.screens.widgets import BASE_W, BASE_H, get_font


class GameScreen:
    """Beer Game play screen (multi-human on one machine).

    Controls
    - TAB: switch between human tiers
    - Type digits: enter order quantity
    - BACKSPACE: delete
    - ENTER or ORDER button: submit order for current tier

    The week automatically advances when all human tiers have submitted their orders.
    """

    def __init__(self, ui, sim):
        self.ui = ui
        self.sim = sim
        pygame.mouse.set_visible(True)

        # back icon (same asset as config screen)
        self.back_icon = None
        try:
            p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "back_button.png"))
            p2 = os.path.abspath(os.path.join(os.getcwd(), "assets", "back_button.png"))
            icon_path = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
            if icon_path:
                self.back_icon = pygame.image.load(icon_path).convert_alpha()
        except Exception:
            self.back_icon = None

        # SCM banner (top header background)
        self.scm_banner = None
        self._scm_banner_cache = None
        self._scm_banner_cache_size = None
        try:
            b1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "scm_banner.png"))
            b2 = os.path.abspath(os.path.join(os.getcwd(), "assets", "scm_banner.png"))
            banner_path = b1 if os.path.exists(b1) else (b2 if os.path.exists(b2) else None)
            if banner_path:
                self.scm_banner = pygame.image.load(banner_path).convert_alpha()
        except Exception:
            self.scm_banner = None

        self.human_roles = self._get_human_roles()
        if not self.human_roles:
            self.human_roles = [ROLES[0]]

        self.view_idx = 0
        self.view_role = self.human_roles[self.view_idx]

        # per-week input state
        self.order_text = {r: "" for r in self.human_roles}
        self.order_value = {r: 0 for r in self.human_roles}
        self.submitted = {r: False for r in self.human_roles}
        self.input_focused = True
        self.error_msg = ""
        self._last_week_seen = None

        # theme (flat, no shadows)
        self.bg = (245, 248, 250)
        self.card = (255, 255, 255)
        self.border = (220, 224, 230)
        self.title_col = (25, 40, 150)
        self.text = (30, 30, 30)
        self.muted = (110, 115, 125)
        self.teal = (0, 150, 136)
        self.red = (200, 40, 40)
        self.orange = (240, 140, 0)

        # layout (base coordinates)
        self.margin = 30
        self.gap = 25
        self.top_y = 130
        self.bottom_margin = 30

        total_h = BASE_H - self.top_y - self.bottom_margin
        left_w = 600
        right_w = BASE_W - 2 * self.margin - self.gap - left_w
        right_top_h = 270
        right_bottom_h = total_h - right_top_h - self.gap

        self.left_rect = pygame.Rect(self.margin, self.top_y, left_w, total_h)
        self.right_top_rect = pygame.Rect(self.left_rect.right + self.gap, self.top_y, right_w, right_top_h)
        self.right_bottom_rect = pygame.Rect(
            self.left_rect.right + self.gap, self.right_top_rect.bottom + self.gap, right_w, right_bottom_h
        )

        # back icon hitbox base (same size idea as config screen arrow button)
        self.back_icon_rect_base = pygame.Rect(30, 30, 72, 56)

        # inside left card
        self.order_input_rect = pygame.Rect(self.left_rect.x + 30, self.left_rect.y + 245, self.left_rect.w - 60, 58)
        self.order_btn_rect = pygame.Rect(self.left_rect.x + 30, self.left_rect.y + 310, self.left_rect.w - 60, 66)

    # ------------------------------------------------------------
    # Scaling helpers
    # ------------------------------------------------------------
    def _scale_info(self, surface):
        w, h = surface.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2
        return scale, ox, oy

    def _sr(self, rect, scale, ox, oy):
        return pygame.Rect(
            int(ox + rect.x * scale),
            int(oy + rect.y * scale),
            int(rect.w * scale),
            int(rect.h * scale),
        )

    def _get_back_icon_rect(self, surface, scale, ox, oy, week_text_surface):
        """
        Match config screen behavior: icon is aligned vertically with the title line.
        No background box; only the image is drawn.
        """
        base = self.back_icon_rect_base
        w = int(base.w * scale)
        h = int(base.h * scale)

        title_pos = (int(ox + 240 * scale), int(oy + 30 * scale))
        title_rect = week_text_surface.get_rect(topleft=title_pos)

        x = int(ox + base.x * scale)
        y = int(title_rect.centery - h // 2)
        return pygame.Rect(x, y, w, h)

    # ------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------
    def _get_human_roles(self):
        roles = []
        cm = getattr(self.sim, "control_mode", None)
        if isinstance(cm, dict):
            for r in ROLES:
                if cm.get(r) == "HUMAN":
                    roles.append(r)
        return roles

    def _get_state(self):
        return self.sim.get_state() if hasattr(self.sim, "get_state") else {}

    def _tier(self, state, role):
        tiers = state.get("tiers")
        if isinstance(tiers, dict):
            return tiers.get(role)
        return None

    def _get(self, obj, name, default=0.0):
        return getattr(obj, name, default) if obj is not None else default

    # ------------------------------------------------------------
    # Week reset
    # ------------------------------------------------------------
    def _reset_week_inputs(self):
        for r in self.human_roles:
            self.order_text[r] = ""
            self.order_value[r] = 0
            self.submitted[r] = False
        self.input_focused = True
        self.error_msg = ""
        # Reset to first human role at start of each week
        if self.human_roles:
            self.view_idx = 0
            self.view_role = self.human_roles[0]

    def _maybe_detect_new_week(self):
        state = self._get_state()
        wk = state.get("week")
        if wk is None:
            return
        if self._last_week_seen is None:
            self._last_week_seen = wk
            self._reset_week_inputs()
            return
        if wk != self._last_week_seen:
            self._last_week_seen = wk
            self._reset_week_inputs()

    # ------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------
    def _switch_view(self, direction=+1):
        if not self.human_roles:
            return
        self.view_idx = (self.view_idx + direction) % len(self.human_roles)
        self.view_role = self.human_roles[self.view_idx]
        self.input_focused = True
        self.error_msg = ""

    def _next_unsubmitted_role(self):
        for i, r in enumerate(self.human_roles):
            if not self.submitted.get(r, False):
                self.view_idx = i
                self.view_role = r
                return

    # ------------------------------------------------------------
    # Submit order + auto advance
    # ------------------------------------------------------------
    def _submit_current(self):
        role = self.view_role

        if self.submitted.get(role, False):
            self.error_msg = "Order already submitted for this tier."
            return

        txt = self.order_text.get(role, "").strip()
        if txt == "":
            self.error_msg = "Type an order quantity first."
            return

        try:
            val = int(txt)
        except ValueError:
            self.error_msg = "Order must be a number."
            return

        if val < 0:
            self.error_msg = "Order must be 0 or higher."
            return
        if val > 9999:
            self.error_msg = "Order too large."
            return

        self.order_value[role] = val
        self.submitted[role] = True
        self.error_msg = ""

        if not all(self.submitted.values()):
            self._next_unsubmitted_role()
            return

        orders = {r: 0 for r in ROLES}
        for r in ROLES:
            if r in self.human_roles:
                orders[r] = self.order_value[r]

        alive = True
        if hasattr(self.sim, "next_week"):
            alive = self.sim.next_week(orders)

        if not alive:
            self.ui.change_state("END")
            return

        self._last_week_seen = self._get_state().get("week", self._last_week_seen)
        self._reset_week_inputs()

    def _go_back(self):
        self.ui.change_state("CONFIG")

    # ------------------------------------------------------------
    # Events
    # ------------------------------------------------------------
    def handle_event(self, event):
        self._maybe_detect_new_week()

        # Touch support: convert finger tap to a click (and ignore any immediate mouse-emulated duplicate)
        now = pygame.time.get_ticks()
        if not hasattr(self, "_ignore_mouse_until_ms"):
            self._ignore_mouse_until_ms = 0
        if event.type == pygame.MOUSEBUTTONDOWN and now < self._ignore_mouse_until_ms:
            return
        if event.type == pygame.FINGERDOWN:
            self._ignore_mouse_until_ms = now + 300
            w, h = self.ui.screen.get_size()
            pos = (int(event.x * w), int(event.y * h))
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._switch_view(-1)
                else:
                    self._switch_view(+1)
                return

            if event.key == pygame.K_RETURN:
                self._submit_current()
                return

            if event.key == pygame.K_ESCAPE:
                self.input_focused = False
                return

            if self.input_focused and not self.submitted.get(self.view_role, False):
                if event.key == pygame.K_BACKSPACE:
                    self.order_text[self.view_role] = self.order_text[self.view_role][:-1]
                    return

                if event.unicode.isdigit():
                    if len(self.order_text[self.view_role]) < 6:
                        self.order_text[self.view_role] += event.unicode
                    return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            scale, ox, oy = self._scale_info(self.ui.screen)

            # recompute icon rect exactly like in draw (so clicks match)
            state = self._get_state()
            week = int(state.get("week", 1))
            dur = int(state.get("duration", 25))
            week_surf = get_font(52, scale, bold=True).render(f"Week {week}/{dur}", True, (20, 20, 20))
            back_icon_r = self._get_back_icon_rect(self.ui.screen, scale, ox, oy, week_surf)

            if back_icon_r.collidepoint(event.pos):
                self.ui.sound.play_click(3000)
                self._go_back()
                return

            input_r = self._sr(self.order_input_rect, scale, ox, oy)
            btn_r = self._sr(self.order_btn_rect, scale, ox, oy)

            if input_r.collidepoint(event.pos):
                self.input_focused = True
                return

            if btn_r.collidepoint(event.pos):
                self.ui.sound.play_click(3000)
                self._submit_current()
                return

            self.input_focused = False

    def update(self):
        self._maybe_detect_new_week()

    # ------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------
    def _draw_card(self, surf, rect, scale, ox, oy, title):
        r = self._sr(rect, scale, ox, oy)
        pygame.draw.rect(surf, self.card, r, border_radius=int(18 * scale))
        pygame.draw.rect(surf, self.border, r, width=max(1, int(2 * scale)), border_radius=int(18 * scale))
        if title:
            tf = get_font(28, scale, bold=True)
            tt = tf.render(title, True, self.title_col)
            surf.blit(tt, (r.x + int(18 * scale), r.y + int(14 * scale)))
        return r

    def _draw_row(self, surf, xL, xR, y, label, value, scale, color=None):
        lf = get_font(18, scale, bold=False)
        vf = get_font(20, scale, bold=True)
        surf.blit(lf.render(label, True, self.muted), (xL, y))
        txt = vf.render(str(value), True, color or self.text)
        surf.blit(txt, (xR - txt.get_width(), y))

    def draw(self, surface):
        self._maybe_detect_new_week()
        surface.fill(self.bg)
        scale, ox, oy = self._scale_info(surface)

        # --- Top SCM banner (fills header area) ---
        if self.scm_banner:
            target_w = int(BASE_W * scale)
            target_h = int(120 * scale)  # header band height
            key = (target_w, target_h)
            if self._scm_banner_cache is None or self._scm_banner_cache_size != key:
                img = self.scm_banner
                if img.get_width() > 0:
                    s = target_w / img.get_width()
                    scaled_h = max(1, int(img.get_height() * s))
                    scaled = pygame.transform.smoothscale(img, (target_w, scaled_h))
                    if scaled_h >= target_h:
                        y0 = (scaled_h - target_h) // 2
                        cropped = scaled.subsurface(pygame.Rect(0, y0, target_w, target_h)).copy()
                    else:
                        cropped = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                        cropped.blit(scaled, (0, (target_h - scaled_h) // 2))
                    cropped.set_alpha(110)  # keep UI readable
                    # subtle white veil to avoid text contrast issues
                    veil = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                    veil.fill((255, 255, 255, 130))
                    cropped.blit(veil, (0, 0))
                    self._scm_banner_cache = cropped
                    self._scm_banner_cache_size = key
            if self._scm_banner_cache:
                surface.blit(self._scm_banner_cache, (int(ox), int(oy)))

        state = self._get_state()
        week = int(state.get("week", 1))
        dur = int(state.get("duration", 25))

        role = self.view_role
        tier = self._tier(state, role)

        inv_start = int(self._get(tier, "inventory", 0))
        bl_start = int(self._get(tier, "backlog", 0))
        in_order = int(self._get(tier, "incoming_order", state.get("demand", 0) if role == "retailer" else 0))
        in_ship_now = int(self._get(tier, "incoming_ship_now", 0))
        in_ship_t1 = int(self._get(tier, "incoming_ship_t1", 0))
        in_ship_t2 = int(self._get(tier, "incoming_ship_t2", 0))

        need = bl_start + in_order
        ship_this_week = min(inv_start, need)
        inv_end = inv_start - ship_this_week
        order_handling = getattr(self.sim, "order_handling", "BACKORDER")
        bl_end = 0 if order_handling == "LOST_SALES" else max(0, need - ship_this_week)

        ch = float(getattr(self.sim, "cost_holding", 1.0))
        cb = float(getattr(self.sim, "cost_backorder", 2.0))
        cp = float(getattr(self.sim, "cost_production", 1.0))

        prod_qty = 0
        if role == "factory":
            if self.submitted.get(role, False):
                prod_qty = int(self.order_value.get(role) or 0)
            else:
                txt = (self.order_text.get(role, "") or "").strip()
                prod_qty = int(txt) if txt.isdigit() else 0

        holding_cost = ch * inv_end
        backlog_cost = cb * bl_end
        production_cost = cp * prod_qty if role == "factory" else 0.0
        total_cost_week = holding_cost + backlog_cost + production_cost

        holding_total = inv_start * ch
        backlog_total = float(self._get(tier, "backlog_cost_total", 0.0))
        cumulative_cost = float(self._get(tier, "cumulative_cost", 0.0))

        expected_next_inv = inv_end + in_ship_t1

        submitted_count = sum(1 for r in self.human_roles if self.submitted.get(r, False))
        total_humans = len(self.human_roles)

        # ---------------- Header ----------------
        week_surf = get_font(52, scale, bold=True).render(f"Week {week}/{dur}", True, (20, 20, 20))
        surface.blit(week_surf, (int(ox + 240 * scale), int(oy + 30 * scale)))

        subtitle = get_font(18, scale, bold=False).render(
            f"{role.capitalize()} view • submitted {submitted_count}/{total_humans} • TAB to switch tier",
            True,
            self.muted,
        )
        surface.blit(subtitle, (int(ox + 240 * scale), int(oy + 92 * scale)))

        # ✅ Icon-only back (no button box)
        back_icon_r = self._get_back_icon_rect(surface, scale, ox, oy, week_surf)
        if self.back_icon:
            icon = pygame.transform.smoothscale(self.back_icon, (back_icon_r.w, back_icon_r.h))
            surface.blit(icon, back_icon_r)
        else:
            # fallback: simple arrow (no box)
            cx, cy = back_icon_r.center
            s = int(14 * scale)
            pygame.draw.polygon(surface, (60, 60, 60), [(cx + s, cy - s), (cx - s, cy), (cx + s, cy + s)])

        # ---------------- Cards ----------------
        left_r = self._draw_card(surface, self.left_rect, scale, ox, oy, role.capitalize())
        rt_r = self._draw_card(surface, self.right_top_rect, scale, ox, oy, "Pipelines & Shipping")
        rb_r = self._draw_card(surface, self.right_bottom_rect, scale, ox, oy, "Totals & Next Week")

        # ---------------- Left card content ----------------
        xL = left_r.x + int(18 * scale)
        xR = left_r.right - int(18 * scale)

        y = left_r.y + int(62 * scale)
        surface.blit(get_font(22, scale, bold=True).render("This Week", True, self.text), (xL, y))
        y += int(34 * scale)
        pygame.draw.line(surface, self.border, (xL, y), (xR, y), width=max(1, int(2 * scale)))
        y += int(12 * scale)

        demand_label = {
            "retailer": "Customer demand",
            "distributor": "Retailer demand",
            "wholesaler": "Distributor demand",
            "factory": "Wholesaler demand",
        }.get(role, "Incoming demand")

        self._draw_row(surface, xL, xR, y, demand_label, f"{in_order} units", scale, self.teal)
        y += int(28 * scale)
        self._draw_row(surface, xL, xR, y, "Inventory", f"{inv_start} units", scale, self.teal)
        y += int(28 * scale)
        self._draw_row(surface, xL, xR, y, "Backlog", f"{bl_start} units", scale, self.red if bl_start > 0 else self.teal)

        y = left_r.y + int(210 * scale)
        surface.blit(get_font(22, scale, bold=True).render("Your Order", True, self.text), (xL, y))
        y += int(34 * scale)
        pygame.draw.line(surface, self.border, (xL, y), (xR, y), width=max(1, int(2 * scale)))

        input_r = self._sr(self.order_input_rect, scale, ox, oy)
        pygame.draw.rect(surface, (255, 255, 255), input_r, border_radius=int(12 * scale))
        pygame.draw.rect(
            surface,
            self.teal if self.input_focused else (170, 170, 170),
            input_r,
            width=max(1, int(2 * scale)),
            border_radius=int(12 * scale),
        )

        is_sub = self.submitted.get(role, False)
        cur_txt = self.order_text.get(role, "")
        tf = get_font(26, scale, bold=True)
        if is_sub:
            display = str(self.order_value.get(role, ""))
            tcol = (70, 70, 70)
        else:
            display = cur_txt
            tcol = (20, 20, 20)

        if display == "" and not is_sub:
            ph = get_font(22, scale, bold=False).render("Type order…", True, (160, 160, 160))
            surface.blit(ph, (input_r.x + int(14 * scale), input_r.y + int(14 * scale)))
        else:
            tx = tf.render(display, True, tcol)
            surface.blit(tx, (input_r.x + int(14 * scale), input_r.y + int(12 * scale)))
            if self.input_focused and not is_sub:
                if (pygame.time.get_ticks() // 400) % 2 == 0:
                    cx = input_r.x + int(14 * scale) + tx.get_width() + int(4 * scale)
                    pygame.draw.line(
                        surface,
                        (0, 0, 0),
                        (cx, input_r.y + int(10 * scale)),
                        (cx, input_r.bottom - int(10 * scale)),
                        max(1, int(2 * scale)),
                    )

        btn_r = self._sr(self.order_btn_rect, scale, ox, oy)
        btn_bg = self.teal if not is_sub else (200, 200, 200)
        pygame.draw.rect(surface, btn_bg, btn_r, border_radius=int(14 * scale))
        pygame.draw.rect(surface, (30, 30, 30), btn_r, width=max(1, int(2 * scale)), border_radius=int(14 * scale))
        bt2 = get_font(28, scale, bold=True).render("ORDER!", True, (255, 255, 255) if not is_sub else (50, 50, 50))
        surface.blit(bt2, bt2.get_rect(center=btn_r.center))

        if self.error_msg:
            err = get_font(18, scale, bold=True).render(self.error_msg, True, self.red)
            surface.blit(err, (input_r.x, input_r.bottom + int(28 * scale)))

        # ---------------- Right top: after-week + pipelines ----------------
        xL2 = rt_r.x + int(18 * scale)
        xR2 = rt_r.right - int(18 * scale)
        midX = (xL2 + xR2) // 2
        gapX = int(18 * scale)
        colL_L = xL2
        colL_R = midX - gapX // 2
        colR_L = midX + gapX // 2
        colR_R = xR2

        y2 = rt_r.y + int(62 * scale)
        surface.blit(get_font(20, scale, bold=True).render("After this week", True, self.text), (colL_L, y2))
        surface.blit(get_font(20, scale, bold=True).render("Pipeline", True, self.text), (colR_L, y2))
        y2 += int(30 * scale)
        pygame.draw.line(surface, self.border, (colL_L, y2), (colL_R, y2), width=max(1, int(2 * scale)))
        pygame.draw.line(surface, self.border, (colR_L, y2), (colR_R, y2), width=max(1, int(2 * scale)))
        y2 += int(12 * scale)

        yy = y2
        self._draw_row(surface, colL_L, colL_R, yy, "Ship", f"{ship_this_week} u", scale, self.teal)
        yy += int(26 * scale)
        self._draw_row(surface, colL_L, colL_R, yy, "Inv end", f"{inv_end} u", scale, self.teal)
        yy += int(26 * scale)
        self._draw_row(surface, colL_L, colL_R, yy, "Backlog end", f"{bl_end} u", scale, self.red if bl_end > 0 else self.teal)
        yy += int(26 * scale)
        self._draw_row(surface, colL_L, colL_R, yy, "Cost (this week)", f"{total_cost_week:.1f} €", scale, self.orange)

        yy2 = y2
        self._draw_row(surface, colR_L, colR_R, yy2, "Arriving t+1", f"{in_ship_t1} u", scale, self.teal)
        yy2 += int(26 * scale)
        self._draw_row(surface, colR_L, colR_R, yy2, "Arriving t+2", f"{in_ship_t2} u", scale, self.teal)
        yy2 += int(26 * scale)

        pygame.draw.line(
            surface,
            self.border,
            (colR_L, yy2 + int(8 * scale)),
            (colR_R, yy2 + int(8 * scale)),
            width=max(1, int(2 * scale)),
        )
        yy2 += int(22 * scale)

        last_ship = int(self._get(tier, "incoming_ship_now", 0))
        last_order = int(self._get(tier, "order_last", 0))
        self._draw_row(surface, colR_L, colR_R, yy2, "Last shipped", f"{last_ship} u", scale, self.teal)
        yy2 += int(26 * scale)
        self._draw_row(surface, colR_L, colR_R, yy2, "Last ordered", f"{last_order} u", scale, self.title_col)

        prog_y = rt_r.bottom - int(55 * scale)
        surface.blit(get_font(18, scale).render("Progress", True, self.muted), (xL2, prog_y))
        pr = pygame.Rect(xL2, prog_y + int(22 * scale), rt_r.w - int(36 * scale), int(10 * scale))
        pygame.draw.rect(surface, (220, 220, 220), pr, border_radius=int(999 * scale))
        filled = int(pr.w * min(max(week / max(dur, 1), 0), 1))
        pygame.draw.rect(surface, self.teal, pygame.Rect(pr.x, pr.y, filled, pr.h), border_radius=int(999 * scale))

        # ---------------- Right bottom: totals & next week ----------------
        xL3 = rb_r.x + int(18 * scale)
        xR3 = rb_r.right - int(18 * scale)
        y3 = rb_r.y + int(70 * scale)

        self._draw_row(surface, xL3, xR3, y3, "Total holding cost", f"{holding_total:.1f} €", scale, self.teal)
        y3 += int(28 * scale)
        self._draw_row(surface, xL3, xR3, y3, "Total backlog cost", f"{backlog_total:.1f} €", scale, self.red)
        y3 += int(28 * scale)
        self._draw_row(surface, xL3, xR3, y3, "Total cost so far", f"{cumulative_cost:.1f} €", scale, self.orange)

        pygame.draw.line(
            surface,
            self.border,
            (xL3, y3 + int(18 * scale)),
            (xR3, y3 + int(18 * scale)),
            width=max(1, int(2 * scale)),
        )
        y3 += int(34 * scale)

        surface.blit(get_font(22, scale, bold=True).render("Start of Next Week", True, self.text), (xL3, y3))
        y3 += int(30 * scale)
        big = get_font(54, scale, bold=True).render(str(expected_next_inv), True, self.teal)
        surface.blit(big, (xL3, y3))
        surface.blit(
            get_font(20, scale).render("units (expected inventory)", True, self.muted),
            (xL3 + big.get_width() + int(12 * scale), y3 + int(18 * scale)),
        )

        eq = get_font(16, scale).render(f"= {inv_end} (end) + {in_ship_t1} (arriving t+1)", True, self.muted)
        surface.blit(eq, (xL3, rb_r.bottom - int(32 * scale)))
