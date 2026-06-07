import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat_simulator import load_combatant, parse_scenario, Combatant, PossessingEntity, Vehicle, MatrixAttributes
from combat_analyzer import run_simulation

def main():
    print("Setting up N-Factorial test...")

    # 1. We load the possessed human rigger
    rigger = load_combatant("npc_templates/n_factorial_drone_rigger.chum5")

    # 2. We load the gestalt technomancer
    technomancer = load_combatant("npc_templates/n_factorial_gestalt.chum5")

    print(f"Rigger loaded: {rigger.name}")
    print(f"Technomancer loaded: {technomancer.name}")

    # Implement the deep binding via nested PossessingEntity classes
    # The prompt says: "the same spirit who is posessing the human above."

    # Create the base entities
    master_spirit = PossessingEntity(name="The Master Spirit")
    mage_with_cfd = PossessingEntity(name="Mage (CFD)", possessed_by=master_spirit)
    bound_spirit = PossessingEntity(name="Bound Spirit", possessed_by=mage_with_cfd)
    bound_sprite = PossessingEntity(name="Bound Sprite", possessed_by=bound_spirit)

    # Apply to characters
    rigger.possessed_by = master_spirit
    technomancer.possessed_by = bound_sprite

    env = parse_scenario("scenario.json")
    if not env:
        from combat_simulator import GameEnvironment
        env = GameEnvironment(name="Empty Arena", description="Test", modifiers={})

    print(f"\nMatch: {rigger.name} vs {technomancer.name}")

    # We run 100 iterations like the main tournament
    iterations_per_match = 100
    t1_wins = 0
    t2_wins = 0
    draws = 0

    for _ in range(iterations_per_match):
        res = run_simulation([rigger], [technomancer], env)
        if res["winning_team"] == 1:
            t1_wins += 1
        elif res["winning_team"] == 2:
            t2_wins += 1
        else:
            draws += 1

    print("\n=== RESULTS ===")
    print(f"Team 1 Wins: {t1_wins}")
    print(f"Team 2 Wins: {t2_wins}")
    print(f"Draws: {draws}")


if __name__ == "__main__":
    main()
