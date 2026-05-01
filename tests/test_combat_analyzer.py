import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.combat_analyzer import run_simulation
from scripts.combat_simulator import Combatant, MatrixAttributes, Weapon, GameEnvironment

def test_combat_analyzer_run_simulation():
    # Setup dummy combatants
    c1 = Combatant(
        name="Team1 Guy",
        attributes={"BOD": 3, "AGI": 4, "REA": 3},
        skills={"Firearms": 4},
        weapons=[Weapon(name="Pistol", damage=5, damage_type="P", ap=0, mode="SA")],
        matrix=MatrixAttributes(),
        team=1
    )
    c2 = Combatant(
        name="Team2 Guy",
        attributes={"BOD": 3, "AGI": 4, "REA": 3},
        skills={"Firearms": 4},
        weapons=[Weapon(name="Pistol", damage=5, damage_type="P", ap=0, mode="SA")],
        matrix=MatrixAttributes(),
        team=2
    )

    env = GameEnvironment("Empty Arena", {}, None, False)

    # Run the simulation
    results = run_simulation([c1], [c2], env)

    assert "winning_team" in results
    assert "turns" in results
