# Project Action Items (Shadowrun 7E Homebrew & Campaign)

Based on the recent systems review, here is a prioritized to-do list for making this project functional.

## Priority 1: Rules & Core Mechanics ("Fan made Shadowrun 7th Edition")

**Goal:** Establish a complete, structurally sound foundation before building tools around it.

*   [x] **Standardize Document Formatting:** Go through `Fan made Shadowrun 7th Edition rules.md` and convert all tables (currently a mix of tabs and spaces) into standard Markdown pipe (`|`) syntax.
    *   [x] *Follow-up required:* Establish a master template for Weapon and Quality tables so that parsing tools know exactly what to look for.
*   [x] **Draft Missing Core Sections:** Write the rules text for the fundamentally missing pillars of the game:
    *   [x] *Follow-up required (Magic):* Need design docs for Spell lists, Adept powers, Drain calculations, Rituals, and Metamagic.
    *   [x] *Follow-up required (Matrix):* Need design docs for Matrix elements:
        *   [x] Programs
        *   [x] Cyberdecks/Commlinks
        *   [x] Host architecture & IC
        *   [x] Matrix actions (how do "Tethers" work in combat?)
    *   [x] *Follow-up required (Rigging/Vehicles):* Need design docs for:
        *   [x] Drone stats
        *   [x] Vehicle modifications
        *   [x] Chase combat
        *   [x] Jumped-in mechanics
    *   [x] *Follow-up required (General Equipment):* Need lists and costs for Armor, Cyberware/Bioware, Commlinks, and Lifestyle.
*   [x] **Define the Baseline Mechanics:** Clarify how "Wild Dice" and "Digital Essence" interact with standard gameplay loops.
    *   [x] Implement rules for HMHVV Infected (Ghouls & Vampires) under Bestiary.


---

## Priority 2: Tooling & Utility Scripts (Python)

**Goal:** Fix the automated balancing and generation scripts once the underlying Markdown document is stable.

*   [x] **Fix File Paths:** Update `analyze_rules.py` to target the actual filename (`Fan made Shadowrun 7th Edition rules.md`), ideally by accepting it as a CLI argument instead of hardcoding it.
*   [x] **Rewrite Parsers:** Ditch the brittle regex approach in both `analyze_rules.py` and `balance_generator.py`.
    *   [x] *Follow-up required:* Implement a proper Markdown parsing library (e.g., `markdown-it-py` or `mistune`) to reliably extract table data.
*   [x] **Refine Balancing Logic:** Update `balance_generator.py`.
    *   [x] *Follow-up required:* A clear, mathematically defined baseline formula for weapon costs and metatype Karma needs to be established and documented before a script can automatically "balance" anything.
*   [x] **Create XML Generator Pipeline:** Write a new Python script to translate the standardized Markdown tables directly into Chummer-compatible XML files (`custom_sr7e_weapons.xml`, `custom_sr7e_qualities.xml`).

---

## Priority 3: Chummer5a Integration (C# Plugin)

**Goal:** Make the `Shadowrun7EPlugin.cs` functional and safe to use.

*   [x] **Remove CalculateCustomInitiative:** Removed the invalid stub `CalculateCustomInitiative()` as it is not part of the Chummer5a `IPlugin` interface.
*   [x] **Implement Core Overrides:**
    *   [x] *Follow-up required:* Wait for the "Digital Essence" and "Initiative" rules to be finalized in the Markdown doc, then code those specific overrides into the C# `IPlugin` interface.

---

## Priority 4: Narrative Consistency (GM Notes & Novellas)

**Goal:** Ensure the story mechanically aligns with the custom ruleset.

*   [x] **Audit NPC Stat Blocks:** Review `GM_Campaign_Guide.md` (Sister Sinalma, Captain Lazlow, Spark+, etc.).
    *   [x] *Follow-up required:* Every Spell, Adept Power, Cyberware, Quality, and Weapon referenced in these stat blocks must be added to the `Fan made Shadowrun 7th Edition rules.md` document (and eventually the Chummer XML). If the rule doesn't exist, the stat block is unplayable.
    *   [x] *Follow-up required:* Update `Fan made Shadowrun 7th Edition rules.tex` to include the `Custom Fit`, `Infection (HMHVV)`, and `Dual Natured` rules added to the markdown.
*   [x] **Draft 'Stopgap' GM Advice:** Add a note to the `Hollow_Resonance_Worldbuilding.md` advising GMs to run the campaign using standard Shadowrun 5E rules until the 7E homebrew is actually finished, using the homebrew concepts strictly for narrative flavor.
*   [x] **Sync GM Notes with Core Rules:** Extracted missing weapons (`Shiawase Arms Hearth Protector`, `Combat Knife`, `Throwing Knives`, `Monofilament Knife`, `Monofilament Whip`) from `GM Notes/GM_Campaign_Guide.md` and added them to the main weapon tables in `Fan made Shadowrun 7th Edition rules.md` and `Fan made Shadowrun 7th Edition rules.tex`. Corrected weapon stats inside the GM Notes to match the balanced rules format.
- [x] **Implement Squad Combat:** Updated the autonomous combat simulator to support multi-character squad combat.

---

## Priority 5: Advanced Combat Simulator Mechanics

**Goal:** Expand the Python combat simulator to fully encompass the breadth of the Shadowrun 7E House Rules.

*   [x] **Rigging & Drone Combat:** Implement remaining rigging features.
    *   [x] Jumping-in mechanics (with Control Rigs)
    *   [x] Matrix Initiative for Riggers
    *   [x] Implement drone swarms
    *   [x] Implement chase combat rules
*   [x] **Environmental Modifiers & Background Count:** Make the simulator read `scenario.json` and apply lighting penalties, AR noise interference, or Matrix Ley Lines (forcing the use of Wild Dice).
*   [x] **Advanced Armor & AP Mechanics:** Expand defense rolls to handle specialized armor like Null-Suits (reducing Matrix targeting) or affliction mechanics like N.I.C.A. (Scrap-Sickness) for prolonged exposure to grey goo.
*   [x] **Edge / Hopepunk Mechanics:** Allow the simulator AI to actively spend the `Edge` attribute during critical failures to re-roll misses or push the limit on wild dice.
*   [x] **Unify Possession Rules:** Centralize and standardize mechanics for BTL possession, Rigger jump-ins, AI inhabitation, and spiritual possession.
*   [x] **N.I.C.A. Glitch Table:** Implement a 'glitch table' for N.I.C.A. (Scrap-Sickness) glitches in the combat simulator to apply varied narrative and mechanical effects.
*   [x] **Sync Combat Analyzer:** Sync `combat_analyzer.py` with all the new mechanics added to `combat_simulator.py` (Squad Combat, Edge spending, Social mechanics, Chunky Salsa, N.I.C.A).

## Recently Completed:
*   [x] **Astral Plane & Spirits:** Added details on the Astral Plane and Canonical Spirits (Elementals, Spirits of Man, Insect Spirits), including new narrative mechanics to fit the Merged World setting.
*   [x] **Spirit Bestiary:** Added full stat blocks for Canonical Spirits to the Bestiary section.
---

## Priority 6: Visual Interface (Pygame)

**Goal:** Build an interactive visual layer for the simulator using Pygame.

*   [x] **Implement UI Components:** Create a 3-panel UI design for Player and GM cards using `pygame` mapping to the backend `Combatant` attributes.
*   [x] **Integrate Full Gamestate:** Connect the interactive cards fully to the live combat loop instead of just rendering dummy data.
*   [x] **Expand Interactions:** Add click events to trigger specific combat actions directly from the UI cards.
