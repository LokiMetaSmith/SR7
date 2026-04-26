with open('scripts/combat_simulator.py', 'r') as f:
    content = f.read()

target = '''    state.log("\\nRolling Initiative...")
    for c in state.combatants:
        c.roll_initiative()'''

replacement = '''    # Apply pre-combat economy & contact modifiers
    for c in state.combatants:
        if c.hot_nuyen >= 1000:
            god_tethers = c.hot_nuyen // 1000
            c.tethers["Grid Overwatch Division"] = god_tethers
            state.log(f"{c.name}'s Hot Nuyen triggered {god_tethers} automatic Tether(s) from Grid Overwatch Division!")

        for contact in c.contacts:
            if contact.connection >= 4 and contact.loyalty >= 4:
                c.edge += 1
                state.log(f"{c.name}'s high-level contact ({contact.name}) provided intel, granting +1 Edge!")

    state.log("\\nRolling Initiative...")
    for c in state.combatants:
        c.roll_initiative()'''

if target in content:
    content = content.replace(target, replacement)
    with open('scripts/combat_simulator.py', 'w') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Target not found.")
