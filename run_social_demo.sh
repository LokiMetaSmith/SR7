#!/bin/bash
source venv/bin/activate
python scripts/combat_simulator.py --team1 npc_templates/Player_Character.md --team2 npc_templates/Fixer_Contact.md --scenario campaigns/necessity/scenarios/social_scenario.json --interactive
