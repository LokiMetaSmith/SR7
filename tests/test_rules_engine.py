import pytest
from unittest.mock import MagicMock
from scripts.rules_engine import DiceRules, MatrixRules, CombatRules, MagicRules

def test_roll_dice_no_wild_dice(monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 5)
    hits, is_glitch = DiceRules.roll_dice(pool=4, wild_dice_count=0)
    assert hits == 4
    assert is_glitch is False

def test_roll_dice_glitch(monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 1)
    hits, is_glitch = DiceRules.roll_dice(pool=4, wild_dice_count=0)
    assert hits == 0
    assert is_glitch is True

def test_roll_dice_wild_dice_success(monkeypatch):
    call_count = 0
    def mock_randint(a, b):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return 5
        elif call_count <= 4:
            return 6
        return 2

    monkeypatch.setattr("random.randint", mock_randint)

    hits, is_glitch = DiceRules.roll_dice(pool=4, wild_dice_count=2)
    assert hits == 8
    assert is_glitch is False

def test_roll_dice_wild_dice_cancels_hits(monkeypatch):
    call_count = 0
    def mock_randint(a, b):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return 5
        elif call_count == 3:
            return 1
        return 3

    monkeypatch.setattr("random.randint", mock_randint)

    hits, is_glitch = DiceRules.roll_dice(pool=4, wild_dice_count=2)
    assert hits == 0
    assert is_glitch is False

def test_roll_attack_with_edge(monkeypatch):
    call_count = 0
    def mock_randint(a, b):
        nonlocal call_count
        call_count += 1
        if call_count <= 4:
            return 3 # 0 hits, triggers edge reroll
        return 5 # Reroll gets hits

    monkeypatch.setattr("random.randint", mock_randint)
    combatant = MagicMock()
    combatant.edge = 1
    combatant.special_rules = []

    hits, glitched, edge_spent = DiceRules.roll_attack_with_edge(pool=4, wild_dice_count=0, combatant=combatant)
    assert hits == 4 # 4 hits from reroll
    assert glitched is False
    assert combatant.edge == 0
    assert edge_spent is True

def test_resolve_erase_tether_success(monkeypatch):
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()
    state.environment.is_extream_mode = False

    active.name = "Hacker"
    active.get_attribute.return_value = 5 # LOG
    active.skills.get.return_value = 5 # Computer

    target.name = "Drone"
    target.get_attribute.return_value = 3 # LOG
    target.skills.get.return_value = 3 # Hacking

    # Active holds tethers from target
    active.tethers = {"Drone": 1}

    def mock_roll_attack_with_edge(pool, combatant, wild_dice_count=0, is_extream_mode=False):
        return 3, False, False

    def mock_roll_dice(pool, wild_dice_count=0, combatant=None, is_extream_mode=False):
        return 1, False

    monkeypatch.setattr(DiceRules, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_dice)

    result = MatrixRules.resolve_erase_tether(state, active, target)

    assert active.tethers["Drone"] == 0
    assert "Successfully erased" in result

def test_resolve_erase_tether_fail(monkeypatch):
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()
    state.environment.is_extream_mode = False

    active.name = "Hacker"
    active.get_attribute.return_value = 5
    active.skills.get.return_value = 5

    target.name = "Drone"
    target.get_attribute.return_value = 3
    target.skills.get.return_value = 3
    active.tethers = {"Drone": 1}

    def mock_roll_attack_with_edge(pool, combatant, wild_dice_count=0, is_extream_mode=False):
        return 1, False, False

    def mock_roll_dice(pool, wild_dice_count=0, combatant=None, is_extream_mode=False):
        return 3, False

    monkeypatch.setattr(DiceRules, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_dice)

    result = MatrixRules.resolve_erase_tether(state, active, target)

    assert active.tethers["Drone"] == 1
    assert "Failed" in result

def test_resolve_data_spike_success(monkeypatch):
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()
    state.environment.is_extream_mode = False
    llm = MagicMock()
    llm.narrate_action.return_value = "Narrative"

    active.name = "Hacker"
    active.get_attribute.return_value = 5 # LOG
    active.skills.get.return_value = 5 # Hacking
    active.matrix.attack = 4
    active.null_bags = 0
    active.special_rules = []

    target.name = "Drone"
    target.get_attribute.return_value = 3 # WIL
    target.matrix.firewall = 3
    target.matrix.data_processing = 4
    target.null_bags = 0
    target.special_rules = []
    target.stun_damage = 0
    target.physical_damage = 0
    target.stun_track = 10
    target.physical_track = 10

    active.tethers = {"Drone": 0}
    target.tethers = {"Hacker": 0}

    def mock_roll_attack_with_edge(pool, combatant, wild_dice_count=0, is_extream_mode=False):
        if combatant == active:
            return 4, False, False
        return 0, False, False

    def mock_roll_dice(pool, wild_dice_count=0, combatant=None, is_extream_mode=False):
        if pool == (3 + 3): # target defense pool (INT + FW)
            return 2, False
        elif pool == (4 + 3): # target soak pool (DP + FW)
            return 0, False # 0 hits on soak so we can see the full dmg
        return 0, False

    monkeypatch.setattr(DiceRules, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_dice)

    narrative, result, edge_spent = CombatRules.resolve_data_spike(state, active, target, "data spike drone", llm)

    assert "launches a Data Spike" in narrative
    assert "Data Spike connects!" in result
    assert "6 Stun (Biofeedback) damage" in result
    target.take_damage.assert_not_called()
    assert target.stun_damage == 6

def test_resolve_spell_success(monkeypatch):
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()
    spell = MagicMock()

    state.environment.is_extream_mode = False
    state.environment.modifiers.get.return_value = 0

    active.name = "Mage"
    active.get_attribute.return_value = 6 # MAG / WIL
    active.skills.get.return_value = 6 # Spellcasting
    active.edge = 0
    active.special_rules = []
    active.take_damage = MagicMock()
    active.physical_damage = 0
    active.physical_track = 10
    active.stun_damage = 0
    active.stun_track = 10

    target.name = "Guard"
    target.get_attribute.return_value = 3 # REA / INT / BOD
    target.null_bags = 0
    target.special_rules = []
    target.total_armor = 10
    target.physical_damage = 0
    target.physical_track = 10
    target.stun_damage = 0
    target.stun_track = 10
    target.take_damage.return_value = "takes damage"

    spell.name = "Fireball"
    spell.category = "Combat"
    spell.type = "P"
    spell.damage = 5
    spell.force = 5

    def mock_roll_attack_with_edge(pool, combatant, wild_dice_count=0, is_extream_mode=False):
        if combatant == active:
            return 5, False, False
        return 0, False, False

    def mock_roll_dice(pool, wild_dice_count=0, combatant=None, is_extream_mode=False):
        if combatant == target:
            return 2, False # target defense hits
        elif combatant == active:
            return 3, False # drain resist hits
        return 0, False

    monkeypatch.setattr(DiceRules, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_dice)

    narrative, result, edge_spent = MagicRules.resolve_spell(state, active, target, spell, "cast fireball")

    assert "casts Fireball" in narrative
    assert "hits vs" in narrative
    assert "Spell hits!" in result

def test_calculate_los_cover():
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()

    state.environment.layout_ascii = [
        "#####",
        "#...#",
        "#.#.#",
        "#...#",
        "#####"
    ]
    state.environment.legend = {"#": "heavy cover", ".": "open"}

    active.zone.name = "0,1"
    target.zone.name = "0,3"

    cover = CombatRules.calculate_los_cover(state, active, target)
    assert cover == 0

def test_resolve_attack_success(monkeypatch):
    active = MagicMock()
    target = MagicMock()
    state = MagicMock()
    state.environment.is_extream_mode = False

    active.name = "Street Samurai"
    active.get_attribute.return_value = 5 # AGI
    active.skills.get.return_value = 5 # Automatics

    w = MagicMock()
    w.name = "Ares Alpha"
    w.type = "Pistols"
    w.damage = 11
    w.ap = -2
    active.weapons = [w]

    target.name = "Guard"
    target.get_attribute.side_effect = lambda x, default: 3 if x == "REA" or x == "INT" or x == "BOD" else default
    target.null_bags = 0
    target.special_rules = []
    target.total_armor = 10
    target.physical_damage = 0
    target.physical_track = 10
    target.stun_damage = 0
    target.stun_track = 10
    target.take_damage.return_value = "takes damage"

    def mock_roll_attack_with_edge(pool, combatant, wild_dice_count=0, is_extream_mode=False):
        if combatant == active:
            return 5, False, False
        return 0, False, False

    def mock_roll_dice(pool, wild_dice_count=0, combatant=None, is_extream_mode=False):
        if pool == 6: # target defense pool (REA 3 + INT 3)
            return 2, False
        elif pool == 11: # target soak pool (BOD 3 + Armor 10 - AP 2)
            return 3, False
        return 0, False

    def mock_calc_los_cover(state, active, target):
        return 0

    monkeypatch.setattr(DiceRules, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(DiceRules, "roll_dice", mock_roll_dice)
    monkeypatch.setattr(CombatRules, "calculate_los_cover", mock_calc_los_cover)

    narrative, result, edge_spent = CombatRules.resolve_attack(state, active, target, "fire ares alpha")

    assert "attacks Guard with Ares Alpha" in action_text(narrative, result) or "attacks Guard" in narrative or "Ares Alpha" in narrative
    assert "Attack hits!" in result or "takes" in result

def action_text(narr, result):
    return narr + " " + result
