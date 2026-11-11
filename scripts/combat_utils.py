import random


def apply_nica_glitch(character) -> str:
    glitch_table = [
        "Takes 1 P damage (short-circuit)",
        "Takes 1 S damage (painful feedback)",
        "Drops weapon (erratic servos)",
        "Loses 1 Initiative (micro-seizure)",
        "Spasms wildly (No action next turn)",
    ]
    effect = random.choice(glitch_table)
    if "1 P damage" in effect:
        character.physical_damage += 1
    elif "1 S damage" in effect:
        character.stun_damage += 1
    elif "Drops weapon" in effect and getattr(character, "weapons", None):
        character.weapons.pop(0)
    elif "Loses 1 Initiative" in effect:
        if hasattr(character, "initiative"):
            character.initiative = max(0, character.initiative - 1)
        if hasattr(character, "initiative_score"):
            character.initiative_score = max(0, character.initiative_score - 1)
    elif "Spasms wildly" in effect:
        character.has_yielded = True
    return effect


def process_turn_end(state) -> str:
    """Handles end-of-turn events such as HMHVV damage and active effects."""
    result_text = ""
    for c in state.combatants:
        if getattr(c, "hmhvv_infection_level", 0) > 2 and c.is_alive:
            dmg_msg = c.take_damage(1, "P")
            msg = f"{c.name} suffers 1 Physical Damage from severe HMHVV infection."
            state.log(msg)
            result_text += msg + "\n"

    state.turn += 1
    return result_text.strip()
