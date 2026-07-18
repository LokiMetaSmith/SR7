import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pygame
from scripts.combat_simulator import Combatant, MatrixAttributes, load_combatant, SimulationState, GameEnvironment
from ui.components import PlayerCard, GMCard, MapGrid, VehicleChaseScreen

import os


@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    # Initialize pygame for headless testing
    pygame.init()
    pygame.font.init()
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
    pygame.font.init()

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

def test_player_card_stealth_ui():
    pygame.font.init()
    c = Combatant(name="Stealthy Guy", team=1, matrix=MatrixAttributes())
    card = PlayerCard(c)
    surface = pygame.Surface((800, 600))

    # Check regular draw (combat actions)
    card.draw(surface, 0, 0, is_stealth=False)

    # Check stealth draw
    card.draw(surface, 0, 0, is_stealth=True)


def test_mapgrid_los_cover_ui():
    pygame.font.init()
    layout_ascii = [
        "###",
        "#.O",
        "###"
    ]
    legend = {"#": "Wall (Heavy Cover)", "O": "Pillar (Medium Cover)", ".": "Open"}
    grid = MapGrid(layout_ascii, legend)

    env = GameEnvironment(
        name="Test",
        description="A test environment.",
        modifiers=[],
        layout_ascii=layout_ascii,
        legend=legend
    )
    state = SimulationState(environment=env)
    state.turn = 1
    state.combatants = []

    surface = pygame.Surface((800, 600))
    # It should not crash while drawing with cover
    grid.draw(surface, 0, 0)


def test_vehicle_chase_ui():
    pygame.font.init()
    rect = pygame.Rect(0, 0, 500, 400)
    action_called = False
    def action_callback(action):
        nonlocal action_called
        action_called = True

    screen = VehicleChaseScreen(rect, on_close=lambda: None, on_action=action_callback)
    surface = pygame.Surface((800, 600))
    screen.draw(surface)

    # Simulate clicking
    click_event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": screen.ram_rect.center}
    )
    screen.handle_event(click_event)
    assert action_called is True
