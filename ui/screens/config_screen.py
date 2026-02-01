# ui/screens/config_screen.py
import os
import pygame
from ui.screens.widgets import get_font, BASE_W, BASE_H
from config import ROLES

# -----------------------------
# Scenario & Policy options
# -----------------------------
SCENARIOS = [
    ("STEP", "Step Change"),
    ("POISSON", "Random (Poisson)"),
    ("TREND_NOISE", "Trend + Noise"),
]

POLICIES = [
    ("BASE_STOCK", "Base-Stock"),
    ("PI", "PI Controller"),
]


class ConfigScreen:
    def __init__(self, ui):
        self.ui = ui
        self.sim = ui.sim
        pygame.mouse.set_visible(True)

        # -----------------------------
        # BASIC CONFIG
        # -----------------------------
        self.num_players = 1
        self.scenario_idx = 0
        self.policy_idx = 0
        self._ignore_mouse_until_ms = 0
        self._last_touch_action_ms = 0

        # which roles are HUMAN (tier selection)
        self.human_roles = set(ROLES[: self.num_players])

        # -----------------------------
        # ADVANCED CONFIG
        # -----------------------------
        self.duration = 25
        self.ship_lt = 1
        self.info_lt = 1

        self.pi_alpha = 0.5
        self.pi_beta = 0.3
        self.pi_gamma = 0.1  # kept in UI/config (may not be used in PI formula)
        self.target_inventory = 12

        self.seed_mode = "FIXED"
        self.seed_value = 42

        self.init_inv = {
            "retailer": 12,
            "distributor": 12,
            "wholesaler": 12,
            "factory": 12,
        }

        self.order_handling = "BACKORDER"  # BACKORDER / LOST_SALES

        self.cost_holding = 1.0
        self.cost_backorder = 5.0
        self.cost_production = 1.0

        self.noise_amplitude = 2.0

        # -----------------------------
        # UI STATE
        # -----------------------------
        self.adv_open = False
        self.adv_selected_index = 0
        self.adv_scroll = 0  # used for touch scrolling inside advanced modal

        self.roles_open = False
        self.roles_error = ""

        self.error_msg = ""

        # IMPORTANT: each adv field must have 6 items
        # (id, label, type, a, b, step) — enum uses a=list of choices, b=None, step=None
        self.adv_fields = [
            ("duration", "Game duration (weeks)", "int", 5, 60, 1),
            ("ship_lt", "Shipping lead time", "int", 0, 10, 1),
            ("info_lt", "Information lead time", "int", 0, 10, 1),
            ("pi_alpha", "PI alpha (α)", "float", 0.0, 2.0, 0.1),
            ("pi_beta", "PI beta (β)", "float", 0.0, 2.0, 0.1),
            ("pi_gamma", "PI gamma (γ)", "float", 0.0, 2.0, 0.1),
            ("target_inventory", "Target (S)", "int", 0, 100, 1),
            ("seed_mode", "Random seed mode", "enum", ["FIXED", "RANDOM"], None, None),
            ("seed_value", "Fixed seed value", "int", 0, 9999, 1),
            ("inv_retailer", "Initial inventory: Retailer", "int", 0, 200, 1),
            ("inv_distributor", "Initial inventory: Distributor", "int", 0, 200, 1),
            ("inv_wholesaler", "Initial inventory: Wholesaler", "int", 0, 200, 1),
            ("inv_factory", "Initial inventory: Factory", "int", 0, 200, 1),
            ("order_handling", "Order handling", "enum", ["BACKORDER", "LOST_SALES"], None, None),
            ("cost_holding", "Holding cost per unit", "float", 0.0, 20.0, 0.5),
            ("cost_backorder", "Backorder cost per unit", "float", 0.0, 40.0, 1.0),
            ("cost_production", "Production cost per unit", "float", 0.0, 40.0, 1.0),
            ("noise_amplitude", "Noise amplitude", "float", 0.0, 10.0, 0.5),
        ]

        # Layout rects in BASE coordinates
        self._compute_layout()

        # Optional back icon (if you use it)
        self.back_icon = None
        for p in ["assets/back_button.png", "./assets/back_button.png"]:
            if os.path.exists(p):
                try:
                    self.back_icon = pygame.image.load(p).convert_alpha()
                except Exception:
                    self.back_icon = None
                break

    # ======================================================
    # BASIC HELPERS
    # ======================================================
    def update(self):
        # Required by your PygameUI (prevents AttributeError)
        pass

    def _compute_layout(self):
        # Header & summary
        self.title_y = 40
        self.summary_rect = pygame.Rect(40, 140, 700, 120)

        # Top buttons
        self.back_rect = pygame.Rect(40, 45, 72, 56)         # original back-arrow size
        self.start_rect = pygame.Rect(BASE_W - 340, 40, 280, 75)

        # Quadrant cards (Layout A)
        margin_side = 40
        margin_between_x = 40
        margin_after_summary = 35
        margin_row = 24

        top_y = self.summary_rect.bottom + margin_after_summary
        available_h = BASE_H - top_y - margin_row - 40
        quad_h = available_h / 2

        total_w = BASE_W - 2 * margin_side - margin_between_x
        quad_w = total_w / 2

        self.q1_rect = pygame.Rect(margin_side, int(top_y), int(quad_w), int(quad_h))
        self.q2_rect = pygame.Rect(int(margin_side + quad_w + margin_between_x),
                                   int(top_y), int(quad_w), int(quad_h))
        self.q3_rect = pygame.Rect(margin_side, int(top_y + quad_h + margin_row),
                                   int(quad_w), int(quad_h))
        self.q4_rect = pygame.Rect(int(margin_side + quad_w + margin_between_x),
                                   int(top_y + quad_h + margin_row),
                                   int(quad_w), int(quad_h))

    def _scale(self, surf):
        w, h = surf.get_size()
        scale = min(w / BASE_W, h / BASE_H)
        ox = (w - BASE_W * scale) / 2
        oy = (h - BASE_H * scale) / 2
        return scale, ox, oy

    def _srect(self, rect, scale, ox, oy):
        return pygame.Rect(
            int(ox + rect.x * scale),
            int(oy + rect.y * scale),
            int(rect.w * scale),
            int(rect.h * scale),
        )

    def _finger_to_pos(self, surf, finger_event):
        """Convert pygame.FINGERDOWN (0..1 coords) to pixel pos."""
        w, h = surf.get_size()
        x = int(finger_event.x * w)
        y = int(finger_event.y * h)
        return (x, y)

    # ======================================================
    # BACK BUTTON RECT (same size as old arrow, aligned with title)
    # ======================================================
    def _get_back_button_rect(self, surf):
        scale, ox, oy = self._scale(surf)

        title_font = get_font(58, scale)
        title_surf = title_font.render("Game Configuration", True, (20, 40, 100))
        title_pos = (ox + 140 * scale, oy + self.title_y * scale)
        title_rect = title_surf.get_rect(topleft=title_pos)

        base = self.back_rect
        w = int(base.w * scale)
        h = int(base.h * scale)

        x = int(ox + base.x * scale)
        y = int(title_rect.centery - h // 2)
        return pygame.Rect(x, y, w, h)

    # ======================================================
    # START GAME (APPLY CONFIG)
    # ======================================================
    def start_game(self):
        if len(self.human_roles) != self.num_players:
            self.error_msg = f"Select exactly {self.num_players} human role(s)."
            return

        control = {}
        for role in ROLES:
            control[role] = "HUMAN" if role in self.human_roles else "AI"

        selected_policy = POLICIES[self.policy_idx][0]
        ai_map = {role: selected_policy for role in ROLES if control[role] == "AI"}

        scenario_key = SCENARIOS[self.scenario_idx][0]

        config = {
            "duration": self.duration,
            "scenario": scenario_key,
            "control_mode": control,
            "ai_policies": ai_map,
            "lead_times": {"shipping": self.ship_lt, "information": self.info_lt},
            "pi_params": {"alpha": self.pi_alpha, "beta": self.pi_beta, "gamma": self.pi_gamma},
            "target_inventory": self.target_inventory,
            "random_seed_mode": self.seed_mode,
            "random_seed_value": self.seed_value,
            "initial_inventory": self.init_inv.copy(),
            "order_handling": self.order_handling,
            "costs": {
                "holding": self.cost_holding,
                "backorder": self.cost_backorder,
                "production": self.cost_production,
            },
            "noise_amplitude": self.noise_amplitude,
        }

        self.error_msg = ""
        self.sim.set_game_configuration(config)
        self.ui.change_state("GAME")

    # ======================================================
    # MODALS
    # ======================================================
    def _close_all_modals(self):
        self.adv_open = False
        self.roles_open = False
        self.roles_error = ""

    # ---------------- Advanced modal controls ----------------
    def _adv_get_value(self, field_id):
        if field_id.startswith("inv_"):
            key = field_id.split("_", 1)[1]
            return self.init_inv[key]
        if field_id == "seed_mode":
            return self.seed_mode
        if field_id == "order_handling":
            return self.order_handling
        return getattr(self, field_id)

    def _adv_set_value(self, field_id, value):
        if field_id.startswith("inv_"):
            key = field_id.split("_", 1)[1]
            self.init_inv[key] = int(value)
            return
        if field_id == "seed_mode":
            self.seed_mode = value
            return
        if field_id == "order_handling":
            self.order_handling = value
            return
        setattr(self, field_id, value)

    def _adv_adjust(self, direction):
        field_id, _, ftype, a, b, step = self.adv_fields[self.adv_selected_index]
        if ftype == "enum":
            return

        cur = self._adv_get_value(field_id)

        if ftype == "int":
            mn, mx = int(a), int(b)
            newv = max(mn, min(mx, int(cur) + int(direction * step)))
            self._adv_set_value(field_id, newv)

        elif ftype == "float":
            mn, mx = float(a), float(b)
            newv = float(cur) + float(direction * step)
            newv = max(mn, min(mx, newv))
            self._adv_set_value(field_id, round(newv, 1))

    def _adv_toggle_enum(self):
        field_id, _, ftype, choices, _, _ = self.adv_fields[self.adv_selected_index]
        if ftype != "enum":
            return
        cur = self._adv_get_value(field_id)
        self._adv_set_value(field_id, choices[1] if cur == choices[0] else choices[0])

    # ===== Advanced touch layout helpers =====
    def _adv_viewport(self, panel: pygame.Rect, scale: float):
        top_y = panel.y + int(118 * scale)
        bottom_pad = int(56 * scale)
        row_h = max(int(44 * scale), 32)
        row_gap = max(int(10 * scale), 6)

        list_left = panel.x + int(20 * scale)
        list_right = panel.right - int(20 * scale) - int(52 * scale)  # reserve scroll buttons area
        list_w = max(10, list_right - list_left)

        avail = max(10, (panel.bottom - bottom_pad) - top_y)
        max_rows = max(1, int(avail // (row_h + row_gap)))
        return {
            "top_y": top_y,
            "row_h": row_h,
            "row_gap": row_gap,
            "bottom_pad": bottom_pad,
            "list_left": list_left,
            "list_w": list_w,
            "max_rows": max_rows,
        }

    def _adv_clamp_scroll(self, max_rows: int):
        max_scroll = max(0, len(self.adv_fields) - max_rows)
        self.adv_scroll = max(0, min(self.adv_scroll, max_scroll))

    def _adv_ensure_visible(self, max_rows: int):
        self._adv_clamp_scroll(max_rows)
        if self.adv_selected_index < self.adv_scroll:
            self.adv_scroll = self.adv_selected_index
        elif self.adv_selected_index > self.adv_scroll + max_rows - 1:
            self.adv_scroll = self.adv_selected_index - (max_rows - 1)
        self._adv_clamp_scroll(max_rows)

    def _adv_row_rects(self, panel: pygame.Rect, scale: float):
        vp = self._adv_viewport(panel, scale)
        top_y = vp["top_y"]
        row_h = vp["row_h"]
        row_gap = vp["row_gap"]
        list_left = vp["list_left"]
        list_w = vp["list_w"]
        max_rows = vp["max_rows"]

        self._adv_clamp_scroll(max_rows)
        start = self.adv_scroll
        end = min(len(self.adv_fields), start + max_rows)

        rows = []
        y = top_y
        for idx in range(start, end):
            field_id, label, ftype, a, b, step = self.adv_fields[idx]
            row = pygame.Rect(list_left, y, list_w, row_h)

            btn_h = max(18, row.h - int(12 * scale))
            btn_y = row.y + (row.h - btn_h) // 2
            btn_w = max(32, int(44 * scale))
            gap = max(6, int(10 * scale))

            plus = pygame.Rect(row.right - int(10 * scale) - btn_w, btn_y, btn_w, btn_h)
            minus = pygame.Rect(plus.x - gap - btn_w, btn_y, btn_w, btn_h)

            toggle_w = max(int(120 * scale), 80)
            toggle = pygame.Rect(row.right - int(10 * scale) - toggle_w, btn_y, toggle_w, btn_h)

            rows.append({
                "idx": idx,
                "field_id": field_id,
                "label": label,
                "ftype": ftype,
                "row": row,
                "minus": minus,
                "plus": plus,
                "toggle": toggle,
                "max_rows": max_rows,
            })
            y += row_h + row_gap

        up_btn = pygame.Rect(panel.right - int(44 * scale), top_y, int(34 * scale), int(34 * scale))
        dn_btn = pygame.Rect(panel.right - int(44 * scale), panel.bottom - int(44 * scale), int(34 * scale), int(34 * scale))
        return rows, up_btn, dn_btn, max_rows

    # ---------------- Roles modal controls ----------------
    def _apply_default_human_roles(self):
        self.human_roles = set(ROLES[: self.num_players])

    def _set_num_players(self, n):
        self.num_players = n
        current = list(self.human_roles)
        current = [r for r in current if r in ROLES]
        if len(current) > n:
            current = current[:n]
        if len(current) < n:
            for r in ROLES:
                if r not in current:
                    current.append(r)
                if len(current) == n:
                    break
        self.human_roles = set(current)

    # ======================================================
    # EVENT HANDLING
    # ======================================================
    def handle_event(self, e):
        if e.type == pygame.VIDEORESIZE:
            self._compute_layout()

        now = pygame.time.get_ticks()

        # If a finger tap also produces a mouse click, ignore that mouse click
        if e.type == pygame.MOUSEBUTTONDOWN and now < self._ignore_mouse_until_ms:
            return

        # Convert touch tap to a click (but prevent double-processing)
        if e.type == pygame.FINGERDOWN:
            # Ignore any mouse-emulated click that comes right after this finger tap
            self._ignore_mouse_until_ms = now + 300  # 300ms is safe

            pos = self._finger_to_pos(self.ui.screen, e)
            e = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})

        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.roles_open or self.adv_open:
                self._close_all_modals()
            else:
                self.ui.change_state("LOGIN_AUTH")
            return

        if self.roles_open:
            self._handle_roles_event(e)
            return

        if self.adv_open:
            self._handle_advanced_event(e)
            return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self._handle_main_click(e.pos)


    def _handle_main_click(self, pos):
        surf = self.ui.screen
        scale, ox, oy = self._scale(surf)

        back_r = self._get_back_button_rect(surf)
        start_r = self._srect(self.start_rect, scale, ox, oy)

        if back_r.collidepoint(pos):
            self.ui.sound.play_click(3000)
            self.ui.change_state("LOGIN_AUTH")
            return

        if start_r.collidepoint(pos):
            self.ui.sound.play_click(3000)
            self.start_game()
            return

        mx, my = pos

        # Q1 Players
        q1 = self._srect(self.q1_rect, scale, ox, oy)
        pad_x, pad_y = 40 * scale, 30 * scale
        inner_top = q1.y + 52 * scale
        card_w = (q1.w - pad_x * 3) / 2
        card_h = (q1.h - (inner_top - q1.y) - pad_y * 2) / 2

        for i in range(4):
            rr, cc = divmod(i, 2)
            rect = pygame.Rect(
                int(q1.x + pad_x + cc * (card_w + pad_x)),
                int(inner_top + rr * (card_h + pad_y)),
                int(card_w),
                int(card_h),
            )
            if rect.collidepoint(mx, my):
                self.ui.sound.play_click(3000)
                self._set_num_players(i + 1)
                self.roles_open = True
                self.roles_error = ""
                return

        # Q2 Scenarios
        q2 = self._srect(self.q2_rect, scale, ox, oy)
        inner_top2 = q2.y + 52 * scale
        gap = 12 * scale
        card_h2 = (q2.h - (inner_top2 - q2.y) - gap * 4) / 3

        for i in range(len(SCENARIOS)):
            rect = pygame.Rect(
                int(q2.x + 26 * scale),
                int(inner_top2 + gap + i * (card_h2 + gap)),
                int(q2.w - 52 * scale),
                int(card_h2),
            )
            if rect.collidepoint(mx, my):
                self.ui.sound.play_click(3000)
                self.scenario_idx = i
                return

        # Q3 Policy
        q3 = self._srect(self.q3_rect, scale, ox, oy)
        inner_top3 = q3.y + 56 * scale
        gap3 = 40 * scale
        card_w3 = (q3.w - gap3 * 3) / 2
        card_h3 = q3.h - (inner_top3 - q3.y) - gap3

        for i in range(len(POLICIES)):
            rect = pygame.Rect(
                int(q3.x + gap3 + i * (card_w3 + gap3)),
                int(inner_top3),
                int(card_w3),
                int(card_h3),
            )
            if rect.collidepoint(mx, my):
                self.ui.sound.play_click(3000)
                self.policy_idx = i
                return

        # Q4 Advanced
        q4 = self._srect(self.q4_rect, scale, ox, oy)
        adv_rect = pygame.Rect(
            int(q4.x + 30 * scale),
            int(q4.y + 60 * scale),
            int(q4.w - 60 * scale),
            int(q4.h - 90 * scale),
        )
        if adv_rect.collidepoint(mx, my):
            self.ui.sound.play_click(3000)
            self.adv_open = True
            self.adv_selected_index = 0
            self.adv_scroll = 0
            return

    # ---------------- Roles modal events ----------------
    def _handle_roles_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                if len(self.human_roles) == self.num_players:
                    self.roles_open = False
                    self.roles_error = ""
                else:
                    self.roles_error = f"Select exactly {self.num_players} role(s)."
                return

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            surf = self.ui.screen
            scale, _, _ = self._scale(surf)

            panel = self._roles_panel_rect(surf)

            close_btn = pygame.Rect(panel.right - int(110 * scale), panel.y + int(18 * scale),
                                    int(90 * scale), int(44 * scale))

            btn_h = int(54 * scale)
            btn_w = int(260 * scale)
            btn_y = panel.bottom - int(75 * scale)
            auto_btn = pygame.Rect(panel.x + int(30 * scale), btn_y, btn_w, btn_h)
            ok_btn = pygame.Rect(panel.right - int(30 * scale) - btn_w, btn_y, btn_w, btn_h)

            if close_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                self.roles_open = False
                self.roles_error = ""
                return

            if auto_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                self._apply_default_human_roles()
                self.roles_error = ""
                return

            if ok_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                if len(self.human_roles) == self.num_players:
                    self.roles_open = False
                    self.roles_error = ""
                else:
                    self.roles_error = f"Select exactly {self.num_players} role(s)."
                return

            items = self._roles_item_rects(surf, panel)
            for role, rr in items:
                if rr.collidepoint(e.pos):
                    self.ui.sound.play_click(3000)
                    if role in self.human_roles:
                        self.human_roles.remove(role)
                    else:
                        if len(self.human_roles) < self.num_players:
                            self.human_roles.add(role)
                        else:
                            self.roles_error = f"Max humans = {self.num_players}"
                    return

    # ---------------- Advanced modal events (KEYBOARD + TOUCH) ----------------
    def _handle_advanced_event(self, e):
        # Keyboard
        if e.type == pygame.KEYDOWN:
            panel = self._adv_panel_rect(self.ui.screen)
            scale, _, _ = self._scale(self.ui.screen)
            max_rows = self._adv_viewport(panel, scale)["max_rows"]

            if e.key == pygame.K_ESCAPE:
                self.adv_open = False
                return

            if e.key in (pygame.K_UP, pygame.K_w):
                self.adv_selected_index = max(0, self.adv_selected_index - 1)
                self._adv_ensure_visible(max_rows)
                return

            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.adv_selected_index = min(len(self.adv_fields) - 1, self.adv_selected_index + 1)
                self._adv_ensure_visible(max_rows)
                return

            if e.key in (pygame.K_LEFT, pygame.K_MINUS):
                self._adv_adjust(-1)
                return

            if e.key in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_EQUALS):
                self._adv_adjust(+1)
                return

            if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._adv_toggle_enum()
                return

        # Mouse wheel (older pygame uses button 4/5)
        if e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", None) in (4, 5):
            panel = self._adv_panel_rect(self.ui.screen)
            scale, _, _ = self._scale(self.ui.screen)
            _, _, _, max_rows = self._adv_row_rects(panel, scale)
            self.adv_scroll += (-1 if e.button == 4 else 1)
            self._adv_clamp_scroll(max_rows)
            return

        # Click / Touch
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            panel = self._adv_panel_rect(self.ui.screen)
            scale, _, _ = self._scale(self.ui.screen)

            close_btn = pygame.Rect(panel.right - int(110 * scale), panel.y + int(18 * scale),
                                    int(90 * scale), int(44 * scale))
            if close_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                self.adv_open = False
                return

            rows, up_btn, dn_btn, max_rows = self._adv_row_rects(panel, scale)

            if up_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                self.adv_scroll -= 1
                self._adv_clamp_scroll(max_rows)
                return
            if dn_btn.collidepoint(e.pos):
                self.ui.sound.play_click(3000)
                self.adv_scroll += 1
                self._adv_clamp_scroll(max_rows)
                return

            for row in rows:
                if row["row"].collidepoint(e.pos):
                    self.adv_selected_index = row["idx"]
                    self._adv_ensure_visible(max_rows)

                    # ✅ FIX: touch-friendly enums — tapping anywhere on the row toggles
                    # prevent accidental double toggle from duplicated events
                    now = pygame.time.get_ticks()
                    if now - self._last_touch_action_ms < 180:
                        return
                    self._last_touch_action_ms = now

                    
                    if row["ftype"] == "enum":
                        self.ui.sound.play_click(3000)
                        self._adv_toggle_enum()
                        return

                    if row["minus"].collidepoint(e.pos):
                        self.ui.sound.play_click(3000)
                        self._adv_adjust(-1)
                        return
                    if row["plus"].collidepoint(e.pos):
                        self.ui.sound.play_click(3000)
                        self._adv_adjust(+1)
                        return
                    return

        # Newer pygame wheel event
        if e.type == pygame.MOUSEWHEEL:
            panel = self._adv_panel_rect(self.ui.screen)
            scale, _, _ = self._scale(self.ui.screen)
            _, _, _, max_rows = self._adv_row_rects(panel, scale)
            self.adv_scroll -= int(e.y)
            self._adv_clamp_scroll(max_rows)
            return

    # ======================================================
    # DRAW
    # ======================================================
    def draw(self, surf):
        surf.fill((245, 247, 250))
        scale, ox, oy = self._scale(surf)

        title = get_font(58, scale).render("Game Configuration", True, (20, 40, 100))
        surf.blit(title, (ox + 140 * scale, oy + self.title_y * scale))

        self._draw_back_arrow_button(surf, scale, ox, oy)
        self._draw_start_button(surf, scale, ox, oy)
        self._draw_summary(surf, scale, ox, oy)

        if self.error_msg:
            f = get_font(22, scale)
            msg = f.render(self.error_msg, True, (180, 0, 0))
            surf.blit(msg, (ox + 40 * scale, oy + (self.summary_rect.bottom + 8) * scale))

        self._draw_quadrant_cards(surf, scale, ox, oy)

        self._draw_players_section(surf, scale, ox, oy)
        self._draw_scenario_section(surf, scale, ox, oy)
        self._draw_policy_section(surf, scale, ox, oy)
        self._draw_advanced_collapsed(surf, scale, ox, oy)

        if self.adv_open:
            self._draw_advanced_overlay(surf, scale)
        if self.roles_open:
            self._draw_roles_overlay(surf, scale)

    # ---------------- Back button draw ----------------
    def _draw_back_arrow_button(self, surf, scale, ox, oy):
        r = self._get_back_button_rect(surf)

        if self.back_icon:
            icon = pygame.transform.smoothscale(self.back_icon, (r.w, r.h))
            surf.blit(icon, r)
            return

        pygame.draw.rect(surf, (240, 240, 240), r, border_radius=14)
        pygame.draw.rect(surf, (150, 150, 150), r, 2, border_radius=14)
        cx, cy = r.centerx, r.centery
        size = int(14 * scale)
        pygame.draw.polygon(
            surf,
            (70, 70, 70),
            [(cx + size, cy - size), (cx - size, cy), (cx + size, cy + size)],
        )
        pygame.draw.line(
            surf, (70, 70, 70),
            (cx + size, cy), (cx + size + int(10 * scale), cy), int(3 * scale)
        )

    def _draw_start_button(self, surf, scale, ox, oy):
        r = self._srect(self.start_rect, scale, ox, oy)
        pygame.draw.rect(surf, (0, 150, 136), r, border_radius=22)
        txt = get_font(32, scale).render("Start Game", True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=r.center))

    def _draw_summary(self, surf, scale, ox, oy):
        r = self._srect(self.summary_rect, scale, ox, oy)
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=20)
        pygame.draw.rect(surf, (225, 225, 225), r, 2, border_radius=20)

        f = get_font(28, scale)

        players_str = f"{self.num_players} Human, {4 - self.num_players} AI"
        policy_str = POLICIES[self.policy_idx][1]
        scenario_str = SCENARIOS[self.scenario_idx][1]

        surf.blit(f.render("Players: " + players_str, True, (40, 40, 40)),
                  (r.x + int(20 * scale), r.y + int(15 * scale)))
        surf.blit(f.render("Scenario: " + scenario_str, True, (40, 40, 40)),
                  (r.x + int(20 * scale), r.y + int(65 * scale)))

        surf.blit(f.render("AI Policy: " + policy_str, True, (40, 40, 40)),
                  (r.x + int(360 * scale), r.y + int(15 * scale)))
        surf.blit(f.render(f"Duration: {self.duration} weeks", True, (40, 40, 40)),
                  (r.x + int(360 * scale), r.y + int(65 * scale)))

        f2 = get_font(20, scale)
        roles_txt = ", ".join([r.capitalize() for r in ROLES if r in self.human_roles]) or "None"
        surf.blit(f2.render(f"Human roles: {roles_txt}", True, (70, 70, 70)),
                  (r.x + int(20 * scale), r.y + int(98 * scale)))

    def _draw_quadrant_cards(self, surf, scale, ox, oy):
        for qr in (self.q1_rect, self.q2_rect, self.q3_rect, self.q4_rect):
            r = self._srect(qr, scale, ox, oy)
            pygame.draw.rect(surf, (255, 255, 255), r, border_radius=18)
            pygame.draw.rect(surf, (225, 225, 225), r, 2, border_radius=18)

    # ---------------- Sections ----------------
    def _draw_players_section(self, surf, scale, ox, oy):
        q1 = self._srect(self.q1_rect, scale, ox, oy)
        title = get_font(26, scale).render("1. Number of Players", True, (25, 40, 150))
        surf.blit(title, (q1.x + int(26 * scale), q1.y + int(10 * scale)))

        pad_x, pad_y = 40 * scale, 30 * scale
        inner_top = q1.y + 52 * scale
        card_w = (q1.w - pad_x * 3) / 2
        card_h = (q1.h - (inner_top - q1.y) - pad_y * 2) / 2

        for i in range(4):
            rr, cc = divmod(i, 2)
            rect = pygame.Rect(
                int(q1.x + pad_x + cc * (card_w + pad_x)),
                int(inner_top + rr * (card_h + pad_y)),
                int(card_w),
                int(card_h),
            )
            selected = (self.num_players == i + 1)

            pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(
                surf,
                (0, 150, 136) if selected else (180, 180, 180),
                rect,
                3,
                border_radius=16,
            )
            txt = get_font(30, scale).render(str(i + 1), True, (20, 40, 90))
            surf.blit(txt, txt.get_rect(center=rect.center))

        hint = get_font(18, scale).render("After selecting, choose which roles are Human.", True, (110, 110, 110))
        surf.blit(hint, (q1.x + int(26 * scale), q1.bottom - int(26 * scale)))

    def _draw_scenario_section(self, surf, scale, ox, oy):
        q2 = self._srect(self.q2_rect, scale, ox, oy)
        title = get_font(26, scale).render("2. Demand Scenario", True, (25, 40, 150))
        surf.blit(title, (q2.x + int(26 * scale), q2.y + int(10 * scale)))

        inner_top2 = q2.y + 52 * scale
        gap = 12 * scale
        card_h2 = (q2.h - (inner_top2 - q2.y) - gap * 4) / 3

        for i, (_, label) in enumerate(SCENARIOS):
            rect = pygame.Rect(
                int(q2.x + 26 * scale),
                int(inner_top2 + gap + i * (card_h2 + gap)),
                int(q2.w - 52 * scale),
                int(card_h2),
            )
            selected = (self.scenario_idx == i)

            pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(
                surf,
                (0, 150, 136) if selected else (180, 180, 180),
                rect,
                3,
                border_radius=16,
            )

            font = get_font(24, scale)
            raw = font.render(label, True, (25, 40, 100))
            b = raw.get_bounding_rect()
            if b.w > 0 and b.h > 0:
                txt = pygame.Surface((b.w, b.h), pygame.SRCALPHA)
                txt.blit(raw, (0, 0), b)
            else:
                txt = raw

            pad = int(22 * scale)
            y = rect.centery - int(2 * scale)
            surf.blit(txt, txt.get_rect(midleft=(rect.x + pad, y)))

    def _draw_policy_section(self, surf, scale, ox, oy):
        q3 = self._srect(self.q3_rect, scale, ox, oy)
        title = get_font(26, scale).render("3. AI Policy", True, (25, 40, 150))
        surf.blit(title, (q3.x + int(26 * scale), q3.y + int(10 * scale)))

        inner_top3 = q3.y + 56 * scale
        gap3 = 40 * scale
        card_w3 = (q3.w - gap3 * 3) / 2
        card_h3 = q3.h - (inner_top3 - q3.y) - gap3

        for i, (_, label) in enumerate(POLICIES):
            rect = pygame.Rect(
                int(q3.x + gap3 + i * (card_w3 + gap3)),
                int(inner_top3),
                int(card_w3),
                int(card_h3),
            )
            selected = (self.policy_idx == i)

            pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=16)
            pygame.draw.rect(
                surf,
                (0, 150, 136) if selected else (180, 180, 180),
                rect,
                3,
                border_radius=16,
            )
            txt = get_font(24, scale).render(label, True, (25, 40, 100))
            surf.blit(txt, txt.get_rect(center=rect.center))

    def _draw_advanced_collapsed(self, surf, scale, ox, oy):
        q4 = self._srect(self.q4_rect, scale, ox, oy)
        title = get_font(26, scale).render("4. Advanced Options", True, (25, 40, 150))
        surf.blit(title, (q4.x + int(26 * scale), q4.y + int(10 * scale)))

        rect = pygame.Rect(
            int(q4.x + 30 * scale),
            int(q4.y + 60 * scale),
            int(q4.w - 60 * scale),
            int(q4.h - 90 * scale),
        )
        pygame.draw.rect(surf, (255, 255, 255), rect, border_radius=16)
        pygame.draw.rect(surf, (180, 180, 180), rect, 2, border_radius=16)

        txt = get_font(20, scale).render("Click to configure advanced parameters", True, (70, 70, 70))
        surf.blit(txt, txt.get_rect(center=rect.center))

    # ======================================================
    # ADVANCED MODAL DRAW
    # ======================================================
    def _adv_panel_rect(self, surf):
        w, h = surf.get_size()
        panel_w = int(w * 0.82)
        panel_h = int(h * 0.82)
        x = (w - panel_w) // 2
        y = (h - panel_h) // 2
        return pygame.Rect(x, y, panel_w, panel_h)

    def _draw_advanced_overlay(self, surf, scale):
        w, h = surf.get_size()

        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        surf.blit(dim, (0, 0))

        panel = self._adv_panel_rect(surf)
        pygame.draw.rect(surf, (255, 255, 255), panel, border_radius=20)
        pygame.draw.rect(surf, (200, 200, 200), panel, 2, border_radius=20)

        title = get_font(36, scale).render("Advanced Options", True, (20, 40, 100))
        surf.blit(title, (panel.x + 30, panel.y + 20))

        hint1 = "Touch: tap a row then use -/+ (or Toggle)."
        hint2 = "Keyboard: UP/DOWN select, LEFT/RIGHT change, ENTER toggle, ESC close."
        hfont = get_font(18, scale)
        surf.blit(hfont.render(hint1, True, (60, 60, 60)), (panel.x + 30, panel.y + 70))
        surf.blit(hfont.render(hint2, True, (60, 60, 60)), (panel.x + 30, panel.y + 92))

        close_btn = pygame.Rect(panel.right - int(110 * scale), panel.y + int(18 * scale),
                                int(90 * scale), int(44 * scale))
        pygame.draw.rect(surf, (240, 240, 240), close_btn, border_radius=12)
        pygame.draw.rect(surf, (170, 170, 170), close_btn, 2, border_radius=12)
        c = get_font(18, scale).render("Close", True, (60, 60, 60))
        surf.blit(c, c.get_rect(center=close_btn.center))

        rows, up_btn, dn_btn, max_rows = self._adv_row_rects(panel, scale)

        if len(self.adv_fields) > max_rows:
            pygame.draw.rect(surf, (240, 240, 240), up_btn, border_radius=10)
            pygame.draw.rect(surf, (170, 170, 170), up_btn, 2, border_radius=10)
            pygame.draw.rect(surf, (240, 240, 240), dn_btn, border_radius=10)
            pygame.draw.rect(surf, (170, 170, 170), dn_btn, 2, border_radius=10)

            fbtn = get_font(18, scale)
            t_up = fbtn.render("UP", True, (60, 60, 60))
            t_dn = fbtn.render("DN", True, (60, 60, 60))
            surf.blit(t_up, t_up.get_rect(center=up_btn.center))
            surf.blit(t_dn, t_dn.get_rect(center=dn_btn.center))

        for row in rows:
            idx = row["idx"]
            selected = (idx == self.adv_selected_index)
            field_id = row["field_id"]
            label = row["label"]
            ftype = row["ftype"]
            rect = row["row"]

            if selected:
                pygame.draw.rect(surf, (230, 245, 250), rect, border_radius=10)

            lbl = get_font(20, scale).render(label, True, (30, 30, 30))
            surf.blit(lbl, (rect.x + int(12 * scale), rect.y + int(12 * scale)))

            val = self._adv_get_value(field_id)
            val_str = f"{val:.1f}" if isinstance(val, float) else str(val)
            vtx = get_font(20, scale).render(val_str, True, (0, 120, 90))

            if ftype == "enum":
                toggle = row["toggle"]
                pygame.draw.rect(surf, (240, 240, 240), toggle, border_radius=10)
                pygame.draw.rect(surf, (170, 170, 170), toggle, 2, border_radius=10)
                ttxt = get_font(18, scale).render("Toggle", True, (60, 60, 60))
                surf.blit(ttxt, ttxt.get_rect(center=toggle.center))

                vx = toggle.x - vtx.get_width() - int(14 * scale)
                surf.blit(vtx, (vx, rect.y + int(12 * scale)))

            else:
                minus = row["minus"]
                plus = row["plus"]

                pygame.draw.rect(surf, (240, 240, 240), minus, border_radius=10)
                pygame.draw.rect(surf, (170, 170, 170), minus, 2, border_radius=10)
                pygame.draw.rect(surf, (240, 240, 240), plus, border_radius=10)
                pygame.draw.rect(surf, (170, 170, 170), plus, 2, border_radius=10)

                fbtn = get_font(22, scale)
                t_minus = fbtn.render("-", True, (60, 60, 60))
                t_plus = fbtn.render("+", True, (60, 60, 60))
                surf.blit(t_minus, t_minus.get_rect(center=minus.center))
                surf.blit(t_plus, t_plus.get_rect(center=plus.center))

                vx = minus.x - vtx.get_width() - int(14 * scale)
                surf.blit(vtx, (vx, rect.y + int(12 * scale)))

    # ======================================================
    # ROLES / TIERS MODAL DRAW
    # ======================================================
    def _roles_panel_rect(self, surf):
        w, h = surf.get_size()
        panel_w = int(w * 0.72)
        panel_h = int(h * 0.62)
        x = (w - panel_w) // 2
        y = (h - panel_h) // 2
        return pygame.Rect(x, y, panel_w, panel_h)

    def _roles_item_rects(self, surf, panel):
        scale, _, _ = self._scale(surf)

        footer_h = int(110 * scale)
        top_pad = int(110 * scale)
        side_pad = int(30 * scale)
        gap = int(14 * scale)

        left = panel.x + side_pad
        width = panel.w - 2 * side_pad

        available_h = panel.h - top_pad - footer_h
        n = len(ROLES)

        height = int((available_h - gap * (n - 1)) / n)
        height = max(height, int(46 * scale))

        top = panel.y + top_pad

        items = []
        for i, role in enumerate(ROLES):
            rr = pygame.Rect(left, top + i * (height + gap), width, height)
            items.append((role, rr))
        return items

    def _draw_roles_overlay(self, surf, scale):
        w, h = surf.get_size()

        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        surf.blit(dim, (0, 0))

        panel = self._roles_panel_rect(surf)
        pygame.draw.rect(surf, (255, 255, 255), panel, border_radius=20)
        pygame.draw.rect(surf, (200, 200, 200), panel, 2, border_radius=20)

        t = get_font(34, scale).render("Select Human Roles (Tier)", True, (20, 40, 100))
        surf.blit(t, (panel.x + 30, panel.y + 20))

        subtitle = get_font(20, scale).render(
            f"Choose exactly {self.num_players} role(s) to be Human. Others will be AI.",
            True, (70, 70, 70)
        )
        surf.blit(subtitle, (panel.x + 30, panel.y + 60))

        close_btn = pygame.Rect(panel.right - int(110 * scale), panel.y + int(18 * scale),
                                int(90 * scale), int(44 * scale))
        pygame.draw.rect(surf, (240, 240, 240), close_btn, border_radius=12)
        pygame.draw.rect(surf, (170, 170, 170), close_btn, 2, border_radius=12)
        txtc = get_font(18, scale).render("Close", True, (60, 60, 60))
        surf.blit(txtc, txtc.get_rect(center=close_btn.center))

        for role, rr in self._roles_item_rects(surf, panel):
            is_human = role in self.human_roles
            pygame.draw.rect(surf, (255, 255, 255), rr, border_radius=14)
            pygame.draw.rect(surf, (0, 150, 136) if is_human else (180, 180, 180),
                             rr, 3, border_radius=14)

            label = role.capitalize()
            left_txt = get_font(22, scale).render(label, True, (25, 40, 100))
            surf.blit(left_txt, (rr.x + int(18 * scale), rr.y + int(16 * scale)))

            tag = "Human" if is_human else "AI"
            tag_color = (0, 120, 90) if is_human else (120, 120, 120)
            right_txt = get_font(22, scale).render(tag, True, tag_color)
            surf.blit(right_txt, (rr.right - right_txt.get_width() - int(18 * scale),
                                  rr.y + int(16 * scale)))

        btn_h = int(54 * scale)
        btn_w = int(260 * scale)
        btn_y = panel.bottom - int(75 * scale)

        auto_btn = pygame.Rect(panel.x + int(30 * scale), btn_y, btn_w, btn_h)
        ok_btn = pygame.Rect(panel.right - int(30 * scale) - btn_w, btn_y, btn_w, btn_h)

        pygame.draw.rect(surf, (240, 240, 240), auto_btn, border_radius=14)
        pygame.draw.rect(surf, (170, 170, 170), auto_btn, 2, border_radius=14)
        auto_txt = get_font(20, scale).render("Auto Assign", True, (60, 60, 60))
        surf.blit(auto_txt, auto_txt.get_rect(center=auto_btn.center))

        pygame.draw.rect(surf, (0, 150, 136), ok_btn, border_radius=14)
        ok_txt = get_font(20, scale).render("Done", True, (255, 255, 255))
        surf.blit(ok_txt, ok_txt.get_rect(center=ok_btn.center))

        if self.roles_error:
            err = get_font(20, scale).render(self.roles_error, True, (180, 0, 0))
            surf.blit(err, (panel.x + int(30 * scale), panel.bottom - int(100 * scale)))
