import pygame
from dataclasses import dataclass
from scripts.combat_simulator import Combatant

# Define some useful colors
COLORS = {
    "bg": (30, 30, 30),
    "border": (0, 204, 255),          # matrixblue
    "border_gm": (230, 57, 70),       # sraccent (reddish)
    "text": (220, 220, 220),
    "text_dark": (150, 150, 150),
    "panel_bg": (45, 45, 45),
    "health_ok": (50, 200, 50),
    "health_warn": (200, 200, 50),
    "health_crit": (200, 50, 50),
    "highlight": (80, 80, 80)
}

class BaseCard:
    def __init__(self, combatant: Combatant, width: int = 350, height: int = 500):
        self.combatant = combatant
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.font_title = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_body = pygame.font.SysFont("sans", 14)
        self.font_small = pygame.font.SysFont("sans", 12)
        self.is_gm = False
        self.expanded = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Left click on card expands/collapses
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
        panel_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, self.rect.width - 10, 80)
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=3)

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
        surface.blit(edge_surf, (panel_rect.right - edge_surf.get_width() - 10, panel_rect.y + 10))

    def _draw_panel_2_status(self, surface: pygame.Surface):
        # Panel 2: Status (Middle)
        panel_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 90, self.rect.width - 10, 100)
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=3)

        # Physical / Stun Tracks
        p_track = self.combatant.physical_track
        p_dmg = self.combatant.physical_damage
        s_track = self.combatant.stun_track
        s_dmg = self.combatant.stun_damage

        phys_text = f"Physical: {p_dmg}/{p_track}"
        stun_text = f"Stun: {s_dmg}/{s_track}"

        p_color = COLORS["health_ok"] if p_dmg < p_track/2 else (COLORS["health_warn"] if p_dmg < p_track else COLORS["health_crit"])
        s_color = COLORS["health_ok"] if s_dmg < s_track/2 else (COLORS["health_warn"] if s_dmg < s_track else COLORS["health_crit"])

        surface.blit(self.font_body.render(phys_text, True, p_color), (panel_rect.x + 10, panel_rect.y + 10))
        surface.blit(self.font_body.render(stun_text, True, s_color), (panel_rect.x + 10, panel_rect.y + 30))

        # Armor & Initiative
        armor_text = f"Armor: {self.combatant.armor}"
        init_text = f"Initiative: {self.combatant.initiative_score}"

        surface.blit(self.font_body.render(armor_text, True, COLORS["text"]), (panel_rect.x + 10, panel_rect.y + 55))
        surface.blit(self.font_body.render(init_text, True, COLORS["text"]), (panel_rect.x + 10, panel_rect.y + 75))

        # Alive Status
        status_text = "ALIVE" if self.combatant.is_alive else "DEAD/UNCONSCIOUS"
        status_color = COLORS["health_ok"] if self.combatant.is_alive else COLORS["health_crit"]
        if self.combatant.has_yielded:
            status_text = "YIELDED"
            status_color = COLORS["health_warn"]

        surf_status = self.font_title.render(status_text, True, status_color)
        surface.blit(surf_status, (panel_rect.right - surf_status.get_width() - 10, panel_rect.y + 10))

    def _draw_panel_3_mechanics(self, surface: pygame.Surface):
        # Panel 3: Mechanics (Bottom)
        panel_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 195, self.rect.width - 10, self.rect.height - 200)
        pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=3)

        y_offset = panel_rect.y + 10

        # Weapons
        wpn_header = self.font_body.render("Weapons:", True, COLORS["text"])
        surface.blit(wpn_header, (panel_rect.x + 10, y_offset))
        y_offset += 20
        for w in self.combatant.weapons[:3]: # Show up to 3
            wpn_text = f"- {w.name} (DV:{w.damage} AP:{w.ap})"
            surface.blit(self.font_small.render(wpn_text, True, COLORS["text_dark"]), (panel_rect.x + 20, y_offset))
            y_offset += 15

        # Matrix/Spells/Tethers if expanded or relevant
        if self.expanded:
            y_offset += 10
            if self.combatant.spells:
                spl_header = self.font_body.render("Spells:", True, COLORS["text"])
                surface.blit(spl_header, (panel_rect.x + 10, y_offset))
                y_offset += 20
                for s in self.combatant.spells[:2]:
                    spl_text = f"- {s.name}"
                    surface.blit(self.font_small.render(spl_text, True, COLORS["text_dark"]), (panel_rect.x + 20, y_offset))
                    y_offset += 15

            y_offset += 10
            mat_header = self.font_body.render(f"Matrix (A:{self.combatant.matrix.attack} S:{self.combatant.matrix.sleaze} D:{self.combatant.matrix.data_processing} F:{self.combatant.matrix.firewall})", True, COLORS["text"])
            surface.blit(mat_header, (panel_rect.x + 10, y_offset))
            y_offset += 20

            if self.combatant.tethers:
                teth_text = f"Tethers: {len(self.combatant.tethers)}"
                surface.blit(self.font_small.render(teth_text, True, COLORS["border"]), (panel_rect.x + 20, y_offset))
                y_offset += 15

            if self.combatant.influence or self.combatant.resolve:
                soc_text = f"Social: Inf({len(self.combatant.influence)}) Res({len(self.combatant.resolve)})"
                surface.blit(self.font_small.render(soc_text, True, COLORS["border_gm"]), (panel_rect.x + 20, y_offset))
                y_offset += 15

class PlayerCard(BaseCard):
    def __init__(self, combatant: Combatant, width: int = 350, height: int = 500):
        super().__init__(combatant, width, height)
        self.is_gm = False

class GMCard(BaseCard):
    def __init__(self, combatant: Combatant, width: int = 350, height: int = 500):
        super().__init__(combatant, width, height)
        self.is_gm = True
