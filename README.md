# Shadowrun 7E Custom Tools & Campaigns

This repository contains fan-made rules, tools, and campaign notes for a custom Shadowrun 7th Edition ruleset centered around the "Hollow Resonance" campaign setting in Zkazena.

## Tools Included

### 1. Autonomous Combat Simulator (`combat_simulator.py`)
This tool runs a fully autonomous, turn-based combat simulation between two teams/squads. It utilizes the custom D6 ruleset and interfaces with a local OpenAI-compatible LLM to roleplay the encounter, make tactical weapon choices, and narrate gritty Shadowrun combat flavor text.

**Features:**
* Parses character sheets from `.chum5` XML files.
* Parses inline NPC stat blocks from Markdown files (e.g., `GM Notes/GM_Campaign_Guide.md:Sargent Igneous`).
* Ingests JSON scenario files for environmental context and map data.
* Outputs a turn-by-turn narrative log, final health summary, and randomized loot drops.
* Saves updated character states (Damage, Edge, Life Status) to a JSON scratchpad in the `campaign_state/` directory, making it easy to track character progression with Git.
* Supports a visual Pygame interface (`--ui`) with dynamic combatant tracking cards.
* Supports an interactive mode (`--interactive`) that pauses for manual input and UI clicks (attacks, spells, data spikes, etc.).

**Usage:**

```bash
# Basic usage with two Chummer XML files
python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5

# Usage with a specific NPC from a Markdown file
python scripts/combat_simulator.py --team1 "GM Notes/GM_Campaign_Guide.md:Sargent Igneous" --team2 npc_templates/feral_fuchsia_dragon_abomination.chum5

# Load a specific scenario for the LLM to use (e.g., Tar Creek Ambush)
python scripts/combat_simulator.py --team1 npc_templates/Kyber.chum5 --team2 npc_templates/wuxing_null_sec_strike_team.chum5 --scenario tar_creek_ambush.json

# Test mechanical output without calling an LLM (uses generic default actions)
python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5 --dry-run

# Squad combat with visual UI and manual inputs
python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 npc_templates/Kyber.chum5 --team2 npc_templates/god_antibody.chum5 npc_templates/wuxing_null_sec_strike_team.chum5 --ui --interactive
```

**LLM Configuration:**
By default, the script points to a locally hosted endpoint at `http://localhost:8000/v1`. You can override this using CLI arguments:
```bash
python scripts/combat_simulator.py --team1 <paths> --team2 <paths> --llm-url "https://api.openai.com/v1" --llm-model "gpt-4o"
```

### 2. Combat Analyzer (`combat_analyzer.py`)
This tool runs the mechanical combat simulation from `combat_simulator.py` headless and repeatedly to gather statistics. It utilizes a `DummyAgent` for decision-making so it is purely mechanical, extremely fast, and completely free to run. Use this tool to balance weapons, test character builds, and verify stat differences.

**Usage:**
```bash
# Run 100 iterations between two combatants
python scripts/combat_analyzer.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5 --iterations 100
```

### 3. NPC Tournament (`tournament.py`)
This tool reads all `.chum5` character files from the `npc_templates/` directory and simulates a full round-robin combat tournament. It pits every character against every other character for 100 iterations and computes a final leaderboard based on wins, draws, and losses.

**Usage:**
```bash
# Run the tournament and generate tournament_results.md
python scripts/tournament.py
```

### 4. Balance Generator (`balance_generator.py`)
Rewrites markdown tables in-place to calculate balanced Nuyen/Karma costs using explicit constants reflecting the 'Balancing Baseline Formulas'.

### 5. XML Generator (`xml_generator.py`)
Extracts game objects (weapons, qualities) from the Markdown rules and merges them into existing Chummer-compatible XML files within the `chummer_plugin/` directory.

## Setup and Installation

It is highly recommended to use a Python virtual environment to manage dependencies and avoid version conflicts (such as issues with the `openai` and `httpx` packages).

**Automated Setup:**
You can run the included setup script to automatically create a virtual environment and install all requirements:
```bash
chmod +x setup.sh
./setup.sh
```

**Manual Setup:**
```bash
# 1. Create a virtual environment named 'venv'
python3 -m venv venv

# 2. Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows (Command Prompt):
venv\Scripts\activate.bat
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# 3. Install the required dependencies
pip install -r requirements.txt
```

---
