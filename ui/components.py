import pygame
from dataclasses import dataclass
from scripts.combat_simulator import Combatant

# Define some useful colors
COLORS = {
    "bg": (30, 30, 30),
    "border": (0, 204, 255),  # matrixblue
    "border_gm": (230, 57, 70),  # sraccent (reddish)
    "text": (220, 220, 220),
    "text_dark": (150, 150, 150),
    "panel_bg": (45, 45, 45),
    "health_ok": (50, 200, 50),
    "health_warn": (200, 200, 50),
    "health_crit": (200, 50, 50),
    "highlight": (80, 80, 80),
    "panel_bg_gm": (60, 20, 20),
    "panel_bg_player": (20, 60, 60),
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

        # Edge
        edge_text = f"Edge: {self.combatant.edge}"
        edge_surf = self.font_body.render(edge_text, True, COLORS["border"])
        surface.blit(
            edge_surf,
            (panel_rect.right - edge_surf.get_width() - 10, panel_rect.y + 10),
        )

    def _draw_action_button(self, surface: pygame.Surface, rect: pygame.Rect, text_render: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)

        bg_color = COLORS["highlight"] if is_hovered else (60, 60, 60)

        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

        # Center the text vertically and pad horizontally
        text_x = rect.x + 8
        text_y = rect.y + (rect.height - text_render.get_height()) // 2
        surface.blit(text_render, (text_x, text_y))

    def _draw_action_button(self, surface: pygame.Surface, rect: pygame.Rect, text_render: pygame.Surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)

        bg_color = COLORS["highlight"] if is_hovered else (60, 60, 60)

        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

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

        # Draw health bars
        bar_width = 150
        bar_height = 14

        p_ratio = max(0, min(1, (p_track - p_dmg) / max(1, p_track)))
        s_ratio = max(0, min(1, (s_track - s_dmg) / max(1, s_track)))

        p_bg_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, bar_width, bar_height)
        p_fill_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 10, int(bar_width * p_ratio), bar_height)

        s_bg_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 30, bar_width, bar_height)
        s_fill_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 30, int(bar_width * s_ratio), bar_height)

        pygame.draw.rect(surface, (60, 60, 60), p_bg_rect, border_radius=2)
        pygame.draw.rect(surface, p_color, p_fill_rect, border_radius=2)

        pygame.draw.rect(surface, (60, 60, 60), s_bg_rect, border_radius=2)
        pygame.draw.rect(surface, s_color, s_fill_rect, border_radius=2)

        # Draw text over bars, using white/light text for contrast or shadow
        phys_render = self.font_body.render(phys_text, True, (255, 255, 255))
        surface.blit(phys_render, (panel_rect.x + 15, panel_rect.y + 9))

        stun_render = self.font_body.render(stun_text, True, (255, 255, 255))
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
            self.action_rects.append((btn_rect, f"attack with {w.name}"))
            y_offset += 26

        y_offset += 10
        if self.combatant.spells:
            y_offset += 20
            for s in self.combatant.spells[:2]:
                spl_text = f"{s.name}"
                rendered_text = self.font_small.render(spl_text, True, COLORS["text"])
                btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, rendered_text.get_width() + 16, 24)
                self.action_rects.append((btn_rect, f"cast {s.name}"))
                y_offset += 26

        y_offset += 10
        y_offset += 20
        if self.combatant.matrix.attack > 0:
            ds_text = "Data Spike"
            ds_render = self.font_small.render(ds_text, True, COLORS["text"])
            btn_rect = pygame.Rect(panel_rect.x + 15, y_offset - 2, ds_render.get_width() + 16, 24)
            self.action_rects.append((btn_rect, "data spike"))
            y_offset += 26

        if self.combatant.tethers:
            y_offset += 18
        if self.combatant.influence or self.combatant.resolve:
            y_offset += 18

        y_offset += 10
        y_offset += 20

        for action_name, action_cmd in [("Sprint", "sprint"), ("Take Cover", "take cover"), ("Yield", "yield")]:
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

            for action_name, action_cmd in [("Sprint", "sprint"), ("Take Cover", "take cover"), ("Yield", "yield")]:
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
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, COLORS.get("border", (100, 100, 100)), self.rect, 2)

        input_height = 30
        input_rect = pygame.Rect(self.rect.x + 5, self.rect.bottom - input_height - 5, self.rect.width - 10, input_height)

        msg_area_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, self.rect.width - 10, self.rect.height - input_height - 15)

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
