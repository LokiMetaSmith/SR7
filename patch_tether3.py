with open('scripts/combat_simulator.py', 'r') as f:
    content = f.read()

old_logic = """    elif is_erase_tether:
        if getattr(active, "is_locked_by_tarpit", False):
            action_text = f"{active.name} attempts to erase Tethers held by {target.name}."
            result_text = f"Failed! {active.name}'s connection is locked by Tar-Pit IC."
            return action_text, result_text, edge_spent
        log = active.get_attribute("LOG", 3)
        computer_skill = active.skills.get("Computer", 4)
        attack_pool = log + computer_skill

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
        attack_hits, attack_hits_glitched, edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        def_pool = target.get_attribute("LOG", 3) + target.skills.get("Hacking", 5)
        def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        action_text = f"attempts to erase Tethers held by {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            current_tethers = active.tethers.get(target.name, 0)
            if current_tethers > 0:
                removed = 2 if net_hits >= 3 else 1
                active.tethers[target.name] = max(0, current_tethers - removed)
                result_text = f"Successfully erased {removed} Tether(s)! {target.name} now holds {active.tethers[target.name]} Tether(s) on {active.name}."
            else:
                result_text = f"{target.name} holds no Tethers on {active.name} to erase."
        else:
            result_text = f"Failed to erase Tether. {target.name}'s connection remains secure." """

new_logic = """    elif is_erase_tether:
        action_text = f"{active.name} attempts to erase Tethers held by {target.name}."
        if getattr(active, "is_locked_by_tarpit", False):
            result_text = f"Failed! {active.name}'s connection is locked by Tar-Pit IC."
            return action_text, result_text, edge_spent
        result_text = RulesEngine.resolve_erase_tether(state, active, target)"""

content = content.replace(old_logic, new_logic)

with open('scripts/combat_simulator.py', 'w') as f:
    f.write(content)
