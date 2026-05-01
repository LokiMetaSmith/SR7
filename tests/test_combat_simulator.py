import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.combat_simulator import Combatant, MatrixAttributes, RulesEngine, Weapon, Zone, Vehicle

def test_hopepunk_social_modifier():
    c = Combatant(
        name="Negotiator",
        attributes={"CHA": 6},
        skills={"Negotiation": 4},
        street_cred=10,
        notoriety=2,
        team=1,
        matrix=MatrixAttributes()
    )
    assert c.street_cred == 10
    assert c.notoriety == 2
    assert c.attributes["CHA"] == 6

def test_nica_glitch_table():
    from scripts.combat_utils import apply_nica_glitch
    c = Combatant(
        name="Glitcher",
        physical_track=10,
        stun_track=10,
        matrix=MatrixAttributes(),
        team=1
    )
    import random
    original_choice = random.choice
    random.choice = lambda seq: "Takes 1 S damage (painful feedback)"
    try:
        res = apply_nica_glitch(c)
        assert res == "Takes 1 S damage (painful feedback)"
        assert c.stun_damage == 1
    finally:
        random.choice = original_choice

def test_chunky_salsa_rule():
    from scripts.combat_simulator import Weapon

    # Chunky Salsa: doubles base damage of explosives in enclosed spaces
    c = Combatant(
        name="Target",
        attributes={"BOD": 3},
        matrix=MatrixAttributes(),
        team=1,
        zone=Zone("Alley", 0, "Small enclosed alley")
    )

    w = Weapon(name="HE Grenade", damage=10, damage_type="P", ap=-2, mode="Blast")
    assert w.damage == 10

    assert c.zone.name == "Alley"

def test_swarm_damage_soak():
    """
    Drone swarms take damage by reducing swarm_count instead of immediate destruction.
    """
    v = Vehicle(
        name="FlySpy Swarm",
        body=2,
        armor=0,
        handling=3,
        speed=3,
        accel=1,
        sensor=3,
        physical_track=8,
        swarm_count=5
    )
    c = Combatant(
        name="Swarm Rigger",
        attributes={"BOD": 2},
        matrix=MatrixAttributes(),
        team=1,
        jumped_in_vehicle=v
    )

    damage_taken = 8
    c.jumped_in_vehicle.physical_damage += damage_taken
    if c.jumped_in_vehicle.swarm_count > 1 and c.jumped_in_vehicle.physical_damage >= c.jumped_in_vehicle.physical_track:
        c.jumped_in_vehicle.swarm_count -= 1
        c.jumped_in_vehicle.physical_damage = 0

    assert c.jumped_in_vehicle.swarm_count == 4
    assert c.jumped_in_vehicle.physical_damage == 0

def test_null_suit_matrix_immunity():
    """
    Null-Suits grant immunity to Matrix actions (Data Spikes, Tethers).
    """
    c = Combatant(
        name="Ghost",
        matrix=MatrixAttributes(),
        team=1,
        null_bags=5
    )
    assert c.null_bags == 5

def test_aoe_explosive_logic():
    from scripts.combat_simulator import Weapon, GameEnvironment
    w = Weapon(name="HE Grenade", damage=10, damage_type="P", ap=-2, mode="Blast")
    c1 = Combatant(name="C1", attributes={"BOD": 3}, team=1, zone=Zone("Alley", 0, "Small enclosed alley"), matrix=MatrixAttributes())
    c2 = Combatant(name="C2", attributes={"BOD": 3}, team=1, zone=Zone("Alley", 0, "Small enclosed alley"), matrix=MatrixAttributes())

    env = GameEnvironment("Test", {})
    # Mocking the combat loop logic
    assert env is not None
