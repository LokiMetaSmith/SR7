import pygame
import sys
from scripts.combat_simulator import Combatant, MatrixAttributes, Weapon, load_combatant
from ui.components import PlayerCard, GMCard, ChatWindow


class App:
    def __init__(self, width: int = 1000, height: int = 700):
        if not pygame.get_init():
            pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Shadowrun 7E - Interactive Cards")
        self.clock = pygame.time.Clock()
        self.running = True

        self.pending_action = None
        self.pending_chat = None

        # Create dummy data initially

        player_combatant = load_combatant("npc_templates/Kyber.chum5")

        gm_combatant = load_combatant("npc_templates/Sargent_Igneous.chum5")
        gm_combatant.team = 1


        self.player_cards = []
        self.gm_cards = []


        chat_width = 300
        chat_rect = pygame.Rect(self.width - chat_width - 20, 20, chat_width, self.height - 40)
        self.chat_window = ChatWindow(chat_rect, on_submit=self.set_pending_chat)


        self.state = None

        self.running = True
        self.scroll_x = 0
        self.scroll_y = 0


    def set_pending_action(self, action: str):
        self.pending_action = action


    def set_pending_chat(self, chat_message: str):
        self.pending_chat = chat_message

    def display_chat_message(self, role: str, message: str):
        self.chat_window.add_message(role, message)



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
        x_offset = 50 + self.scroll_x
        for card in self.player_cards:
            card.rect.topleft = (x_offset, 100 + self.scroll_y)
            card.update_rects()
            x_offset += 370

        x_offset = max(x_offset, 550 + self.scroll_x)
        for card in self.gm_cards:
            card.rect.topleft = (x_offset, 100 + self.scroll_y)
            card.update_rects()
            x_offset += 370

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                chat_width = 300
                self.chat_window.rect = pygame.Rect(self.width - chat_width - 20, 20, chat_width, self.height - 40)

            elif event.type == pygame.MOUSEWHEEL:
                # Use shift+scroll or regular scroll to move horizontally
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self.scroll_x += event.y * 30
                else:
                    self.scroll_x += event.x * 30
                    self.scroll_y += event.y * 30


                # Limit scrolling
                total_width = 50 + len(self.player_cards) * 370
                total_width = max(total_width, 550)
                total_width += len(self.gm_cards) * 370 + 50 + 320 # +320 to account for chat window

                min_scroll_x = min(0, self.width - total_width)
                self.scroll_x = max(min_scroll_x, min(0, self.scroll_x))


                # Assume a fixed max height for cards for now
                min_scroll_y = min(0, self.height - 650)
                self.scroll_y = max(min_scroll_y, min(0, self.scroll_y))


            # Pass events to components
            self.chat_window.handle_event(event)
            for card in self.player_cards:

                card.handle_event(event)
            for card in self.gm_cards:
                card.handle_event(event)

        mouse_pos = pygame.mouse.get_pos()
        hovered = False
        for card in self.player_cards + self.gm_cards:
            if not card.expanded and card.rect.collidepoint(mouse_pos):
                hovered = True
                break
            if card.expanded and any(r.collidepoint(mouse_pos) for r, _ in card.action_rects):
                hovered = True
                break

        if hovered:
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            except pygame.error:
                pass # Dummy driver issues
        else:
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass # Dummy driver issues

    def draw(self):
        # Draw a dark grid background
        self.screen.fill((10, 12, 15))
        for x in range(0, self.width, 40):
            pygame.draw.line(self.screen, (20, 24, 30), (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(self.screen, (20, 24, 30), (0, y), (self.width, y))

        font = pygame.font.SysFont("monospace", 18, bold=True)
        # Title text
        title_surf = font.render("SHADOWRUN 7E TACTICAL SIMULATOR", True, (0, 255, 204))
        self.screen.blit(title_surf, (50, 20))

        if self.state:
            turn_text = f"Turn: {self.state.turn}"
            turn_surf = font.render(turn_text, True, (220, 220, 220))
            self.screen.blit(turn_surf, (50, 50))

        # Draw cards side by side
        x_offset = 50 + self.scroll_x
        for card in self.player_cards:
            card.draw(self.screen, x_offset, 100 + self.scroll_y)
            x_offset += 370


        x_offset = max(x_offset, 550 + self.scroll_x)
        for card in self.gm_cards:
            card.draw(self.screen, x_offset, 100 + self.scroll_y)
            x_offset += 370

        self.chat_window.draw(self.screen)

        pygame.display.flip()
