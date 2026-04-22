Let's see what I need to change in `scripts/combat_simulator.py`.

**Dataclasses to add:**
```python
@dataclass
class Contact:
    name: str
    connection: int
    loyalty: int
```

**Fields to add to `Combatant`:**
```python
    digital_nuyen: int = 0
    clean_nuyen: int = 0
    hot_nuyen: int = 0
    contacts: List[Contact] = field(default_factory=list)
```

**Parsing Markdown:**
```python
    # Economy (Nuyen)
    nuyen_match = re.search(r"Digital Nuyen:\s*(\d+)", content, re.IGNORECASE)
    if nuyen_match:
        c.digital_nuyen = int(nuyen_match.group(1))
    clean_nuyen_match = re.search(r"Clean Nuyen:\s*(\d+)", content, re.IGNORECASE)
    if clean_nuyen_match:
        c.clean_nuyen = int(clean_nuyen_match.group(1))
    hot_nuyen_match = re.search(r"Hot Nuyen:\s*(\d+)", content, re.IGNORECASE)
    if hot_nuyen_match:
        c.hot_nuyen = int(hot_nuyen_match.group(1))

    # Contacts
    contact_matches = re.findall(r"\*\*Contacts:\*\*(.*?)(?=\n\n|\n\*\*|\Z)", content, re.DOTALL)
    if contact_matches:
        contacts_text = contact_matches[0]
        for part in contacts_text.split(","):
            part = part.strip()
            if part:
                # Look for name and two numbers
                m = re.search(r"^(.*?)\s*\(.*?(?:Connection|Conn)?\s*(\d+).*?(?:Loyalty|Loy)?\s*(\d+)\)", part, re.IGNORECASE)
                if m:
                    c.contacts.append(Contact(name=m.group(1).strip(), connection=int(m.group(2)), loyalty=int(m.group(3))))
```

**Parsing Chummer:**
```python
    # Economy
    nuyen_node = char.find("nuyen")
    if nuyen_node is not None:
        c.digital_nuyen = int(nuyen_node.text)

    # Contacts
    contacts_node = char.find("contacts")
    if contacts_node is not None:
        for contact in contacts_node.findall("contact"):
            cn = contact.find("name").text if contact.find("name") is not None else "Unknown Contact"
            cc = int(contact.find("connection").text) if contact.find("connection") is not None else 1
            cl = int(contact.find("loyalty").text) if contact.find("loyalty") is not None else 1
            c.contacts.append(Contact(name=cn, connection=cc, loyalty=cl))
```

**Pre-Combat Modifiers (in main):**
```python
    # After rolling initiative, apply contact pre-combat bonuses and AR tracking penalties
    for c in state.combatants:
        # AR Tracking / Hot Nuyen penalty
        if c.hot_nuyen > 0:
            state.log(f"{c.name} is carrying Hot Nuyen! Grid Overwatch Division automatically acquires 1 Tether on them.")
            c.tethers["G.O.D."] = c.tethers.get("G.O.D.", 0) + 1

        # Contacts intel / legwork bonuses
        if c.contacts:
            best_contact = max(c.contacts, key=lambda x: x.connection + x.loyalty)
            if best_contact.connection + best_contact.loyalty >= 8:
                c.edge += 1
                state.log(f"{c.name}'s contact {best_contact.name} provided excellent pre-combat intel! {c.name} gains +1 Edge.")
```

**LLM Prompt (in `ask_action`):**
Add to the prompt:
```python
    prompt += "Choose an action: Attack with a weapon, Cast a spell, Establish Tether, Data Spike, Social Influence (Negotiate/Intimidate/Con), Sprint (move to better cover), Take Cover, Yield, Pass Turn, Send Encrypted Pulse (communicate securely), or Use Dead Drop (hide/exchange item).\n"
```

**Action Handling (in main loop):**
```python
            is_encrypted_pulse = "encrypted pulse" in action_lower
            is_dead_drop = "dead drop" in action_lower

            elif is_encrypted_pulse:
                attack_pool = active.attributes.get("AGI", 3) + active.skills.get("Sneaking", 4)
                attack_hits, attack_hits_glitched, edge_spent = RulesEngine.roll_attack_with_edge(attack_pool, active)

                def_pool = target.attributes.get("INT", 3) + target.skills.get("Perception", 4)
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)

                action_text = f"attempts to send an Encrypted Pulse to an ally"
                if attack_hits >= def_hits:
                    result_text = f"Encrypted Pulse successfully sent! {active.name} secretly coordinates with their team, granting a tactical advantage."
                else:
                    result_text = f"Encrypted Pulse intercepted! {target.name} notices the communication."

            elif is_dead_drop:
                action_text = f"utilizes a Dead Drop location"
                result_text = f"{active.name} securely stashes or retrieves an item from a Matrix-shielded Dead Drop, hiding it from AR tracking."
```

Let's also make sure we sync this to `combat_analyzer.py`.
