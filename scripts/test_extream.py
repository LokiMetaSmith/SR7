import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.combat_simulator import load_combatant, parse_scenario, GameEnvironment
from scripts.combat_analyzer import run_simulation

def main():
    if not os.path.exists("scenario.json"):
        import json
        with open("scenario.json", "w") as f:
            json.dump({"description": "Test", "modifiers": {}}, f)

    # Need two combatants
    import glob
    templates = glob.glob("npc_templates/*.chum5")
    if len(templates) < 2:
        print("Need at least two NPC templates.")
        return

    c1_path = templates[0]
    c2_path = templates[1]

    print(f"Comparing standard vs eXtream rules: {os.path.basename(c1_path)} vs {os.path.basename(c2_path)}")
    print("-" * 50)

    # Standard Rules
    print("Running 10 Standard Iterations...")
    env_std = parse_scenario("scenario.json", is_extream_mode=False)

    std_t1_wins = 0
    std_t2_wins = 0
    for _ in range(10):
        c1 = load_combatant(c1_path)
        c2 = load_combatant(c2_path)
        c1.team = 1
        c2.team = 2
        res = run_simulation([c1], [c2], env_std)
        if res["winning_team"] == 1:
            std_t1_wins += 1
        elif res["winning_team"] == 2:
            std_t2_wins += 1

    print(f"Standard Results: T1 Wins: {std_t1_wins}, T2 Wins: {std_t2_wins}, Draws: {10 - std_t1_wins - std_t2_wins}")

    # eXtream Rules
    print("\nRunning 10 eXtream Iterations...")
    env_ext = parse_scenario("scenario.json", is_extream_mode=True)

    ext_t1_wins = 0
    ext_t2_wins = 0
    for _ in range(10):
        c1 = load_combatant(c1_path)
        c2 = load_combatant(c2_path)
        c1.team = 1
        c2.team = 2
        res = run_simulation([c1], [c2], env_ext)
        if res["winning_team"] == 1:
            ext_t1_wins += 1
        elif res["winning_team"] == 2:
            ext_t2_wins += 1

    print(f"eXtream Results: T1 Wins: {ext_t1_wins}, T2 Wins: {ext_t2_wins}, Draws: {10 - ext_t1_wins - ext_t2_wins}")

if __name__ == '__main__':
    main()
