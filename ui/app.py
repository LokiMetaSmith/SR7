import pygame
import sys
from scripts.combat_simulator import Combatant, MatrixAttributes, Weapon, load_combatant
from ui.components import PlayerCard, GMCard, ChatWindow, MapGrid, OverworldMap, TradeScreen, SaveLoadScreen, VehicleChaseScreen
from scripts.combat_simulator import simulate_trade
from ui.network import NetworkManager


class App:
    def __init__(self, width: int = 1000, height: int = 700, campaign_file: str = "campaigns/default/campaign.json", is_host: bool = True, host_ip: str = "127.0.0.1"):
        if not pygame.get_init():
            pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Shadowrun 7E - Interactive Cards")
        self.clock = pygame.time.Clock()
        self.running = True
        self.in_campaign_select = True
        self.in_overworld = False
        self.in_trade_screen = False
        self.trade_screen = TradeScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=self.close_trade, on_trade=self.execute_trade)

        self.in_save_load_screen = False
        self.in_chase_screen = False
        self.save_load_screen = SaveLoadScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400))
        self.chase_screen = VehicleChaseScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=lambda: setattr(self, 'in_chase_screen', False), on_action=lambda action: f"Performed {action}")


        self.pending_action = None
        self.pending_chat = None

        # Create dummy data initially

        player_combatant = load_combatant("npc_templates/Kyber.chum5")

        gm_combatant = load_combatant("npc_templates/Sargent_Igneous.chum5")
        gm_combatant.team = 1


        self.player_cards = [PlayerCard(player_combatant)]
        self.gm_cards = []


        chat_width = 300
        chat_rect = pygame.Rect(self.width - chat_width - 20, 20, chat_width, self.height - 40)
        self.chat_window = ChatWindow(chat_rect, on_submit=self.set_pending_chat)


        self.state = None
        self.map_grid = None
        self.scroll_x = 0
        self.scroll_y = 0

        self.is_host = is_host
        self.network_manager = NetworkManager(is_host=is_host, host_ip=host_ip)
        self.network_manager.start(self.network_update_callback)

        self.global_campaign_state = {"economy_multiplier": 1.0}
        self.overworld_map = None

    def network_update_callback(self, state):
        if not self.is_host:
            # When acting as client, receiving a full state update replaces the local state.
            # We call update_state so that the UI can refresh cards/maps normally.
            self.update_state(state)

    def load_campaign(self, campaign_file: str):
        import json
        import os
        import random
        campaign_nodes = []
        try:
            campaign_path = os.path.join(os.path.dirname(__file__), "..", campaign_file)
            if os.path.exists(campaign_path):
                with open(campaign_path, "r") as f:
                    data = json.load(f)
                    campaign_nodes = data.get("nodes", [])
                    random_nodes = data.get("random_nodes", [])
                    # Append some random nodes randomly
                    for r_node in random_nodes:
                        if random.random() < r_node.get("probability", 0.5):
                            campaign_nodes.append(r_node)
            else:
                print(f"Warning: {campaign_file} not found, loading empty map.")
        except Exception as e:
            print(f"Error loading {campaign_file}: {e}")

        self.overworld_map = OverworldMap(pygame.Rect(50, 100, 600, 400), on_node_click=self.load_module, nodes=campaign_nodes)
        self.in_campaign_select = False
        self.in_overworld = True
        self.in_trade_screen = False
        self.trade_screen = TradeScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=self.close_trade, on_trade=self.execute_trade)

        self.in_save_load_screen = False
        self.in_chase_screen = False
        self.save_load_screen = SaveLoadScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400))
        self.chase_screen = VehicleChaseScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=lambda: setattr(self, 'in_chase_screen', False), on_action=lambda action: f"Performed {action}")


    def load_module(self, module_path: str):
        import random
        # 20% chance to trigger random encounter if module_path is not already a random encounter
        if "random" not in module_path.lower() and random.random() < 0.20:
            print("RANDOM ENCOUNTER TRIGGERED!")
            # Default fallback for an ambush
            module_path = "campaigns/default/modules/random_ambush.json"

        print(f"Loading module: {module_path}")
        self.in_overworld = False
        self.in_trade_screen = False
        self.trade_screen = TradeScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=self.close_trade, on_trade=self.execute_trade)

        self.in_save_load_screen = False
        self.in_chase_screen = False
        self.save_load_screen = SaveLoadScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400))
        self.chase_screen = VehicleChaseScreen(pygame.Rect((self.width - 500) // 2, (self.height - 400) // 2, 500, 400), on_close=lambda: setattr(self, 'in_chase_screen', False), on_action=lambda action: f"Performed {action}")



    def close_trade(self):
        self.in_trade_screen = False

    def execute_trade(self, item_name, base_value, difficulty):
        if self.player_cards:
            buyer = self.player_cards[0].combatant

            # Apply economy multiplier
            multiplier = self.global_campaign_state.get("economy_multiplier", 1.0)
            adjusted_value = int(base_value * multiplier)

            import io
            import sys
            # Capture print output from simulate_trade
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            try:
                simulate_trade(buyer, item_name, adjusted_value, difficulty)
                output = new_stdout.getvalue()

                # Parse final price from output
                import re
                match = re.search(r"Final Price: (\d+)¥", output)
                if match:
                    return match.group(1) + "¥"
                elif "REFUSED" in output:
                    return "Refused"
                else:
                    return "Completed"
            finally:
                sys.stdout = old_stdout
        return "No Buyer"

    def set_pending_action(self, action: str):
        self.pending_action = action


    def set_pending_chat(self, chat_message: str):
        self.pending_chat = chat_message

    def display_chat_message(self, role: str, message: str):
        self.chat_window.add_message(role, message)



    def update_state(self, state):
        """Updates the internal UI cards with live data from the simulation."""
        # Deepcopy isn't needed here as Python assigns references, but we need to ensure
        # that client-side gets a valid state update without infinitely broadcasting.
        self.state = state

        if self.is_host:
            self.network_manager.broadcast_state(self.state)

        # Check for map data
        if getattr(self.state, "environment", None) and hasattr(self.state.environment, "scenario_data"):
            if self.state.environment.scenario_data:
                map_data = self.state.environment.scenario_data.get("map", None)
                if map_data and not self.map_grid:
                    layout = map_data.get("layout_ascii", [])
                    legend = map_data.get("legend", {})
                    self.map_grid = MapGrid(layout, legend)

        if self.map_grid and getattr(self.state, "environment", None):
            self.map_grid.blast_zones = getattr(self.state.environment, "recent_blasts", [])

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
        if not self.in_campaign_select and not self.in_overworld:
            start_y = 100 + self.scroll_y
            if self.map_grid:
                start_y += self.map_grid.rect.height + 20

            x_offset = 50 + self.scroll_x
            for card in self.player_cards:
                card.rect.topleft = (x_offset, start_y)
                card.update_rects()
                x_offset += 370

            x_offset = max(x_offset, 550 + self.scroll_x)
            for card in self.gm_cards:
                card.rect.topleft = (x_offset, start_y)
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

            if self.in_save_load_screen:
                self.save_load_screen.handle_event(event, self)
                continue

            if self.in_chase_screen:
                self.chase_screen.handle_event(event)
                continue

            if self.in_trade_screen:
                self.trade_screen.handle_event(event)
                continue
            if self.in_campaign_select:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Campaign select buttons
                    # 1: Default
                    # 2: Cold Storage
                    # 3: Necessity


                    if 100 <= mx <= 400:
                        if 150 <= my <= 200:
                            self.load_campaign("campaigns/default/campaign.json")
                        elif 220 <= my <= 270:
                            self.load_campaign("campaigns/cold_storage/campaign.json")
                        elif 290 <= my <= 340:
                            self.load_campaign("campaigns/necessity/campaign.json")

            elif self.in_overworld:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if self.width - 220 <= mx <= self.width - 20 and 20 <= my <= 70:
                        self.in_trade_screen = True
                        return
                    if self.width - 440 <= mx <= self.width - 240 and 20 <= my <= 70:
                        self.in_save_load_screen = True
                        self.save_load_screen.refresh_states()
                        return
                if self.overworld_map:
                    self.overworld_map.handle_event(event)
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if 250 <= mx <= 410 and 40 <= my <= 75:
                        self.in_save_load_screen = True
                        self.save_load_screen.refresh_states()
                        return
                    if self.state and getattr(self.state, "environment", None) and self.state.environment.is_chase_combat:
                        if 420 <= mx <= 580 and 40 <= my <= 75:
                            self.in_chase_screen = True
                            return
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

        if self.in_campaign_select:
            # Draw Campaign Select Screen
            title_surf = font.render("SELECT CAMPAIGN", True, (0, 255, 204))
            self.screen.blit(title_surf, (100, 100))

            # Button 1: Default
            pygame.draw.rect(self.screen, (40, 45, 55), (100, 150, 300, 50), border_radius=4)
            def_text = font.render("Default Demo Campaign", True, (230, 230, 235))
            self.screen.blit(def_text, (120, 165))

            # Button 2: Cold Storage
            pygame.draw.rect(self.screen, (40, 45, 55), (100, 220, 300, 50), border_radius=4)
            cs_text = font.render("Cold Storage Campaign", True, (230, 230, 235))
            self.screen.blit(cs_text, (120, 235))

            # Button 3: Necessity
            pygame.draw.rect(self.screen, (40, 45, 55), (100, 290, 300, 50), border_radius=4)
            nec_text = font.render("Necessity Knows No Law", True, (230, 230, 235))
            self.screen.blit(nec_text, (120, 305))



        elif self.in_overworld:
            if self.overworld_map:
                self.overworld_map.draw(self.screen)
            pygame.draw.rect(self.screen, (40, 45, 55), (self.width - 220, 20, 200, 50), border_radius=4)
            pygame.draw.rect(self.screen, (0, 255, 204), (self.width - 220, 20, 200, 50), 2, border_radius=4)
            trade_text = font.render("Open Market", True, (230, 230, 235))
            self.screen.blit(trade_text, (self.width - 180, 35))

            pygame.draw.rect(self.screen, (40, 45, 55), (self.width - 440, 20, 200, 50), border_radius=4)
            pygame.draw.rect(self.screen, (0, 255, 204), (self.width - 440, 20, 200, 50), 2, border_radius=4)
            sm_text = font.render("State Manager", True, (230, 230, 235))
            self.screen.blit(sm_text, (self.width - 410, 35))
        else:
            if self.state:
                turn_text = f"Turn: {self.state.turn}"
                turn_surf = font.render(turn_text, True, (220, 220, 220))
                self.screen.blit(turn_surf, (50, 50))

            # Tactical state manager button
            pygame.draw.rect(self.screen, (40, 45, 55), (250, 40, 160, 35), border_radius=4)
            pygame.draw.rect(self.screen, (0, 255, 204), (250, 40, 160, 35), 2, border_radius=4)
            font_sm = pygame.font.SysFont("monospace", 14, bold=True)
            sm_text = font_sm.render("STATE MANAGER", True, (230, 230, 235))
            self.screen.blit(sm_text, (270, 50))

            if self.state and getattr(self.state, "environment", None) and self.state.environment.is_chase_combat:
                pygame.draw.rect(self.screen, (40, 45, 55), (420, 40, 160, 35), border_radius=4)
                pygame.draw.rect(self.screen, (255, 204, 0), (420, 40, 160, 35), 2, border_radius=4)
                chase_text = font_sm.render("CHASE MINIGAME", True, (230, 230, 235))
                self.screen.blit(chase_text, (440, 50))

            start_y = 100 + self.scroll_y

            if self.map_grid:
                self.map_grid.draw(self.screen, 50, 100 + self.scroll_y)
                start_y += self.map_grid.rect.height + 20

            # Draw cards side by side
            x_offset = 50 + self.scroll_x
            for card in self.player_cards:
                card.draw(self.screen, x_offset, start_y)
                x_offset += 370


            x_offset = max(x_offset, 550 + self.scroll_x)
            for card in self.gm_cards:
                card.draw(self.screen, x_offset, start_y)
                x_offset += 370

            self.chat_window.draw(self.screen)


        if self.in_trade_screen:
            self.trade_screen.draw(self.screen)

        if self.in_save_load_screen:
            self.save_load_screen.draw(self.screen)

        if self.in_chase_screen:
            self.chase_screen.draw(self.screen)

        pygame.display.flip()
