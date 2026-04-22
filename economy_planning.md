Ah, the Chummer files don't have `<contacts>` blocks currently. That's fine, the parser can just be defensive.

```python
    contacts_node = char.find("contacts")
    if contacts_node is not None:
        for contact in contacts_node.findall("contact"):
            cn = contact.find("name").text if contact.find("name") is not None else "Unknown Contact"
            cc = int(contact.find("connection").text) if contact.find("connection") is not None else 1
            cl = int(contact.find("loyalty").text) if contact.find("loyalty") is not None else 1
            c.contacts.append(Contact(name=cn, connection=cc, loyalty=cl))
```

And for Markdown:
```python
    contact_matches = re.findall(r"\*\*Contacts:\*\*(.*?)(?=\n\n|\n\*\*|\Z)", content, re.DOTALL)
    if contact_matches:
        contacts_text = contact_matches[0]
        # Parse "Sam (Connection 6, Loyalty 5), Ennis (Connection 4, Loyalty 5)"
        for part in contacts_text.split(","):
            part = part.strip()
            if part:
                # regex to extract name, connection, loyalty
                # e.g. "Sam (6/5)", "Sam (Connection 6, Loyalty 5)", etc.
                m = re.search(r"^(.*?)\s*\(.*?(?:Connection|Conn)?\s*(\d+).*?(?:Loyalty|Loy)?\s*(\d+)\)", part, re.IGNORECASE)
                if m:
                    c.contacts.append(Contact(name=m.group(1).strip(), connection=int(m.group(2)), loyalty=int(m.group(3))))
```

Wait, Economy Implementation: `Implement mechanics for "Digital Nuyen" vs "Clean Nuyen/Barter" (affecting availability or AR tracking).`
The TO-DO item I'm taking is:
*   [ ] **Economy Implementation:** Implement mechanics for "Digital Nuyen" vs "Clean Nuyen/Barter" (affecting availability or AR tracking).
*   [ ] **Social Combat/Contacts:** Implement Contact Connection/Loyalty integration in simulation stat blocks or pre-combat modifiers, and Communication Protocols (The Dead Drop, Encrypted Pulses) within the `combat_simulator.py`.

Actually, wait. The prompt says "review the ToDo, pick an item and implement it, update the todo when done". I can pick the Economy Implementation or Social Combat/Contacts. Let's do Social Combat/Contacts, or even better, Economy Implementation AND Social Combat/Contacts (or just Economy Implementation).
Actually, I'll implement Economy Implementation: adding "Digital Nuyen" and "Clean Nuyen" to Combatant, and when they use Digital Nuyen to buy things or whatever... wait, this is a combat simulator. How does buying gear affect combat?
Wait! In combat, maybe they drop Loot? The loot summary currently drops scrubbed credsticks or raw karma.
What about pre-combat modifiers or AR tracking? If they carry hot Nuyen, they might have Tethers applied to them automatically!
From the rulebook: `Buying illegal gear with standard, unscrubbed Nuyen automatically grants the corporate grid a Tether on the buyer.`
Maybe if `digital_nuyen` is hot, they get an automatic tether from GOD or the corp grid at the start of combat?

Let's look at the first incomplete item:
`Economy Implementation: Implement mechanics for "Digital Nuyen" vs "Clean Nuyen/Barter" (affecting availability or AR tracking).`

Since availability is pre-combat, maybe we can add a pre-combat gear acquisition simulation? No, just add properties `digital_nuyen: int = 0`, `clean_nuyen: int = 0`, `hot_nuyen: int = 0` to `Combatant`. If they have `hot_nuyen > 0`, they start with 1 tether from "Grid Overwatch Division".

Let's do the "Economy Implementation" AND "Social Combat/Contacts".

Let's plan for Social Combat/Contacts:
1. Add `Contact` dataclass. Add `contacts: List[Contact]` to `Combatant`.
2. Parse `<contacts>` from `.chum5` and `**Contacts:**` from `.md`.
3. Give pre-combat modifiers: If you have a contact with high connection/loyalty, you gain intel, translating to +1 Initiative Die, or +1 Edge, or +2 to defense in the first round (ambush awareness). Let's say: For each contact with Connection + Loyalty >= 8, the combatant gains +1 starting Edge or +1 to Initiative. Let's add an Edge bonus for strong contacts (Loyalty >= 4).
4. Add "Send Encrypted Pulse" as an action. Opposed test: sender's Sneaking + Agility vs all enemies' Perception + Intuition. If successful, sender can pass a tactical message, maybe giving an ally +1 DPM on their next attack.
5. Add "Use Dead Drop" as an action or narrative flavor for exchanging items safely mid-combat.

Wait, the prompt says:
*   [ ] **Economy Implementation:** Implement mechanics for "Digital Nuyen" vs "Clean Nuyen/Barter" (affecting availability or AR tracking).
    *   [x] Implemented Smuggling items (Null-bags affecting Matrix targeting/Concealability) in the simulator.
*   [ ] **Social Combat/Contacts:** Implement Contact Connection/Loyalty integration in simulation stat blocks or pre-combat modifiers, and Communication Protocols (The Dead Drop, Encrypted Pulses) within the `combat_simulator.py`.
    *   [x] Implemented the Hopepunk Social Modifier.

So I need to implement these two bullets. I will do BOTH to finish Priority 7.

Let's write a python script to test parsing these things:
