import argparse
import json
import os
import sys

# Ensure we can import modules from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import time
import xml.etree.ElementTree as ET
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import openai  # ensure it's in requirements.txt
from scripts.combat_utils import apply_nica_glitch


@dataclass
class Weapon:
    name: str
    damage: int
    damage_type: str  # P or S
    ap: int
    ammo: int = 10
    mode: str = "SA"


@dataclass
class Spell:
    name: str
    type: str  # M or P


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
    body: int = 4
    armor: int = 4
    physical_track: int = 10
    physical_damage: int = 0
    weapons: List[Weapon] = field(default_factory=list)
    swarm_count: int = 1


@dataclass
class Zone:
    name: str
    cover: str = "None"
    description: str = ""


@dataclass
class Combatant:
    name: str
    attributes: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    weapons: List[Weapon] = field(default_factory=list)
    spells: List[Spell] = field(default_factory=list)
    matrix: MatrixAttributes = field(default_factory=MatrixAttributes)
    tethers: Dict[str, int] = field(default_factory=dict)  # target_name -> tether_count
    influence: Dict[str, int] = field(
        default_factory=dict
    )  # target_name -> influence_points
    resolve: Dict[str, int] = field(
        default_factory=dict
    )  # target_name -> resolve_points
    has_yielded: bool = False
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
    zone: Optional[Zone] = None

    control_rig: int = 0
    jumped_in_vehicle: Optional[Vehicle] = None

    def roll_initiative(self) -> int:
        if self.jumped_in_vehicle:
            # Matrix Initiative (Data Processing + Intuition) + 1 Initiative Die per Rig level
            base = self.matrix.data_processing + self.attributes.get("INT", 3)
            dice = 1 + self.control_rig
        else:
            base = self.attributes.get("REA", 3) + self.attributes.get("INT", 3)
            dice = 1
            if "Wired Reflexes" in " ".join(self.special_rules):
                dice += 1

        roll = sum(random.randint(1, 6) for _ in range(dice))
        self.initiative_score = base + roll
        return self.initiative_score


class GameEnvironment:
    def __init__(
        self,
        description: str,
        modifiers: Dict[str, int],
        zones: List[Zone] = None,
        is_chase_combat: bool = False,
    ):
        self.description = description
        self.modifiers = modifiers
        self.zones = zones if zones else []
        self.is_chase_combat = is_chase_combat


class RulesEngine:
    @staticmethod
    def roll_dice(pool: int) -> tuple[int, bool]:
        hits = 0
        ones_twos = 0
        for _ in range(max(1, pool)):
            roll = random.randint(1, 6)
            if roll >= 5:
                hits += 1
            elif roll in [1, 2]:
                ones_twos += 1
        glitched = ones_twos >= (max(1, pool) / 2.0)
        return hits, glitched

    @staticmethod
    def roll_attack_with_edge(
        pool: int, combatant: "Combatant"
    ) -> tuple[int, bool, bool]:
        """Rolls an attack and automatically spends Edge to reroll if 0 hits are rolled."""
        hits, glitched = RulesEngine.roll_dice(pool)
        edge_spent = False
        if hits == 0 and combatant.edge > 0:
            combatant.edge -= 1
            reroll_hits, reroll_glitched = RulesEngine.roll_dice(pool)
            hits += reroll_hits
            glitched = reroll_glitched
            edge_spent = True
        return hits, glitched, edge_spent


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
            prompt += f"Vehicle Stats: BOD {combatant.jumped_in_vehicle.body}, ARM {combatant.jumped_in_vehicle.armor}, HP ({combatant.jumped_in_vehicle.physical_track-combatant.jumped_in_vehicle.physical_damage}/{combatant.jumped_in_vehicle.physical_track}), Swarm Count: {combatant.jumped_in_vehicle.swarm_count}\n"
            prompt += f"Vehicle Weapons: {[w.name for w in combatant.jumped_in_vehicle.weapons]}\n"

        if combatant.zone:
            prompt += f"Your Location: {combatant.zone.name} (Cover: {combatant.zone.cover})\n"
        if state.environment.is_chase_combat:
            prompt += (
                f"Special Rule: You are currently engaged in a Chase Combat scenario.\n"
            )
        prompt += f"Your Stats: HP ({combatant.physical_track-combatant.physical_damage}/{combatant.physical_track}), Weapons: {[w.name for w in combatant.weapons]}, Spells: {[s.name for s in combatant.spells]}\n"

        social_skills = {
            k: v
            for k, v in combatant.skills.items()
            if k in ["Con", "Negotiation", "Intimidation", "Leadership", "Etiquette"]
        }
        if social_skills:
            prompt += f"Social Skills: {social_skills}\n"

        if combatant.influence or combatant.resolve:
            prompt += f"Social State: Influence over others: {combatant.influence}, Resolve against others: {combatant.resolve}\n"

        prompt += f"Matrix Attributes: Attack {combatant.matrix.attack}, Sleaze {combatant.matrix.sleaze}, DP {combatant.matrix.data_processing}, Firewall {combatant.matrix.firewall}\n"
        prompt += "Choose an action: Attack with a weapon, Cast a spell, Establish Tether, Data Spike, Social Influence (Negotiate/Intimidate/Con), or Sprint (move to better cover).\n"
        # etc.
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
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
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[{combatant.name} performs the action.]"


def parse_chummer(file_path: str) -> Combatant:
    tree = ET.parse(file_path)
    root = tree.getroot()
    char = root.find("character")
    if char is None:
        raise ValueError("Invalid Chummer XML")
    name = char.find("name").text if char.find("name") is not None else "Unknown"

    attributes = {}
    attr_node = char.find("attributes")
    if attr_node is not None:
        for attr in attr_node.findall("attribute"):
            n = attr.find("name").text
            v = int(float(attr.find("value").text))
            attributes[n] = v

    skills = {}
    skill_node = char.find("skills")
    if skill_node is not None:
        for skill in skill_node.findall("skill"):
            n = skill.find("name").text
            v = int(skill.find("value").text)
            skills[n] = v

    c = Combatant(name=name, attributes=attributes, skills=skills)

    spells_node = char.find("spells")
    if spells_node is not None:
        for spell in spells_node.findall("spell"):
            sn = spell.find("name").text
            # Basic parsing of spell tags if present, default to generic "Mana" / "F-2" otherwise
            st = "M"

            c.spells.append(Spell(name=sn, type=st))

    # Try mapping matrix stats
    if (
        "Technomancer"
        in " ".join(
            [
                q.text
                for q in char.findall(".//qualities/quality/name")
                if q.find("name") is not None
            ]
        )
        or "RES" in attributes
    ):
        res = attributes.get("RES", 3)
        c.matrix = MatrixAttributes(
            attack=res, sleaze=res, data_processing=res, firewall=res
        )
    else:
        deck = char.find('.//gear/item[category="Cyberdeck"]')
        if deck is not None:
            c.matrix = MatrixAttributes(
                attack=5, sleaze=5, data_processing=5, firewall=5
            )
        else:
            c.matrix = MatrixAttributes(
                attack=0, sleaze=0, data_processing=3, firewall=3
            )

    cyberware_node = char.find("cyberwares")
    if cyberware_node is not None:
        for ware in cyberware_node.findall("cyberware"):
            n = ware.find("name").text if ware.find("name") is not None else ""
            if "Control Rig" in n:
                rtg_match = re.search(r"Rating (\d+)", n, re.IGNORECASE)
                if rtg_match:
                    c.control_rig = int(rtg_match.group(1))
                else:
                    c.control_rig = 1

    vehicles_node = char.find("vehicles")
    if vehicles_node is not None:
        for v_node in vehicles_node.findall("vehicle"):
            vn = (
                v_node.find("name").text if v_node.find("name") is not None else "Drone"
            )
            v_arm = (
                int(v_node.find("armor").text)
                if v_node.find("armor") is not None
                else 4
            )
            v_bod = (
                int(v_node.find("body").text) if v_node.find("body") is not None else 4
            )

            veh = Vehicle(name=vn, armor=v_arm, body=v_bod)
            veh.physical_track = 8 + (v_bod // 2)

            # Simple weapon parsing for drones
            v_weaps = v_node.find("weapons")
            if v_weaps is not None:
                for w in v_weaps.findall("weapon"):
                    wn = (
                        w.find("name").text
                        if w.find("name") is not None
                        else "Mounted Weapon"
                    )
                    wd = (
                        int(w.find("damage").text.replace("P", "").replace("S", ""))
                        if w.find("damage") is not None and w.find("damage").text
                        else 8
                    )
                    veh.weapons.append(
                        Weapon(name=wn, damage=wd, damage_type="P", ap=-1)
                    )

            if not veh.weapons:
                veh.weapons.append(
                    Weapon(name="Mounted Turret", damage=8, damage_type="P", ap=-1)
                )

            c.jumped_in_vehicle = veh
            break  # Just take the first one for the sim

    gear_node = char.find("gear")
    if gear_node is not None:
        for item in gear_node.findall("item"):
            text = item.text
            # Basic matching for weapons like Nanite Claws / Bite
            if (
                "Claw" in text
                or "Bite" in text
                or "Knife" in text
                or "Sword" in text
                or "Unarmed" in text
            ):
                c.weapons.append(
                    Weapon(
                        name=text,
                        damage=int(attributes.get("STR", 3) + 2),
                        damage_type="P",
                        ap=-2,
                    )
                )
            elif "Alpha" in text or "Rifle" in text or "Pistol" in text:
                c.weapons.append(Weapon(name=text, damage=10, damage_type="P", ap=-2))

            # Match armor
            if "Armor" in text:
                m = re.search(r"Armor (\d+)", text)
                if m:
                    c.armor += int(m.group(1))

    c.physical_track = 8 + (attributes.get("BOD", 3) // 2)
    c.stun_track = 8 + (attributes.get("WIL", 3) // 2)
    return c


def parse_markdown(file_path: str, block_name: str = None) -> Combatant:
    with open(file_path, "r") as f:
        content = f.read()

    # Find the block for the specific NPC if provided, otherwise just find the first NPC-like block
    if block_name:
        # Match e.g., `**Sargent Igneous (Fuchsia Dragon Marine)**` up to next double newline and double-asterisk
        pattern = re.compile(
            rf"\*\*{re.escape(block_name)}\s*\(.*?\*\*[\s\S]*?(?=\n\n\*\*|\Z)"
        )
        block_match = pattern.search(content)
        if block_match:
            content = block_match.group(0)

    name_match = re.search(r"\*\*(.*?)\*\*", content)
    name = (
        name_match.group(1).split("(")[0].strip()
        if name_match
        else "Unknown Markdown NPC"
    )

    attributes = {}
    # Handles `**Attributes:** BOD 4 | AGI 5...` or `**BOD** 2, **AGI** 3...`
    attr_matches = re.findall(r"\*?\*?([A-Z]{3})\*?\*?\s*(\d+)", content)
    for m in attr_matches:
        attributes[m[0]] = int(m[1])

    skills = {}
    skills_line = re.search(r"\*\*Skills:\*\*(.*)", content)
    if skills_line:
        skills_text = skills_line.group(1)
        for part in skills_text.split(","):
            m = re.search(r"([A-Za-z\s]+)\s+(\d+)", part)
            if m:
                skills[m.group(1).strip()] = int(m.group(2))

    c = Combatant(name=name, attributes=attributes, skills=skills)

    # Try finding Armor
    armor_match = re.search(r"Armor.*?(?:(\d+))", content, re.IGNORECASE)
    if armor_match:
        c.armor = int(armor_match.group(1))

    # Health
    hp_match = re.search(r"Condition Monitor:\s*(\d+)/(\d+)", content)
    if hp_match:
        c.physical_track = int(hp_match.group(1))
        c.stun_track = int(hp_match.group(2))
    else:
        c.physical_track = 8 + (attributes.get("BOD", 3) // 2)
        c.stun_track = 8 + (attributes.get("WIL", 3) // 2)

    # Weapons: handles multiple weapons on one line, e.g. `**Weapons:** Ares Alpha (15P, -10 AP, SA/BF/FA), Combat Knife (10P, -2 AP).`
    # We will search for any weapon stat block format like: `Some Name (15P, -10 AP)`
    weapon_matches = re.findall(
        r"([A-Za-z0-s\s\-]+?)\s*\(\s*(\d+)([PS])\s*,\s*([+-]\d+)\s*AP", content
    )
    for wm in weapon_matches:
        # wm[0] might contain things like "**Weapons:** Ares Alpha"
        w_name = wm[0].replace("**Weapons:**", "").strip()
        dmg = int(wm[1])
        typ = wm[2]
        ap = int(wm[3])
        c.weapons.append(Weapon(name=w_name, damage=dmg, damage_type=typ, ap=ap))

    # Spells
    spell_matches = re.findall(
        r"\*\*Spells:\*\*(.*?)(?=\n\n|\n\*\*|\Z)", content, re.DOTALL
    )
    if spell_matches:
        spells_text = spell_matches[0]
        # Basic split by comma. We assume generic M and F/F-2.
        for sp in spells_text.split(","):
            sp = sp.strip()
            if sp:
                c.spells.append(Spell(name=sp, type="M"))

    # Matrix Attributes
    # Typically found in commlink/deck gear or special attributes
    matrix_match = re.search(
        r"\*\*Matrix Attributes:\*\*\s*Attack\s*(\d+),\s*Sleaze\s*(\d+),\s*Data Processing\s*(\d+),\s*Firewall\s*(\d+)",
        content,
    )
    if matrix_match:
        c.matrix = MatrixAttributes(
            attack=int(matrix_match.group(1)),
            sleaze=int(matrix_match.group(2)),
            data_processing=int(matrix_match.group(3)),
            firewall=int(matrix_match.group(4)),
        )
    elif "RES" in attributes:
        res = attributes.get("RES", 3)
        c.matrix = MatrixAttributes(
            attack=res, sleaze=res, data_processing=res, firewall=res
        )
    else:
        # check if it mentions a commlink/deck
        if re.search(r"deck|commlink", content, re.IGNORECASE):
            c.matrix = MatrixAttributes(
                attack=0, sleaze=0, data_processing=4, firewall=4
            )
        else:
            c.matrix = MatrixAttributes(
                attack=0, sleaze=0, data_processing=1, firewall=1
            )

    cr_match = re.search(
        r"Control Rig(?:\s*\(?Rating\s*)?(\d+)?", content, re.IGNORECASE
    )
    if cr_match:
        c.control_rig = int(cr_match.group(1)) if cr_match.group(1) else 1

    veh_match = re.search(
        r"\*\*Vehicle/Drone:\*\*\s*(.*?)\s*\(.*?\s*BOD\s*(\d+).*?ARM\s*(\d+)",
        content,
        re.IGNORECASE,
    )
    if veh_match:
        vn = veh_match.group(1).strip()
        v_bod = int(veh_match.group(2))
        v_arm = int(veh_match.group(3))
        veh = Vehicle(name=vn, armor=v_arm, body=v_bod)
        veh.physical_track = 8 + (v_bod // 2)
        veh.weapons.append(Weapon(name=f"{vn} Mount", damage=8, damage_type="P", ap=-1))
        if "Swarm" in vn or re.search(r"Swarm", content, re.IGNORECASE):
            veh.swarm_count = 3  # default swarm size
        c.jumped_in_vehicle = veh

    # Add dummy weapon if empty
    if not c.weapons:
        c.weapons.append(
            Weapon(
                name="Unarmed Strike",
                damage=int(attributes.get("STR", 3) / 2),
                damage_type="S",
                ap=0,
            )
        )

    # Special Rules
    if re.search(r"Null-Suit", content, re.IGNORECASE):
        c.special_rules.append("Null-Suit")
    if re.search(r"N\.I\.C\.A\.|Scrap-Sickness", content, re.IGNORECASE):
        c.special_rules.append("N.I.C.A.")

    return c


def parse_scenario(file_path: str) -> GameEnvironment:
    if file_path.endswith(".json"):
        with open(file_path, "r") as f:
            data = json.load(f)
            zones = []
            if "map" in data and "zones" in data["map"]:
                for z in data["map"]["zones"]:
                    zones.append(
                        Zone(
                            name=z.get("name", "Unknown Zone"),
                            cover=z.get("cover", "None"),
                            description=z.get("description", ""),
                        )
                    )
            is_chase = data.get("is_chase_combat", False)
            return GameEnvironment(
                description=data.get("description", "A dark alleyway."),
                modifiers=data.get("modifiers", {}),
                zones=zones,
                is_chase_combat=is_chase,
            )
    elif file_path.endswith(".md"):
        with open(file_path, "r") as f:
            content = f.read()
            return GameEnvironment(
                description=content, modifiers={}, is_chase_combat=False
            )
    return GameEnvironment("An empty arena.", {}, None, False)


def load_combatant(path: str) -> Combatant:
    # Handle passing an NPC name along with the file, like "GM Notes/GM_Campaign_Guide.md:Sargent Igneous"
    block_name = None
    if ":" in path and path.endswith(".md") == False:
        parts = path.split(":", 1)
        path = parts[0]
        block_name = parts[1]

    if path.endswith(".chum5"):
        return parse_chummer(path)
    elif path.endswith(".md"):
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
        "is_alive": combatant.is_alive,
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved state for {combatant.name} to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Combat Simulator for Shadowrun 7E"
    )
    parser.add_argument(
        "--team1",
        nargs="+",
        required=True,
        help="List of paths to Chummer or Markdown files for Team 1",
    )
    parser.add_argument(
        "--team2",
        nargs="+",
        required=True,
        help="List of paths to Chummer or Markdown files for Team 2",
    )
    parser.add_argument(
        "--scenario", help="Path to scenario JSON or Markdown", default="scenario.json"
    )
    parser.add_argument(
        "--llm-url",
        help="URL of the OpenAI-compatible endpoint",
        default="http://localhost:8000/v1",
    )
    parser.add_argument(
        "--llm-model", help="Name of the model to use", default="local-model"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without connecting to an actual LLM"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Pause to allow user to input actions manually",
    )
    parser.add_argument(
        "--ui", action="store_true", help="Launch the Pygame visual interface"
    )

    args = parser.parse_args()

    # Create dummy scenario if missing
    if not os.path.exists(args.scenario):
        with open(args.scenario, "w") as f:
            json.dump(
                {
                    "description": "An abandoned Wuxing lab facility. Dim lighting, flickering neon tubes, and patches of humming grey-goo on the walls.",
                    "modifiers": {"lighting": -2},
                },
                f,
            )

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
                if combatant.spells and combatant.attributes.get("MAG", 0) > 0:
                    return f"cast {combatant.spells[0].name}"
                elif combatant.matrix.attack > 3:
                    if random.random() > 0.5:
                        return "data spike"
                    else:
                        return "establish tether"
                return (
                    "sprint to cover"
                    if random.random() > 0.8
                    else (
                        f"attack with {combatant.weapons[0].name}"
                        if combatant.weapons
                        else "attack with Unarmed Strike"
                    )
                )

            def narrate_action(self, combatant, action, result):
                return f"{combatant.name} takes action, resulting in: {result}"

        llm = DummyAgent()
    else:
        llm = LLM_Agent(endpoint_url=args.llm_url, model_name=args.llm_model)

    app = None
    if args.ui:
        from ui.app import App

        app = App()
    state.log(f"=== Beginning Shadowrun 7E Combat Simulation ===")
    state.log(f"Scenario: {env.description}")

    team1_names = [
        f"{c.name} (in {c.jumped_in_vehicle.name})" if c.jumped_in_vehicle else c.name
        for c in state.combatants
        if c.team == 1
    ]
    team2_names = [
        f"{c.name} (in {c.jumped_in_vehicle.name})" if c.jumped_in_vehicle else c.name
        for c in state.combatants
        if c.team == 2
    ]
    state.log(
        f"Combatants: Team 1 ({', '.join(team1_names)}) vs Team 2 ({', '.join(team2_names)})"
    )

    # Assign zones
    if env.zones:
        for c in state.combatants:
            if c.team == 1:
                c.zone = env.zones[0]
            else:
                c.zone = env.zones[-1]

    # Roll Initiative
    for c in state.combatants:
        c.roll_initiative()
        # Apply high ground / surprise initiative modifiers
        if c.zone and (
            "High Ground" in c.zone.name or "High Ground" in c.zone.description
        ):
            extra = RulesEngine.roll_dice(1)  # 1 extra die
            c.initiative_score += extra
    init_log = " | ".join(f"{c.name} ({c.initiative_score})" for c in state.combatants)
    state.log(f"Initiative: {init_log}")

    # Sort by initiative descending
    state.combatants.sort(key=lambda c: c.initiative_score, reverse=True)

    # Main combat loop
    while (
        any(
            c.is_alive and not getattr(c, "has_yielded", False)
            for c in state.combatants
            if c.team == 1
        )
        and any(
            c.is_alive and not getattr(c, "has_yielded", False)
            for c in state.combatants
            if c.team == 2
        )
        and state.turn < 20
    ):
        if app:
            app.update_state(state)
            app.tick()
        state.log(f"\n--- Turn {state.turn} ---")

        for active in state.combatants:
            if not active.is_alive or getattr(active, "has_yielded", False):
                continue

            # Need to check if there are still valid targets before acting
            valid_targets = [
                c
                for c in state.combatants
                if c.team != active.team
                and c.is_alive
                and not getattr(c, "has_yielded", False)
            ]
            if not valid_targets:
                break

            target = random.choice(valid_targets)

            if app or args.interactive:
                if app:

                    app.pending_action = None
                    print(f"Waiting for UI action for {active.name}...")
                    while app.pending_action is None:
                        app.tick()
                        # If user closes window during wait, fallback
                        if not app.running:
                            app.pending_action = llm.ask_action(active, state)
                            break
                    action_decision = app.pending_action
                else:
                    user_input = input(
                        f"Enter action for {active.name} (or press Enter to let AI decide): "
                    )
                    if user_input.strip():
                        action_decision = user_input
                    else:
                        action_decision = llm.ask_action(active, state)
            else:
                # Use LLM to decide tactical action
                action_decision = llm.ask_action(active, state)

            state.log(f"[{active.name} Tactical Decision]: {action_decision.strip()}")

            action_lower = action_decision.lower()
            action_text = ""
            result_text = ""
            edge_spent = False
            attack_hits_glitched = False
            def_hits_glitched = False
            soak_hits_glitched = False
            drain_hits_glitched = False
            bio_hits_glitched = False

            is_spell = "cast" in action_lower or any(
                s.name.lower() in action_lower for s in active.spells
            )
            is_data_spike = "data spike" in action_lower
            is_tether = "tether" in action_lower
            is_social = any(
                kw in action_lower
                for kw in [
                    "social",
                    "negotiate",
                    "negotiation",
                    "intimidate",
                    "intimidation",
                    "con ",
                    "influence",
                ]
            )
            is_sprint = "sprint" in action_lower
            is_cover = "take cover" in action_lower
            is_yield = "yield" in action_lower

            if is_yield:
                active.has_yielded = True
                action_text = f"{active.name} yields and surrenders!"
                result_text = f"{active.name} drops their weapons and stops fighting."
            elif is_sprint:
                action_text = f"{active.name} uses a Complex Action to Sprint!"
                result_text = f"{active.name} sprints to a new position, covering 16m."
            elif is_cover:
                action_text = f"{active.name} dives for cover!"
                result_text = (
                    f"{active.name} secures Medium cover, granting a +2 defense bonus."
                )
                if active.zone:
                    active.zone.cover = "Medium"
            elif is_social:
                # Find the highest social skill
                social_skills = {
                    k: v
                    for k, v in active.skills.items()
                    if k
                    in ["Con", "Negotiation", "Intimidation", "Leadership", "Etiquette"]
                }
                skill_name = (
                    max(social_skills, key=social_skills.get)
                    if social_skills
                    else "Con"
                )
                skill_rating = active.skills.get(skill_name, 0)
                cha = active.attributes.get("CHA", 3)

                attack_pool = cha + skill_rating
                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(attack_pool, active)
                )

                target_wil = target.attributes.get("WIL", 3)
                # Resisting attribute logic
                if skill_name == "Intimidation":
                    target_resist = target.attributes.get("STR", 3)
                elif skill_name in ["Negotiation", "Leadership"]:
                    target_resist = target.attributes.get("LOG", 3)
                else:
                    target_resist = target.attributes.get("CHA", 3)

                def_pool = target_wil + target_resist
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)

                action_text = f"attempts to {skill_name} {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if attack_hits >= def_hits:
                    net_hits = attack_hits - def_hits
                    influence_gain = 1 + net_hits
                    current_influence = active.influence.get(target.name, 0)
                    active.influence[target.name] = current_influence + influence_gain
                    result_text = f"Social attack succeeds! {active.name} gains {influence_gain} Influence over {target.name}. (Total: {active.influence[target.name]}/{target_wil} needed to yield)."

                    if active.influence[target.name] >= target_wil:
                        target.has_yielded = True
                        result_text += f" {target.name}'s resolve breaks! They agree to the terms, yield, or surrender!"
                else:
                    net_hits = def_hits - attack_hits
                    resolve_gain = 1 + net_hits
                    current_resolve = target.resolve.get(active.name, 0)
                    target.resolve[active.name] = current_resolve + resolve_gain
                    active_wil = active.attributes.get("WIL", 3)
                    result_text = f"Social attack fails! {target.name} gains {resolve_gain} Resolve against {active.name}. (Total: {target.resolve[active.name]}/{active_wil} needed to become intractable)."

            elif is_spell and active.spells:
                spell = next(
                    (s for s in active.spells if s.name.lower() in action_lower),
                    active.spells[0],
                )
                mag = active.attributes.get("MAG", 1)
                spell_skill = active.skills.get("Spellcasting", 5)

                attack_pool = mag + spell_skill
                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(attack_pool, active)
                )

                # Defense
                if spell.type == "M":
                    def_pool = target.attributes.get("ESS", 6) + target.attributes.get(
                        "WIL", 3
                    )
                else:
                    def_pool = target.attributes.get("REA", 3) + target.attributes.get(
                        "INT", 3
                    )

                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                action_text = f"casts {spell.name} at {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    base_damage = mag  # Assume Force = MAG
                    modified_damage = base_damage + net_hits

                    if spell.type == "M":
                        soak_pool = 0  # Mana spells ignore armor
                    else:
                        soak_pool = max(
                            0, target.attributes.get("BOD", 3) + target.armor - mag
                        )

                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)

                    result_text = f"Spell hits! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} P damage."
                    target.physical_damage += final_damage
                else:
                    result_text = f"Spell misses or is resisted by {target.name}."

                # Drain
                drain_value = max(2, mag - 2)  # Assume F-2
                drain_resist_pool = active.attributes.get(
                    "WIL", 3
                ) + active.attributes.get("LOG", 3)
                drain_hits, drain_hits_glitched = RulesEngine.roll_dice(
                    drain_resist_pool
                )
                drain_taken = max(0, drain_value - drain_hits)
                result_text += f" {active.name} rolls {drain_resist_pool} to resist drain, taking {drain_taken} Stun damage."
                active.stun_damage += drain_taken

                if (
                    target.physical_damage >= target.physical_track
                    or target.stun_damage >= target.stun_track
                ):
                    target.is_alive = False
                    result_text += f" {target.name} is incapacitated!"
                if (
                    active.physical_damage >= active.physical_track
                    or active.stun_damage >= active.stun_track
                ):
                    active.is_alive = False
                    result_text += f" {active.name} is incapacitated from Drain!"

            elif is_data_spike:
                if "Null-Suit" in target.special_rules:
                    action_text = f"attempts a Matrix action on {target.name}"
                    result_text = f"Action fails: {target.name} is wearing a Null-Suit and is immune to Matrix targeting."
                    narration = llm.narrate_action(active, action_text, result_text)
                    state.log(narration)
                    continue
                log = active.attributes.get("LOG", 3)
                cyber_skill = active.skills.get("Cybercombat", 5)
                attack_pool = log + cyber_skill
                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(attack_pool, active)
                )

                def_pool = target.attributes.get("INT", 3) + target.matrix.firewall
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
                net_hits = attack_hits - def_hits

                action_text = f"launches a Data Spike at {target.name}'s persona ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    tethers = active.tethers.get(target.name, 0)
                    modified_damage = active.matrix.attack + net_hits + (tethers * 2)

                    soak_pool = target.matrix.data_processing + target.matrix.firewall
                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)
                    final_damage = max(0, modified_damage - soak_hits)

                    result_text = f"Data Spike connects! {target.name} rolls {soak_pool} soak dice, taking {final_damage} Stun (Biofeedback) damage."
                    target.stun_damage += final_damage

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

            elif "sprint" in action_lower or "move" in action_lower:
                action_text = f"sprints and repositions"
                result_text = f"{active.name} moves 16m (Complex Action), shifting Range Bands or securing better cover."
                if active.zone and active.zone.cover == "None":
                    result_text += (
                        " They scramble towards whatever light cover they can find."
                    )
                elif getattr(target, "zone", None) and target.zone != active.zone:
                    result_text += (
                        f" They close the distance towards {target.name}'s zone."
                    )

            elif (
                "chase" in action_lower
                or "pilot" in action_lower
                or "drive" in action_lower
            ):
                attack_pool = active.attributes.get("REA", 3) + active.skills.get(
                    "Piloting", 4
                )
                if active.jumped_in_vehicle:
                    attack_pool += (
                        active.jumped_in_vehicle.handling + active.control_rig
                    )
                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(max(1, attack_pool), active)
                )

                def_pool = target.attributes.get("REA", 3) + target.skills.get(
                    "Piloting", 4
                )
                if target.jumped_in_vehicle:
                    def_pool += target.jumped_in_vehicle.handling + target.control_rig
                def_hits, def_hits_glitched = RulesEngine.roll_dice(max(1, def_pool))

                net_hits = attack_hits - def_hits
                action_text = f"attempts a chase maneuver against {target.name} ({attack_hits} hits vs {def_hits} defense hits)"

                if net_hits > 0:
                    result_text = f"Chase maneuver successful! {active.name} gains the upper hand and shifts the Range Band."
                else:
                    result_text = f"Chase maneuver fails! {target.name} outmaneuvers {active.name}."

            elif is_tether:
                if "Null-Suit" in target.special_rules:
                    action_text = f"attempts a Matrix action on {target.name}"
                    result_text = f"Action fails: {target.name} is wearing a Null-Suit and is immune to Matrix targeting."
                    narration = llm.narrate_action(active, action_text, result_text)
                    state.log(narration)
                    continue
                log = active.attributes.get("LOG", 3)
                hack_skill = active.skills.get("Hacking", 5)
                attack_pool = log + hack_skill
                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(attack_pool, active)
                )

                def_pool = target.attributes.get("WIL", 3) + target.matrix.firewall
                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)
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
                available_weapons = (
                    active.jumped_in_vehicle.weapons
                    if active.jumped_in_vehicle
                    else active.weapons
                )
                for w in available_weapons:
                    if w.name.lower() in action_lower:
                        chosen_weapon_name = w.name
                        break

                if chosen_weapon_name:
                    weapon = next(
                        (w for w in available_weapons if w.name == chosen_weapon_name),
                        available_weapons[0],
                    )
                else:
                    weapon = (
                        available_weapons[0]
                        if available_weapons
                        else Weapon("Unarmed Strike", 4, "S", 0)
                    )

                # Scenario Modifiers
                lighting_mod = state.environment.modifiers.get("lighting", 0)

                # Attack Roll: Agility + Skill
                if active.jumped_in_vehicle:
                    # Gunnery + Agility + Control Rig
                    attack_pool = (
                        active.attributes.get("AGI", 3)
                        + active.skills.get("Gunnery", 5)
                        + active.control_rig
                        + lighting_mod
                    )
                    if active.jumped_in_vehicle.swarm_count > 1:
                        attack_pool += active.jumped_in_vehicle.swarm_count - 1
                else:
                    attack_pool = active.attributes.get("AGI", 3) + 5 + lighting_mod

                attack_hits, attack_hits_glitched, edge_spent = (
                    RulesEngine.roll_attack_with_edge(max(1, attack_pool), active)
                )

                # Defense Roll: Reaction + Intuition + Cover
                if target.jumped_in_vehicle:
                    def_pool = (
                        target.attributes.get("REA", 3)
                        + target.attributes.get("INT", 3)
                        + target.jumped_in_vehicle.handling
                    )
                else:
                    def_pool = target.attributes.get("REA", 3) + target.attributes.get(
                        "INT", 3
                    )

                # Apply Cover
                if target.zone:
                    if target.zone.cover.lower() == "light":
                        def_pool += 1
                    elif target.zone.cover.lower() == "medium":
                        def_pool += 2
                    elif target.zone.cover.lower() == "heavy":
                        def_pool += 4

                def_hits, def_hits_glitched = RulesEngine.roll_dice(def_pool)

                net_hits = attack_hits - def_hits
                action_text = f"attacks {target.name} with {weapon.name} ({attack_hits} hits vs {def_hits} defense hits)"

                is_explosive = (
                    "grenade" in weapon.name.lower()
                    or "missile" in weapon.name.lower()
                    or "rocket" in weapon.name.lower()
                )

                if net_hits > 0 or is_explosive:
                    base_dmg = weapon.damage
                    if (
                        is_explosive
                        and target.zone
                        and (
                            target.zone.cover.lower() == "heavy"
                            or "enclosed" in target.zone.description.lower()
                            or "enclosed" in target.zone.name.lower()
                        )
                    ):
                        base_dmg *= 2
                        action_text += " [CHUNKY SALSA EFFECT!]"
                        # Grenades can still deviate on a miss, but for sim purposes we assume it lands in the zone if attack fired
                        net_hits = max(
                            0, net_hits
                        )  # Just use 0 net hits if it missed but landed in the room

                    modified_damage = base_dmg + net_hits
                    modified_ap = weapon.ap

                    # Soak Roll: Body + Armor + AP
                    if target.jumped_in_vehicle:
                        soak_pool = max(
                            0,
                            target.jumped_in_vehicle.body
                            + target.jumped_in_vehicle.armor
                            + modified_ap,
                        )
                    else:
                        soak_pool = max(
                            0,
                            target.attributes.get("BOD", 3)
                            + target.armor
                            + modified_ap,
                        )

                    soak_hits, soak_hits_glitched = RulesEngine.roll_dice(soak_pool)

                    final_damage = max(0, modified_damage - soak_hits)
                    result_text = f"Attack succeeds! Net hits: {net_hits}. {target.name} rolls {soak_pool} soak dice, getting {soak_hits} hits. {target.name} takes {final_damage} {weapon.damage_type} damage."

                    if target.jumped_in_vehicle:
                        # Physical damage goes to vehicle, Rigger takes half as Stun Biofeedback
                        if weapon.damage_type == "P":
                            target.jumped_in_vehicle.physical_damage += final_damage
                            biofeedback = final_damage // 2
                            if biofeedback > 0:
                                bio_resist = target.attributes.get(
                                    "WIL", 3
                                ) + target.attributes.get("BOD", 3)
                                bio_hits, bio_hits_glitched = RulesEngine.roll_dice(
                                    bio_resist
                                )
                                net_bio = max(0, biofeedback - bio_hits)
                                target.stun_damage += net_bio
                                result_text += f" Vehicle takes the damage! {target.name} rolls {bio_resist} dice to resist Stun Biofeedback, taking {net_bio} Stun damage."

                            if (
                                target.jumped_in_vehicle.physical_damage
                                >= target.jumped_in_vehicle.physical_track
                            ):
                                target.jumped_in_vehicle.swarm_count -= 1
                                if target.jumped_in_vehicle.swarm_count <= 0:
                                    pass
                                    target.stun_damage += 6
                                    target.jumped_in_vehicle = None  # Dumped
                                    result_text += f" The vehicle is DESTROYED! {target.name} takes 6 Stun dumpshock damage!"
                                else:
                                    target.jumped_in_vehicle.physical_damage = 0
                                    result_text += f" A drone in the swarm is destroyed! Swarm size reduced to {target.jumped_in_vehicle.swarm_count}."
                        else:
                            target.stun_damage += final_damage
                    else:
                        if weapon.damage_type == "P":
                            target.physical_damage += final_damage
                        else:
                            target.stun_damage += final_damage

                    if (
                        target.physical_damage >= target.physical_track
                        or target.stun_damage >= target.stun_track
                    ):
                        target.is_alive = False
                        result_text += f" {target.name} is incapacitated!"
                else:
                    result_text = f"Attack misses! {target.name} dodges the attack."

            # Narration
            if edge_spent:
                action_text += " [Spent Edge to re-roll misses!]"

            if "N.I.C.A." in active.special_rules:
                if locals().get("attack_hits_glitched") or locals().get(
                    "drain_hits_glitched"
                ):
                    effect = apply_nica_glitch(active)
                    action_text += f" [N.I.C.A. Glitch! Rogue 'ware sparks! {effect}]"

            if "N.I.C.A." in target.special_rules:
                if (
                    locals().get("def_hits_glitched")
                    or locals().get("soak_hits_glitched")
                    or locals().get("bio_hits_glitched")
                ):
                    effect = apply_nica_glitch(target)
                    result_text += (
                        f" [N.I.C.A. Glitch! Target's rogue 'ware sparks! {effect}]"
                    )

            if (
                target.physical_damage >= target.physical_track
                or target.stun_damage >= target.stun_track
            ):
                target.is_alive = False
                result_text += f" {target.name} is incapacitated!"
            if (
                active.physical_damage >= active.physical_track
                or active.stun_damage >= active.stun_track
            ):
                active.is_alive = False
                action_text += f" {active.name} is incapacitated!"

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
        state.log(
            f"Team {c.team} - {c.name}: {status} | Physical Damage: {c.physical_damage}/{c.physical_track} | Stun Damage: {c.stun_damage}/{c.stun_track}"
        )

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
                "A pristine piece of 'Dead Tech'.",
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
