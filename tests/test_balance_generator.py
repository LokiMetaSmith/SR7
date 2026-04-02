import unittest
import sys
import os

# Add scripts directory to path to import balance_generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
import balance_generator

class TestBalanceGenerator(unittest.TestCase):

    def test_parse_int_or_float(self):
        self.assertEqual(balance_generator.parse_int_or_float("100"), 100.0)
        self.assertEqual(balance_generator.parse_int_or_float("100¥"), 100.0)
        self.assertEqual(balance_generator.parse_int_or_float("1,000"), 1000.0)
        self.assertEqual(balance_generator.parse_int_or_float("10(20)"), 10.0)
        self.assertEqual(balance_generator.parse_int_or_float("5/10"), 5.0)
        self.assertEqual(balance_generator.parse_int_or_float("invalid"), 0.0)

    def test_balance_metatypes(self):
        # A simple markdown table for testing metatypes
        # Total base stats:
        # BOD 6 + AGI 6 + REA 6 + STR 6 + WIL 6 + LOG 6 + INT 6 + CHA 6 + EDG 6 = 54
        # Human test (should skip)
        # Elf test: +1 AGI, +2 CHA -> stats: 6, 7, 6, 6, 6, 6, 6, 8, 6 = 57
        # Difference from 56 = 1. Base Cost: 1 * 15 = 15.
        # Traits: Low-Light Vision (+5)
        # Total expected cost: 20
        md_text = """
| Race | BOD | AGI | REA | STR | WIL | LOG | INT | CHA | EDG | Karma Cost | Traits |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Human** | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 2/7 | 0 | +1 Edge |
| **Elf** | 1/6 | 2/7 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 3/8 | 1/6 | 0 | Low-Light Vision |
"""
        balanced_text = balance_generator.balance_metatypes(md_text)

        # Human should remain unchanged
        self.assertIn("| **Human** | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 2/7 | 0 | +1 Edge |", balanced_text)

        # Elf should be updated to 20
        self.assertIn("| **Elf** | 1/6 | 2/7 | 1/6 | 1/6 | 1/6 | 1/6 | 1/6 | 3/8 | 1/6 | 20 | Low-Light Vision |", balanced_text)

    def test_balance_weapons(self):
        md_text = """
**Pistols**

| Weapon Name | ACC | DV | AP | MODE | RC | RANGE | AMMO | AVAIL | WEIGHT | COST |
|---|---|---|---|---|---|---|---|---|---|---|
| Fichetti Security 600 | 6(7) | 7P | 0 | SA | 1 | Close | 30(c) | 6R | 1.5 | 350¥ |

**Sniper Rifles**

| Weapon Name | ACC | DV | AP | MODE | RC | RANGE | AMMO | AVAIL | WEIGHT | COST |
|---|---|---|---|---|---|---|---|---|---|---|
| Ares Desert Strike | 7 | 13P | -4 | SA | 1(2) | Far | 14(c) | 10F | 4.0 | 17,500¥ |
"""
        balanced_text = balance_generator.balance_weapons(md_text)

        # We'll just verify the generator actually modifies the lines correctly
        # Fichetti Security 600
        # DV: 7 -> 49 * 2 = 98
        # AP: 0 -> 0
        # Mode: SA -> 50
        # RC: 1 -> 100
        # Ammo: 30 -> 150
        # Total: 100 + 98 + 0 + 50 + 100 + 150 = 498
        # Category: Pistol -> 498 * 0.8 = 398.4
        # Rounding: >100 -> nearest 50. 398.4 / 50 = 7.968 -> 8. 8 * 50 = 400
        # Update: In python, 398.4 / 50 = 7.968, round(7.968) = 8, 8 * 50 = 400.

        self.assertIn("| Fichetti Security 600 | 6(7) | 7P | 0 | SA | 1 | Close | 30(c) | 6R | 1.5 | 400¥ |", balanced_text)

        # Ares Desert Strike
        # DV: 13 -> 169 * 2 = 338
        # AP: -4 -> 200
        # Mode: SA -> 50
        # RC: 1 -> 100
        # Ammo: 14 -> 70
        # Total: 100 + 338 + 200 + 50 + 100 + 70 = 858
        # Category: Sniper -> 858 * 1.5 = 1287
        # Rounding: >1000 -> nearest 100. 1287 / 100 = 12.87 -> 13. 13 * 100 = 1300
        self.assertIn("| Ares Desert Strike | 7 | 13P | -4 | SA | 1(2) | Far | 14(c) | 10F | 4.0 | 1300¥ |", balanced_text)

if __name__ == "__main__":
    unittest.main()
