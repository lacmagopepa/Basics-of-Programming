# ui/pygame_ui.py
import pygame

from ui.sound_manager import sound

# Import all screens
from ui.screens.login_screen import LoginScreen          # Start menu (cup icon)
from ui.screens.auth_screen import AuthScreen            # Username/password login
from ui.screens.config_screen import ConfigScreen        # Game configuration
from ui.screens.game_screen import GameScreen            # Main gameplay
from ui.screens.end_screen import EndScreen              # Results screen
from ui.screens.analysis_screen import AnalysisScreen    # Analysis screen
from ui.screens.about_screen import AboutScreen          # About screen


class PygameUI:
    """
    Central UI Manager: handles which screen is active,
    routes events, updates, and manages transitions.
    """

    def __init__(self, screen, simulation):
        self.screen = screen
        self.sim = simulation

        # Shared audio manager
        self.sound = sound

        # Register all screens here
        self.screens = {
            "START": LoginScreen(self),
            "LOGIN_AUTH": AuthScreen(self),
            "ABOUT": AboutScreen(self),
            "CONFIG": ConfigScreen(self),
            "GAME": GameScreen(self, simulation),
            "END": EndScreen(self),
            "ANALYSIS": AnalysisScreen(self),
        }

        # Start at main menu
        self.state = "START"

        # Play START screen intro audio
        self.sound.on_state_change(self.state)

    # -----------------------------------------
    # Handle pygame events
    # -----------------------------------------
    def handle_event(self, event):
        self.screens[self.state].handle_event(event)

    # -----------------------------------------
    # Update active screen
    # -----------------------------------------
    def update(self):
        # audio timers
        self.sound.update()
        self.screens[self.state].update()

    # -----------------------------------------
    # Draw active screen
    # -----------------------------------------
    def draw(self):
        self.screens[self.state].draw(self.screen)

    # -----------------------------------------
    # Switch screen
    # -----------------------------------------
    def change_state(self, new_state: str):
        if new_state not in self.screens:
            print(f"[ERROR] Screen '{new_state}' does not exist.")
            return

        # IMPORTANT: Re-initialize stateful screens on transition.
        # This ensures the GAME screen picks up the latest configuration
        # (human vs AI roles, selected policies, lead times, etc.).
        if new_state == "GAME":
            self.screens["GAME"] = GameScreen(self, self.sim)
        elif new_state == "CONFIG":
            self.screens["CONFIG"] = ConfigScreen(self)
        elif new_state == "END":
            self.screens["END"] = EndScreen(self)
        elif new_state == "ANALYSIS":
            self.screens["ANALYSIS"] = AnalysisScreen(self)

        self.state = new_state
        self.sound.on_state_change(new_state)
