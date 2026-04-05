import argparse
import copy
import sys
import os

# Ensure we can import combat_simulator when running from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Fallback for root execution

from combat_simulator import (
    load_combatant,
    parse_scenario,
    SimulationState,
    RulesEngine,
    Weapon,
    Combatant
)

class DummyAgent:
    def ask_action(self, combatant, state):
        return f"attack with {combatant.weapons[0].name}" if combatant.weapons else "attack with Unarmed Strike"
    def narrate_action(self, combatant, action, result):
        return ""

def run_simulation(c1_base: Combatant, c2_base: Combatant, env) -> dict:
    c1 = copy.deepcopy(c1_base)
    c1.team = 1
    c2 = copy.deepcopy(c2_base)
    c2.team = 2

    state = SimulationState(environment=env)
    state.combatants = [c1, c2]
    # Mute logs
    state.log = lambda msg: None

    c1.roll_initiative()
    c2.roll_initiative()

    state.combatants.sort(key=lambda c: c.initiative_score, reverse=True)

    llm = DummyAgent()

    while any(c.is_alive for c in state.combatants if c.team == 1) and any(c.is_alive for c in state.combatants if c.team == 2) and state.turn < 20:
        for active in state.combatants:
            if not active.is_alive:
                continue

            target = next(c for c in state.combatants if c.team != active.team and c.is_alive)

            action_decision = llm.ask_action(active, state)

            chosen_weapon_name = ""
            for w in active.weapons:
                if w.name.lower() in action_decision.lower():
                    chosen_weapon_name = w.name
                    break

            if chosen_weapon_name:
                weapon = next((w for w in active.weapons if w.name == chosen_weapon_name), active.weapons[0])
            else:
                weapon = active.weapons[0] if active.weapons else Weapon("Unarmed Strike", 4, "S", 0)

            # Attack Roll
            skill_val = 5 # Default if unknown
            if weapon.damage_type == 'P' and "Unarmed" not in weapon.name and "Sword" not in weapon.name and "Knife" not in weapon.name and "Claw" not in weapon.name and "Bite" not in weapon.name:
                skill_val = active.skills.get('Firearms', active.skills.get('Heavy Weapons', 5))
            else:
                skill_val = active.skills.get('Close Combat', active.skills.get('Unarmed Combat', 5))

            attack_pool = active.attributes.get('AGI', 3) + skill_val
            attack_hits = RulesEngine.roll_dice(attack_pool)

            # Defense Roll
            def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)
            def_hits = RulesEngine.roll_dice(def_pool)

            net_hits = attack_hits - def_hits

            if net_hits > 0:
                modified_damage = weapon.damage + net_hits
                modified_ap = weapon.ap

                soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor + modified_ap)
                soak_hits = RulesEngine.roll_dice(soak_pool)

                final_damage = max(0, modified_damage - soak_hits)

                if weapon.damage_type == 'P':
                    target.physical_damage += final_damage
                else:
                    target.stun_damage += final_damage

                if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                    target.is_alive = False

            if not target.is_alive:
                break

        state.turn += 1

    if all(c.is_alive for c in state.combatants):
        winner = "Draw"
    else:
        winner = next((c.name for c in state.combatants if c.is_alive), "Draw")

    return {
        "winner": winner,
        "turns": state.turn - 1,
        "c1_name": c1.name,
        "c2_name": c2.name,
        "c1_damage_taken": c1.physical_damage + c1.stun_damage,
        "c2_damage_taken": c2.physical_damage + c2.stun_damage
    }

def main():
    parser = argparse.ArgumentParser(description="Statistical Combat Analyzer for Shadowrun 7E")
    parser.add_argument("combatant1", help="Path to Chummer or Markdown file for combatant 1")
    parser.add_argument("combatant2", help="Path to Chummer or Markdown file for combatant 2")
    parser.add_argument("--scenario", help="Path to scenario JSON or Markdown", default="scenario.json")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of simulations to run")

    args = parser.parse_args()

    if not os.path.exists(args.scenario):
        import json
        with open(args.scenario, 'w') as f:
            json.dump({"description": "Empty Arena", "modifiers": {}}, f)

    env = parse_scenario(args.scenario)
    c1_base = load_combatant(args.combatant1)
    c2_base = load_combatant(args.combatant2)

    print(f"Running {args.iterations} simulations between {c1_base.name} and {c2_base.name}...")

    results = []
    for _ in range(args.iterations):
        res = run_simulation(c1_base, c2_base, env)
        results.append(res)

    c1_wins = sum(1 for r in results if r["winner"] == c1_base.name)
    c2_wins = sum(1 for r in results if r["winner"] == c2_base.name)
    draws = sum(1 for r in results if r["winner"] == "Draw")

    avg_turns = sum(r["turns"] for r in results) / args.iterations

    c1_avg_dmg_taken = sum(r["c1_damage_taken"] for r in results) / args.iterations
    c2_avg_dmg_taken = sum(r["c2_damage_taken"] for r in results) / args.iterations

    print("\n=== Statistical Analysis Results ===")
    print(f"Total Matches: {args.iterations}")
    print(f"{c1_base.name} Win Rate: {(c1_wins / args.iterations) * 100:.2f}% ({c1_wins} wins)")
    print(f"{c2_base.name} Win Rate: {(c2_wins / args.iterations) * 100:.2f}% ({c2_wins} wins)")
    print(f"Draws / Timeouts: {(draws / args.iterations) * 100:.2f}% ({draws} draws)")
    print(f"Average Duration: {avg_turns:.2f} turns")
    print(f"Average Damage Taken by {c1_base.name}: {c1_avg_dmg_taken:.2f}")
    print(f"Average Damage Taken by {c2_base.name}: {c2_avg_dmg_taken:.2f}")

if __name__ == "__main__":
    main()
