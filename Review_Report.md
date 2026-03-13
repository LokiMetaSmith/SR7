# Project Review: "Necessity Knows No Law" & Shadowrun 7E (Fan Made)
**Reviewer:** Jules (Systems & Code Architecture)
**Date:** March 13, 2024

## Executive Summary
This project aims to combine an ambitious, atmosphere-heavy Shadowrun narrative campaign ("Hollow Resonance" / "Necessity Knows No Law") with a sweeping homebrew ruleset dubbed "Shadowrun 7th Edition: The Merged World," complete with automated balance scripting and a Chummer5a plugin.

While the narrative vision is strong and thematic ("Hopepunk," "Necessity Knows No Law"), the technical execution of the ruleset and its supporting software infrastructure is fundamentally flawed. The project currently exists as a collection of disconnected prototypes. The utility scripts are broken, the rules document is wildly incomplete and inconsistently formatted, and the Chummer plugin is an empty shell that would actively break the game if compiled.

This report outlines the critical areas requiring immediate attention before this project can be considered playable or usable by collaborators.

---

## 1. Tooling & Utility Scripts (Python)

The repository includes two Python scripts intended to parse and balance the custom rules: `analyze_rules.py` and `balance_generator.py`. In their current state, they are completely non-functional.

*   **Hardcoded & Incorrect File Paths:** `analyze_rules.py` attempts to open `rules.md`, a file that does not exist in the repository (the actual file is `Fan made Shadowrun 7th Edition rules.md`). This results in an immediate `FileNotFoundError`.
*   **Fragile Regular Expressions:** Both scripts rely on highly specific regex patterns to find tables (e.g., looking for exact strings like `**ACC    	DV        	AP    	MODE    RC	RANGE    AMMO    AVAIL    WEIGHT	COST**`). The actual Markdown document is horribly inconsistent with its table formatting—some tables use tabs, some use Markdown pipes (`|`), and column headers vary wildly. Consequently, the scripts silently fail to find any weapons or metatypes.
*   **Flawed Balancing Logic:** The heuristics in `balance_generator.py` are rudimentary at best. Calculating weapon cost as `100 + (dv ** 2) * 2 + (ap * 50) + ...` might generate a number, but without a unified baseline established in the rules document, it's a shot in the dark. Furthermore, because the regex fails to parse the document, this logic is never actually applied.

**Actionable Feedback:**
*   Standardize the Markdown tables in the rules document strictly to the standard Markdown pipe (`|`) format.
*   Rewrite the Python scripts using a proper Markdown parser (like `markdown-it-py` or `mistune`) instead of brittle regexes to extract table data reliably.
*   Parameterize file paths so the scripts can be run dynamically via CLI arguments.

---

## 2. Rules & Mechanics ("Fan made Shadowrun 7th Edition")

The "Merged World" homebrew document promises a massive overhaul of the Shadowrun system (merging the Matrix and Gaiasphere, introducing Wild Dice, replacing Marks with Tethers). However, it currently reads more like an unedited manifesto than a playable rulebook.

*   **Glaring Omissions:** As acknowledged, the document is missing critical, foundational sections. There are no rules for:
    *   **Magic:** Spell lists, Adept powers, Drain calculations, Rituals, or Metamagic.
    *   **The Matrix:** Programs, Cyberdecks/Commlinks, IC, Host architecture, or detailed Matrix actions.
    *   **Rigging & Vehicles:** Drone stats, Vehicle modifications, Chase combat, or Jumped-in mechanics (despite extensive vehicle weapon lists being present).
    *   **General Equipment:** Armor, Cyberware/Bioware, Commlinks, Lifestyle costs, or basic adventuring gear.
*   **Formatting Inconsistencies:** The document is a structural nightmare. Qualities are listed cleanly, but then it abruptly transitions into massive, poorly formatted walls of text detailing real-world ammunition types (e.g., `.300 Ultra Magnum`, `14.5x114mm`) and highly specific torpedoes. This level of granular simulationism clashes heavily with the "streamlined success-counting system" proposed in Section I.
*   **Mechanical Disconnects:** The core mechanics section introduces "Wild Dice" and "Digital Essence," but the rest of the document (what little there is) fails to explain how these interact with standard gameplay loops or how they are acquired/measured.

**Actionable Feedback:**
*   Pause adding hyper-specific weapon profiles (like 15 different types of 7.62mm cartridges) and focus on writing the core systems first: Magic, Matrix, Rigging, and base Equipment.
*   Standardize the formatting. Use consistent headers, bullet points, and properly formatted Markdown tables.
*   Create a "Changelog" or "Design Philosophy" document separate from the actual rules text to keep the manual clean for players.

---

## 3. Chummer5a Integration (C# Plugin)

The `Shadowrun7EPlugin.cs` file is intended to adapt Chummer5a to these radical house rules. Currently, it is a liability.

*   **Hollow Boilerplate:** The code implements the `IPlugin` interface but does absolutely nothing with it.
*   **Game-Breaking Stubs:** The method `CalculateCustomInitiative()` simply `return 0;`. If a user were to compile this DLL and load it into Chummer5a, every character would roll a 0 for initiative, breaking the game's combat engine entirely.
*   **Misguided Scope:** The `README_PLUGIN.md` correctly notes that adding Qualities/Weapons should be done via XML (`custom_*.xml`), yet the Python scripts are designed to balance a Markdown file. There is no pipeline to convert the balanced Markdown tables into the required Chummer XML format.

**Actionable Feedback:**
*   Remove or comment out `CalculateCustomInitiative()` until the actual formula (which is supposedly derived from REA + INT, as per line 214 of the rules doc) is implemented.
*   Develop a Python script to translate the Markdown tables (once standardized) directly into Chummer-compatible XML files (`custom_sr7e_weapons.xml`, `custom_sr7e_qualities.xml`). This bridges the gap between the design doc and the software tool.

---

## 4. Narrative Consistency (GM Notes & Novellas)

The worldbuilding (Zkazena, The New Garden, Fuchsia Dragons) is compelling, brutal, and atmospheric. The "Necessity Knows No Law" philosophy is well-articulated. However, there is a severe disconnect between the narrative and the mechanical ruleset.

*   **Stat Block Discrepancies:** The `GM_Campaign_Guide.md` includes extensive stat blocks for NPCs like Sister Sinalma, Captain Lazlow, and Spark+. These stat blocks reference Spells (e.g., *Trid Phantasm*, *Agony*), Adept Powers, Cyberware (*Synaptic Booster 2*), and specific weapons that **do not exist** in the `Fan made Shadowrun 7th Edition rules.md` document.
*   **Unplayable Encounters:** If a GM attempted to run the "Siege of White Tower" using only the provided 7E rules doc, they would have no way to resolve Matrix actions against the Oracle AI or calculate Drain for the Horrors' magic, as those systems are missing.

**Actionable Feedback:**
*   The narrative and the ruleset must be developed in tandem. Every weapon, spell, piece of cyberware, and quality referenced in an NPC stat block in the GM Guide must have a corresponding entry in the rules document (and subsequently, the Chummer XML files).
*   Until the 7E ruleset is complete, it is highly recommended to advise GMs to run the campaign using standard Shadowrun 5th Edition rules, using the homebrew strictly for flavor rather than mechanical enforcement.

---

## Conclusion
The project has excellent creative momentum but is currently crippled by a lack of foundational discipline. The immediate priority must be standardizing the Markdown formatting of the rules document and writing the missing core systems (Magic, Matrix, Rigging). Only once the document is structurally sound should the Python tooling and C# plugin be revisited to automate the balance and integration processes.