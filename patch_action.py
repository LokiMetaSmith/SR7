with open("scripts/combat_simulator.py", "r") as f:
    content = f.read()

# 1. Add is_astral_projection and is_astral_return to boolean checks in process_action
old_bools = """    is_sprint = "sprint" in action_lower
    is_cover = "take cover" in action_lower"""

new_bools = """    is_sprint = "sprint" in action_lower
    is_cover = "take cover" in action_lower
    is_astral_projection = "astral project" in action_lower
    is_astral_return = "return to physical" in action_lower"""

content = content.replace(old_bools, new_bools)

# 2. Implement the actions
old_logic = """    elif is_compile:
        sprite_level = 5"""

new_logic = """    elif is_astral_projection:
        active.current_plane = Plane.ASTRAL
        action_text = f"{active.name} projects their consciousness into the Astral Plane."
        result_text = f"{active.name} is now astrally projecting."

    elif is_astral_return:
        active.current_plane = Plane.PHYSICAL
        action_text = f"{active.name} snaps their consciousness back to their physical body."
        result_text = f"{active.name} has returned to the physical plane."

    elif is_compile:
        sprite_level = 5"""

content = content.replace(old_logic, new_logic)

with open("scripts/combat_simulator.py", "w") as f:
    f.write(content)
