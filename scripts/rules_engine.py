from typing import Tuple, List, Optional, Dict
import random

class DiceRules:


    @staticmethod
    def roll_dice(pool: int, wild_dice_count: int = 0, combatant=None, is_extream_mode: bool = False) -> tuple[int, bool]:
        hits = 0
        ones_twos = 0
        normal_fives = 0
        wild_ones = 0
        crit_sixes = 0
        crit_ones = 0

        actual_pool = pool
        if combatant and getattr(combatant, 'hmhvv_infection_level', 0) and type(getattr(combatant, 'hmhvv_infection_level', 0)) == int and getattr(combatant, 'hmhvv_infection_level', 0) > 0:
            actual_pool -= 1
        actual_pool = max(1, actual_pool)

        # Centering Metamagic reduces negative modifiers in a roundabout way, but effectively acts
        # as a bonus to the final dice pool based on Initiation grade if they are taking a magic action.
        # We handle this in the spellcasting block mostly, but we can do a general dice pool bonus here
        # if Centering is present in special rules.
        if combatant and combatant.special_rules:
            for rule in combatant.special_rules:
                if "centering" in rule.lower():
                    # For simplicity, grant +1 die if they have Centering
                    actual_pool += 1
                    break
        wild_dice = min(actual_pool, max(0, wild_dice_count))

        if is_extream_mode:
            # Extream Mode uses SRX Crit Dice rules (2 dice are Crit Dice)
            crit_dice = min(actual_pool, 2)
            standard_dice = max(0, actual_pool - crit_dice - wild_dice)
            # Ensure wild dice does not over-consume pool (crit takes precedence)
            if wild_dice + crit_dice > actual_pool:
                wild_dice = actual_pool - crit_dice

            for _ in range(crit_dice):
                roll = random.randint(1, 6)
                if roll == 5:
                    normal_fives += 1
                    hits += 1
                elif roll == 6:
                    crit_sixes += 1
                    hits += 1
                elif roll == 1:
                    crit_ones += 1
                    ones_twos += 1
                elif roll == 2:
                    ones_twos += 1

            for _ in range(standard_dice):
                roll = random.randint(1, 6)
                if roll == 5:
                    normal_fives += 1
                    hits += 1
                elif roll == 6:
                    hits += 1
                elif roll in [1, 2]:
                    ones_twos += 1

            for _ in range(wild_dice):
                roll = random.randint(1, 6)
                if roll == 6:
                    hits += 3
                elif roll == 5:
                    hits += 1
                elif roll == 1:
                    wild_ones += 1
                    ones_twos += 1
                elif roll == 2:
                    ones_twos += 1

            # SRX Crit Dice: Double 6s = +3 hits, Double 1s = Glitch
            if crit_sixes >= 2:
                hits += 3

            # Wild Dice 1s cancel all standard 5s
            if wild_ones > 0:
                hits -= normal_fives

            glitched = (crit_ones >= 2) or (wild_ones > 0) # G.O.D. Manifestation glitch occurs on wild one in hacking

        else:
            standard_dice = actual_pool - wild_dice

            for _ in range(standard_dice):
                roll = random.randint(1, 6)
                if roll == 5:
                    normal_fives += 1
                    hits += 1
                elif roll == 6:
                    hits += 1
                elif roll in [1, 2]:
                    ones_twos += 1

            for _ in range(wild_dice):
                roll = random.randint(1, 6)
                if roll == 6:
                    hits += 3
                elif roll == 5:
                    hits += 1
                elif roll == 1:
                    wild_ones += 1
                    ones_twos += 1
                elif roll == 2:
                    ones_twos += 1

            # Wild Dice 1s cancel all standard 5s
            if wild_ones > 0:
                hits -= normal_fives

            glitched = ones_twos >= (actual_pool / 2.0)

        return hits, glitched

    @staticmethod
    def roll_attack_with_edge(
        pool: int, combatant: "Combatant", wild_dice_count: int = 0, is_extream_mode: bool = False
    ) -> tuple[int, bool, bool]:
        """Rolls an attack and automatically spends Edge to reroll if 0 hits are rolled."""
        hits, glitched = DiceRules.roll_dice(pool, wild_dice_count, combatant=combatant, is_extream_mode=is_extream_mode)
        edge_spent = False
        if hits == 0 and combatant.edge > 0:
            combatant.edge -= 1
            reroll_hits, reroll_glitched = DiceRules.roll_dice(pool, wild_dice_count, combatant=combatant, is_extream_mode=is_extream_mode)
            hits += reroll_hits
            glitched = reroll_glitched
            edge_spent = True
        return hits, glitched, edge_spent


class MatrixRules:

    @staticmethod
    def resolve_ic_attack(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        action_text = ""
        result_text = ""
        is_tar_pit_attack = "tar-pit" in action_lower
        is_patrol_scan = "patrol scan" in action_lower
        is_killer_ic = "killer ic" in action_lower
        is_sparky_ic = "sparky ic" in action_lower
        is_data_ic_response = "data ic" in action_lower

        if is_tar_pit_attack:
            attack_pool = active.skills.get("Cybercombat", 5) + active.get_attribute("LOG", 3)

            wild_dice_count = 0
            if state.environment.is_extream_mode:
                wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
            attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

            def_pool = getattr(target.matrix, "firewall", 3) + target.get_attribute("INT", 3)
            if target.null_bags > 0:
                def_pool += target.null_bags
            def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)

            net_hits = attack_hits - def_hits
            action_text = f"The Tar-Pit IC attacks {target.name} ({attack_hits} hits vs {def_hits} defense hits)."

            if net_hits > 0:
                target.is_locked_by_tarpit = True
                result_text = f"Tar-Pit IC strikes! It deals no damage but locks all of {target.name}'s Tethers. {target.name} cannot voluntarily Jack Out or Erase Tethers."
            else:
                result_text = f"Tar-Pit IC misses or is resisted by {target.name}."

        elif is_patrol_scan:
            attack_pool = active.host_rating * 2 if getattr(active, "host_rating", 0) > 0 else active.get_attribute("LOG", 3) + active.skills.get("Computer", 5)

            wild_dice_count = 0
            if state.environment.is_extream_mode:
                wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
            attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

            def_pool = target.get_attribute("INT", 3) + getattr(target.matrix, "sleaze", 3)
            if target.null_bags > 0:
                def_pool += target.null_bags
            def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
            net_hits = attack_hits - def_hits

            action_text = f"Patrol IC scans for intruders ({attack_hits} hits vs {def_hits} defense hits)."

            if net_hits > 0:
                active.tethers[target.name] = active.tethers.get(target.name, 0) + 1
                state.environment.alert_level += 1
                result_text = f"Patrol IC spots {target.name}! It alerts the Hive, placing 1 Tether on {target.name} and raising the Host Alert Level to {state.environment.alert_level}!"
            else:
                result_text = f"Patrol IC fails to spot {target.name}."

        elif is_killer_ic:
            attack_pool = active.host_rating * 2 if getattr(active, "host_rating", 0) > 0 else active.get_attribute("LOG", 3) + active.skills.get("Cybercombat", 5)

            wild_dice_count = 0
            if state.environment.is_extream_mode:
                wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
            attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

            def_pool = target.get_attribute("INT", 3) + getattr(target.matrix, "firewall", 3)
            if target.null_bags > 0:
                def_pool += target.null_bags
            def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
            net_hits = attack_hits - def_hits

            action_text = f"Killer IC strikes {target.name} ({attack_hits} hits vs {def_hits} defense hits)."

            if net_hits > 0:
                tethers = active.tethers.get(target.name, 0)
                base_damage = active.host_rating if getattr(active, "host_rating", 0) > 0 else active.matrix.attack
                modified_damage = base_damage + net_hits + (tethers * 2)

                soak_pool = getattr(target.matrix, "data_processing", 3) + getattr(target.matrix, "firewall", 3)
                soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
                final_damage = max(0, modified_damage - soak_hits)

                result_text = f"Killer IC connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Matrix damage."
                # Matrix damage generally routes to stun or device depending on target
                target.stun_damage += final_damage
            else:
                result_text = f"Killer IC attack is deflected by {target.name}'s firewall."

        elif is_sparky_ic:
            attack_pool = active.host_rating * 2 if getattr(active, "host_rating", 0) > 0 else active.get_attribute("LOG", 3) + active.skills.get("Cybercombat", 5)

            wild_dice_count = 0
            if state.environment.is_extream_mode:
                wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
            attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

            def_pool = target.get_attribute("INT", 3) + getattr(target.matrix, "firewall", 3)
            if target.null_bags > 0:
                def_pool += target.null_bags
            def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
            net_hits = attack_hits - def_hits

            action_text = f"Sparky IC unleashes a biofeedback surge at {target.name} ({attack_hits} hits vs {def_hits} defense hits)."

            if net_hits > 0:
                base_damage = active.host_rating if getattr(active, "host_rating", 0) > 0 else active.matrix.attack
                modified_damage = base_damage + net_hits

                soak_pool = getattr(target.matrix, "data_processing", 3) + getattr(target.matrix, "firewall", 3)
                soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
                final_damage = max(0, modified_damage - soak_hits)

                result_text = f"Sparky IC connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Matrix damage AND an equal amount of Stun Biofeedback!"
                target.stun_damage += final_damage
                target.stun_damage += final_damage # Extra biofeedback
            else:
                result_text = f"Sparky IC attack is deflected by {target.name}'s firewall."

        elif is_data_ic_response:
            log = active.get_attribute("LOG", 3)
            cyber_skill = active.skills.get("Cybercombat", 5)
            attack_pool = log + cyber_skill

            wild_dice_count = 0
            if state.environment.is_extream_mode:
                wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
            attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

            def_pool = target.get_attribute("INT", 3) + getattr(target.matrix, "firewall", 3)
            if target.null_bags > 0:
                def_pool += target.null_bags
            def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
            net_hits = attack_hits - def_hits

            action_text = f"Data IC deploys an EMP burst/scrambler at {target.name} ({attack_hits} hits vs {def_hits} defense hits)."

            if net_hits > 0:
                soak_pool = getattr(target.matrix, "data_processing", 3) + getattr(target.matrix, "firewall", 3)
                soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
                final_damage = max(0, 4 - soak_hits)
                result_text = f"Data IC connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Stun damage."
                target.stun_damage += final_damage
            else:
                result_text = f"Data IC attack is deflected by {target.name}'s firewall."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_compile(state: "SimulationState", active: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        sprite_level = 5
        import re
        match = re.search(r'level\s*(\d+)', action_lower)
        if match:
            sprite_level = int(match.group(1))

        compiling_pool = active.skills.get("Compiling", 0) + active.get_attribute("RES", 3)

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
        compiling_hits, compiling_glitched, edge_spent = DiceRules.roll_attack_with_edge(compiling_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        sprite_hits, sprite_glitched = DiceRules.roll_dice(sprite_level)

        net_hits = compiling_hits - sprite_hits

        # Fading
        fading_value = sprite_hits * 2
        fading_resist_pool = active.get_attribute("WIL", 3) + active.get_attribute("RES", 3)
        fading_resist_hits, fading_glitched = DiceRules.roll_dice(fading_resist_pool)
        fading_damage = max(0, fading_value - fading_resist_hits)
        fading_type = "P" if fading_value > active.get_attribute("RES", 3) else "S"

        action_text = f"{active.name} attempts to compile a Level {sprite_level} sprite (Compiling Pool: {compiling_pool})."
        result_text = ""
        if net_hits > 0:
            result_text = f"{active.name} successfully compiles a sprite with {net_hits} tasks. "
            import glob

            sprite_path = None
            templates = glob.glob("npc_templates/*sprite*.chum5")
            if templates:
                import random
                sprite_path = random.choice(templates)

            if sprite_path:
                try:
                    from scripts.combat_simulator import load_combatant
                    sprite = load_combatant(sprite_path)
                    sprite.name = f"{active.name}'s {sprite.name} (Level {sprite_level})"
                    sprite.team = active.team

                    # Adjust stats based on level loosely
                    sprite.attributes['BOD'] = sprite_level
                    sprite.attributes['AGI'] = sprite_level + 1
                    sprite.attributes['REA'] = sprite_level
                    sprite.attributes['STR'] = sprite_level
                    sprite.attributes['WIL'] = sprite_level
                    sprite.attributes['LOG'] = sprite_level
                    sprite.attributes['INT'] = sprite_level
                    sprite.attributes['CHA'] = sprite_level
                    if hasattr(sprite, 'special_rules'):
                        sprite.special_rules.append(f"Armor {sprite_level}")

                    state.combatants.append(sprite)
                    result_text += f"The {sprite.name} compiles and manifests! "
                except Exception as e:
                    pass
            else:
                from scripts.combat_simulator import Combatant, MatrixAttributes
                sprite = Combatant(
                    name=f"{active.name}'s Compiled Sprite (Level {sprite_level})",
                    attributes={
                        'BOD': sprite_level,
                        'AGI': sprite_level + 1,
                        'REA': sprite_level,
                        'STR': sprite_level,
                        'WIL': sprite_level,
                        'LOG': sprite_level,
                        'INT': sprite_level,
                        'CHA': sprite_level,
                    },
                    skills={"Cybercombat": sprite_level, "Hacking": sprite_level},
                    matrix=MatrixAttributes(),
                    team=active.team
                )
                state.combatants.append(sprite)
                result_text += f"The {sprite.name} compiles and manifests! "

        else:
            result_text = f"{active.name} fails to compile the sprite. "

        if fading_damage > 0:
            status = active.take_damage(fading_damage, fading_type)
            result_text += f"{active.name} takes {fading_damage}{fading_type} Fading. {status}"
        else:
            result_text += f"{active.name} resists all Fading."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_erase_tether(state: "SimulationState", active: "Combatant", target: "Combatant") -> str:
        log = active.get_attribute("LOG", 3)
        computer_skill = active.skills.get("Computer", 4)
        attack_pool = log + computer_skill

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
        attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        def_pool = target.get_attribute("LOG", 3) + target.skills.get("Hacking", 5)
        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        if net_hits > 0:
            current_tethers = active.tethers.get(target.name, 0)
            if current_tethers > 0:
                removed = 2 if net_hits >= 3 else 1
                active.tethers[target.name] = max(0, current_tethers - removed)
                return f"Successfully erased {removed} Tether(s)! {target.name} now holds {active.tethers[target.name]} Tether(s) on {active.name}."
            else:
                return f"{target.name} holds no Tethers on {active.name} to erase."
        else:
            return f"Failed to erase Tether. {target.name}'s connection remains secure."

class MagicRules:

    @staticmethod
    def resolve_summon(state: "SimulationState", active: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        # Find spirit name and force in action or pick random
        spirit_force = 5
        import re
        match = re.search(r'force\s*(\d+)', action_lower)
        if match:
            spirit_force = int(match.group(1))

        conjuring_pool = active.skills.get("Conjuring", 0) + active.get_attribute("MAG", 3)

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
        conjuring_hits, conjuring_glitched, edge_spent = DiceRules.roll_attack_with_edge(conjuring_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        spirit_hits, spirit_glitched = DiceRules.roll_dice(spirit_force)

        net_hits = conjuring_hits - spirit_hits

        # Drain
        drain_value = spirit_hits * 2
        drain_resist_pool = active.get_attribute("WIL", 3) + active.get_attribute("LOG", 3)
        drain_resist_hits, drain_glitched = DiceRules.roll_dice(drain_resist_pool)
        drain_damage = max(0, drain_value - drain_resist_hits)
        drain_type = "P" if spirit_force > active.get_attribute("MAG", 3) else "S"

        action_text = f"{active.name} attempts to summon a Force {spirit_force} spirit (Conjuring Pool: {conjuring_pool})."
        result_text = ""
        if net_hits > 0:
            result_text = f"{active.name} successfully summons a spirit with {net_hits} services. "
            import glob

            templates = glob.glob("npc_templates/*spirit*.chum5")
            if templates:
                import random
                spirit_path = random.choice(templates)
                try:
                    from scripts.combat_simulator import load_combatant
                    spirit = load_combatant(spirit_path)
                    spirit.name = f"{active.name}'s {spirit.name} (Force {spirit_force})"
                    spirit.team = active.team

                    # Adjust stats based on force loosely
                    spirit.attributes['BOD'] = spirit_force
                    spirit.attributes['AGI'] = spirit_force + 1
                    spirit.attributes['REA'] = spirit_force
                    spirit.attributes['STR'] = spirit_force
                    spirit.attributes['WIL'] = spirit_force
                    spirit.attributes['LOG'] = spirit_force
                    spirit.attributes['INT'] = spirit_force
                    spirit.attributes['CHA'] = spirit_force

                    state.combatants.append(spirit)
                    result_text += f"The {spirit.name} materializes and joins the fight! "
                except:
                    pass
        else:
            result_text = f"{active.name} fails to summon the spirit. "

        if drain_damage > 0:
            status = active.take_damage(drain_damage, drain_type)
            result_text += f"{active.name} takes {drain_damage}{drain_type} Summoning Drain. {status}"
        else:
            result_text += f"{active.name} resists all Summoning Drain."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_spell(state: "SimulationState", active: "Combatant", target: "Combatant", spell, action_lower: str) -> tuple[str, str, bool]:
        import re
        mag = active.get_attribute("MAG", 1)
        spell_skill = active.skills.get("Spellcasting", 5)

        attack_pool = mag + spell_skill

        wild_dice_count = state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0)) if state.environment.is_extream_mode else 0
        attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        # Defense
        if spell.type == "M":
            def_pool = target.get_attribute("ESS", 6) + target.get_attribute("WIL", 3)
        else:
            def_pool = target.get_attribute("REA", 3) + target.get_attribute("INT", 3)

        # Shielding Metamagic adds dice to spell defense tests
        if target.special_rules:
            for rule in target.special_rules:
                if "shielding" in rule.lower():
                    m = re.search(r"shielding (\d+)", rule, re.IGNORECASE)
                    def_pool += int(m.group(1)) if m else 1
                    break

        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        action_text = f"casts {spell.name} at {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            base_damage = mag  # Assume Force = MAG
            modified_damage = base_damage + net_hits

            if spell.type == "M":
                soak_pool = 0  # Mana spells ignore armor
            else:
                soak_pool = max(0, target.get_attribute("BOD", 3) + getattr(target, "total_armor", 0) - mag)

            soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
            final_damage = max(0, modified_damage - soak_hits)

            result_text = f"Spell hits! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} P damage."
            result_text += target.take_damage(final_damage, 'P')
        else:
            result_text = f"Spell misses or is resisted by {target.name}."

        # Drain
        drain_value = max(2, mag - 2)  # Assume F-2
        drain_resist_pool = active.get_attribute("WIL", 3) + active.get_attribute("LOG", 3)
        # Shielding Metamagic
        for rule in active.special_rules:
            if rule.lower().startswith("shielding"):
                m = re.search(r"shielding (\d+)", rule, re.IGNORECASE)
                drain_resist_pool += int(m.group(1)) if m else 1
                break

        drain_hits, drain_hits_glitched = DiceRules.roll_dice(drain_resist_pool)
        drain_taken = max(0, drain_value - drain_hits)

        # Check for physical drain due to Matrix noise in merged world
        drain_type = "Stun"
        if state.environment.modifiers.get("background_count", 0) > 2 or drain_value > mag:
            drain_type = "Physical"

        result_text += f" {active.name} rolls {drain_resist_pool} to resist drain, taking {drain_taken} {drain_type} damage."

        if drain_type == "Physical":
            active.take_damage(drain_taken, "P")
        else:
            active.take_damage(drain_taken, "S")

        if (target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track):
            target.is_alive = False
            result_text += f" {target.name} is incapacitated!"
        if (active.physical_damage >= active.physical_track or active.stun_damage >= active.stun_track):
            active.is_alive = False
            result_text += f" {active.name} is incapacitated from Drain!"

        return action_text, result_text, edge_spent


class CombatRules:

    @staticmethod
    def roll_initiative(combatant) -> int:
        import random
        from scripts.combat_simulator import Plane
        if combatant.current_plane == Plane.ASTRAL or combatant.is_dual_natured:
            base = combatant.get_attribute("REA", 3) + combatant.get_attribute("INT", 3) + combatant.get_attribute("MAG", 0)
            dice = 1
        elif combatant.current_plane == Plane.MATRIX or combatant.jumped_in_vehicle:
            base = combatant.matrix.data_processing + combatant.get_attribute("INT", 3)
            dice = 1 + getattr(combatant, 'control_rig', 0)
        else:
            base = combatant.get_attribute("REA", 3) + combatant.get_attribute("INT", 3)
            dice = 1
            if "Wired Reflexes" in " ".join(combatant.special_rules):
                dice += 1

        roll = sum(random.randint(1, 6) for _ in range(dice))
        combatant.initiative_score = base + roll

        if getattr(combatant, "hmhvv_infection_level", 0) > 0:
            combatant.initiative_score = max(0, combatant.initiative_score - 1)

        return combatant.initiative_score


    @staticmethod
    def _get_zone_center(layout_ascii: List[str], legend: Dict[str, str], zone_name: str) -> Optional[tuple[int, int]]:
        """Finds the geometric center of a zone based on the layout and legend."""
        char_to_find = None
        for k, v in legend.items():
            if zone_name.lower() in v.lower():
                char_to_find = k
                break

        if not char_to_find:
            return None

        points = []
        for y, row in enumerate(layout_ascii):
            for x, char in enumerate(row):
                if char == char_to_find:
                    points.append((x, y))

        if not points:
            return None

        sum_x = sum(p[0] for p in points)
        sum_y = sum(p[1] for p in points)
        return (sum_x // len(points), sum_y // len(points))

    @staticmethod
    def calculate_los_cover(state: "SimulationState", active: 'Combatant', target: 'Combatant') -> int:
        """Calculates dynamic cover bonus using Bresenham's line algorithm on the map grid."""
        if not state.environment.layout_ascii or not active.zone or not target.zone:
            # Fallback to simple zone cover
            return 0

        if active.zone == target.zone:
            return 0 # No cover inside the same zone generally

        start = CombatRules._get_zone_center(state.environment.layout_ascii, state.environment.legend, active.zone.name)
        end = CombatRules._get_zone_center(state.environment.layout_ascii, state.environment.legend, target.zone.name)

        if not start or not end:
             return 0

        x0, y0 = start
        x1, y1 = end
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        cover_bonus = 0

        while True:
            if (x0, y0) != start and (x0, y0) != end:
                # Check cell for cover
                if 0 <= y0 < len(state.environment.layout_ascii) and 0 <= x0 < len(state.environment.layout_ascii[y0]):
                    char = state.environment.layout_ascii[y0][x0]
                    desc = state.environment.legend.get(char, "").lower()
                    if "heavy cover" in desc: cover_bonus = max(cover_bonus, 4)
                    elif "medium cover" in desc: cover_bonus = max(cover_bonus, 2)
                    elif "light cover" in desc: cover_bonus = max(cover_bonus, 1)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

        return cover_bonus

    @staticmethod
    def resolve_data_spike(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str, llm) -> tuple[str, str, bool]:
        edge_spent = False
        if "Null-Suit" in target.special_rules:
            action_text = f"attempts a Matrix action on {target.name}"
            result_text = f"Action fails: {target.name} is wearing a Null-Suit and is immune to Matrix targeting."
            narration = llm.narrate_action(active, action_text, result_text, state=state)
            state.log(narration)
            return action_text, result_text, edge_spent
        log = active.get_attribute("LOG", 3)
        cyber_skill = active.skills.get("Cybercombat", 5)
        attack_pool = log + cyber_skill

        wild_dice_count = state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0)) if state.environment.is_extream_mode else 0
        attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        def_pool = target.get_attribute("INT", 3) + target.matrix.firewall
        if target.null_bags > 0:
            def_pool += target.null_bags
        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        action_text = f"launches a Data Spike at {target.name}'s persona ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            tethers = active.tethers.get(target.name, 0)
            modified_damage = active.matrix.attack + net_hits + (tethers * 2)

            soak_pool = target.matrix.data_processing + target.matrix.firewall
            soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
            final_damage = max(0, modified_damage - soak_hits)

            result_text = f"Data Spike connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Stun (Biofeedback) damage."
            target.stun_damage += final_damage

            # Check Mutual Tether Feedback Loop
            if target.tethers.get(active.name, 0) > 0 and active.tethers.get(target.name, 0) > 0:
                feedback_damage = final_damage // 2
                if feedback_damage > 0:
                    active.stun_damage += feedback_damage
                    result_text += f" Mutual Tethers trigger a Feedback Loop! {active.name} takes {feedback_damage} unresisted Stun feedback."
                    if active.stun_damage >= active.stun_track:
                        active.is_alive = False
                        result_text += f" {active.name} is incapacitated by the feedback!"

            if (
                target.physical_damage >= target.physical_track
                or target.stun_damage >= target.stun_track
            ):
                target.is_alive = False
                result_text += f" {target.name} is incapacitated!"
        else:
            result_text = (
                f"Data Spike is deflected by {target.name}'s firewall."
            )
            if attack_hits_glitched and getattr(state, "is_stealth_phase_active", False):
                state.is_stealth_phase_active = False
                result_text += " Critical glitch! Alarm triggered, stealth broken!"
            elif getattr(state, "is_stealth_phase_active", False):
                result_text += " Failed hack attempts raise suspicion but stealth is maintained."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_attack(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        # Determine weapon
        weapon_used = None
        for w in active.weapons:
            if w.name.lower() in action_lower:
                weapon_used = w
                break

        if not weapon_used and active.weapons:
            weapon_used = active.weapons[0]

        is_loud = "grenade" in action_lower or "rocket" in action_lower or "missile" in action_lower or (weapon_used and "suppressed" not in weapon_used.name.lower() and "bow" not in weapon_used.name.lower() and "knife" not in weapon_used.name.lower() and "blade" not in weapon_used.name.lower())

        attack_pool = active.get_attribute("AGI", 3)
        if weapon_used:
            if hasattr(weapon_used, "type") and weapon_used.type in ["Pistols", "Automatics", "Longarms", "Heavy Weapons"]:
                attack_pool += active.skills.get("Firearms", 4)
            elif hasattr(weapon_used, "type") and weapon_used.type in ["Blades", "Clubs", "Unarmed"]:
                attack_pool += active.skills.get("Close Combat", 4)
            else:
                attack_pool += active.skills.get("Firearms", 4)

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))

        attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        def_pool = target.get_attribute("REA", 3) + target.get_attribute("INT", 3)
        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
        net_hits = attack_hits - def_hits

        weapon_name = weapon_used.name if weapon_used else "unarmed"
        action_text = f"attacks {target.name} with {weapon_name} ({attack_hits} hits vs {def_hits} defense hits)"
        result_text = ""

        if getattr(state, "is_stealth_phase_active", False) and is_loud:
            state.is_stealth_phase_active = False
            result_text += " Loud weapon used! Stealth broken! "

        if net_hits > 0:
            base_dmg = weapon_used.damage if weapon_used else active.get_attribute("STR", 3) // 2
            dmg_type = weapon_used.type if weapon_used and hasattr(weapon_used, 'type') else 'P'
            if type(dmg_type) is not str: dmg_type = 'P'
            ap = weapon_used.ap if weapon_used else 0

            is_explosive = "grenade" in weapon_name.lower() or "rocket" in weapon_name.lower() or "missile" in weapon_name.lower()
            cover_val = getattr(target.zone, "cover", "") if target.zone else ""
            desc_val = getattr(target.zone, "description", "") if target.zone else ""
            name_val = getattr(target.zone, "name", "") if target.zone else ""

            if is_explosive and target.zone and (
                (cover_val and cover_val.lower() == "heavy")
                or "enclosed" in desc_val.lower()
                or "enclosed" in name_val.lower()
            ):
                base_dmg *= 2
                result_text += " [CHUNKY SALSA EFFECT! Explosive force doubled in confined space.]"

            modified_damage = base_dmg + net_hits
            soak_pool = target.get_attribute("BOD", 3) + max(0, getattr(target, "total_armor", 0) + ap)

            soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
            final_damage = max(0, modified_damage - soak_hits)

            result_text += f"Attack connects! {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} damage."
            result_text += target.take_damage(final_damage, 'P') # Simplicity

            if (target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track):
                target.is_alive = False
                result_text += f" {target.name} is incapacitated!"

                # Check for Gun-Fu (Flow State)
                for rule in active.special_rules:
                    if "Gun-Fu" in rule or "Flow State" in rule:
                        if not hasattr(state, "bonus_actions"):
                            state.bonus_actions = []
                        state.bonus_actions.append(active)
                        result_text += f" {active.name} enters a Flow State (Gun-Fu) and gains an immediate bonus action!"
        else:
            result_text += f"Attack missed! {target.name} successfully dodged or the attack failed to connect."

        return action_text, result_text, edge_spent

class SocialRules:
    @staticmethod
    def resolve_social_attack(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        cha = active.get_attribute("CHA", 3)
        skill_name = "Con"
        skill_rating = active.skills.get("Con", 0)

        if "intimidate" in action_lower or "threaten" in action_lower:
            skill_name = "Intimidation"
            skill_rating = active.skills.get("Intimidation", 0)
        elif "negotiate" in action_lower or "haggle" in action_lower:
            skill_name = "Negotiation"
            skill_rating = active.skills.get("Negotiation", 0)
        elif "command" in action_lower or "lead" in action_lower:
            skill_name = "Leadership"
            skill_rating = active.skills.get("Leadership", 0)
        elif "impersonate" in action_lower or "perform" in action_lower:
            skill_name = "Performance"
            skill_rating = active.skills.get("Performance", 0)

        attack_pool = cha + skill_rating + active.street_cred - active.notoriety

        attack_hits, attack_hits_glitched, edge_spent = (
            DiceRules.roll_attack_with_edge(attack_pool, active)
        )

        target_wil = target.get_attribute("WIL", 3)
        # Resisting attribute logic
        if skill_name == "Intimidation":
            target_resist = target.get_attribute("STR", 3)
        elif skill_name in ["Negotiation", "Leadership"]:
            target_resist = target.get_attribute("LOG", 3)
        else:
            target_resist = target.get_attribute("CHA", 3)

        def_pool = target_wil + target_resist
        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)

        action_text = f"attempts to {skill_name} {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if attack_hits >= def_hits:
            net_hits = attack_hits - def_hits
            influence_gain = 1 + net_hits
            current_influence = active.influence.get(target.name, 0)
            active.influence[target.name] = current_influence + influence_gain
            result_text = f"Social attack succeeds! {active.name} gains {influence_gain} Influence over {target.name}. (Total: {active.influence[target.name]}/{target_wil} needed to yield)."

            if active.influence[target.name] >= target_wil:
                target.has_yielded = True
                result_text += f" {target.name}'s resolve breaks! They agree to the terms, yield, or surrender!"
        else:
            net_hits = def_hits - attack_hits
            resolve_gain = 1 + net_hits
            current_resolve = target.resolve.get(active.name, 0)
            target.resolve[active.name] = current_resolve + resolve_gain
            active_wil = active.get_attribute("WIL", 3)
            result_text = f"Social attack fails! {target.name} gains {resolve_gain} Resolve against {active.name}. (Total: {target.resolve[active.name]}/{active_wil} needed to become intractable)."

        return action_text, result_text, edge_spent

class ChaseRules:
    @staticmethod
    def resolve_ram(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        attack_pool = active.get_attribute("REA", 3) + active.skills.get(
            "Piloting", 4
        )
        if active.jumped_in_vehicle:
            attack_pool += (
                active.jumped_in_vehicle.handling + getattr(active, 'control_rig', 0)
            )

            # Target threshold reduced by Control Rig rating
            threshold_reduction = getattr(active, 'control_rig', 0)
        else:
            threshold_reduction = 0

        attack_hits, attack_hits_glitched, edge_spent = (
            DiceRules.roll_attack_with_edge(max(1, attack_pool), active)
        )

        def_pool = target.get_attribute("REA", 3) + target.skills.get(
            "Piloting", 4
        )

        # Evade bonus
        evade_mod = 0
        for rule in target.special_rules:
            if rule.startswith("Evade"):
                try:
                    evade_mod += int(rule.split("(+")[1].split(")")[0])
                except:
                    pass

        def_pool += evade_mod

        if target.jumped_in_vehicle:
            def_pool += target.jumped_in_vehicle.handling + getattr(target, 'control_rig', 0)
        def_hits, def_hits_glitched = DiceRules.roll_dice(max(1, def_pool))

        # Apply Threshold reduction logic here.
        # Threshold effectively subtracts from def_hits to calculate net_hits
        net_hits = attack_hits - max(0, def_hits - threshold_reduction)

        action_text = f"attempts to RAM {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            active_veh = active.jumped_in_vehicle
            target_veh = target.jumped_in_vehicle

            if active_veh and target_veh:
                base_ram_dmg = active_veh.body + active_veh.speed
                active_resist_pool = (active_veh.body + active_veh.armor) * 2 if (active_veh.body + active_veh.armor) > (target_veh.body + target_veh.armor) else (active_veh.body + active_veh.armor)
                target_resist_pool = (target_veh.body + target_veh.armor) * 2 if (target_veh.body + target_veh.armor) > (active_veh.body + active_veh.armor) else (target_veh.body + target_veh.armor)

                active_resist_hits, _ = DiceRules.roll_dice(active_resist_pool)
                target_resist_hits, _ = DiceRules.roll_dice(target_resist_pool)

                active_dmg_taken = max(0, base_ram_dmg - active_resist_hits)
                target_dmg_taken = max(0, base_ram_dmg - target_resist_hits)

                if (active_veh.body + active_veh.armor) > (target_veh.body + target_veh.armor):
                    active_dmg_taken = active_dmg_taken // 2
                elif (target_veh.body + target_veh.armor) > (active_veh.body + active_veh.armor):
                    target_dmg_taken = target_dmg_taken // 2

                if active.jumped_in_vehicle:
                    # Route physical damage to vehicle, triggering possession logic
                    active.jumped_in_vehicle.physical_damage += active_dmg_taken
                    active_bio = active_dmg_taken // 2
                    active_bio_resist = active.get_attribute("WIL", 3) + active.get_attribute("BOD", 3)
                    active_bio_hits, _ = DiceRules.roll_dice(active_bio_resist)
                    active_net_bio = max(0, active_bio - active_bio_hits)
                    active.stun_damage += active_net_bio

                    res1 = f" {active.name}'s vehicle takes {active_dmg_taken} damage! {active.name} resists biofeedback with {active_bio_resist} dice, taking {active_net_bio} Stun biofeedback!"
                    if active.jumped_in_vehicle.physical_damage >= active.jumped_in_vehicle.physical_track:
                        active.jumped_in_vehicle.is_destroyed = True
                        active.stun_damage += 6
                        active.jumped_in_vehicle = None
                        res1 += f" The vehicle is DESTROYED! {active.name} takes 6 Stun dumpshock damage!"
                else:
                    res1 = active.take_damage(active_dmg_taken, 'P')

                if target.jumped_in_vehicle:
                    target.jumped_in_vehicle.physical_damage += target_dmg_taken
                    target_bio = target_dmg_taken // 2
                    target_bio_resist = target.get_attribute("WIL", 3) + target.get_attribute("BOD", 3)
                    target_bio_hits, _ = DiceRules.roll_dice(target_bio_resist)
                    target_net_bio = max(0, target_bio - target_bio_hits)
                    target.stun_damage += target_net_bio

                    res2 = f" {target.name}'s vehicle takes {target_dmg_taken} damage! {target.name} resists biofeedback with {target_bio_resist} dice, taking {target_net_bio} Stun biofeedback!"
                    if target.jumped_in_vehicle.physical_damage >= target.jumped_in_vehicle.physical_track:
                        target.jumped_in_vehicle.is_destroyed = True
                        target.stun_damage += 6
                        target.jumped_in_vehicle = None
                        res2 += f" The vehicle is DESTROYED! {target.name} takes 6 Stun dumpshock damage!"
                else:
                    res2 = target.take_damage(target_dmg_taken, 'P')

                result_text = f"Ram successful! Both vehicles crash.{res1}{res2}"
            else:
                base_ram_dmg = active.get_attribute("BOD", 3)
                if active.jumped_in_vehicle:
                    base_ram_dmg = active.jumped_in_vehicle.body + active.jumped_in_vehicle.speed
                result_text = f"Ram successful! "

                if target.jumped_in_vehicle:
                    target.jumped_in_vehicle.physical_damage += base_ram_dmg
                    target_bio = base_ram_dmg // 2
                    target_bio_resist = target.get_attribute("WIL", 3) + target.get_attribute("BOD", 3)
                    target_bio_hits, _ = DiceRules.roll_dice(target_bio_resist)
                    target_net_bio = max(0, target_bio - target_bio_hits)
                    target.stun_damage += target_net_bio

                    result_text += f"{target.name}'s vehicle takes {base_ram_dmg} damage! {target.name} resists biofeedback with {target_bio_resist} dice, taking {target_net_bio} Stun biofeedback!"
                    if target.jumped_in_vehicle.physical_damage >= target.jumped_in_vehicle.physical_track:
                        target.jumped_in_vehicle.is_destroyed = True
                        target.stun_damage += 6
                        target.jumped_in_vehicle = None
                        result_text += f" The vehicle is DESTROYED! {target.name} takes 6 Stun dumpshock damage!"
                else:
                    result_text += target.take_damage(base_ram_dmg, 'P')
        else:
            result_text = f"Ram maneuver fails! {target.name} swerves out of the way."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_cut_off(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        attack_pool = active.get_attribute("REA", 3) + active.skills.get(
            "Piloting", 4
        )
        if active.jumped_in_vehicle:
            attack_pool += (
                active.jumped_in_vehicle.handling + getattr(active, 'control_rig', 0)
            )
            threshold_reduction = getattr(active, 'control_rig', 0)
        else:
            threshold_reduction = 0

        attack_hits, attack_hits_glitched, edge_spent = (
            DiceRules.roll_attack_with_edge(max(1, attack_pool), active)
        )

        def_pool = target.get_attribute("REA", 3) + target.skills.get(
            "Piloting", 4
        )

        # Evade bonus
        evade_mod = 0
        for rule in target.special_rules:
            if rule.startswith("Evade"):
                try:
                    evade_mod += int(rule.split("(+")[1].split(")")[0])
                except:
                    pass

        def_pool += evade_mod

        if target.jumped_in_vehicle:
            def_pool += target.jumped_in_vehicle.handling + getattr(target, 'control_rig', 0)
        def_hits, def_hits_glitched = DiceRules.roll_dice(max(1, def_pool))

        net_hits = attack_hits - max(0, def_hits - threshold_reduction)
        action_text = f"attempts to CUT OFF {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            result_text = f"Cut Off successful! {target.name} is forced to make a Crash Test."
        else:
            result_text = f"Cut Off fails! {target.name} avoids the block."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_evade(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        action_text = f"attempts to Evade"
        if active.jumped_in_vehicle:
            evade_bonus = active.jumped_in_vehicle.handling + getattr(active, 'control_rig', 0)
            active.special_rules.append(f"Evade (+{evade_bonus})")
            result_text = f"Evade successful! {active.name} gains +{evade_bonus} to defense pool this round."
        else:
            evade_bonus = active.get_attribute("REA", 3) // 2
            active.special_rules.append(f"Evade (+{evade_bonus})")
            result_text = f"Evade successful! {active.name} focuses on dodging, gaining +{evade_bonus} defense."

        return action_text, result_text, edge_spent

    @staticmethod
    def resolve_chase_maneuver(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        attack_pool = active.get_attribute("REA", 3) + active.skills.get(
            "Piloting", 4
        )
        if active.jumped_in_vehicle:
            attack_pool += (
                active.jumped_in_vehicle.handling + getattr(active, 'control_rig', 0)
            )
            threshold_reduction = getattr(active, 'control_rig', 0)
        else:
            threshold_reduction = 0

        attack_hits, attack_hits_glitched, edge_spent = (
            DiceRules.roll_attack_with_edge(max(1, attack_pool), active)
        )

        def_pool = target.get_attribute("REA", 3) + target.skills.get(
            "Piloting", 4
        )

        # Evade bonus
        evade_mod = 0
        for rule in target.special_rules:
            if rule.startswith("Evade"):
                try:
                    evade_mod += int(rule.split("(+")[1].split(")")[0])
                except:
                    pass

        def_pool += evade_mod

        if target.jumped_in_vehicle:
            def_pool += target.jumped_in_vehicle.handling + getattr(target, 'control_rig', 0)
        def_hits, def_hits_glitched = DiceRules.roll_dice(max(1, def_pool))

        net_hits = attack_hits - max(0, def_hits - threshold_reduction)
        action_text = f"attempts a chase maneuver against {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

        if net_hits > 0:
            result_text = f"Chase maneuver successful! {active.name} gains the upper hand and shifts the Range Band."
        else:
            result_text = f"Chase maneuver fails! {target.name} outmaneuvers {active.name}."

        return action_text, result_text, edge_spent

class AstralRules:
    @staticmethod
    def resolve_astral_combat(state: "SimulationState", active: "Combatant", target: "Combatant", action_lower: str) -> tuple[str, str, bool]:
        edge_spent = False
        from scripts.combat_simulator import Plane

        if target.current_plane != Plane.ASTRAL and not target.is_dual_natured:
            action_text = f"attempts astral combat on {target.name}"
            result_text = f"Action fails: {target.name} is not present on the astral plane."
            return action_text, result_text, edge_spent

        attack_pool = active.get_attribute("WIL", 3) + active.skills.get("Astral Combat", 5)

        wild_dice_count = 0
        if state.environment.is_extream_mode:
            wild_dice_count = min(6, max(1, state.environment.modifiers.get("saturation_level", state.environment.modifiers.get("background_count", 0))))
        attack_hits, attack_hits_glitched, edge_spent = DiceRules.roll_attack_with_edge(attack_pool, active, wild_dice_count=wild_dice_count, is_extream_mode=state.environment.is_extream_mode)

        def_pool = target.get_attribute("INT", 3) + target.get_attribute("LOG", 3)
        def_hits, def_hits_glitched = DiceRules.roll_dice(def_pool)
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

            soak_hits, soak_hits_glitched = DiceRules.roll_dice(soak_pool)
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

        return action_text, result_text, edge_spent
