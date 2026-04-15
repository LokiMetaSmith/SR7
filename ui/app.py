import pygame
import sys
from scripts.combat_simulator import Combatant, MatrixAttributes, Weapon
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

        # Create dummy data initially
        player_combatant = Combatant(
            name="Kyber",
            source_file="",
            attributes={"BOD": 5, "AGI": 6, "REA": 5, "STR": 4, "WIL": 4, "LOG": 5, "INT": 4, "CHA": 2},
            weapons=[Weapon(name="Ares Predator V", damage=8, damage_type="P", ap=-1, ammo=15, mode="SA")],
            matrix=MatrixAttributes(attack=0, sleaze=0, data_processing=4, firewall=5),
            armor=12,
            physical_track=11,
            stun_track=10,
            physical_damage=3,
            stun_damage=0,
            edge=3,
            initiative_score=9
        )

        gm_combatant = Combatant(
            name="Lone Star Enforcer",
            source_file="",
            attributes={"BOD": 4, "AGI": 4, "REA": 4, "STR": 4, "WIL": 3, "LOG": 3, "INT": 3, "CHA": 3},
            weapons=[Weapon(name="Defiance T-250", damage=10, damage_type="P", ap=-1, ammo=5, mode="SS/SA")],
            matrix=MatrixAttributes(attack=0, sleaze=0, data_processing=3, firewall=3),
            armor=9,
            physical_track=10,
            stun_track=10,
            physical_damage=0,
            stun_damage=0,
            edge=1,
            initiative_score=7,
            team=1
        )

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
            self.player_cards.append(PlayerCard(t1[len(self.player_cards)], width=350, height=500, on_action=self.set_pending_action))
        while len(self.player_cards) > len(t1):
            self.player_cards.pop()

        for i, c in enumerate(t1):
            self.player_cards[i].combatant = c

        while len(self.gm_cards) < len(t2):
            self.gm_cards.append(GMCard(t2[len(self.gm_cards)], width=350, height=500, on_action=self.set_pending_action))
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
        self.screen.fill((20, 20, 20)) # Dark background

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
