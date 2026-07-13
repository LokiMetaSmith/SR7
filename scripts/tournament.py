import os
import sys
import glob

# Ensure we can import combat_analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from combat_simulator import load_combatant, parse_scenario
from combat_analyzer import run_simulation


def main():
    npc_files = glob.glob("npc_templates/*.chum5")
    if not npc_files:
        print("No NPC templates found!")
        return

    combatants = []
    for file in npc_files:
        try:
            c = load_combatant(file)
            combatants.append((c, file))
        except Exception as e:
            print(f"Failed to load {file}: {e}")

    scenario_files = glob.glob("campaigns/default/scenarios/*.json")
    if not scenario_files:
        if not os.path.exists("scenario.json"):
            import json
            with open("scenario.json", "w") as f:
                json.dump({"description": "Empty Arena", "modifiers": {}}, f)
        scenario_files = ["scenario.json"]

    environments = {}
    for sf in scenario_files:
        env = parse_scenario(sf)
        name = getattr(env, 'name', sf)
        if not name:
            name = sf
        environments[name] = env

    iterations_per_match = 100
    print(f"Starting tournament with {len(combatants)} combatants.")
    print(f"Testing across {len(environments)} environments.")
    print(f"Each match consists of {iterations_per_match} iterations per environment.")
    print("-" * 40)

    # Dictionary to track points: Win = 3, Draw = 1, Loss = 0
    standings = {
        c[0].name: {"wins": 0, "draws": 0, "losses": 0, "points": 0} for c in combatants
    }

    scenario_standings = {
        env_name: {c[0].name: {"wins": 0, "draws": 0, "losses": 0, "points": 0} for c in combatants}
        for env_name in environments
    }

    for i in range(len(combatants)):
        for j in range(i + 1, len(combatants)):
            c1_base, _file1 = combatants[i]
            c2_base, _file2 = combatants[j]

            # print(f"Match: {c1_base.name} vs {c2_base.name}...")

            for env_name, env in environments.items():
                c1_wins = 0
                c2_wins = 0
                draws = 0

                for _ in range(iterations_per_match):
                    res = run_simulation([c1_base], [c2_base], env)
                    if res["winning_team"] == 1:
                        c1_wins += 1
                    elif res["winning_team"] == 2:
                        c2_wins += 1
                    else:
                        draws += 1

                # Update Scenario Standings
                if c1_wins > c2_wins:
                    scenario_standings[env_name][c1_base.name]["wins"] += 1
                    scenario_standings[env_name][c1_base.name]["points"] += 3
                    scenario_standings[env_name][c2_base.name]["losses"] += 1

                    standings[c1_base.name]["wins"] += 1
                    standings[c1_base.name]["points"] += 3
                    standings[c2_base.name]["losses"] += 1
                elif c2_wins > c1_wins:
                    scenario_standings[env_name][c2_base.name]["wins"] += 1
                    scenario_standings[env_name][c2_base.name]["points"] += 3
                    scenario_standings[env_name][c1_base.name]["losses"] += 1

                    standings[c2_base.name]["wins"] += 1
                    standings[c2_base.name]["points"] += 3
                    standings[c1_base.name]["losses"] += 1
                else:
                    scenario_standings[env_name][c1_base.name]["draws"] += 1
                    scenario_standings[env_name][c1_base.name]["points"] += 1
                    scenario_standings[env_name][c2_base.name]["draws"] += 1
                    scenario_standings[env_name][c2_base.name]["points"] += 1

                    standings[c1_base.name]["draws"] += 1
                    standings[c1_base.name]["points"] += 1
                    standings[c2_base.name]["draws"] += 1
                    standings[c2_base.name]["points"] += 1

    print("\n=== TOURNAMENT LEADERBOARD ===")
    sorted_standings = sorted(
        standings.items(), key=lambda item: item[1]["points"], reverse=True
    )

    # Format for markdown saving
    output = "# Shadowrun 7E NPC Tournament Leaderboard\n\n"
    output += "## Overall Standings\n\n"
    output += "| Rank | Name | Points | Win/Draw/Loss |\n"
    output += "|---|---|---|---|\n"

    for rank, (name, stats) in enumerate(sorted_standings, 1):
        line = f"| {rank} | {name} | {stats['points']} | {stats['wins']}-{stats['draws']}-{stats['losses']} |"
        print(line)
        output += line + "\n"

    for env_name, env_standings in scenario_standings.items():
        output += f"\n## Environment: {env_name}\n\n"
        output += "| Rank | Name | Points | Win/Draw/Loss |\n"
        output += "|---|---|---|---|\n"

        sorted_env_standings = sorted(
            env_standings.items(), key=lambda item: item[1]["points"], reverse=True
        )
        for rank, (name, stats) in enumerate(sorted_env_standings, 1):
            line = f"| {rank} | {name} | {stats['points']} | {stats['wins']}-{stats['draws']}-{stats['losses']} |"
            output += line + "\n"

    with open("tournament_results.md", "w") as f:
        f.write(output)
    print("\nResults saved to tournament_results.md")


if __name__ == "__main__":
    main()
