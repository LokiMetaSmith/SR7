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
        self.running = False
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

        self.player_card = PlayerCard(player_combatant, width=350, height=500, on_action=self.set_pending_action)
        self.gm_card = GMCard(gm_combatant, width=350, height=500, on_action=self.set_pending_action)

    def set_pending_action(self, action: str):
        self.pending_action = action

    def update_state(self, combatants: list[Combatant]):
        """Updates the internal UI cards with live data from the simulation."""
        t1 = [c for c in combatants if c.team == 1]
        t2 = [c for c in combatants if c.team == 2]
        if t1:
            self.player_card.combatant = t1[0]
        if t2:
            self.gm_card.combatant = t2[0]

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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Pass events to components
            self.player_card.handle_event(event)
            self.gm_card.handle_event(event)

    def draw(self):
        self.screen.fill((20, 20, 20)) # Dark background

        # Draw cards side by side
        self.player_card.draw(self.screen, 100, 100)
        self.gm_card.draw(self.screen, 550, 100)

        pygame.display.flip()
