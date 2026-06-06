with open("scripts/combat_simulator.py", "r") as f:
    content = f.read()

content = content.replace("""@dataclass
from enum import Enum""", """from enum import Enum""")

with open("scripts/combat_simulator.py", "w") as f:
    f.write(content)
