import pytest
import sys
import os
import copy
import random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.combat_analyzer import run_simulation
from scripts.combat_simulator import Combatant, MatrixAttributes, Weapon, GameEnvironment

def test_combat_analyzer_math_accuracy(monkeypatch):
    """
    Ensures that the math formulas in the combat analyzer simulation work exactly as expected
    by forcing deterministic dice rolls.
    """

    def mock_roll_attack_with_edge(pool, active):
        return (3, False, False) # Returns 3 hits, no glitch, no edge spent

    def mock_roll_dice(pool, wild_dice_count=0):
        return (2, False) # Returns 2 hits, no glitch

    import scripts.combat_simulator as sim
    monkeypatch.setattr(sim.RulesEngine, "roll_attack_with_edge", mock_roll_attack_with_edge)
    monkeypatch.setattr(sim.RulesEngine, "roll_dice", mock_roll_dice)

    # Also mock random to prevent non-deterministic decisions from DummyAgent and Initiative
    monkeypatch.setattr(random, "random", lambda: 0.1) # Never sprint to cover or use data spike randomly
    monkeypatch.setattr(random, "randint", lambda a, b: 6)

    c1_base = Combatant(
        name="Team1 Guy",
        attributes={"BOD": 3, "AGI": 4, "REA": 3, "INT": 3, "WIL": 3},
        skills={"Firearms": 4},
        weapons=[Weapon(name="Pistol", damage=5, damage_type="P", ap=0, mode="SA")],
        armor=0,
        matrix=MatrixAttributes(),
        team=1,
        physical_track=10,
        stun_track=10,
        is_alive=True
    )
    c2_base = Combatant(
        name="Team2 Guy",
        attributes={"BOD": 3, "AGI": 4, "REA": 3, "INT": 3, "WIL": 3},
        skills={"Firearms": 4},
        weapons=[Weapon(name="Pistol", damage=5, damage_type="P", ap=0, mode="SA")],
        armor=0,
        matrix=MatrixAttributes(),
        team=2,
        physical_track=10,
        stun_track=10,
        is_alive=True
    )

    env = GameEnvironment("Empty Arena", {}, None, False)

    iterations = 10
    t1_wins = 0
    t2_wins = 0
    draws = 0
    t1_dmg_total = 0
    t2_dmg_total = 0

    for _ in range(iterations):
        # We need to copy combatants to avoid mutated states between runs
        c1_copy = copy.deepcopy(c1_base)
        c2_copy = copy.deepcopy(c2_base)

        # We explicitly set initiative to ensure T1 always goes first.
        # random.randint is mocked to 6, so they would normally tie (both 12), and python sort is stable,
        # but to be 100% deterministic mathematically we enforce the score here:
        c1_copy.initiative_score = 10
        c2_copy.initiative_score = 5

        res = run_simulation([c1_copy], [c2_copy], env)
        if res["winning_team"] == 1:
            t1_wins += 1
        elif res["winning_team"] == 2:
            t2_wins += 1
        else:
            draws += 1

        t1_dmg_total += res["t1_damage_taken"]
        t2_dmg_total += res["t2_damage_taken"]

    # Since they have exactly the same stats, but Team 1 acts first in the loop:
    # Turn 1: T1 attacks T2 (4 damage -> T2 has 4/10 damage). T2 attacks T1 (4 damage -> T1 has 4/10 damage).
    # Turn 2: T1 attacks T2 (4 damage -> T2 has 8/10 damage). T2 attacks T1 (4 damage -> T1 has 8/10 damage).
    # Turn 3: T1 attacks T2 (4 damage -> T2 has 12/10 damage, T2 dies!). T2 doesn't attack.
    # Result: Team 1 wins in 3 turns.
    # T1 damage taken = 8.
    # T2 damage taken = 12.

    assert t1_wins == 10
    assert t2_wins == 0
    assert draws == 0
    assert t1_dmg_total == 80
    assert t2_dmg_total == 120
