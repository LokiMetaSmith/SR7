import pygame
import sys
from ui.components import PlayerCard, GMCard


class App:
    def __init__(self, width: int = 1000, height: int = 700):
        if not pygame.get_init():
            pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Shadowrun 7E - Interactive Cards")
        self.clock = pygame.time.Clock()
        self.running = True
        self.pending_action = None

        self.player_cards = []
        self.gm_cards = []
        self.state = None
        self.running = True

    def set_pending_action(self, action: str):
        self.pending_action = action

    def update_state(self, state):
        """Updates the internal UI cards with live data from the simulation."""
        self.state = state

        t1 = [c for c in state.combatants if c.team == 1]
        t2 = [c for c in state.combatants if c.team == 2]

        # Match lengths or update existing to preserve state
        while len(self.player_cards) < len(t1):
            self.player_cards.append(
                PlayerCard(
                    t1[len(self.player_cards)],
                    width=350,
                    height=500,
                    on_action=self.set_pending_action,
                )
            )
        while len(self.player_cards) > len(t1):
            self.player_cards.pop()

        for i, c in enumerate(t1):
            self.player_cards[i].combatant = c

        while len(self.gm_cards) < len(t2):
            self.gm_cards.append(
                GMCard(
                    t2[len(self.gm_cards)],
                    width=350,
                    height=500,
                    on_action=self.set_pending_action,
                )
            )
        while len(self.gm_cards) > len(t2):
            self.gm_cards.pop()

        for i, c in enumerate(t2):
            self.gm_cards[i].combatant = c

    def tick(self):
        """Processes one frame of the UI, suitable for a host event loop."""
        self.handle_events()
        self.draw()
        self.clock.tick(60)

    def run(self):
        """Legacy blocking loop for standalone testing."""
        self.running = True
        while self.running:
            self.tick()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        # Ensure rects are up-to-date before clicks
        x_offset = 50
        for card in self.player_cards:
            card.rect.topleft = (x_offset, 100)
            card.update_rects()
            x_offset += 370

        x_offset = max(x_offset, 550)
        for card in self.gm_cards:
            card.rect.topleft = (x_offset, 100)
            card.update_rects()
            x_offset += 370

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Pass events to components
            for card in self.player_cards:
                card.handle_event(event)
            for card in self.gm_cards:
                card.handle_event(event)

    def draw(self):
        self.screen.fill((20, 20, 20))  # Dark background

        font = pygame.font.SysFont("monospace", 16, bold=True)
        if self.state:
            turn_text = f"Turn: {self.state.turn}"
            turn_surf = font.render(turn_text, True, (220, 220, 220))
            self.screen.blit(turn_surf, (100, 20))

        # Draw cards side by side
        x_offset = 50
        for card in self.player_cards:
            card.draw(self.screen, x_offset, 100)
            x_offset += 370

        x_offset = max(x_offset, 550)
        for card in self.gm_cards:
            card.draw(self.screen, x_offset, 100)
            x_offset += 370

        pygame.display.flip()
