from scripts.combat_simulator import Combatant, SimulationState, GameEnvironment
from scripts.rules_engine import DiceRules, CombatRules
from scripts.combat_utils import process_turn_end
import pytest

def test_hmhvv_initiative_penalty():
    c = Combatant(name="Test Vampire", attributes={"REA": 3, "INT": 3}, hmhvv_infection_level=1)

    results = [CombatRules.roll_initiative(c) for _ in range(50)]
    assert max(results) <= 11

    c_normal = Combatant(name="Normal", attributes={"REA": 3, "INT": 3}, hmhvv_infection_level=0)
    results_normal = [CombatRules.roll_initiative(c_normal) for _ in range(50)]
    assert max(results_normal) <= 12

def test_hmhvv_dice_pool_penalty():
    c = Combatant(name="Test Vampire", attributes={"REA": 3, "INT": 3}, hmhvv_infection_level=1)

    results = [DiceRules.roll_dice(5, combatant=c)[0] for _ in range(50)]
    assert max(results) <= 4

    c_normal = Combatant(name="Normal", attributes={"REA": 3, "INT": 3}, hmhvv_infection_level=0)
    results_normal = [DiceRules.roll_dice(5, combatant=c_normal)[0] for _ in range(50)]
    assert max(results_normal) <= 5

def test_hmhvv_turn_damage():
    c = Combatant(name="Test Vampire", attributes={"REA": 3, "INT": 3}, hmhvv_infection_level=3)
    c.team = 1
    c2 = Combatant(name="Enemy", attributes={"REA": 3, "INT": 3}, team=2)

    state = SimulationState(environment=GameEnvironment("test", {}))
    state.combatants = [c, c2]

    process_turn_end(state)

    assert c.physical_damage == 1
    assert c2.physical_damage == 0
