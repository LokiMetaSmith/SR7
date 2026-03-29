# Project Action Items (Shadowrun 7E Homebrew & Campaign)

Based on the recent systems review, here is a prioritized to-do list for making this project functional.

## Priority 1: Rules & Core Mechanics ("Fan made Shadowrun 7th Edition")

**Goal:** Establish a complete, structurally sound foundation before building tools around it.

*   [x] **Standardize Document Formatting:** Go through `Fan made Shadowrun 7th Edition rules.md` and convert all tables (currently a mix of tabs and spaces) into standard Markdown pipe (`|`) syntax.
    *   [x] *Follow-up required:* Establish a master template for Weapon and Quality tables so that parsing tools know exactly what to look for.
*   [x] **Draft Missing Core Sections:** Write the rules text for the fundamentally missing pillars of the game:
    *   [x] *Follow-up required (Magic):* Need design docs for Spell lists, Adept powers, Drain calculations, Rituals, and Metamagic.
    *   [x] *Follow-up required (Matrix):* Need design docs for Programs, Cyberdecks/Commlinks, IC, Host architecture, and Matrix actions (how do "Tethers" work in combat?).
    *   [ ] *Follow-up required (Rigging/Vehicles):* Need design docs for:
        *   [x] Drone stats
        *   [x] Vehicle modifications
        *   [x] Chase combat
        *   [x] Jumped-in mechanics
    *   [x] *Follow-up required (General Equipment):* Need lists and costs for Armor, Cyberware/Bioware, Commlinks, and Lifestyle.
*   [x] **Define the Baseline Mechanics:** Clarify how "Wild Dice" and "Digital Essence" interact with standard gameplay loops.

---

## Priority 2: Tooling & Utility Scripts (Python)

**Goal:** Fix the automated balancing and generation scripts once the underlying Markdown document is stable.

*   [x] **Fix File Paths:** Update `analyze_rules.py` to target the actual filename (`Fan made Shadowrun 7th Edition rules.md`), ideally by accepting it as a CLI argument instead of hardcoding it.
*   [x] **Rewrite Parsers:** Ditch the brittle regex approach in both `analyze_rules.py` and `balance_generator.py`.
    *   *Follow-up required:* Implement a proper Markdown parsing library (e.g., `markdown-it-py` or `mistune`) to reliably extract table data.
*   [x] **Refine Balancing Logic:** Update `balance_generator.py`.
    *   *Follow-up required:* A clear, mathematically defined baseline formula for weapon costs and metatype Karma needs to be established and documented before a script can automatically "balance" anything.
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