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
class Spell:
    name: str
    type: str # M or P
    damage_formula: str # e.g. "F-2"
    drain_formula: str # e.g. "F-4"

@dataclass
class MatrixAttributes:
    attack: int = 0
    sleaze: int = 0
    data_processing: int = 1
    firewall: int = 1

@dataclass
class Vehicle:
    name: str
    handling: int = 4
    speed: int = 3
    accel: int = 2
    body: int = 4
    armor: int = 4
    sensor: int = 3
    physical_track: int = 10
    physical_damage: int = 0
    is_destroyed: bool = False
    weapons: List[Weapon] = field(default_factory=list)

@dataclass
class Combatant:
    name: str
    source_file: str
    attributes: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    weapons: List[Weapon] = field(default_factory=list)
    spells: List[Spell] = field(default_factory=list)
    matrix: MatrixAttributes = field(default_factory=MatrixAttributes)
    tethers: Dict[str, int] = field(default_factory=dict) # target_name -> tether_count
    armor: int = 0
    physical_track: int = 10
    stun_track: int = 10
    physical_damage: int = 0
    stun_damage: int = 0
    edge: int = 1
    initiative_score: int = 0
    special_rules: List[str] = field(default_factory=list)
    is_alive: bool = True
    team: int = 0

    control_rig: int = 0
    jumped_in_vehicle: Optional[Vehicle] = None

    def roll_initiative(self) -> int:
        if self.jumped_in_vehicle:
            # Matrix Initiative (Data Processing + Intuition) + 1 Initiative Die per Rig level
            base = self.matrix.data_processing + self.attributes.get('INT', 3)
            dice = 1 + self.control_rig
        else:
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

        if combatant.jumped_in_vehicle:
            prompt += f"You are Jumped Into a {combatant.jumped_in_vehicle.name}.\n"
            prompt += f"Vehicle Stats: BOD {combatant.jumped_in_vehicle.body}, ARM {combatant.jumped_in_vehicle.armor}, HP ({combatant.jumped_in_vehicle.physical_track-combatant.jumped_in_vehicle.physical_damage}/{combatant.jumped_in_vehicle.physical_track})\n"
            prompt += f"Vehicle Weapons: {[w.name for w in combatant.jumped_in_vehicle.weapons]}\n"

        prompt += f"Your Stats: HP ({combatant.physical_track-combatant.physical_damage}/{combatant.physical_track}), Weapons: {[w.name for w in combatant.weapons]}, Spells: {[s.name for s in combatant.spells]}\n"
        prompt += f"Matrix Attributes: Attack {combatant.matrix.attack}, Sleaze {combatant.matrix.sleaze}, DP {combatant.matrix.data_processing}, Firewall {combatant.matrix.firewall}\n"
        prompt += "Choose an action: Attack with a weapon, Cast a spell, Establish Tether, or Data Spike.\n"
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

    spells_node = char.find('spells')
    if spells_node is not None:
        for spell in spells_node.findall('spell'):
            sn = spell.find('name').text
            # Basic parsing of spell tags if present, default to generic "Mana" / "F-2" otherwise
            st = "M"
            sd = "F"
            sdr = "F-2"

            c.spells.append(Spell(name=sn, type=st, damage_formula=sd, drain_formula=sdr))

    # Try mapping matrix stats
    if "Technomancer" in " ".join([q.text for q in char.findall('.//qualities/quality/name') if q.find('name') is not None]) or "RES" in attributes:
        res = attributes.get('RES', 3)
        c.matrix = MatrixAttributes(attack=res, sleaze=res, data_processing=res, firewall=res)
    else:
        deck = char.find('.//gear/item[category="Cyberdeck"]')
        if deck is not None:
            c.matrix = MatrixAttributes(attack=5, sleaze=5, data_processing=5, firewall=5)
        else:
            c.matrix = MatrixAttributes(attack=0, sleaze=0, data_processing=3, firewall=3)

    cyberware_node = char.find('cyberwares')
    if cyberware_node is not None:
        for ware in cyberware_node.findall('cyberware'):
            n = ware.find('name').text if ware.find('name') is not None else ""
            if "Control Rig" in n:
                rtg_match = re.search(r'Rating (\d+)', n, re.IGNORECASE)
                if rtg_match:
                    c.control_rig = int(rtg_match.group(1))
                else:
                    c.control_rig = 1

    vehicles_node = char.find('vehicles')
    if vehicles_node is not None:
        for v_node in vehicles_node.findall('vehicle'):
            vn = v_node.find('name').text if v_node.find('name') is not None else "Drone"
            v_arm = int(v_node.find('armor').text) if v_node.find('armor') is not None else 4
            v_bod = int(v_node.find('body').text) if v_node.find('body') is not None else 4

            veh = Vehicle(name=vn, armor=v_arm, body=v_bod)
            veh.physical_track = 8 + (v_bod // 2)

            # Simple weapon parsing for drones
            v_weaps = v_node.find('weapons')
            if v_weaps is not None:
                for w in v_weaps.findall('weapon'):
                    wn = w.find('name').text if w.find('name') is not None else "Mounted Weapon"
                    wd = int(w.find('damage').text.replace('P','').replace('S','')) if w.find('damage') is not None and w.find('damage').text else 8
                    veh.weapons.append(Weapon(name=wn, damage=wd, damage_type="P", ap=-1))

            if not veh.weapons:
                 veh.weapons.append(Weapon(name="Mounted Turret", damage=8, damage_type="P", ap=-1))

            c.jumped_in_vehicle = veh
            break # Just take the first one for the sim

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

    # Spells
    spell_matches = re.findall(r'\*\*Spells:\*\*(.*?)(?=\n\n|\n\*\*|\Z)', content, re.DOTALL)
    if spell_matches:
        spells_text = spell_matches[0]
        # Basic split by comma. We assume generic M and F/F-2.
        for sp in spells_text.split(','):
            sp = sp.strip()
            if sp:
                c.spells.append(Spell(name=sp, type="M", damage_formula="F", drain_formula="F-2"))

    # Matrix Attributes
    # Typically found in commlink/deck gear or special attributes
    matrix_match = re.search(r'\*\*Matrix Attributes:\*\*\s*Attack\s*(\d+),\s*Sleaze\s*(\d+),\s*Data Processing\s*(\d+),\s*Firewall\s*(\d+)', content)
    if matrix_match:
        c.matrix = MatrixAttributes(
            attack=int(matrix_match.group(1)),
            sleaze=int(matrix_match.group(2)),
            data_processing=int(matrix_match.group(3)),
            firewall=int(matrix_match.group(4))
        )
    elif "RES" in attributes:
        res = attributes.get('RES', 3)
        c.matrix = MatrixAttributes(attack=res, sleaze=res, data_processing=res, firewall=res)
    else:
        # check if it mentions a commlink/deck
        if re.search(r'deck|commlink', content, re.IGNORECASE):
             c.matrix = MatrixAttributes(attack=0, sleaze=0, data_processing=4, firewall=4)
        else:
             c.matrix = MatrixAttributes(attack=0, sleaze=0, data_processing=1, firewall=1)

    cr_match = re.search(r'Control Rig(?:\s*\(?Rating\s*)?(\d+)?', content, re.IGNORECASE)
    if cr_match:
        c.control_rig = int(cr_match.group(1)) if cr_match.group(1) else 1

    veh_match = re.search(r'\*\*Vehicle/Drone:\*\*\s*(.*?)\s*\(.*?\s*BOD\s*(\d+).*?ARM\s*(\d+)', content, re.IGNORECASE)
    if veh_match:
        vn = veh_match.group(1).strip()
        v_bod = int(veh_match.group(2))
        v_arm = int(veh_match.group(3))
        veh = Vehicle(name=vn, armor=v_arm, body=v_bod)
        veh.physical_track = 8 + (v_bod // 2)
        veh.weapons.append(Weapon(name=f"{vn} Mount", damage=8, damage_type="P", ap=-1))
        c.jumped_in_vehicle = veh

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
    parser.add_argument("--team1", nargs='+', required=True, help="List of paths to Chummer or Markdown files for Team 1")
    parser.add_argument("--team2", nargs='+', required=True, help="List of paths to Chummer or Markdown files for Team 2")
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

    state.combatants = []
    for path in args.team1:
        c = load_combatant(path)
        c.team = 1
        state.combatants.append(c)
    for path in args.team2:
        c = load_combatant(path)
        c.team = 2
        state.combatants.append(c)

    # Initialize dummy LLM Agent if dry-run
    if args.dry_run:
        class DummyAgent:
            def ask_action(self, combatant, state):
                if combatant.jumped_in_vehicle and combatant.jumped_in_vehicle.weapons:
                    return f"attack with {combatant.jumped_in_vehicle.weapons[0].name}"
                if combatant.spells and combatant.attributes.get('MAG', 0) > 0:
                    return f"cast {combatant.spells[0].name}"
                elif combatant.matrix.attack > 3:
                    if random.random() > 0.5:
                        return "data spike"
                    else:
                        return "establish tether"
                return f"attack with {combatant.weapons[0].name}" if combatant.weapons else "attack with Unarmed Strike"
            def narrate_action(self, combatant, action, result):
                return f"{combatant.name} takes action, resulting in: {result}"
        llm = DummyAgent()
    else:
        llm = LLM_Agent(endpoint_url=args.llm_url, model_name=args.llm_model)

    state.log(f"=== Beginning Shadowrun 7E Combat Simulation ===")
    state.log(f"Scenario: {env.description}")

    team1_names = [f"{c.name} (in {c.jumped_in_vehicle.name})" if c.jumped_in_vehicle else c.name for c in state.combatants if c.team == 1]
    team2_names = [f"{c.name} (in {c.jumped_in_vehicle.name})" if c.jumped_in_vehicle else c.name for c in state.combatants if c.team == 2]
    state.log(f"Combatants: Team 1 ({', '.join(team1_names)}) vs Team 2 ({', '.join(team2_names)})")

    # Roll Initiative
    for c in state.combatants:
        c.roll_initiative()
    init_log = " | ".join(f"{c.name} ({c.initiative_score})" for c in state.combatants)
    state.log(f"Initiative: {init_log}")

    # Sort by initiative descending
    state.combatants.sort(key=lambda c: c.initiative_score, reverse=True)

    # Main combat loop
    while any(c.is_alive for c in state.combatants if c.team == 1) and any(c.is_alive for c in state.combatants if c.team == 2) and state.turn < 20:
        state.log(f"\n--- Turn {state.turn} ---")

        for active in state.combatants:
            if not active.is_alive:
                continue

            # Need to check if there are still valid targets before acting
            valid_targets = [c for c in state.combatants if c.team != active.team and c.is_alive]
            if not valid_targets:
                break

            target = random.choice(valid_targets)

            # Use LLM to decide tactical action
            action_decision = llm.ask_action(active, state)
            state.log(f"[{active.name} Tactical Decision]: {action_decision.strip()}")

            action_lower = action_decision.lower()
            action_text = ""
            result_text = ""

            is_spell = "cast" in action_lower or any(s.name.lower() in action_lower for s in active.spells)
            is_data_spike = "data spike" in action_lower
            is_tether = "tether" in action_lower

            if is_spell and active.spells:
                spell = next((s for s in active.spells if s.name.lower() in action_lower), active.spells[0])
                mag = active.attributes.get('MAG', 1)
                spell_skill = active.skills.get('Spellcasting', 5)

                attack_pool = mag + spell_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                # Defense
                if spell.type == "M":
                    def_pool = target.attributes.get('ESS', 6) + target.attributes.get('WIL', 3)
                else:
                    def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)

                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                action_text = f"casts {spell.name} at {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    base_damage = mag # Assume Force = MAG
                    modified_damage = base_damage + net_hits

                    if spell.type == "M":
                        soak_pool = 0 # Mana spells ignore armor
                    else:
                        soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor - mag)

                    soak_hits = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)

                    result_text = f"Spell hits! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} P damage."
                    target.physical_damage += final_damage
                else:
                    result_text = f"Spell misses or is resisted by {target.name}."

                # Drain
                drain_value = max(2, mag - 2) # Assume F-2
                drain_resist_pool = active.attributes.get('WIL', 3) + active.attributes.get('LOG', 3)
                drain_hits = RulesEngine.roll_dice(drain_resist_pool)
                drain_taken = max(0, drain_value - drain_hits)
                result_text += f" {active.name} rolls {drain_resist_pool} to resist drain, taking {drain_taken} Stun damage."
                active.stun_damage += drain_taken

                if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                    target.is_alive = False
                    result_text += f" {target.name} is incapacitated!"
                if active.physical_damage >= active.physical_track or active.stun_damage >= active.stun_track:
                    active.is_alive = False
                    result_text += f" {active.name} is incapacitated from Drain!"

            elif is_data_spike:
                log = active.attributes.get('LOG', 3)
                cyber_skill = active.skills.get('Cybercombat', 5)
                attack_pool = log + cyber_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                def_pool = target.attributes.get('INT', 3) + target.matrix.firewall
                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                action_text = f"launches a Data Spike at {target.name}'s persona ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    tethers = active.tethers.get(target.name, 0)
                    modified_damage = active.matrix.attack + net_hits + (tethers * 2)

                    soak_pool = target.matrix.data_processing + target.matrix.firewall
                    soak_hits = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)

                    result_text = f"Data Spike connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Stun (Biofeedback) damage."
                    target.stun_damage += final_damage

                    if target.physical_damage >= target.physical_track or target.stun_damage >= target.stun_track:
                        target.is_alive = False
                        result_text += f" {target.name} is incapacitated!"
                else:
                    result_text = f"Data Spike is deflected by {target.name}'s firewall."

            elif is_tether:
                log = active.attributes.get('LOG', 3)
                hack_skill = active.skills.get('Hacking', 5)
                attack_pool = log + hack_skill
                attack_hits = RulesEngine.roll_dice(attack_pool)

                def_pool = target.attributes.get('WIL', 3) + target.matrix.firewall
                def_hits = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                action_text = f"attempts to establish a Tether on {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    current_tethers = active.tethers.get(target.name, 0)
                    active.tethers[target.name] = current_tethers + 1
                    result_text = f"Tether established! {active.name} now has {active.tethers[target.name]} Tether(s) on {target.name}."
                else:
                    result_text = f"Tether attempt blocked by {target.name}'s firewall."

            else:
                # Weapon Attack
                chosen_weapon_name = ""
                available_weapons = active.jumped_in_vehicle.weapons if active.jumped_in_vehicle else active.weapons
                for w in available_weapons:
                    if w.name.lower() in action_lower:
                        chosen_weapon_name = w.name
                        break

                if chosen_weapon_name:
                    weapon = next((w for w in available_weapons if w.name == chosen_weapon_name), available_weapons[0])
                else:
                    weapon = available_weapons[0] if available_weapons else Weapon("Unarmed Strike", 4, "S", 0)

                # Attack Roll: Agility + Skill
                if active.jumped_in_vehicle:
                    # Gunnery + Agility + Control Rig
                    attack_pool = active.attributes.get('AGI', 3) + active.skills.get('Gunnery', 5) + active.control_rig
                else:
                    attack_pool = active.attributes.get('AGI', 3) + 5

                attack_hits = RulesEngine.roll_dice(attack_pool)

                # Defense Roll: Reaction + Intuition
                if target.jumped_in_vehicle:
                     def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3) + target.jumped_in_vehicle.handling
                else:
                     def_pool = target.attributes.get('REA', 3) + target.attributes.get('INT', 3)

                def_hits = RulesEngine.roll_dice(def_pool)

                net_hits = attack_hits - def_hits
                action_text = f"attacks {target.name} with {weapon.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    modified_damage = weapon.damage + net_hits
                    modified_ap = weapon.ap

                    # Soak Roll: Body + Armor + AP
                    if target.jumped_in_vehicle:
                         soak_pool = max(0, target.jumped_in_vehicle.body + target.jumped_in_vehicle.armor + modified_ap)
                    else:
                         soak_pool = max(0, target.attributes.get('BOD', 3) + target.armor + modified_ap)

                    soak_hits = RulesEngine.roll_dice(soak_pool)

                    final_damage = max(0, modified_damage - soak_hits)
                    result_text = f"Attack succeeds! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} {weapon.damage_type} damage."

                    if target.jumped_in_vehicle:
                        # Physical damage goes to vehicle, Rigger takes half as Stun Biofeedback
                        if weapon.damage_type == 'P':
                            target.jumped_in_vehicle.physical_damage += final_damage
                            biofeedback = final_damage // 2
                            if biofeedback > 0:
                                bio_resist = target.attributes.get('WIL', 3) + target.attributes.get('BOD', 3)
                                bio_hits = RulesEngine.roll_dice(bio_resist)
                                net_bio = max(0, biofeedback - bio_hits)
                                target.stun_damage += net_bio
                                result_text += f" Vehicle takes the damage! {target.name} rolls {bio_resist} dice to resist Stun Biofeedback, taking {net_bio} Stun damage."

                            if target.jumped_in_vehicle.physical_damage >= target.jumped_in_vehicle.physical_track:
                                target.jumped_in_vehicle.is_destroyed = True
                                target.stun_damage += 6
                                target.jumped_in_vehicle = None # Dumped
                                result_text += f" The vehicle is DESTROYED! {target.name} takes 6 Stun dumpshock damage!"
                        else:
                            target.stun_damage += final_damage
                    else:
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

        state.turn += 1

    # Summary
    state.log("\n=== Combat Summary ===")

    t1_alive = any(c.is_alive for c in state.combatants if c.team == 1)
    t2_alive = any(c.is_alive for c in state.combatants if c.team == 2)
    if t1_alive and not t2_alive:
        winning_team = 1
    elif t2_alive and not t1_alive:
        winning_team = 2
    else:
        winning_team = None

    if winning_team:
        state.log(f"Winner: Team {winning_team} wins in {state.turn - 1} turns!")
    else:
        state.log("Mutual destruction or timeout.")

    for c in state.combatants:
        status = "Alive" if c.is_alive else "Incapacitated"
        state.log(f"Team {c.team} - {c.name}: {status} | Physical Damage: {c.physical_damage}/{c.physical_track} | Stun Damage: {c.stun_damage}/{c.stun_track}")

    # Generate Loot Summary
    if winning_team:
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
            # using global random module
            loot_item = random.choice(loot_table)
            state.log(f"\nLoot Acquired by Team {winning_team}: {loot_item}")

    # Save State
    state.log("\nSaving scratchpad states...")
    for c in state.combatants:
        save_state(c, "campaign_state")

if __name__ == "__main__":
    main()
