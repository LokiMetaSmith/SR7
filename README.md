# Shadowrun 7E Custom Tools & Campaigns

This repository contains fan-made rules, tools, and campaign notes for a custom Shadowrun 7th Edition ruleset centered around the "Hollow Resonance" campaign setting in Zkazena.

## Tools Included

### 1. Autonomous Combat Simulator (`combat_simulator.py`)
This tool runs a fully autonomous, turn-based combat simulation between two entities. It utilizes the custom D6 ruleset and interfaces with a local OpenAI-compatible LLM to roleplay the encounter, make tactical weapon choices, and narrate gritty Shadowrun combat flavor text.

**Features:**
* Parses character sheets from `.chum5` XML files.
* Parses inline NPC stat blocks from Markdown files (e.g., `GM Notes/GM_Campaign_Guide.md:Sargent Igneous`).
* Ingests JSON scenario files for environmental context and map data.
* Outputs a turn-by-turn narrative log, final health summary, and randomized loot drops.
* Saves updated character states (Damage, Edge, Life Status) to a JSON scratchpad in the `campaign_state/` directory, making it easy to track character progression with Git.

**Usage:**

```bash
# Basic usage with two Chummer XML files
python combat_simulator.py npc_templates/Cryptolock.chum5 npc_templates/god_antibody.chum5

# Usage with a specific NPC from a Markdown file
python combat_simulator.py "GM Notes/GM_Campaign_Guide.md:Sargent Igneous" npc_templates/feral_fuchsia_dragon_abomination.chum5

# Load a specific scenario for the LLM to use (e.g., Tar Creek Ambush)
python combat_simulator.py npc_templates/Kyber.chum5 npc_templates/wuxing_null_sec_strike_team.chum5 --scenario tar_creek_ambush.json

# Test mechanical output without calling an LLM (uses generic default actions)
python combat_simulator.py npc_templates/Cryptolock.chum5 npc_templates/god_antibody.chum5 --dry-run
```

**LLM Configuration:**
By default, the script points to a locally hosted endpoint at `http://localhost:8000/v1`. You can override this using CLI arguments:
```bash
python combat_simulator.py <c1> <c2> --llm-url "https://api.openai.com/v1" --llm-model "gpt-4o"
```

### 2. Balance Generator (`balance_generator.py`)
Rewrites markdown tables in-place to calculate balanced Nuyen/Karma costs using explicit constants reflecting the 'Balancing Baseline Formulas'.

### 3. XML Generator (`xml_generator.py`)
Extracts game objects (weapons, qualities) from the Markdown rules and merges them into existing Chummer-compatible XML files within the `chummer_plugin/` directory.

---
*Note: Make sure to install the required Python packages via `pip install -r requirements.txt` before running these tools.*
