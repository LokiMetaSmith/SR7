import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import openai # ensure it's in requirements.txt


@dataclass
class Weapon:
    name: str
    damage: int
    damage_type: str # P or S
    ap: int
    ammo: int = 10
    mode: str = "SA"

@dataclass
class Combatant:
    name: str
    source_file: str
    attributes: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    weapons: List[Weapon] = field(default_factory=list)
    armor: int = 0
    physical_track: int = 10
    stun_track: int = 10
    physical_damage: int = 0
    stun_damage: int = 0
    edge: int = 1
    initiative_score: int = 0
    special_rules: List[str] = field(default_factory=list)
    is_alive: bool = True

    def roll_initiative(self) -> int:
        base = self.attributes.get('REA', 3) + self.attributes.get('INT', 3)
        dice = 1
        if "Wired Reflexes" in " ".join(self.special_rules):
            dice += 1
        roll = sum(random.randint(1, 6) for _ in range(dice))
        self.initiative_score = base + roll
        return self.initiative_score

class GameEnvironment:
    def __init__(self, description: str, modifiers: Dict[str, int]):
        self.description = description
        self.modifiers = modifiers

class RulesEngine:
    @staticmethod
    def roll_dice(pool: int) -> int:
        hits = 0
        for _ in range(max(1, pool)):
            if random.randint(1, 6) >= 5:
                hits += 1
        return hits

class SimulationState:
    def __init__(self, environment: GameEnvironment):
        self.environment = environment
        self.combatants: List[Combatant] = []
        self.turn = 1
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)
        print(message)

class LLM_Agent:
    def __init__(self, endpoint_url: str, model_name: str, api_key: str = "sk-dummy"):
        self.client = openai.OpenAI(base_url=endpoint_url, api_key=api_key)
        self.model = model_name

    def ask_action(self, combatant: Combatant, state: SimulationState) -> str:
        # Prompt construction to instruct LLM to choose an action
        prompt = f"You are playing as {combatant.name} in Shadowrun 7E combat.\n"
        prompt += f"Environment: {state.environment.description}\n"
        prompt += f"Your Stats: HP ({combatant.physical_track-combatant.physical_damage}/{combatant.physical_track}), Weapons: {[w.name for w in combatant.weapons]}\n"
        # etc.
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to LLM: {e}"

    def narrate_action(self, combatant: Combatant, action: str, result: str) -> str:
        prompt = f"Write 2-3 sentences of gritty Shadowrun combat flavor text describing {combatant.name} doing the following: {action}. The result is: {result}."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[{combatant.name} performs the action.]"


def parse_chummer(file_path: str) -> Combatant:
    tree = ET.parse(file_path)
    root = tree.getroot()
    char = root.find('character')
    if char is None:
        raise ValueError("Invalid Chummer XML")
    name = char.find('name').text if char.find('name') is not None else "Unknown"

    attributes = {}
    attr_node = char.find('attributes')
    if attr_node is not None:
        for attr in attr_node.findall('attribute'):
            n = attr.find('name').text
            v = int(float(attr.find('value').text))
            attributes[n] = v

    skills = {}
    skill_node = char.find('skills')
    if skill_node is not None:
        for skill in skill_node.findall('skill'):
            n = skill.find('name').text
            v = int(skill.find('value').text)
            skills[n] = v

    c = Combatant(name=name, source_file=file_path, attributes=attributes, skills=skills)

    gear_node = char.find('gear')
    if gear_node is not None:
        for item in gear_node.findall('item'):
            text = item.text
            # Basic matching for weapons like Nanite Claws / Bite
            if "Claw" in text or "Bite" in text or "Knife" in text or "Sword" in text or "Unarmed" in text:
                c.weapons.append(Weapon(name=text, damage=int(attributes.get('STR', 3) + 2), damage_type="P", ap=-2))
            elif "Alpha" in text or "Rifle" in text or "Pistol" in text:
                c.weapons.append(Weapon(name=text, damage=10, damage_type="P", ap=-2))

            # Match armor
            if "Armor" in text:
                m = re.search(r'Armor (\d+)', text)
                if m:
                    c.armor += int(m.group(1))

    c.physical_track = 8 + (attributes.get('BOD', 3) // 2)
    c.stun_track = 8 + (attributes.get('WIL', 3) // 2)
    return c

def parse_markdown(file_path: str, block_name: str = None) -> Combatant:
    with open(file_path, 'r') as f:
        content = f.read()

    # Find the block for the specific NPC if provided, otherwise just find the first NPC-like block
    if block_name:
        # Match e.g., `**Sargent Igneous (Fuchsia Dragon Marine)**` up to next double newline and double-asterisk
        pattern = re.compile(rf'\*\*{re.escape(block_name)}\s*\(.*?\*\*[\s\S]*?(?=\n\n\*\*|\Z)')
        block_match = pattern.search(content)
        if block_match:
            content = block_match.group(0)

    name_match = re.search(r'\*\*(.*?)\*\*', content)
    name = name_match.group(1).split('(')[0].strip() if name_match else "Unknown Markdown NPC"

    attributes = {}
    # Handles `**Attributes:** BOD 4 | AGI 5...` or `**BOD** 2, **AGI** 3...`
    attr_matches = re.findall(r'\*?\*?([A-Z]{3})\*?\*?\s*(\d+)', content)
    for m in attr_matches:
        attributes[m[0]] = int(m[1])

    skills = {}
    skills_line = re.search(r'\*\*Skills:\*\*(.*)', content)
    if skills_line:
        skills_text = skills_line.group(1)
        for part in skills_text.split(','):
            m = re.search(r'([A-Za-z\s]+)\s+(\d+)', part)
            if m:
                skills[m.group(1).strip()] = int(m.group(2))

    c = Combatant(name=name, source_file=file_path, attributes=attributes, skills=skills)

    # Try finding Armor
    armor_match = re.search(r'Armor.*?(?:(\d+))', content, re.IGNORECASE)
    if armor_match:
        c.armor = int(armor_match.group(1))

    # Health
    hp_match = re.search(r'Condition Monitor:\s*(\d+)/(\d+)', content)
    if hp_match:
        c.physical_track = int(hp_match.group(1))
        c.stun_track = int(hp_match.group(2))
    else:
        c.physical_track = 8 + (attributes.get('BOD', 3) // 2)
        c.stun_track = 8 + (attributes.get('WIL', 3) // 2)

    # Weapons: handles multiple weapons on one line, e.g. `**Weapons:** Ares Alpha (15P, -10 AP, SA/BF/FA), Combat Knife (10P, -2 AP).`
    # We will search for any weapon stat block format like: `Some Name (15P, -10 AP)`
    weapon_matches = re.findall(r'([A-Za-z0-s\s\-]+?)\s*\(\s*(\d+)([PS])\s*,\s*([+-]\d+)\s*AP', content)
    for wm in weapon_matches:
        # wm[0] might contain things like "**Weapons:** Ares Alpha"
        w_name = wm[0].replace('**Weapons:**', '').strip()
        dmg = int(wm[1])
        typ = wm[2]
        ap = int(wm[3])
        c.weapons.append(Weapon(name=w_name, damage=dmg, damage_type=typ, ap=ap))

    # Add dummy weapon if empty
    if not c.weapons:
        c.weapons.append(Weapon(name="Unarmed Strike", damage=int(attributes.get('STR', 3) / 2), damage_type="S", ap=0))

    return c

def parse_scenario(file_path: str) -> GameEnvironment:
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return GameEnvironment(description=data.get('description', 'A dark alleyway.'), modifiers=data.get('modifiers', {}))
    elif file_path.endswith('.md'):
        with open(file_path, 'r') as f:
            content = f.read()
            return GameEnvironment(description=content, modifiers={})
    return GameEnvironment("An empty arena.", {})

def load_combatant(path: str) -> Combatant:
    # Handle passing an NPC name along with the file, like "GM Notes/GM_Campaign_Guide.md:Sargent Igneous"
    block_name = None
    if ':' in path and path.endswith('.md') == False:
        parts = path.split(':', 1)
        path = parts[0]
        block_name = parts[1]

    if path.endswith('.chum5'):
        return parse_chummer(path)
    elif path.endswith('.md'):
        return parse_markdown(path, block_name)
    else:
        raise ValueError(f"Unknown format for file: {path}")

def save_state(combatant: Combatant, scratchpad_dir: str):
    os.makedirs(scratchpad_dir, exist_ok=True)
    filename = "".join(x for x in combatant.name if x.isalnum()) + ".json"
    filepath = os.path.join(scratchpad_dir, filename)
    data = {
        "name": combatant.name,
        "physical_damage": combatant.physical_damage,
        "stun_damage": combatant.stun_damage,
        "edge": combatant.edge,
        "is_alive": combatant.is_alive
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved state for {combatant.name} to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous Combat Simulator for Shadowrun 7E")
    parser.add_argument("combatant1", help="Path to Chummer or Markdown file for combatant 1")
    parser.add_argument("combatant2", help="Path to Chummer or Markdown file for combatant 2")
    parser.add_argument("--scenario", help="Path to scenario JSON or Markdown", default="scenario.json")
    parser.add_argument("--llm-url", help="URL of the OpenAI-compatible endpoint", default="http://localhost:8000/v1")
    parser.add_argument("--llm-model", help="Name of the model to use", default="local-model")
    parser.add_argument("--dry-run", action="store_true", help="Run without connecting to an actual LLM")

    args = parser.parse_args()

    # Create dummy scenario if missing
    if not os.path.exists(args.scenario):
        with open(args.scenario, 'w') as f:
            json.dump({"description": "An abandoned Wuxing lab facility. Dim lighting, flickering neon tubes, and patches of humming grey-goo on the walls.", "modifiers": {"lighting": -2}}, f)

    env = parse_scenario(args.scenario)
    state = SimulationState(environment=env)

    c1 = load_combatant(args.combatant1)
    c2 = load_combatant(args.combatant2)
    state.combatants = [c1, c2]

    # Initialize dummy LLM Agent if dry-run
    if args.dry_run:
        class DummyAgent:
            def ask_action(self, combatant, state):
                return f"attack with {combatant.weapons[0].name}" if combatant.weapons else "attack with Unarmed Strike"
            def narrate_action(self, combatant, action, result):
                return f"{combatant.name} fiercely attacks, resulting in: {result}"
        llm = DummyAgent()
    else:
        llm = LLM_Agent(endpoint_url=args.llm_url, model_name=args.llm_model)

    state.log(f"=== Beginning Shadowrun 7E Combat Simulation ===")
    state.log(f"Scenario: {env.description}")
    state.log(f"Combatants: {c1.name} vs {c2.name}")

    # Roll Initiative
    c1.roll_initiative()
    c2.roll_initiative()
    state.log(f"Initiative: {c1.name} ({c1.initiative_score}) | {c2.name} ({c2.initiative_score})")

    # Sort by initiative descending
    state.combatants.sort(key=lambda c: c.initiative_score, reverse=True)

    # Main combat loop
    while all(c.is_alive for c in state.combatants) and state.turn < 20:
        state.log(f"\n--- Turn {state.turn} ---")

        for active in state.combatants:
            if not active.is_alive:
                continue

            target = next(c for c in state.combatants if c != active and c.is_alive)

            # Use LLM to decide tactical action
            action_decision = llm.ask_action(active, state)
            state.log(f"[{active.name} Tactical Decision]: {action_decision.strip()}")

            # Simple heuristic to parse the LLM action choice
            chosen_weapon_name = ""
            for w in active.weapons:
                if w.name.lower() in action_decision.lower():
                    chosen_weapon_name = w.name
                    break

            if chosen_weapon_name:
                weapon = next((w for w in active.weapons if w.name == chosen_weapon_name), active.weapons[0])
            else:
                weapon = active.weapons[0] if active.weapons else Weapon("Unarmed Strike", 4, "S", 0)


            # Attack Roll: Agility + Skill (assuming Firearms/Close Combat ~ 5 if unknown)
            attack_pool = active.attributes.get('AGI', 3) + 5
            attack_hits = RulesEngine.roll_dice(attack_pool)

            # Defense Roll: Reaction + Intuition
            def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)
            def_hits = RulesEngine.roll_dice(def_pool)

            net_hits = attack_hits - def_hits
            action_text = f"attacks {target.name} with {weapon.name} ({attack_hits} hits vs {def_hits} defense hits)"

            if net_hits > 0:
                modified_damage = weapon.damage + net_hits
                modified_ap = weapon.ap

                # Soak Roll: Body + Armor + AP
                soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor + modified_ap)
                soak_hits = RulesEngine.roll_dice(soak_pool)

                final_damage = max(0, modified_damage - soak_hits)
                result_text = f"Attack succeeds! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} {weapon.damage_type} damage."

                if weapon.damage_type == 'P':
                    target.physical_damage += final_damage
                else:
                    target.stun_damage += final_damage

                if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                    target.is_alive = False
                    result_text += f" {target.name} is incapacitated!"
            else:
                result_text = f"Attack misses! {target.name} dodges the attack."

            # Narration
            narration = llm.narrate_action(active, action_text, result_text)
            state.log(narration)

            if not target.is_alive:
                break

        state.turn += 1

    # Summary
    state.log("\n=== Combat Summary ===")
    winner = next((c for c in state.combatants if c.is_alive), None)
    if winner:
        state.log(f"Winner: {winner.name} wins in {state.turn - 1} turns!")
    else:
        state.log("Mutual destruction or timeout.")

    for c in state.combatants:
        status = "Alive" if c.is_alive else "Incapacitated"
        state.log(f"{c.name}: {status} | Physical Damage: {c.physical_damage}/{c.physical_track} | Stun Damage: {c.stun_damage}/{c.stun_track}")

    # Generate Loot Summary
    if winner:
        losers = [c for c in state.combatants if not c.is_alive]
        if losers:
            loot_table = [
                "A handful of raw, buzzing Karma shards.",
                "A glitchy Rating 2 commlink.",
                "A half-empty magazine of Nanite-Buster rounds.",
                "A shard of Living Crystal.",
                "A scrubbed, high-capacity credstick holding 5,000¥.",
                "A pristine piece of 'Dead Tech'."
            ]
            import random
            loot_item = random.choice(loot_table)
            state.log(f"\nLoot Acquired by {winner.name}: {loot_item}")

    # Save State
    state.log("\nSaving scratchpad states...")
    for c in state.combatants:
        save_state(c, "campaign_state")

if __name__ == "__main__":
    main()
