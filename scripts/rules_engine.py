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

        actual_pool = max(1, pool)

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
