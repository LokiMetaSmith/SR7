import pytest
import pygame
import os
from scripts.combat_simulator import Combatant, MatrixAttributes
from ui.app import App

class MockGameState:
    def __init__(self, combatants, turn, scenario):
        self.combatants = combatants
        self.turn = turn
        self.scenario = scenario

@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()

def test_app_scroll_limits():
    app = App(width=800, height=600)

    # Create enough combatants to force scrolling
    combatants = []
    for i in range(5):
        combatants.append(Combatant(
            name=f"Player {i}",

            attributes={"BOD": 3},
            matrix=MatrixAttributes(),
            team=1
        ))
    for i in range(5):
        combatants.append(Combatant(
            name=f"GM {i}",

            attributes={"BOD": 3},
            matrix=MatrixAttributes(),
            team=2
        ))

    state = MockGameState(combatants=combatants, turn=1, scenario={})
    app.update_state(state)

    # Send a massive scroll event
    scroll_event = pygame.event.Event(pygame.MOUSEWHEEL, {"x": -100, "y": 0})
    pygame.event.post(scroll_event)

    app.handle_events()

    # It should hit the min limit
    assert app.scroll_x < 0
    # The total width is 50 + 5 * 370 = 1900, max(1900, 550) = 1900, + 5 * 370 + 50 = 3800
    # min_scroll_x = 800 - 3800 = -3000
    assert app.scroll_x == -3000

def test_app_scroll_positive_limit():
    app = App(width=800, height=600)
    # Scroll right explicitly
    app.scroll_x = -100

    scroll_event = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 100, "y": 0})
    pygame.event.post(scroll_event)

    app.handle_events()

    # It should not exceed 0
    assert app.scroll_x == 0
