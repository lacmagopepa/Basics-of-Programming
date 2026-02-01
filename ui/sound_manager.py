"""Centralized audio handling for the Beer Game UI (pygame).

Implements these behaviors:
  - game_start.mp3: play ~3s when entering START screen
  - game_play.mp3: loop while in GAME screen
  - game_over.mp3: play ~5s when entering END screen
  - game_click.mp3: play ~3s whenever a UI button/action is activated

We use:
  - pygame.mixer.music for the *screen music* (start/play/over)
  - pygame.mixer.Channel for the *click SFX* so it can overlap with music
"""

from __future__ import annotations

import os
import pygame


def _asset_path(*parts: str) -> str:
    """Resolve paths inside the project's assets folder."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    p = os.path.join(base_dir, *parts)
    if os.path.exists(p):
        return p
    # fallback: cwd/assets
    p2 = os.path.abspath(os.path.join(os.getcwd(), "assets", *parts))
    return p2


class SoundManager:
    def __init__(self):
        self._ready = False

        # paths
        self.path_click = _asset_path("audio", "game_click.mp3")
        self.path_play = _asset_path("audio", "game_play.mp3")
        self.path_over = _asset_path("audio", "game_over.mp3")
        self.path_start = _asset_path("audio", "game_start.mp3")

        # state
        self.current_state: str | None = None
        self._music_stop_at_ms: int | None = None
        self.muted = False

        # click sfx
        self._click_sound: pygame.mixer.Sound | None = None
        self._click_channel: pygame.mixer.Channel | None = None
        self._click_stop_at_ms: int | None = None

        # input de-bounce between touch and mouse
        self._last_finger_ms = -10_000

    # -----------------------------
    # Init / Update
    # -----------------------------
    def init(self):
        """Initialize mixer and load the click sound (if possible)."""
        if self._ready:
            return

        # Ensure mixer is initialized
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()  # use defaults
        except Exception as e:
            print("[SOUND] pygame.mixer.init failed:", e)
            self._ready = False
            return

        # Reserve a channel for click SFX
        try:
            pygame.mixer.set_num_channels(16)
        except Exception:
            pass

        self._click_channel = pygame.mixer.Channel(1)

        # Load click sound (best effort)
        try:
            if os.path.exists(self.path_click):
                self._click_sound = pygame.mixer.Sound(self.path_click)
        except Exception as e:
            print("[SOUND] Could not load click sound:", e)
            self._click_sound = None

        self._ready = True

    def update(self):
        """Call every frame (stops any timed sounds)."""
        if not self._ready:
            return
        now = pygame.time.get_ticks()

        if self._music_stop_at_ms is not None and now >= self._music_stop_at_ms:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self._music_stop_at_ms = None

        if self._click_stop_at_ms is not None and now >= self._click_stop_at_ms:
            if self._click_channel is not None:
                try:
                    self._click_channel.stop()
                except Exception:
                    pass
            self._click_stop_at_ms = None

    def toggle_mute(self):
        self.muted = not self.muted
        volume = 0.0 if self.muted else 1.0
        try:
            pygame.mixer.music.set_volume(volume)
        except Exception:
            pass
        # Also mute click sounds if needed
        if self._click_channel:
            self._click_channel.set_volume(volume)
    def note_finger_event(self):
        self._last_finger_ms = pygame.time.get_ticks()

    def should_ignore_mouse_after_finger(self, window_ms: int = 80) -> bool:
        """Some systems emit BOTH FINGERDOWN and MOUSEBUTTONDOWN for the same tap."""
        return pygame.time.get_ticks() - self._last_finger_ms <= window_ms

    # -----------------------------
    # Click SFX
    # -----------------------------
    def play_click(self, duration_ms: int = 3000):
        if not self._ready:
            return
        if self._click_channel is None or self._click_sound is None:
            return
        try:
            self._click_channel.play(self._click_sound)
            self._click_stop_at_ms = pygame.time.get_ticks() + int(duration_ms)
        except Exception:
            pass

    # -----------------------------
    # Screen music (start / play / over)
    # -----------------------------
    def _play_music(self, path: str, loops: int, duration_ms: int | None):
        if not self._ready:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        if not path or not os.path.exists(path):
            self._music_stop_at_ms = None
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
            self._music_stop_at_ms = (pygame.time.get_ticks() + int(duration_ms)) if duration_ms else None
        except Exception as e:
            print("[SOUND] Could not play music:", e)
            self._music_stop_at_ms = None

    def on_state_change(self, new_state: str):
        """Call whenever the UI changes to a new screen/state."""
        if not self._ready:
            return

        # Stop music when leaving GAME unless next state is also GAME
        if new_state == "START":
            self._play_music(self.path_start, loops=0, duration_ms=3000)
        elif new_state == "GAME":
            self._play_music(self.path_play, loops=-1, duration_ms=None)
        elif new_state == "END":
            self._play_music(self.path_over, loops=0, duration_ms=5000)
        else:
            # For other screens, stop background music (but keep click sfx)
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self._music_stop_at_ms = None

        self.current_state = new_state


# Module-level singleton
sound = SoundManager()
