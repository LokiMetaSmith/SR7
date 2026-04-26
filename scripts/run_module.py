import argparse
import json
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Run a sequence of combat simulator scenarios from a module JSON.")
    parser.add_argument("--module", required=True, help="Path to the module JSON file.")
    parser.add_argument("--team1", nargs="+", required=True, help="List of paths to Chummer or Markdown files for Team 1 (the players).")
    parser.add_argument("--dry-run", action="store_true", help="Run the simulator with dummy LLM agent.")
    parser.add_argument("--ui", action="store_true", help="Launch the Pygame UI for each stage.")
    parser.add_argument("--interactive", action="store_true", help="Pause for manual input.")

    args = parser.parse_args()

    if not os.path.exists(args.module):
        print(f"Error: Module file not found at {args.module}")
        sys.exit(1)

    with open(args.module, "r") as f:
        module_data = json.load(f)

    module_name = module_data.get("name", "Unknown Module")
    print(f"=== Starting Module: {module_name} ===")
    print(f"Description: {module_data.get('description', '')}\n")

    stages = module_data.get("stages", [])
    if not stages:
        print("No stages found in module.")
        sys.exit(0)

    for i, stage in enumerate(stages, 1):
        stage_name = stage.get("name", f"Stage {i}")
        scenario_file = stage.get("scenario_file")
        team2 = stage.get("team2", [])

        print(f"\n--- Starting Stage {i}: {stage_name} ---")
        if scenario_file:
            print(f"Loading scenario: {scenario_file}")

        cmd = ["python", "scripts/combat_simulator.py"]
        cmd.extend(["--team1"] + args.team1)
        if team2:
            cmd.extend(["--team2"] + team2)
        if scenario_file:
            cmd.extend(["--scenario", scenario_file])
        if args.dry_run:
            cmd.append("--dry-run")
        if args.ui:
            cmd.append("--ui")
        if args.interactive:
            cmd.append("--interactive")

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"Stage {i} failed or was aborted. Aborting module.")
            sys.exit(result.returncode)

    print(f"\n=== Module '{module_name}' Completed Successfully ===")

if __name__ == "__main__":
    main()