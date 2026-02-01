# ui/screens/end_screen.py
from __future__ import annotations

import pygame

from config import ROLES
from ui.screens.widgets import BASE_W, BASE_H, get_font, Button
from persistence.analysis_tools import compute_report
from persistence.csv_export import export_csv


class EndScreen:
    def __init__(self, ui):
        self.ui = ui
        self.report = compute_report()

        # message toast
        self.msg = ""
        self.msg_t = 0

        # theme (flat, no drop shadows)
        self.bg = (245, 248, 250)
        self.card = (255, 255, 255)
        self.border = (220, 224, 230)
        self.title = (25, 40, 150)
        self.text = (40, 40, 40)
        self.muted = (110, 115, 125)
        self.teal = (0, 150, 136)
        self.red = (200, 40, 40)
        self.orange = (240, 140, 0)

        # ===== Bottom buttons (CENTERED as a group) =====
        btn_y = BASE_H - 65
        btn_h = 55
        gap = 20

        w_analysis = 220
        w_play = 200
        w_export = 200
        w_exit = 160

        total_w = w_analysis + w_play + w_export + w_exit + 3 * gap
        start_x = (BASE_W - total_w) // 2  # ✅ centered

        self.btn_analysis = Button((start_x, btn_y, w_analysis, btn_h), "View Analysis", self.go_analysis)
        self.btn_play = Button((start_x + w_analysis + gap, btn_y, w_play, btn_h), "Play Again", self.play_again)
        self.btn_export = Button((start_x + w_analysis + gap + w_play + gap, btn_y, w_export, btn_h), "Export CSV", self.export)
        self.btn_exit = Button((start_x + w_analysis + gap + w_play + gap + w_export + gap, btn_y, w_exit, btn_h), "Exit", self.exit)

    def go_analysis(self):
        self.ui.change_state("ANALYSIS")

    def play_again(self):
        self.ui.change_state("CONFIG")

    def export(self):
        p = export_csv()
        self.msg = f"Saved: {p}"
        self.msg_t = pygame.time.get_ticks()

    def exit(self):
        self.ui.change_state("START")

    def handle_event(self, event):
        self.btn_analysis.handle_event(event)
        self.btn_play.handle_event(event)
        self.btn_export.handle_event(event)
        self.btn_exit.handle_event(event)

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
        if title:
            t = get_font(28, scale, bold=True).render(title, True, self.title)
            surf.blit(t, (r.x + int(18 * scale), r.y + int(14 * scale)))
        return r

    def _draw_bar(self, surf, rect, scale, labels, values, baseline=1.0):
        r = rect
        left = r.x + int(18 * scale)
        right = r.right - int(18 * scale)
        top = r.y + int(70 * scale)
        bottom = r.bottom - int(18 * scale)

        pygame.draw.rect(surf, (250, 250, 250), (left, top, right - left, bottom - top), border_radius=int(12 * scale))
        pygame.draw.rect(surf, self.border, (left, top, right - left, bottom - top),
                         width=max(1, int(2 * scale)), border_radius=int(12 * scale))

        vmax = max(max(values), baseline, 1.0)
        bar_w = (right - left) / max(len(values), 1)

        for i, (lab, val) in enumerate(zip(labels, values)):
            x0 = left + int(i * bar_w + bar_w * 0.15)
            x1 = left + int((i + 1) * bar_w - bar_w * 0.15)
            bw = max(2, x1 - x0)
            h = int((bottom - top) * (val / vmax)) if vmax > 0 else 0
            y0 = bottom - h

            col = self.teal if i == 0 else (25, 40, 150)
            pygame.draw.rect(surf, col, (x0, y0, bw, h), border_radius=int(10 * scale))

            lf = get_font(16, scale, bold=True)
            txt = lf.render(lab, True, self.muted)
            surf.blit(txt, txt.get_rect(center=(x0 + bw // 2, bottom + int(10 * scale))))

            vf = get_font(16, scale, bold=True)
            vtxt = vf.render(f"{val:.1f}", True, self.text)
            vy = max(top + int(10 * scale), y0 - int(12 * scale))  # clamp
            surf.blit(vtxt, vtxt.get_rect(center=(x0 + bw // 2, vy)))

        yb = bottom - int((bottom - top) * (baseline / vmax)) if vmax > 0 else bottom
        pygame.draw.line(surf, (150, 150, 150), (left, yb), (right, yb), width=max(1, int(2 * scale)))

        # keep baseline label inside plot (no overlap on the far right)
        bl = get_font(16, scale).render(f"Baseline ({baseline:.1f})", True, self.muted)
        surf.blit(bl, (right - bl.get_width(), top - int(22 * scale)))

    def draw(self, surface):
        surface.fill(self.bg)
        scale, ox, oy = self._scale(surface)

        # Header
        t = get_font(50, scale, bold=True).render("Game Complete!", True, (20, 20, 20))
        surface.blit(t, (int(ox + 40 * scale), int(oy + 30 * scale)))

        if not self.report:
            msg = get_font(26, scale, bold=True).render("No results yet. Play a game first.", True, (150, 0, 0))
            surface.blit(msg, (int(ox + 40 * scale), int(oy + 120 * scale)))
            self.btn_play.draw(surface)
            self.btn_exit.draw(surface)
            return

        # Overall results card
        overall = self._draw_card(surface, (40, 110, 600, 210), scale, ox, oy, "Overall Results")
        total_cost = self.report["total_cost_all"]
        avg_inv_sys = sum(self.report["role_totals"][r]["avg_inv"] for r in ROLES) / len(ROLES)
        service = self.report["service_level"]

        f_lab = get_font(18, scale)
        f_val = get_font(34, scale, bold=True)

        # ✅ evenly spaced KPI columns so "Service Level" stays inside the box
        pad = int(18 * scale)
        col_w = (overall.w - 2 * pad) // 3
        x1 = overall.x + pad
        x2 = overall.x + pad + col_w
        x3 = overall.x + pad + 2 * col_w
        y0 = overall.y + int(70 * scale)

        def kpi_block(x_left, width, label, value, color, align="left"):
            lab = f_lab.render(label, True, self.muted)
            val = f_val.render(value, True, color)
            w = max(lab.get_width(), val.get_width())
            if align == "center":
                x = x_left + (width - w) // 2
            elif align == "right":
                x = x_left + (width - w)
            else:
                x = x_left
            surface.blit(lab, (x, y0))
            surface.blit(val, (x, y0 + int(22 * scale)))

        kpi_block(x1, col_w, "Total Cost", f"{total_cost:,.0f} €", self.orange, align="left")
        kpi_block(x2, col_w, "Average Inventory", f"{avg_inv_sys:.1f} units", self.teal, align="center")
        kpi_block(x3, col_w, "Service Level", f"{service*100:.0f}%", self.title, align="right")

        # Bullwhip card
        bw_card = self._draw_card(surface, (680, 110, 560, 210), scale, ox, oy, "Bullwhip Effect Analysis")
        labels = [r.capitalize() for r in ROLES]
        values = [float(self.report["bullwhip"].get(r, 0.0)) for r in ROLES]
        self._draw_bar(surface, bw_card, scale, labels, values, baseline=1.0)

        # Per-tier breakdown card (slightly shorter to free space for Key Insights)
        table = self._draw_card(surface, (40, 330, 1200, 220), scale, ox, oy, "Per-Tier Breakdown")

        headers = ["Tier", "Total Cost", "Avg Inv", "Avg Backlog", "Bullwhip"]

        # Use relative positions so columns “fill” the table nicely
        pad = int(18 * scale)
        col_x = [
            table.x + pad,                        # Tier (left)
            table.x + int(table.w * 0.38),        # Total Cost
            table.x + int(table.w * 0.58),        # Avg Inv
            table.x + int(table.w * 0.78),        # Avg Backlog
            table.x + int(table.w * 0.93),        # Bullwhip
        ]

        hy = table.y + int(60 * scale)
        hf = get_font(18, scale, bold=True)
        for hx, hname in zip(col_x, headers):
            surface.blit(hf.render(hname, True, self.muted), (hx, hy))

        pygame.draw.line(
            surface, self.border,
            (table.x + pad, hy + int(26 * scale)),
            (table.right - pad, hy + int(26 * scale)),
            width=max(1, int(2 * scale))
        )

        # ✅ Dynamic row height so Retailer..Factory always fit & fill the card
        rf = get_font(20, scale, bold=False)
        start_y = hy + int(38 * scale)
        bottom_pad = int(16 * scale)
        avail = max(1, (table.bottom - bottom_pad) - start_y)
        row_h = max(int(24 * scale), int(avail / max(len(ROLES), 1)))

        # Right-align numeric columns to look “filled”
        def draw_right(text, x_right, y, color):
            s = rf.render(text, True, color)
            rect = s.get_rect(topright=(x_right, y))
            surface.blit(s, rect)

        # define right edges for numeric columns (a bit to the right of header x)
        cost_r = table.x + int(table.w * 0.48)
        inv_r = table.x + int(table.w * 0.67)
        bl_r = table.x + int(table.w * 0.86)
        bull_r = table.right - pad

        y = start_y
        for r in ROLES:
            rt = self.report["role_totals"][r]
            surface.blit(rf.render(r.capitalize(), True, self.text), (col_x[0], y))
            draw_right(f"{rt['total_cost']:.0f} €", cost_r, y, self.text)
            draw_right(f"{rt['avg_inv']:.1f}", inv_r, y, self.text)
            draw_right(f"{rt['avg_bl']:.1f}", bl_r, y, self.text)
            draw_right(f"{rt['bullwhip']:.1f}", bull_r, y, self.text)
            y += row_h

        # Key Insights card (taller + moved a bit up so it doesn't touch buttons)
        ins = self._draw_card(surface, (40, 555, 1200, 95), scale, ox, oy, "Key Insights")

        lf = get_font(17, scale)
        pad_x = int(18 * scale)
        pad_y = int(52 * scale)   # was 36 (more space under the title)
        col_w = (ins.w - 2 * pad_x) // 2
        row_h2 = int(20 * scale)  # slightly more line spacing

        sx = ins.x + pad_x
        sy = ins.y + pad_y


        if self.report is None:
            # If no report, show a message
            surface.blit(lf.render("No data available for analysis.", True, self.red), (sx, sy))
            return

        assert self.report is not None  # for type checker

        bw = self.report["bullwhip"]
        max_r = max(ROLES, key=lambda rr: bw.get(rr, 0.0))
        max_bw = bw.get(max_r, 0.0)

        role_totals = self.report["role_totals"]
        max_bl_r = max(ROLES, key=lambda rr: role_totals[rr]["avg_bl"])
        max_bl = role_totals[max_bl_r]["avg_bl"]

        min_cost_r = min(ROLES, key=lambda rr: role_totals[rr]["total_cost"])
        min_cost = role_totals[min_cost_r]["total_cost"]

        lines = [
            f"Bullwhip: {max_bw:.1f}× (highest: {max_r.capitalize()})",
            f"Avg backlog highest: {max_bl:.1f} ({max_bl_r.capitalize()})",
            f"Lowest total cost: {min_cost:,.0f} € ({min_cost_r.capitalize()})",
            "Tip: Try PI Controller to reduce oscillations",
        ]
        lf = get_font(17, scale)
        pad_x = int(18 * scale)
        pad_y = int(36 * scale)
        col_w = (ins.w - 2 * pad_x) // 2
        row_h2 = int(18 * scale)
        start_x = ins.x + pad_x
        start_y = ins.y + pad_y

        surface.blit(lf.render("• " + lines[0], True, self.text), (start_x, start_y))
        surface.blit(lf.render("• " + lines[1], True, self.text), (start_x, start_y + row_h2))

        rx = start_x + col_w
        surface.blit(lf.render("• " + lines[2], True, self.text), (rx, start_y))
        surface.blit(lf.render("• " + lines[3], True, self.text), (rx, start_y + row_h2))

        # Buttons (centered group)
        self.btn_analysis.draw(surface)
        self.btn_play.draw(surface)
        self.btn_export.draw(surface)
        self.btn_exit.draw(surface)

        # toast
        if self.msg and pygame.time.get_ticks() - self.msg_t < 3500:
            box = self._srect((40, 285, 1200, 46), scale, ox, oy)
            pygame.draw.rect(surface, (255, 255, 255), box, border_radius=int(14 * scale))
            pygame.draw.rect(surface, self.border, box, width=max(1, int(2 * scale)), border_radius=int(14 * scale))
            tx = get_font(20, scale, bold=True).render(self.msg, True, self.text)
            surface.blit(tx, tx.get_rect(center=box.center))