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