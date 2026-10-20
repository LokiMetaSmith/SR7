import os
import json
import pytest
import tempfile
import pygame

import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()
pygame.font.init()
pygame.display.set_mode((100, 100), pygame.HIDDEN)

from ui.components import TradeScreen, SaveLoadScreen
from scripts.rules_engine import DiceRules
from scripts.combat_simulator import Combatant, simulate_trade

class MockCombatant:
    def __init__(self, name="Test", physical_damage=0, stun_damage=0, edge=1, is_alive=True,
                 digital_nuyen=0, clean_nuyen=0, hot_nuyen=0, faction_standings=None):
        self.name = name
        self.physical_damage = physical_damage
        self.stun_damage = stun_damage
        self.edge = edge
        self.is_alive = is_alive
        self.digital_nuyen = digital_nuyen
        self.clean_nuyen = clean_nuyen
        self.hot_nuyen = hot_nuyen
        self.faction_standings = faction_standings or {}
        self.contacts = []
        self.weapons = []

class MockState:
    def __init__(self, combatants):
        self.combatants = combatants

class MockApp:
    def __init__(self, state=None):
        self.in_save_load_screen = True
        self.state = state
        self.global_campaign_state = {}

@pytest.fixture(scope="module", autouse=True)
def setup_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((100, 100), pygame.HIDDEN)
    yield
    pygame.quit()

@pytest.fixture
def temp_campaign_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        old_cwd = os.getcwd()
        os.chdir(d)
        yield d
        os.chdir(old_cwd)

def test_save_load_screen_missing_dir(temp_campaign_dir):
    # Ensure it handles no campaign_state dir gracefully
    rect = pygame.Rect(0, 0, 800, 600)
    screen = SaveLoadScreen(rect)
    assert len(screen.state_data) == 0
    assert screen.global_state == {"economy_multiplier": 1.0}

def test_save_load_screen_bad_json(temp_campaign_dir):
    os.makedirs("campaign_state")
    with open("campaign_state/bad.json", "w") as f:
        f.write("{bad json")

    with open("campaign_state/global_campaign_state.json", "w") as f:
        f.write("{also bad json")

    rect = pygame.Rect(0, 0, 800, 600)
    screen = SaveLoadScreen(rect)
    assert len(screen.state_data) == 0
    assert screen.global_state == {"economy_multiplier": 1.0}

def test_save_load_screen_apply_states(temp_campaign_dir):
    os.makedirs("campaign_state")
    with open("campaign_state/char1.json", "w") as f:
        json.dump({"name": "TestChar", "physical_damage": 5, "edge": 3, "faction_standings": {"Corp": 10}}, f)

    with open("campaign_state/global_campaign_state.json", "w") as f:
        json.dump({"economy_multiplier": 1.5}, f)

    rect = pygame.Rect(0, 0, 800, 600)
    screen = SaveLoadScreen(rect)

    c1 = MockCombatant(name="TestChar", physical_damage=0, edge=1)
    app = MockApp(state=MockState([c1]))

    screen.apply_states(app)

    assert app.global_campaign_state == {"economy_multiplier": 1.5}
    assert c1.physical_damage == 5
    assert c1.edge == 3
    assert c1.faction_standings == {"Corp": 10}

def test_trade_screen_events():
    trade_called = []
    close_called = []

    def on_trade(*args):
        trade_called.append(args)
        return "Traded!"

    def on_close():
        close_called.append(True)

    rect = pygame.Rect(0, 0, 800, 600)
    screen = TradeScreen(rect, on_close=on_close, on_trade=on_trade)

    # Test Close
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=screen.close_rect.center)
    screen.handle_event(event)
    assert len(close_called) == 1

    # Test Mode Buy -> Sell
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=screen.mode_sell_rect.center)
    screen.handle_event(event)
    assert screen.is_selling == True

    # Test Condition Change
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=screen.condition_rects["damaged"].center)
    screen.handle_event(event)
    assert screen.item_condition == "damaged"

    # Test Trade Call
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=screen.trade_rect.center)
    screen.handle_event(event)
    assert len(trade_called) == 1
    assert trade_called[0] == ("Ares Predator", 350, 1, True, "damaged")
    assert screen.trade_result == "Traded!"

def test_simulate_trade_edge_cases(capsys, monkeypatch):
    c = Combatant(name="Tester", attributes={"CHA": 5}, skills={"Negotiation": 5}, street_cred=2)

    # Force tie
    monkeypatch.setattr(DiceRules, "roll_dice", lambda pool: (3, False))
    simulate_trade(c, "Gun", 100, fixer_difficulty=-2, is_selling=False)
    captured = capsys.readouterr()
    assert "Result: Tie." in captured.out

    # Force player critical failure / glitch
    def mock_roll_glitch(pool):
        # player rolls first, fixer rolls second.
        if mock_roll_glitch.calls == 0:
            mock_roll_glitch.calls += 1
            return (0, True) # Player glitches
        return (2, False)
    mock_roll_glitch.calls = 0
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_glitch)
    simulate_trade(c, "Gun", 100, fixer_difficulty=1, is_selling=False)
    captured = capsys.readouterr()
    assert "Critical Failure: Tester offended the fixer." in captured.out

    # Force player glitch while selling
    mock_roll_glitch.calls = 0
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_glitch)
    simulate_trade(c, "Gun", 100, fixer_difficulty=1, is_selling=True)
    captured = capsys.readouterr()
    assert "Critical Failure: Tester offended the fixer." in captured.out
