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
        if combatant.jumped_in_vehicle and combatant.jumped_in_vehicle.weapons:
            return f"attack with {combatant.jumped_in_vehicle.weapons[0].name}"
        if combatant.spells and combatant.attributes.get('MAG', 0) > 0:
            return f"cast {combatant.spells[0].name}"
        elif combatant.matrix.attack > 3:
            import random
            if random.random() > 0.5:
                return "data spike"
            else:
                return "establish tether"
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

            valid_targets = [c for c in state.combatants if c.team != active.team and c.is_alive]
            if not valid_targets:
                break
            target = valid_targets[0]

            action_decision = llm.ask_action(active, state)
            action_lower = action_decision.lower()

            is_spell = "cast" in action_lower or any(s.name.lower() in action_lower for s in active.spells)
            is_data_spike = "data spike" in action_lower
            is_tether = "tether" in action_lower

            if is_spell and active.spells:
                spell = next((s for s in active.spells if s.name.lower() in action_lower), active.spells[0])
                mag = active.attributes.get('MAG', 1)
                spell_skill = active.skills.get('Spellcasting', 5)

                attack_pool = mag + spell_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                if spell.type == "M":
                    def_pool = target.attributes.get('ESS', 6) + target.attributes.get('WIL', 3)
                else:
                    def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)

                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    modified_damage = mag + net_hits
                    if spell.type == "M":
                        soak_pool = 0
                    else:
                        soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor - mag)

                    soak_hits = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)
                    target.physical_damage += final_damage

                drain_value = max(2, mag - 2)
                drain_resist_pool = active.attributes.get('WIL', 3) + active.attributes.get('LOG', 3)
                drain_hits = RulesEngine.roll_dice(drain_resist_pool)
                drain_taken = max(0, drain_value - drain_hits)
                active.stun_damage += drain_taken

                if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                    target.is_alive = False
                if active.physical_damage >= active.physical_track or active.stun_damage >= active.stun_track:
                    active.is_alive = False

            elif is_data_spike:
                log = active.attributes.get('LOG', 3)
                cyber_skill = active.skills.get('Cybercombat', 5)
                attack_pool = log + cyber_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                def_pool = target.attributes.get('INT', 3) + target.matrix.firewall
                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    tethers = active.tethers.get(target.name, 0)
                    modified_damage = active.matrix.attack + net_hits + (tethers * 2)

                    soak_pool = target.matrix.data_processing + target.matrix.firewall
                    soak_hits = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)
                    target.stun_damage += final_damage

                    if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                        target.is_alive = False

            elif is_tether:
                log = active.attributes.get('LOG', 3)
                hack_skill = active.skills.get('Hacking', 5)
                attack_pool = log + hack_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                def_pool = target.attributes.get('WIL', 3) + target.matrix.firewall
                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    current_tethers = active.tethers.get(target.name, 0)
                    active.tethers[target.name] = current_tethers + 1

            else:
                chosen_weapon_name = ""
                available_weapons = active.jumped_in_vehicle.weapons if active.jumped_in_vehicle else active.weapons
                for w in available_weapons:
                    if w.name.lower() in action_lower:
                        chosen_weapon_name = w.name
                        break

                if chosen_weapon_name:
                    weapon = next((w for w in available_weapons if w.name == chosen_weapon_name), available_weapons[0])
                else:
                    weapon = available_weapons[0] if available_weapons else Weapon("Unarmed Strike", 4, "S", 0)

                if active.jumped_in_vehicle:
                    attack_pool = active.attributes.get('AGI', 3) + active.skills.get('Gunnery', 5) + active.control_rig
                else:
                    skill_val = 5
                    if weapon.damage_type == 'P' and "Unarmed" not in weapon.name and "Sword" not in weapon.name and "Knife" not in weapon.name and "Claw" not in weapon.name and "Bite" not in weapon.name:
                        skill_val = active.skills.get('Firearms', active.skills.get('Heavy Weapons', 5))
                    else:
                        skill_val = active.skills.get('Close Combat', active.skills.get('Unarmed Combat', 5))
                    attack_pool = active.attributes.get('AGI', 3) + skill_val

                attack_hits = RulesEngine.roll_dice(attack_pool)

                if target.jumped_in_vehicle:
                     def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3) + target.jumped_in_vehicle.handling
                else:
                     def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)
                def_hits = RulesEngine.roll_dice(def_pool)

                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    modified_damage = weapon.damage + net_hits
                    modified_ap = weapon.ap

                    if target.jumped_in_vehicle:
                         soak_pool = max(0, target.jumped_in_vehicle.body + target.jumped_in_vehicle.armor + modified_ap)
                    else:
                         soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor + modified_ap)

                    soak_hits = RulesEngine.roll_dice(soak_pool)

                    final_damage = max(0, modified_damage - soak_hits)

                    if target.jumped_in_vehicle:
                        if weapon.damage_type == 'P':
                            target.jumped_in_vehicle.physical_damage += final_damage
                            biofeedback = final_damage // 2
                            if biofeedback > 0:
                                bio_resist = target.attributes.get('WIL', 3) + target.attributes.get('BOD', 3)
                                bio_hits = RulesEngine.roll_dice(bio_resist)
                                net_bio = max(0, biofeedback - bio_hits)
                                target.stun_damage += net_bio
                            if target.jumped_in_vehicle.physical_damage >= target.jumped_in_vehicle.physical_track:
                                target.jumped_in_vehicle.is_destroyed = True
                                target.stun_damage += 6
                                target.jumped_in_vehicle = None
                        else:
                            target.stun_damage += final_damage
                    else:
                        if weapon.damage_type == 'P':
                            target.physical_damage += final_damage
                        else:
                            target.stun_damage += final_damage

                    if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                        target.is_alive = False

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
