import pytest
import pygame
from scripts.combat_simulator import Combatant, MatrixAttributes
from ui.components import PlayerCard, GMCard

@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    # Initialize pygame for headless testing
    pygame.init()
    # Need to set a video mode for some font rendering or surface creation
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()

def test_player_card_initialization():
    combatant = Combatant(
        name="Test Player",
        source_file="",
        attributes={"BOD": 3},
        matrix=MatrixAttributes()
    )
    card = PlayerCard(combatant)
    assert not card.is_gm
    assert card.combatant.name == "Test Player"
    assert not card.expanded

def test_gm_card_initialization():
    combatant = Combatant(
        name="Test GM",
        source_file="",
        attributes={"BOD": 4},
        matrix=MatrixAttributes(),
        team=1
    )
    card = GMCard(combatant)
    assert card.is_gm
    assert card.combatant.name == "Test GM"
    assert not card.expanded

def test_card_draw_headless():
    combatant = Combatant(
        name="Test Character",
        source_file="",
        attributes={"BOD": 3},
        matrix=MatrixAttributes()
    )
    card = PlayerCard(combatant)

    # Create an invisible surface
    surface = pygame.Surface((800, 600))

    # Draw shouldn't crash
    card.draw(surface, 50, 50)
    assert card.rect.topleft == (50, 50)

def test_card_click_expansion():
    combatant = Combatant(
        name="Test Character",
        source_file="",
        attributes={"BOD": 3},
        matrix=MatrixAttributes()
    )
    card = PlayerCard(combatant)

    # Simulate drawing to set the rect position
    surface = pygame.Surface((800, 600))
    card.draw(surface, 0, 0)

    assert not card.expanded

    # Simulate a mouse click within the card's rect
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)})
    handled = card.handle_event(click_event)

    assert handled
    assert card.expanded
