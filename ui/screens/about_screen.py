import pygame
from ui.screens.widgets import Button, get_font, BASE_W, BASE_H

class AboutScreen:
    def __init__(self, ui):
        self.ui = ui

        self.text = (
            "Beer Game 2.0 Interactive Edition.\n\n"
            "Developed by Team 4 in the course Basics of Programming.\n\n"
            "Simulates supply chain dynamics and demonstrates the bullwhip effect.\n\n"
            "Educational tool used for Industrial Engineering and Logistics courses."
        )

        self.back_button = Button(
            (BASE_W / 2 - 120, BASE_H - 100, 240, 60),
            "BACK",
            self.go_back,
        )

    def go_back(self):
        self.ui.change_state("START")

    def wrap_paragraphs(self, text, font, max_width):
        lines = []
        paragraphs = text.split("\n")

        for p in paragraphs:
            if p.strip() == "":
                lines.append("")
                continue

            words = p.split(" ")
            current = ""
            for word in words:
                test = current + word + " "
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    lines.append(current.strip())
                    current = word + " "
            lines.append(current.strip())

        return lines

    def handle_event(self, event):
        self.back_button.handle_event(event)

    def update(self):
        pass

    def draw(self, surface):
        surface.fill((245, 248, 255))
        w, h = surface.get_size()
        scale = min(w / BASE_W, h / BASE_H)

        # Title
        title_font = get_font(48, scale, bold=True)
        title_surf = title_font.render("About", True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(w // 2, int(120 * scale)))
        surface.blit(title_surf, title_rect)

        # Wrapped text
        text_font = get_font(28, scale)
        max_width = int((BASE_W - 200) * scale)
        wrapped_lines = self.wrap_paragraphs(self.text, text_font, max_width)

        y = int(200 * scale)
        for line in wrapped_lines:
            line_surf = text_font.render(line, True, (0, 0, 0))
            line_rect = line_surf.get_rect(center=(w // 2, y))
            surface.blit(line_surf, line_rect)
            y += int(40 * scale)

        self.back_button.draw(surface)
