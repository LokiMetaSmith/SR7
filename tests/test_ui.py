import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pygame
from scripts.combat_simulator import Combatant, MatrixAttributes, load_combatant
from ui.components import PlayerCard, GMCard

import os


@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    # Initialize pygame for headless testing
    pygame.init()
    # Need to set a video mode for some font rendering or surface creation
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()


def test_player_card_initialization():
    combatant = load_combatant("npc_templates/Kyber.chum5")
    card = PlayerCard(combatant)
    assert not card.is_gm
    assert card.combatant.name == "Kyber"
    assert not card.expanded


def test_gm_card_initialization():
    combatant = load_combatant("npc_templates/Sargent_Igneous.chum5")
    combatant.team = 1
    card = GMCard(combatant)
    assert card.is_gm
    assert card.combatant.name == "Sargent Igneous"
    assert not card.expanded


def test_card_draw_headless():
    combatant = load_combatant("npc_templates/Kyber.chum5")
    card = PlayerCard(combatant)

    # Create an invisible surface
    surface = pygame.Surface((800, 600))

    # Draw shouldn't crash
    card.draw(surface, 50, 50)
    assert card.rect.topleft == (50, 50)


def test_card_click_expansion():
    combatant = load_combatant("npc_templates/Kyber.chum5")
    card = PlayerCard(combatant)

    # Simulate drawing to set the rect position
    surface = pygame.Surface((800, 600))
    card.draw(surface, 0, 0)

    assert not card.expanded

    # Simulate a mouse click within the card's rect
    click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)}
    )
    handled = card.handle_event(click_event)

    assert handled
    assert card.expanded

def test_vehicle_chase_screen():
    import pygame
    from ui.components import VehicleChaseScreen
    pygame.init()

    # Initialize the screen just to test creation
    rect = pygame.Rect(0, 0, 500, 400)
    screen = VehicleChaseScreen(rect)

    assert screen.distance == 100, "Distance should initialize to 100"

    # Check interaction bounds
    evade_rect = screen.evade_rect
    ram_rect = screen.ram_rect

    assert evade_rect.collidepoint(evade_rect.center), "Evade rect should be interactive"
    assert ram_rect.collidepoint(ram_rect.center), "Ram rect should be interactive"

    pygame.quit()
