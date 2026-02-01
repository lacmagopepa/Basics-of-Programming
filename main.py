import pygame
from ui.pygame_ui import PygameUI
from simulation.simulation_engine import SimulationEngine
from ui.sound_manager import sound

def main():
    pygame.init()

    # Audio (best-effort). If mixer fails, the game still runs.
    sound.init()

    # Start with 1280x720 but RESIZABLE
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Beer Game 2.0 Interactive")
    clock = pygame.time.Clock()

    sim = SimulationEngine()
    ui = PygameUI(screen, sim)
    pygame.mouse.set_visible(True) # pyright: ignore[reportUnknownMemberType]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            ui.handle_event(event)

        ui.update()
        ui.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
