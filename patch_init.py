with open("scripts/combat_simulator.py", "r") as f:
    content = f.read()

old_init = """    def roll_initiative(self) -> int:
        if self.jumped_in_vehicle:
            # Matrix Initiative (Data Processing + Intuition) + 1 Initiative Die per Rig level
            base = self.matrix.data_processing + self.get_attribute("INT", 3)
            dice = 1 + self.control_rig
        else:
            base = self.get_attribute("REA", 3) + self.get_attribute("INT", 3)
            dice = 1
            if "Wired Reflexes" in " ".join(self.special_rules):
                dice += 1

        roll = sum(random.randint(1, 6) for _ in range(dice))
        self.initiative_score = base + roll
        return self.initiative_score"""

new_init = """    def roll_initiative(self) -> int:
        if self.current_plane == Plane.ASTRAL or self.is_dual_natured:
            # Astral Initiative (REA + INT) + 1 Initiative Die per Force/MAG
            base = self.get_attribute("REA", 3) + self.get_attribute("INT", 3)
            dice = 1 + self.get_attribute("MAG", 0)
        elif self.current_plane == Plane.MATRIX or self.jumped_in_vehicle:
            # Matrix Initiative (Data Processing + Intuition) + 1 Initiative Die per Rig level
            base = self.matrix.data_processing + self.get_attribute("INT", 3)
            dice = 1 + getattr(self, 'control_rig', 0)
        else:
            base = self.get_attribute("REA", 3) + self.get_attribute("INT", 3)
            dice = 1
            if "Wired Reflexes" in " ".join(self.special_rules):
                dice += 1

        roll = sum(random.randint(1, 6) for _ in range(dice))
        self.initiative_score = base + roll
        return self.initiative_score"""

content = content.replace(old_init, new_init)

with open("scripts/combat_simulator.py", "w") as f:
    f.write(content)
