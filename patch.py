import re

with open("scripts/combat_simulator.py", "r") as f:
    content = f.read()

# 1. Add Plane Enum
if "class Plane(Enum):" not in content:
    content = content.replace(
        "class MatrixAttributes:",
        """from enum import Enum

class Plane(Enum):
    PHYSICAL = 1
    ASTRAL = 2
    MATRIX = 3

@dataclass
class MatrixAttributes:"""
    )

# 2. Add properties to Combatant
if "current_plane: Plane =" not in content:
    content = content.replace(
        "    has_yielded: bool = False",
        """    has_yielded: bool = False
    current_plane: Plane = Plane.PHYSICAL
    is_dual_natured: bool = False"""
    )

# 3. Update load_combatant functions to set is_dual_natured
if "c.is_dual_natured = True" not in content:
    # Update parse_chummer
    content = content.replace(
        """    c.physical_track = 8 + (attributes.get("BOD", 3) // 2)
    c.stun_track = 8 + (attributes.get("WIL", 3) // 2)
    return c""",
        """    c.physical_track = 8 + (attributes.get("BOD", 3) // 2)
    c.stun_track = 8 + (attributes.get("WIL", 3) // 2)

    # Check for Dual Natured in special rules or qualities
    if any("dual natured" in r.lower() or "dual-natured" in r.lower() for r in c.special_rules):
        c.is_dual_natured = True
    elif char.find(".//qualities/quality[name='Dual Natured']") is not None:
        c.is_dual_natured = True

    return c"""
    )

    # Update parse_markdown
    content = content.replace(
        """    if re.search(r"N\.I\.C\.A\.|Scrap-Sickness", content, re.IGNORECASE):
        c.special_rules.append("N.I.C.A.")

    return c""",
        """    if re.search(r"N\.I\.C\.A\.|Scrap-Sickness", content, re.IGNORECASE):
        c.special_rules.append("N.I.C.A.")

    if re.search(r"Dual-Natured|Dual Natured", content, re.IGNORECASE):
        c.is_dual_natured = True

    return c"""
    )

with open("scripts/combat_simulator.py", "w") as f:
    f.write(content)
