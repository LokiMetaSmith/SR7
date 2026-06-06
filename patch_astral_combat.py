with open("scripts/combat_simulator.py", "r") as f:
    content = f.read()

# 1. Add is_astral_combat boolean
old_bools = """    is_astral_projection = "astral project" in action_lower
    is_astral_return = "return to physical" in action_lower"""

new_bools = """    is_astral_projection = "astral project" in action_lower
    is_astral_return = "return to physical" in action_lower
    is_astral_combat = "astral combat" in action_lower or "astral attack" in action_lower"""

content = content.replace(old_bools, new_bools)

# 2. Implement Astral Combat Logic
old_logic = """    elif is_erase_tether:
        log = active.get_attribute("LOG", 3)"""

new_logic = """    elif is_astral_combat:
        if target.current_plane != Plane.ASTRAL and not target.is_dual_natured:
            action_text = f"attempts astral combat on {target.name}"
            result_text = f"Action fails: {target.name} is not present on the astral plane."
            narration = llm.narrate_action(active, action_text, result_text, state=state)
            state.log(narration)
            return action_text, result_text, edge_spent

        attack_pool = active.get_attribute("WIL", 3) + active.skills.get("Astral Combat", 5)
        attack_hits, attack_hits_glitched, edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

        def_pool = target.get_attribute("INT", 3) + target.get_attribute("LOG", 3)
        def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        action_text = f"engages {target.name} in astral combat ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            base_dmg = active.get_attribute("CHA", 3) // 2
            damage_type = "S"

            # Use weapon focus or physical damage if dual natured
            if active.is_dual_natured or "focus" in action_lower:
                damage_type = "P"
                if "focus" in action_lower and active.weapons:
                    base_dmg = active.weapons[0].damage # simplification

            modified_damage = base_dmg + net_hits

            soak_pool = target.get_attribute("WIL", 3)
            # Add mystic armor if any
            for rule in target.special_rules:
                if rule.startswith("Mystic Armor"):
                    try:
                        soak_pool += int(rule.split("[Rating ")[1].split("]")[0])
                    except:
                        pass

            soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)
            final_damage = max(0, modified_damage - soak_hits)

            result_text = f"Astral Attack succeeds! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} {damage_type} damage."
            result_text += target.take_damage(final_damage, damage_type)

            if (
                target.physical_damage >= target.physical_track
                or target.stun_damage >= target.stun_track
            ):
                target.is_alive = False
                result_text += f" {target.name} is incapacitated!"
        else:
            result_text = f"Astral Attack missed! {target.name} successfully defended."

    elif is_erase_tether:
        log = active.get_attribute("LOG", 3)"""

content = content.replace(old_logic, new_logic)

with open("scripts/combat_simulator.py", "w") as f:
    f.write(content)
