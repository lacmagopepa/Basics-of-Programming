# ui/screens/analysis_screen.py
from __future__ import annotations

import pygame

from config import ROLES
from ui.screens.widgets import BASE_W, BASE_H, get_font, Button
from persistence.analysis_tools import compute_report
from persistence.csv_export import export_csv


class AnalysisScreen:
    """Simple time-series analysis view (TAB cycles roles)."""

    def __init__(self, ui):
        self.ui = ui
        self.report = compute_report()
        self.role_idx = 0
        self.role = ROLES[self.role_idx]

        self.msg = ""
        self.msg_t = 0

        # buttons in BASE coordinates
        self.back_btn = Button((40, 40, 180, 60), "Results", self.go_back)
        self.export_btn = Button((BASE_W - 260, 40, 220, 60), "Export CSV", self.export)

        self.bg = (245, 248, 250)
        self.card = (255, 255, 255)
        self.border = (220, 224, 230)
        self.title = (25, 40, 150)
        self.text = (40, 40, 40)
        self.muted = (110, 115, 125)
        self.teal = (0, 150, 136)
        self.red = (200, 40, 40)
        self.orange = (240, 140, 0)

    def go_back(self):
        self.ui.change_state("END")

    def export(self):
        p = export_csv()
        self.msg = f"Saved: {p}"
        self.msg_t = pygame.time.get_ticks()

    def handle_event(self, event):
        self.back_btn.handle_event(event)
        self.export_btn.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.role_idx = (self.role_idx + 1) % len(ROLES)
                self.role = ROLES[self.role_idx]

    def update(self):
        pass

    def _scale(self, surf):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2
        return scale, ox, oy

    def _srect(self, rect, scale, ox, oy):
        return pygame.Rect(
            int(ox + rect[0] * scale),
            int(oy + rect[1] * scale),
            int(rect[2] * scale),
            int(rect[3] * scale),
        )

    def _draw_card(self, surf, rect, scale, ox, oy, title):
        r = self._srect(rect, scale, ox, oy)
        pygame.draw.rect(surf, self.card, r, border_radius=int(18 * scale))
        pygame.draw.rect(surf, self.border, r, width=max(1, int(2 * scale)), border_radius=int(18 * scale))
        t = get_font(26, scale, bold=True).render(title, True, self.title)
        surf.blit(t, (r.x + int(18 * scale), r.y + int(14 * scale)))
        return r

    def _draw_line_chart(self, surf, rect, scale, series, colors, y_label=""):
        """series: dict(name->list), all lists same length"""
        r = rect
        left = r.x + int(18 * scale)
        top = r.y + int(60 * scale)
        right = r.right - int(18 * scale)
        # leave extra space for x-axis week labels
        bottom = r.bottom - int(34 * scale)

        # axis box
        pygame.draw.rect(surf, (250, 250, 250), (left, top, right - left, bottom - top), border_radius=int(12 * scale))
        pygame.draw.rect(
            surf,
            self.border,
            (left, top, right - left, bottom - top),
            width=max(1, int(2 * scale)),
            border_radius=int(12 * scale),
        )

        # find bounds
        all_vals = []
        n = 0
        for _, vals in series.items():
            vals = list(vals)
            n = max(n, len(vals))
            all_vals.extend([float(v) for v in vals])
        if n < 2 or not all_vals:
            return

        vmin = min(all_vals)
        vmax = max(all_vals)
        if vmax == vmin:
            vmax = vmin + 1.0

        def xy(i, v):
            x = left + int((right - left) * (i / (n - 1)))
            y = bottom - int((bottom - top) * ((float(v) - vmin) / (vmax - vmin)))
            return x, y

        # --- X axis: week numbers (0..n-1) ---
        # smart label step so text doesn't overlap too much
        if n <= 26:
            step = 1
        elif n <= 52:
            step = 2
        else:
            step = 5

        axis_col = (160, 160, 160)
        pygame.draw.line(surf, axis_col, (left, bottom), (right, bottom), width=max(1, int(2 * scale)))

        tick_h = int(6 * scale)
        tf = get_font(14, scale, bold=False)
        for i in range(0, n, step):
            x = left + int((right - left) * (i / (n - 1)))
            pygame.draw.line(surf, axis_col, (x, bottom), (x, bottom + tick_h), width=max(1, int(2 * scale)))
            lab = tf.render(str(i), True, self.muted)
            surf.blit(lab, lab.get_rect(midtop=(x, bottom + tick_h + int(2 * scale))))

        # always show last week label
        if (n - 1) % step != 0 and n >= 2:
            i = n - 1
            x = left + int((right - left) * (i / (n - 1)))
            pygame.draw.line(surf, axis_col, (x, bottom), (x, bottom + tick_h), width=max(1, int(2 * scale)))
            lab = tf.render(str(i), True, self.muted)
            surf.blit(lab, lab.get_rect(midtop=(x, bottom + tick_h + int(2 * scale))))

        xl = get_font(16, scale, bold=False).render("Week", True, self.muted)
        surf.blit(xl, xl.get_rect(midtop=((left + right) // 2, bottom + tick_h + int(22 * scale))))

        # y label
        if y_label:
            lab = get_font(18, scale, bold=False).render(y_label, True, self.muted)
            surf.blit(lab, (left, top - int(24 * scale)))

        # draw lines
        for idx, (name, vals) in enumerate(series.items()):
            col = colors[idx % len(colors)]
            pts = [xy(i, v) for i, v in enumerate(vals[:n])]
            if len(pts) >= 2:
                pygame.draw.lines(surf, col, False, pts, width=max(1, int(3 * scale)))
            # legend
            leg = get_font(18, scale, bold=True).render(name, True, col)
            surf.blit(leg, (left + int(8 * scale), top + int(8 * scale) + idx * int(22 * scale)))

    def draw(self, surface):
        surface.fill(self.bg)
        scale, ox, oy = self._scale(surface)

        # title
        tt = get_font(42, scale, bold=True).render("Analysis", True, (20, 20, 20))
        surface.blit(tt, (int(ox + 250 * scale), int(oy + 42 * scale)))
        st = get_font(18, scale).render(f"TAB to switch tier • Current: {self.role.capitalize()}", True, self.muted)
        surface.blit(st, (int(ox + 250 * scale), int(oy + 100 * scale)))

        self.back_btn.draw(surface)
        self.export_btn.draw(surface)

        if not self.report:
            msg = get_font(24, scale, bold=True).render("No log data yet. Play a game first.", True, (150, 0, 0))
            surface.blit(msg, (int(ox + 250 * scale), int(oy + 180 * scale)))
            return

        # cards
        c1 = self._draw_card(surface, (40, 150, 1200, 170), scale, ox, oy, "Demand vs Orders")
        c2 = self._draw_card(surface, (40, 335, 1200, 170), scale, ox, oy, "Inventory & Backlog")
        c3 = self._draw_card(surface, (40, 520, 1200, 170), scale, ox, oy, "Weekly Cost")

        demand = self.report["customer_demand"]
        orders = self.report["orders"][self.role]
        inv = self.report["inventory"][self.role]
        bl = self.report["backlog"][self.role]
        cost = self.report["weekly_cost"][self.role]

        self._draw_line_chart(
            surface,
            c1,
            scale,
            {"Customer demand": demand, f"{self.role.capitalize()} order": orders},
            [(0, 150, 136), (25, 40, 150)],
            y_label="units",
        )
        self._draw_line_chart(
            surface,
            c2,
            scale,
            {"Inventory": inv, "Backlog": bl},
            [(0, 150, 136), (200, 40, 40)],
            y_label="units",
        )
        self._draw_line_chart(
            surface,
            c3,
            scale,
            {"Cost": cost},
            [(240, 140, 0)],
            y_label="€",
        )

        # toast
        if self.msg and pygame.time.get_ticks() - self.msg_t < 3500:
            box = self._srect((40, BASE_H - 95, 1200, 55), scale, ox, oy)
            pygame.draw.rect(surface, (255, 255, 255), box, border_radius=int(14 * scale))
            pygame.draw.rect(surface, self.border, box, width=max(1, int(2 * scale)), border_radius=int(14 * scale))
            t = get_font(20, scale, bold=True).render(self.msg, True, self.text)
            surface.blit(t, t.get_rect(center=box.center))
