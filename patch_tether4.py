with open('scripts/combat_simulator.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.strip() == "elif is_erase_tether:":
        skip = True
        new_lines.append(line)
        new_lines.append('        action_text = f"attempts to erase Tethers held by {target.name}"\n')
        new_lines.append('        if getattr(active, "is_locked_by_tarpit", False):\n')
        new_lines.append('            result_text = f"Failed! {active.name}\'s connection is locked by Tar-Pit IC."\n')
        new_lines.append('            return action_text, result_text, edge_spent\n')
        new_lines.append('        result_text = RulesEngine.resolve_erase_tether(state, active, target)\n')
        continue
    if skip:
        if line.strip() == "elif is_tar_pit_attack:":
            skip = False
            new_lines.append(line)
        continue
    if not skip:
        new_lines.append(line)

with open('scripts/combat_simulator.py', 'w') as f:
    f.writelines(new_lines)
