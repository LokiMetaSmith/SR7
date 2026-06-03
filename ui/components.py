import pygame
import os
from dataclasses import dataclass

_IMAGE_CACHE = {}

from scripts.combat_simulator import Combatant

# Define some useful colors
# Define cyberpunk/Shadowrun themed colors
COLORS = {
    "bg": (15, 15, 18),               # Deep dark background
    "border": (0, 255, 204),          # Neon cyan for players
    "border_gm": (255, 50, 80),       # Neon pink/red for GM
    "text": (230, 230, 235),          # Off-white text
    "text_dark": (140, 150, 160),     # Muted text
    "panel_bg": (25, 25, 30),         # Slightly lighter dark
    "health_ok": (46, 204, 113),      # Emerald green
    "health_warn": (241, 196, 15),    # Warning yellow
    "health_crit": (231, 76, 60),     # Danger red
    "highlight": (0, 204, 255, 60),   # Highlight with alpha
    "panel_bg_gm": (50, 10, 20),      # Dark red tint
    "panel_bg_player": (10, 30, 40),  # Dark blue/cyan tint
    "button_bg": (40, 45, 55),        # Button idle
    "button_hover": (60, 120, 150),   # Button hover (player)
    "button_hover_gm": (150, 60, 80), # Button hover (GM)
}


class BaseCard:
    def __init__(
        self, combatant: Combatant, width: int = 350, height: int = 500, on_action=None
    ):
        self.combatant = combatant
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.font_title = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_body = pygame.font.SysFont("sans", 14)
        self.font_small = pygame.font.SysFont("sans", 12)
        self.is_gm = False
        self.expanded = False
        self.on_action = on_action
        self.action_rects = []  # List of tuples: (pygame.Rect, action_string)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check action buttons first if expanded
                if self.expanded:
                    for r, action_str in self.action_rects:
                        if r.collidepoint(event.pos):
                            if self.on_action:
                                self.on_action(action_str)
                            return True

                # Otherwise, left click on card expands/collapses
                if self.rect.collidepoint(event.pos):
                    self.expanded = not self.expanded
                    self.update_rects()
                    return True
        return False

    def draw(self, surface: pygame.Surface, x: int, y: int):
        self.rect.topleft = (x, y)

        # Main background
        pygame.draw.rect(surface, COLORS["bg"], self.rect)

        # Border
        border_color = COLORS["border_gm"] if self.is_gm else COLORS["border"]
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=5)

        # Draw the three panels
        self._draw_panel_1_identity(surface)
        self._draw_panel_2_status(surface)
        self._draw_panel_3_mechanics(surface)

    def _draw_panel_1_identity(self, surface: pygame.Surface):
        # Panel 1: Identity & Core Stats (Top)
        panel_rect = pygame.Rect(
            self.rect.x + 5, self.rect.y + 5, self.rect.width - 10, 80
        )
        bg_color = COLORS["panel_bg_gm"] if self.is_gm else COLORS["panel_bg_player"]
        pygame.draw.rect(surface, bg_color, panel_rect, border_radius=3)

        # Name
        title_surf = self.font_title.render(self.combatant.name, True, COLORS["text"])
        surface.blit(title_surf, (panel_rect.x + 10, panel_rect.y + 10))

        # Attributes (BOD, AGI, REA, STR, WIL, LOG, INT, CHA)
        attrs = self.combatant.attributes
        attr_text = f"BOD:{attrs.get('BOD',0)} AGI:{attrs.get('AGI',0)} REA:{attrs.get('REA',0)} STR:{attrs.get('STR',0)}"
        attr_text2 = f"WIL:{attrs.get('WIL',0)} LOG:{attrs.get('LOG',0)} INT:{attrs.get('INT',0)} CHA:{attrs.get('CHA',0)}"

        attr_surf = self.font_small.render(attr_text, True, COLORS["text_dark"])
        attr_surf2 = self.font_small.render(attr_text2, True, COLORS["text_dark"])

        surface.blit(attr_surf, (panel_rect.x + 10, panel_rect.y + 35))
        surface.blit(attr_surf2, (panel_rect.x + 10, panel_rect.y + 50))

        # Portrait
        portrait_width = 0
        if getattr(self.combatant, "portrait", None):
            portrait_path = self.combatant.portrait
            if portrait_path not in _IMAGE_CACHE:
                actual_path = None
                if os.path.exists(portrait_path):
                    actual_path = portrait_path
                else:
                    filename = os.path.basename(portrait_path)
                    if os.path.exists(os.path.join("npc_templates", filename)):
                        actual_path = os.path.join("npc_templates", filename)

                if actual_path:
                    try:
                        img = pygame.image.load(actual_path).convert_alpha()
                        img = pygame.transform.smoothscale(img, (60, 60))
                        _IMAGE_CACHE[portrait_path] = img
                    except Exception:
                        _IMAGE_CACHE[portrait_path] = None
                else:
                    _IMAGE_CACHE[portrait_path] = None

            cached_img = _IMAGE_CACHE.get(portrait_path)
            if cached_img:
                portrait_width = 60
                surface.blit(cached_img, (panel_rect.right - portrait_width - 10, panel_rect.y + 10))

        # Edge
        edge_text = f"Edge: {self.combatant.edge}"
        edge_surf = self.font_body.render(edge_text, True, COLORS["border"])
        edge_x = panel_rect.right - edge_surf.get_width() - 10
        if portrait_width > 0:
            edge_x -= (portrait_width + 10)
        surface.blit(edge_surf, (edge_x, panel_rect.y + 10))

    def _draw_action_button(self, surface: pygame.Surface, rect: pygame.Rect, text_render: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)

        if is_hovered:
            bg_color = COLORS["button_hover_gm"] if self.is_gm else COLORS["button_hover"]
        else:
            bg_color = COLORS["button_bg"]

        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

        # Draw a thin border when hovered
        if is_hovered:
            border_c = COLORS["border_gm"] if self.is_gm else COLORS["border"]
            pygame.draw.rect(surface, border_c, rect, 1, border_radius=4)

        # Center the text vertically and pad horizontally
        text_x = rect.x + 8
        text_y = rect.y + (rect.height - text_render.get_height()) // 2
        surface.blit(text_render, (text_x, text_y))

    def _draw_action_button(self, surface: pygame.Surface, rect: pygame.Rect, text_render: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)

        if is_hovered:
            bg_color = COLORS["button_hover_gm"] if self.is_gm else COLORS["button_hover"]
        else:
            bg_color = COLORS["button_bg"]

        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

        # Draw a thin border when hovered
        if is_hovered:
            border_c = COLORS["border_gm"] if self.is_gm else COLORS["border"]
            pygame.draw.rect(surface, border_c, rect, 1, border_radius=4)

        # Center the text vertically and pad horizontally
        text_x = rect.x + 8
        text_y = rect.y + (rect.height - text_render.get_height()) // 2
        surface.blit(text_render, (text_x, text_y))

    def _draw_panel_2_status(self, surface: pygame.Surface):
        # Panel 2: Status (Middle)
        panel_rect = pygame.Rect(
            self.rect.x + 5, self.rect.y + 90, self.rect.width - 10, 100
        )
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=3)

        # Physical / Stun Tracks
        p_track = self.combatant.physical_track
        p_dmg = self.combatant.physical_damage
        s_track = self.combatant.stun_track
        s_dmg = self.combatant.stun_damage

        phys_text = f"Physical: {p_dmg}/{p_track}"
        stun_text = f"Stun: {s_dmg}/{s_track}"

        p_color = (
            COLORS["health_ok"]
            if p_dmg < p_track / 2
            else (COLORS["health_warn"] if p_dmg < p_track else COLORS["health_crit"])
        )
        s_color = (
            COLORS["health_ok"]
            if s_dmg < s_track / 2
            else (COLORS["health_warn"] if s_dmg < s_track else COLORS["health_crit"])
        )

        # Draw segmented health bars
        bar_width = 160
        bar_height = 16

        p_ratio = max(0, min(1, (p_track - p_dmg) / max(1, p_track)))
        s_ratio = max(0, min(1, (s_track - s_dmg) / max(1, s_track)))

        p_bg_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, bar_width, bar_height)
        p_fill_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, int(bar_width * p_ratio), bar_height)

        s_bg_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 30, bar_width, bar_height)
        s_fill_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 30, int(bar_width * s_ratio), bar_height)

        pygame.draw.rect(surface, (40, 20, 20), p_bg_rect, border_radius=2)
        pygame.draw.rect(surface, p_color, p_fill_rect, border_radius=2)

        # Physical segments
        if p_track > 0:
            seg_w = bar_width / p_track
            for i in range(1, p_track):
                pygame.draw.line(surface, COLORS["panel_bg"], (p_bg_rect.x + int(i * seg_w), p_bg_rect.y), (p_bg_rect.x + int(i * seg_w), p_bg_rect.bottom - 1), 2)
        pygame.draw.rect(surface, (100, 100, 100), p_bg_rect, 1, border_radius=2)

        pygame.draw.rect(surface, (20, 20, 40), s_bg_rect, border_radius=2)
        pygame.draw.rect(surface, s_color, s_fill_rect, border_radius=2)

        # Stun segments
        if s_track > 0:
            seg_w = bar_width / s_track
            for i in range(1, s_track):
                pygame.draw.line(surface, COLORS["panel_bg"], (s_bg_rect.x + int(i * seg_w), s_bg_rect.y), (s_bg_rect.x + int(i * seg_w), s_bg_rect.bottom - 1), 2)
        pygame.draw.rect(surface, (100, 100, 100), s_bg_rect, 1, border_radius=2)

        # Draw text over bars with slight shadow
        phys_render_shadow = self.font_body.render(phys_text, True, (0, 0, 0))
        phys_render = self.font_body.render(phys_text, True, (255, 255, 255))
        surface.blit(phys_render_shadow, (panel_rect.x + 16, panel_rect.y + 10))
        surface.blit(phys_render, (panel_rect.x + 15, panel_rect.y + 9))

        stun_render_shadow = self.font_body.render(stun_text, True, (0, 0, 0))
        stun_render = self.font_body.render(stun_text, True, (255, 255, 255))
        surface.blit(stun_render_shadow, (panel_rect.x + 16, panel_rect.y + 30))
        surface.blit(stun_render, (panel_rect.x + 15, panel_rect.y + 29))

        # Armor & Initiative
        armor_text = f"Armor: {self.combatant.armor}"
        init_text = f"Initiative: {self.combatant.initiative_score}"

        surface.blit(
            self.font_body.render(armor_text, True, COLORS["text"]),
            (panel_rect.x + 10, panel_rect.y + 55),
        )
        surface.blit(
            self.font_body.render(init_text, True, COLORS["text"]),
            (panel_rect.x + 10, panel_rect.y + 75),
        )

        # Alive Status
        status_text = "ALIVE" if self.combatant.is_alive else "DEAD/UNCONSCIOUS"
        status_color = (
            COLORS["health_ok"] if self.combatant.is_alive else COLORS["health_crit"]
        )
        if self.combatant.has_yielded:
            status_text = "YIELDED"
            status_color = COLORS["health_warn"]

        surf_status = self.font_title.render(status_text, True, status_color)
        surface.blit(
            surf_status,
            (panel_rect.right - surf_status.get_width() - 10, panel_rect.y + 10),
        )

    def update_rects(self):
        self.action_rects.clear()
        if not self.expanded:
            return

        panel_rect = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 195,
            self.rect.width - 10,
            self.rect.height - 200,
        )
        y_offset = panel_rect.y + 10
        y_offset += 20

        for w in self.combatant.weapons[:3]:
            wpn_text = f"{w.name} (DV:{w.damage} AP:{w.ap})"
            rendered_text = self.font_small.render(wpn_text, True, COLORS["text"])
            btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, rendered_text.get_width() + 16, 24)
            self._draw_action_button(surface, btn_rect, rendered_text)
            self.action_rects.append((btn_rect, f"attack with {w.name}"))
            y_offset += 26

        y_offset += 10
        if self.combatant.spells:
            y_offset += 20
            for s in self.combatant.spells[:2]:
                spl_text = f"{s.name}"
                rendered_text = self.font_small.render(spl_text, True, COLORS["text"])
                btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, rendered_text.get_width() + 16, 24)
                self._draw_action_button(surface, btn_rect, rendered_text)
                self.action_rects.append((btn_rect, f"cast {s.name}"))
                y_offset += 26

        y_offset += 10
        y_offset += 20
        if self.combatant.matrix.attack > 0:
            ds_text = "Data Spike"
            ds_render = self.font_small.render(ds_text, True, COLORS["text"])
            btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, ds_render.get_width() + 16, 24)
            self._draw_action_button(surface, btn_rect, ds_render)
            self.action_rects.append((btn_rect, "data spike"))
            y_offset += 26

        if self.combatant.tethers:
            y_offset += 18
        if self.combatant.influence or self.combatant.resolve:
            y_offset += 18

        y_offset += 10
        y_offset += 20

        for action_name, action_cmd in [("Sprint", "sprint"), ("Take Cover", "take cover"), ("Yield", "yield"), ("Pass Turn", "pass")]:
            act_render = self.font_small.render(f"{action_name}", True, COLORS["text"])
            btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, act_render.get_width() + 16, 24)
            self.action_rects.append((btn_rect, action_cmd))
            y_offset += 26

    def _draw_panel_3_mechanics(self, surface: pygame.Surface):
        self.action_rects.clear()

        # Panel 3: Mechanics (Bottom)
        panel_rect = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 195,
            self.rect.width - 10,
            self.rect.height - 200,
        )
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=3)

        y_offset = panel_rect.y + 10

        # Weapons
        wpn_header = self.font_body.render("Weapons:", True, COLORS["text"])
        surface.blit(wpn_header, (panel_rect.x + 10, y_offset))
        y_offset += 20
        for w in self.combatant.weapons[:3]: # Show up to 3
            wpn_text = f"{w.name} (DV:{w.damage} AP:{w.ap})"
            rendered_text = self.font_small.render(wpn_text, True, COLORS["text"])

            if self.expanded:
                btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, rendered_text.get_width() + 16, 24)
                self._draw_action_button(surface, btn_rect, rendered_text)
                self.action_rects.append((btn_rect, f"attack with {w.name}"))
                y_offset += 26
            else:
                surface.blit(rendered_text, (panel_rect.x + 20, y_offset))
                y_offset += 18

        # Matrix/Spells/Tethers if expanded or relevant
        if self.expanded:
            y_offset += 10
            if self.combatant.spells:
                spl_header = self.font_body.render("Spells:", True, COLORS["text"])
                surface.blit(spl_header, (panel_rect.x + 10, y_offset))
                y_offset += 20
                for s in self.combatant.spells[:2]:
                    spl_text = f"{s.name}"
                    rendered_text = self.font_small.render(spl_text, True, COLORS["text"])
                    btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, rendered_text.get_width() + 16, 24)
                    self._draw_action_button(surface, btn_rect, rendered_text)
                    self.action_rects.append((btn_rect, f"cast {s.name}"))
                    y_offset += 26

            y_offset += 10
            mat_header = self.font_body.render(
                f"Matrix (A:{self.combatant.matrix.attack} S:{self.combatant.matrix.sleaze} D:{self.combatant.matrix.data_processing} F:{self.combatant.matrix.firewall})",
                True,
                COLORS["text"],
            )
            surface.blit(mat_header, (panel_rect.x + 10, y_offset))
            y_offset += 20

            if self.combatant.matrix.attack > 0:
                ds_text = "Data Spike"
                ds_render = self.font_small.render(ds_text, True, COLORS["text"])
                btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, ds_render.get_width() + 16, 24)
                self._draw_action_button(surface, btn_rect, ds_render)
                self.action_rects.append((btn_rect, "data spike"))
                y_offset += 26

            if self.combatant.tethers:
                teth_text = f"Tethers: {len(self.combatant.tethers)}"
                surface.blit(
                    self.font_small.render(teth_text, True, COLORS["border"]),
                    (panel_rect.x + 20, y_offset),
                )
                y_offset += 18

            if self.combatant.influence or self.combatant.resolve:
                soc_text = f"Social: Inf({len(self.combatant.influence)}) Res({len(self.combatant.resolve)})"
                surface.blit(
                    self.font_small.render(soc_text, True, COLORS["border_gm"]),
                    (panel_rect.x + 20, y_offset),
                )
                y_offset += 18

            y_offset += 10
            actions_header = self.font_body.render(
                "General Actions:", True, COLORS["text"]
            )
            surface.blit(actions_header, (panel_rect.x + 10, y_offset))
            y_offset += 20

            for action_name, action_cmd in [("Sprint", "sprint"), ("Take Cover", "take cover"), ("Yield", "yield"), ("Pass Turn", "pass")]:
                act_render = self.font_small.render(f"{action_name}", True, COLORS["text"])
                btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, act_render.get_width() + 16, 24)
                self._draw_action_button(surface, btn_rect, act_render)
                self.action_rects.append((btn_rect, action_cmd))
                y_offset += 26


class PlayerCard(BaseCard):
    def __init__(
        self, combatant: Combatant, width: int = 350, height: int = 500, on_action=None
    ):
        super().__init__(combatant, width, height, on_action)
        self.is_gm = False


class GMCard(BaseCard):
    def __init__(
        self, combatant: Combatant, width: int = 350, height: int = 500, on_action=None
    ):
        super().__init__(combatant, width, height, on_action)
        self.is_gm = True



class ChatWindow:
    def __init__(self, rect: pygame.Rect, on_submit=None):
        self.rect = pygame.Rect(rect)
        self.messages = []
        self.input_text = ""
        self.active = False
        self.font = pygame.font.SysFont("monospace", 14)
        self.on_submit = on_submit
        self.scroll_y = 0

    def add_message(self, role: str, text: str):
        self.messages.append({"role": role, "text": text})
        self.scroll_y = -999999  # scroll to bottom flag

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                if self.input_text.strip() and self.on_submit:
                    self.on_submit(self.input_text.strip())
                    self.add_message("User", self.input_text.strip())
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        elif event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y += event.y * 20

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, COLORS.get("panel_bg", (30, 30, 30)), self.rect)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), self.rect, 2, border_radius=4)

        # Draw a header for chat
        header_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 25)
        pygame.draw.rect(surface, (20, 25, 30), header_rect, border_top_left_radius=4, border_top_right_radius=4)
        pygame.draw.line(surface, COLORS.get("border", (100, 100, 100)), (self.rect.x, self.rect.y + 25), (self.rect.right, self.rect.y + 25))
        title = self.font.render("COMMLINK LINK", True, COLORS.get("border", (100, 100, 100)))
        surface.blit(title, (self.rect.x + 10, self.rect.y + 5))

        input_height = 30
        input_rect = pygame.Rect(self.rect.x + 5, self.rect.bottom - input_height - 5, self.rect.width - 10, input_height)

        msg_area_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 30, self.rect.width - 10, self.rect.height - input_height - 40)

        old_clip = surface.get_clip()
        surface.set_clip(msg_area_rect)

        lines_to_draw = []
        for msg in self.messages:
            role_color = (150, 200, 255) if msg["role"] == "User" else (200, 150, 255)
            words = f"{msg['role']}: {msg['text']}".split(' ')
            line = ""
            for word in words:
                if self.font.size(line + word)[0] < msg_area_rect.width - 10:
                    line += word + " "
                else:
                    lines_to_draw.append((line, role_color))
                    line = word + " "
            if line:
                lines_to_draw.append((line, role_color))

        total_height = len(lines_to_draw) * 18

        max_scroll = 0
        min_scroll = min(0, msg_area_rect.height - total_height)

        if self.scroll_y == -999999:
            self.scroll_y = min_scroll
        else:
            self.scroll_y = max(min_scroll, min(max_scroll, self.scroll_y))

        y_offset = msg_area_rect.y + self.scroll_y
        for text, color in lines_to_draw:
            if msg_area_rect.y - 18 <= y_offset <= msg_area_rect.bottom:
                surf = self.font.render(text, True, color)
                surface.blit(surf, (msg_area_rect.x + 5, y_offset))
            y_offset += 18

        surface.set_clip(old_clip)

        pygame.draw.rect(surface, (50, 50, 50) if self.active else (40, 40, 40), input_rect)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), input_rect, 1)

        input_display = self.input_text
        while self.font.size(input_display)[0] > input_rect.width - 10:
            input_display = input_display[1:]

        input_surf = self.font.render(input_display, True, (255, 255, 255))
        surface.blit(input_surf, (input_rect.x + 5, input_rect.y + 7))



class OverworldMap:
    def __init__(self, rect: pygame.Rect, on_node_click=None, nodes=None):
        self.rect = pygame.Rect(rect)
        self.on_node_click = on_node_click
        self.font = pygame.font.SysFont("monospace", 14, bold=True)
        self.nodes = nodes if nodes is not None else []

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for node in self.nodes:
                node_x = self.rect.x + node["x"]
                node_y = self.rect.y + node["y"]
                distance = ((event.pos[0] - node_x) ** 2 + (event.pos[1] - node_y) ** 2) ** 0.5
                if distance <= node["radius"]:
                    if self.on_node_click:
                        self.on_node_click(node["module"])

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, COLORS.get("panel_bg", (30, 30, 30)), self.rect, border_radius=4)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), self.rect, 2, border_radius=4)

        title_surf = self.font.render("OVERWORLD MAP", True, (0, 255, 204))
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 20))

        if len(self.nodes) > 1:
            for i in range(len(self.nodes) - 1):
                start = (self.rect.x + self.nodes[i]["x"], self.rect.y + self.nodes[i]["y"])
                end = (self.rect.x + self.nodes[i+1]["x"], self.rect.y + self.nodes[i+1]["y"])
                pygame.draw.line(surface, (100, 100, 100), start, end, 2)

        for node in self.nodes:
            center = (self.rect.x + node["x"], self.rect.y + node["y"])
            pygame.draw.circle(surface, (255, 0, 128), center, node["radius"])
            pygame.draw.circle(surface, (255, 255, 255), center, node["radius"], 2)

            name_surf = self.font.render(node["name"], True, (255, 255, 255))
            name_rect = name_surf.get_rect(center=(center[0], center[1] + 25))
            surface.blit(name_surf, name_rect)


class MapGrid:
    def __init__(self, layout_ascii, legend):
        self.layout_ascii = layout_ascii
        self.legend = legend
        self.cell_size = 30
        self.margin = 10
        self.font = pygame.font.SysFont("monospace", 14)

        self.blast_zones = [] # Store zones to highlight for AoE explosions

        self.colors = {
            ".": (40, 40, 40), # Default ground
            " ": (0, 0, 0, 0)  # Transparent/Empty
        }

        # Auto-assign colors for legend keys
        palette = [
            (100, 50, 50), (50, 100, 50), (50, 50, 100),
            (100, 100, 50), (100, 50, 100), (50, 100, 100),
            (150, 80, 20), (20, 150, 80)
        ]
        color_idx = 0
        for key in legend:
            if key not in self.colors:
                self.colors[key] = palette[color_idx % len(palette)]
                color_idx += 1

        # Parse layout grid dimensions
        self.rows = len(layout_ascii)
        self.cols = max((len(row) for row in layout_ascii)) if self.rows > 0 else 0

        # Calculate width/height
        self.grid_width = self.cols * self.cell_size
        self.grid_height = self.rows * self.cell_size

        self.rect = pygame.Rect(0, 0, self.grid_width + 300, max(self.grid_height, len(self.legend) * 20) + 40)

    def draw(self, surface: pygame.Surface, x: int, y: int):
        self.rect.topleft = (x, y)

        # Draw background panel
        pygame.draw.rect(surface, COLORS.get("panel_bg", (30, 30, 30)), self.rect, border_radius=4)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), self.rect, 2, border_radius=4)

        # Draw Map title
        title_surf = self.font.render("TACTICAL MAP", True, (200, 200, 200))
        surface.blit(title_surf, (x + 10, y + 10))

        grid_x = x + 10
        grid_y = y + 30

        # Draw the grid cells
        for r, row_str in enumerate(self.layout_ascii):
            for c, char in enumerate(row_str):
                cell_rect = pygame.Rect(grid_x + c * self.cell_size, grid_y + r * self.cell_size, self.cell_size, self.cell_size)

                # Fill color
                color = self.colors.get(char, self.colors.get(".", (40, 40, 40)))

                # Highlight if in a blast zone (we can match by legend key if the zone name matches the legend description roughly)
                # But since the MapGrid just draws characters, we'll highlight cells that belong to the blasted zones.
                # A simple way: if `desc` in legend matches any `zone_name` in `self.blast_zones`.
                is_blasted = False
                if char in self.legend:
                    desc = self.legend[char].lower()
                    for bz in self.blast_zones:
                        if bz.lower() in desc or desc in bz.lower():
                            is_blasted = True

                if is_blasted:
                    color = (200, 50, 50) # Orange-red blast hue

                if char != " ":
                    pygame.draw.rect(surface, color, cell_rect)

                # Outline
                pygame.draw.rect(surface, (80, 80, 80), cell_rect, 1)

                # Draw blast effect over it
                if is_blasted:
                    s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    s.fill((255, 100, 0, 80)) # Semi transparent orange
                    surface.blit(s, cell_rect.topleft)

                # Text char
                if char.strip() and char != ".":
                    char_surf = self.font.render(char, True, (255, 255, 255))
                    char_rect = char_surf.get_rect(center=cell_rect.center)
                    surface.blit(char_surf, char_rect)

        # Draw the legend to the right of the grid
        legend_x = grid_x + self.grid_width + 20
        legend_y = grid_y

        legend_title = self.font.render("LEGEND:", True, (200, 200, 200))
        surface.blit(legend_title, (legend_x, legend_y))
        legend_y += 20

        for key, desc in self.legend.items():
            color = self.colors.get(key, (100, 100, 100))
            # Draw color box
            box_rect = pygame.Rect(legend_x, legend_y + 2, 12, 12)
            pygame.draw.rect(surface, color, box_rect)
            pygame.draw.rect(surface, (200, 200, 200), box_rect, 1)

            # Draw text
            # Truncate text if it's too long
            desc_str = f"{key} - {desc}"
            if len(desc_str) > 30:
                desc_str = desc_str[:27] + "..."

            text_surf = self.font.render(desc_str, True, (180, 180, 180))
            surface.blit(text_surf, (legend_x + 20, legend_y))
            legend_y += 18

class TradeScreen:
    def __init__(self, rect: pygame.Rect, on_close=None, on_trade=None):
        self.rect = pygame.Rect(rect)
        self.on_close = on_close
        self.on_trade = on_trade
        self.font_title = pygame.font.SysFont("monospace", 24, bold=True)
        self.font_body = pygame.font.SysFont("monospace", 16)

        self.close_rect = pygame.Rect(self.rect.right - 40, self.rect.y + 10, 30, 30)
        self.trade_rect = pygame.Rect(self.rect.centerx - 75, self.rect.bottom - 60, 150, 40)

        self.buyer_name = "Player"
        self.item_name = "Ares Predator"
        self.item_value = 350
        self.fixer_difficulty = 1

        self.trade_result = None

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.close_rect.collidepoint(event.pos):
                    if self.on_close:
                        self.on_close()
                elif self.trade_rect.collidepoint(event.pos):
                    if self.on_trade:
                        self.trade_result = self.on_trade(self.item_name, self.item_value, self.fixer_difficulty)

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, COLORS.get("panel_bg", (30, 30, 30)), self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), self.rect, 2, border_radius=8)

        # Title
        title_surf = self.font_title.render("BLACK MARKET TRADE", True, (0, 255, 204))
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 20))

        # Close button
        pygame.draw.rect(surface, COLORS.get("health_crit", (200, 50, 50)), self.close_rect, border_radius=4)
        x_surf = self.font_title.render("X", True, (255, 255, 255))
        surface.blit(x_surf, (self.close_rect.x + 8, self.close_rect.y + 2))

        # Content
        y_offset = self.rect.y + 80

        buyer_surf = self.font_body.render(f"Buyer: {self.buyer_name}", True, COLORS.get("text", (200, 200, 200)))
        surface.blit(buyer_surf, (self.rect.x + 40, y_offset))
        y_offset += 30

        item_surf = self.font_body.render(f"Item: {self.item_name} (Base: {self.item_value}¥)", True, COLORS.get("text", (200, 200, 200)))
        surface.blit(item_surf, (self.rect.x + 40, y_offset))
        y_offset += 30

        diff_surf = self.font_body.render(f"Fixer Difficulty: {self.fixer_difficulty}", True, COLORS.get("text", (200, 200, 200)))
        surface.blit(diff_surf, (self.rect.x + 40, y_offset))
        y_offset += 50

        if self.trade_result:
            res_surf = self.font_body.render(f"Result: {self.trade_result}", True, (255, 215, 0))
            surface.blit(res_surf, (self.rect.x + 40, y_offset))

        # Trade Button
        pygame.draw.rect(surface, COLORS.get("button_bg", (50, 60, 70)), self.trade_rect, border_radius=4)
        pygame.draw.rect(surface, (0, 200, 150), self.trade_rect, 2, border_radius=4)
        trade_text = self.font_body.render("HAGGLE", True, (255, 255, 255))
        surface.blit(trade_text, (self.trade_rect.x + 45, self.trade_rect.y + 10))
