import copy
import argparse
import sys
import os

# Ensure we can import combat_simulator when running from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # Fallback for root execution

from combat_utils import apply_nica_glitch

from combat_simulator import (
    load_combatant,
    parse_scenario,
    SimulationState,
    RulesEngine,
    Weapon,
    Combatant,
)


class DummyAgent:
    def ask_action(self, combatant, state):
        if combatant.jumped_in_vehicle and combatant.jumped_in_vehicle.weapons:
            return f"attack with {combatant.jumped_in_vehicle.weapons[0].name}"
        if combatant.spells and combatant.get_attribute("MAG", 0) > 0:
            return f"cast {combatant.spells[0].name}"
        elif combatant.matrix.attack > 3:
            import random

            if random.random() > 0.5:
                return "data spike"
            else:
                return "establish tether"
        import random

        return (
            "sprint to cover"
            if random.random() > 0.8
            else (
                f"attack with {combatant.weapons[0].name}"
                if combatant.weapons
                else "attack with Unarmed Strike"
            )
        )

    def narrate_action(self, combatant, action, result):
        return ""


def run_simulation(t1_bases: list, t2_bases: list, env) -> dict:
    state = SimulationState(environment=env)
    # Mute logs
    state.log = lambda msg: None

    state.combatants = []
    for c_base in t1_bases:
        c = copy.deepcopy(c_base)
        c.team = 1
        state.combatants.append(c)
    for c_base in t2_bases:
        c = copy.deepcopy(c_base)
        c.team = 2
        state.combatants.append(c)

    llm = DummyAgent()

    # Apply pre-combat economy & contact modifiers
    for c in state.combatants:
        if getattr(c, 'hot_nuyen', 0) >= 1000:
            god_tethers = c.hot_nuyen // 1000
            c.tethers["Grid Overwatch Division"] = god_tethers

        for contact in getattr(c, 'contacts', []):
            if contact.connection >= 4 and contact.loyalty >= 4:
                c.edge += 1

    for c in state.combatants:
        c.initiative_score = c.roll_initiative()
        # Apply high ground / surprise initiative modifiers
        if c.zone and (
            "High Ground" in c.zone.name or "High Ground" in c.zone.description
        ):
            import random

            extra = sum(random.randint(1, 6) for _ in range(1))  # 1 extra die
            c.initiative_score += extra

        if c.zone and ("Surprise" in c.zone.name or "Surprise" in c.zone.description):
            c.initiative_score += 2  # +2 base

    state.combatants.sort(key=lambda c: c.initiative_score, reverse=True)

    while (
        any(
            c.is_alive and not getattr(c, "has_yielded", False)
            for c in state.combatants
            if c.team == 1
        )
        and any(
            c.is_alive and not getattr(c, "has_yielded", False)
            for c in state.combatants
            if c.team == 2
        )
        and state.turn < 20
    ):
        for active in state.combatants:
            if not active.is_alive or getattr(active, "has_yielded", False):
                continue

            attack_hits_glitched = False
            def_hits_glitched = False
            soak_hits_glitched = False
            drain_hits_glitched = False
            bio_hits_glitched = False

            valid_targets = [
                c
                for c in state.combatants
                if c.team != active.team
                and c.is_alive
                and not getattr(c, "has_yielded", False)
            ]
            if not valid_targets:
                break
            target = valid_targets[0]

            action_decision = llm.ask_action(active, state)
            action_lower = action_decision.lower()

            is_social = (
                "social" in action_lower
                or "negotiate" in action_lower
                or "intimidate" in action_lower
                or "con" in action_lower
            )
            is_spell = "cast" in action_lower or any(
                s.name.lower() in action_lower for s in active.spells
            )
            is_data_spike = "data spike" in action_lower
            is_tether = "tether" in action_lower

            if is_social:
                cha = active.get_attribute("CHA", 3)
                attack_pool = cha + 5
                attack_hits, attack_hits_glitched, _edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                target_wil = target.get_attribute("WIL", 3)
                target_resist = target_wil + target.get_attribute("CHA", 3)

                def_hits, def_hits_glitched = RulesEngine.roll_dice(target_resist)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    influence_gain = 1 + net_hits
                    if not hasattr(active, "influence"):
                        active.influence = {}
                    current_influence = active.influence.get(target.name, 0)
                    active.influence[target.name] = current_influence + influence_gain

                    if active.influence[target.name] >= target_wil:
                        target.has_yielded = True

            elif is_spell and active.spells:

                spell = next(
                    (s for s in active.spells if s.name.lower() in action_lower),
                    active.spells[0],
                )
                mag = active.get_attribute("MAG", 1)
                spell_skill = active.skills.get("Spellcasting", 5)

                attack_pool = mag + spell_skill
                attack_hits, attack_hits_glitched, _edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                if spell.type == "M":
                    def_pool = target.get_attribute("ESS", 6) + target.get_attribute(
                        "WIL", 3
                    )
                else:
                    def_pool = target.get_attribute("REA", 3) + target.get_attribute(
                        "INT", 3
                    )

                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    modified_damage = mag + net_hits
                    if spell.type == "M":
                        soak_pool = 0
                    else:
                        soak_pool = max(
                            0, target.get_attribute("BOD", 3) + target.armor - mag
                        )

                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)
                    target.take_damage(final_damage, "P")

                drain_value = max(2, mag - 2)
                drain_resist_pool = active.get_attribute(
                    "WIL", 3
                ) + active.get_attribute("LOG", 3)
                drain_hits, drain_hits_glitched = RulesEngine.roll_dice(
                    drain_resist_pool
                )
                drain_taken = max(0, drain_value - drain_hits)
                active.stun_damage += drain_taken

                if (
                    target.physical_damage >= target.physical_track
                    or target.stun_damage >= target.stun_track
                ):
                    target.is_alive = False
                if (
                    active.physical_damage >= active.physical_track
                    or active.stun_damage >= active.stun_track
                ):
                    active.is_alive = False

            elif is_data_spike:
                log = active.get_attribute("LOG", 3)
                cyber_skill = active.skills.get("Cybercombat", 5)
                attack_pool = log + cyber_skill
                attack_hits, attack_hits_glitched, _edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                def_pool = target.get_attribute("INT", 3) + target.matrix.firewall
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    tethers = active.tethers.get(target.name, 0)
                    modified_damage = active.matrix.attack + net_hits + (tethers * 2)

                    soak_pool = target.matrix.data_processing + target.matrix.firewall
                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)
                    target.stun_damage += final_damage

                    if (
                        target.physical_damage >= target.physical_track
                        or target.stun_damage >= target.stun_track
                    ):
                        target.is_alive = False

            elif "sprint" in action_lower or "move" in action_lower:
                pass  # Abstract repositioning, no opposed roll needed

            elif is_tether:
                log = active.get_attribute("LOG", 3)
                hack_skill = active.skills.get("Hacking", 5)
                attack_pool = log + hack_skill
                attack_hits, attack_hits_glitched, _edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                def_pool = target.get_attribute("WIL", 3) + target.matrix.firewall
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    current_tethers = active.tethers.get(target.name, 0)
                    active.tethers[target.name] = current_tethers + 1

            else:
                chosen_weapon_name = ""
                available_weapons = (
                    active.jumped_in_vehicle.weapons
                    if active.jumped_in_vehicle
                    else active.weapons
                )
                for w in available_weapons:
                    if w.name.lower() in action_lower:
                        chosen_weapon_name = w.name
                        break

                if chosen_weapon_name:
                    weapon = next(
                        (w for w in available_weapons if w.name == chosen_weapon_name),
                        available_weapons[0],
                    )
                else:
                    weapon = (
                        available_weapons[0]
                        if available_weapons
                        else Weapon("Unarmed Strike", 4, "S", 0)
                    )

                if active.jumped_in_vehicle:
                    attack_pool = (
                        active.get_attribute("AGI", 3)
                        + active.skills.get("Gunnery", 5)
                        + active.control_rig
                    )
                else:
                    skill_val = 5
                    if (
                        weapon.damage_type == "P"
                        and "Unarmed" not in weapon.name
                        and "Sword" not in weapon.name
                        and "Knife" not in weapon.name
                        and "Claw" not in weapon.name
                        and "Bite" not in weapon.name
                    ):
                        skill_val = active.skills.get(
                            "Firearms", active.skills.get("Heavy Weapons", 5)
                        )
                    else:
                        skill_val = active.skills.get(
                            "Close Combat", active.skills.get("Unarmed Combat", 5)
                        )
                    attack_pool = active.get_attribute("AGI", 3) + skill_val

                attack_hits, attack_hits_glitched, _edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                if target.jumped_in_vehicle:
                    def_pool = (
                        target.get_attribute("REA", 3)
                        + target.get_attribute("INT", 3)
                        + target.jumped_in_vehicle.handling
                    )
                else:
                    def_pool = target.get_attribute("REA", 3) + target.get_attribute(
                        "INT", 3
                    )

                if target.zone and getattr(target.zone, "cover", None):
                    if target.zone.cover.lower() == "light":
                        def_pool += 1
                    elif target.zone.cover.lower() == "medium":
                        def_pool += 2
                    elif target.zone.cover.lower() == "heavy":
                        def_pool += 4
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)

                net_hits = attack_hits - def_hits

                if net_hits > 0:
                    is_explosive = (
                        "grenade" in weapon.name.lower()
                        or "missile" in weapon.name.lower()
                        or "rocket" in weapon.name.lower()
                    )
                    base_dmg = weapon.damage
                    cover_val = getattr(target.zone, "cover", "") if target.zone else ""
                    desc_val = (
                        getattr(target.zone, "description", "") if target.zone else ""
                    )
                    name_val = getattr(target.zone, "name", "") if target.zone else ""

                    if (
                        is_explosive
                        and target.zone
                        and (
                            cover_val
                            and cover_val.lower() == "heavy"
                            or "enclosed" in desc_val.lower()
                            or "enclosed" in name_val.lower()
                        )
                    ):
                        base_dmg *= 2
                        net_hits = max(0, net_hits)

                    modified_damage = base_dmg + net_hits
                    modified_ap = weapon.ap

                    if target.jumped_in_vehicle:
                        soak_pool = max(
                            0,
                            target.jumped_in_vehicle.body
                            + target.jumped_in_vehicle.armor
                            + modified_ap,
                        )
                    else:
                        soak_pool = max(
                            0,
                            target.get_attribute("BOD", 3)
                            + target.armor
                            + modified_ap,
                        )

                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)

                    final_damage = max(0, modified_damage - soak_hits)

                    target.take_damage(final_damage, weapon.damage_type)

                    if (
                        target.physical_damage >= target.physical_track
                        or target.stun_damage >= target.stun_track
                    ):
                        target.is_alive = False

            if "N.I.C.A." in getattr(active, "special_rules", []):
                if attack_hits_glitched or drain_hits_glitched:
                    apply_nica_glitch(active)

            if "N.I.C.A." in getattr(target, "special_rules", []):
                if def_hits_glitched or soak_hits_glitched or bio_hits_glitched:
                    apply_nica_glitch(target)

            if (
                target.physical_damage >= target.physical_track
                or target.stun_damage >= target.stun_track
            ):
                target.is_alive = False
            if (
                active.physical_damage >= active.physical_track
                or active.stun_damage >= active.stun_track
            ):
                active.is_alive = False

        state.turn += 1

    t1_alive = any(
        c.is_alive and not getattr(c, "has_yielded", False)
        for c in state.combatants
        if c.team == 1
    )
    t2_alive = any(
        c.is_alive and not getattr(c, "has_yielded", False)
        for c in state.combatants
        if c.team == 2
    )

    if t1_alive and not t2_alive:
        winning_team = 1
    elif t2_alive and not t1_alive:
        winning_team = 2
    else:
        winning_team = "Draw"

    t1_dmg = sum(
        c.physical_damage + c.stun_damage for c in state.combatants if c.team == 1
    )
    t2_dmg = sum(
        c.physical_damage + c.stun_damage for c in state.combatants if c.team == 2
    )

    return {
        "winning_team": winning_team,
        "turns": state.turn - 1,
        "t1_damage_taken": t1_dmg,
        "t2_damage_taken": t2_dmg,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Statistical Combat Analyzer for Shadowrun 7E"
    )
    parser.add_argument(
        "--team1",
        nargs="+",
        required=True,
        help="Paths to Chummer or Markdown files for Team 1",
    )
    parser.add_argument(
        "--team2",
        nargs="+",
        required=True,
        help="Paths to Chummer or Markdown files for Team 2",
    )
    parser.add_argument(
        "--scenario", help="Path to scenario JSON or Markdown", default="scenario.json"
    )
    parser.add_argument(
        "--iterations", type=int, default=1000, help="Number of simulations to run"
    )

    args = parser.parse_args()

    if not os.path.exists(args.scenario):
        import json

        with open(args.scenario, "w") as f:
            json.dump({"description": "Empty Arena", "modifiers": {}}, f)

    env = parse_scenario(args.scenario)

    t1_bases = [load_combatant(p) for p in args.team1]
    t2_bases = [load_combatant(p) for p in args.team2]

    for c in t1_bases:
        c.team = 1
    for c in t2_bases:
        c.team = 2

    print(f"Running {args.iterations} squad simulations...")

    results = []
    for _ in range(args.iterations):
        res = run_simulation(t1_bases, t2_bases, env)
        results.append(res)

    t1_wins = sum(1 for r in results if r["winning_team"] == 1)
    t2_wins = sum(1 for r in results if r["winning_team"] == 2)
    draws = sum(1 for r in results if r["winning_team"] == "Draw")

    avg_turns = sum(r["turns"] for r in results) / args.iterations

    t1_avg_dmg = sum(r["t1_damage_taken"] for r in results) / args.iterations
    t2_avg_dmg = sum(r["t2_damage_taken"] for r in results) / args.iterations

    print("\n=== Statistical Analysis Results ===")
    print(f"Total Matches: {args.iterations}")
    print(f"Team 1 Win Rate: {(t1_wins / args.iterations) * 100:.2f}% ({t1_wins} wins)")
    print(f"Team 2 Win Rate: {(t2_wins / args.iterations) * 100:.2f}% ({t2_wins} wins)")
    print(f"Draws / Timeouts: {(draws / args.iterations) * 100:.2f}% ({draws} draws)")
    print(f"Average Duration: {avg_turns:.2f} turns")
    print(f"Average Damage Taken by Team 1: {t1_avg_dmg:.2f}")
    print(f"Average Damage Taken by Team 2: {t2_avg_dmg:.2f}")


if __name__ == "__main__":
    main()
