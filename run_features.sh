#!/bin/bash

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

select_combatants() {
    local prompt_msg="$1"
    echo "--- $prompt_msg ---" >&2

    # Gather all .chum5 and .md files in npc_templates/ and Player Handouts/
    local files=()
    while IFS=  read -r -d $'\0'; do
        files+=("$REPLY")
    done < <(find "npc_templates" "Player Handouts" -type f \( -name "*.chum5" -o -name "*.md" \) 2>/dev/null | sort | tr '\n' '\0')

    if [ ${#files[@]} -eq 0 ]; then
        echo "No combatants found." >&2
        echo "" >&2
        return
    fi

    for i in "${!files[@]}"; do
        echo "$((i+1))) ${files[$i]}" >&2
    done
    echo "" >&2
    read -p "Enter numbers separated by spaces (or press Enter for default): " selections >&2

    if [[ -z "${selections// /}" ]]; then
        return
    else
        local selected_paths=""
        for sel in $selections; do
            if [[ "$sel" =~ ^[0-9]+$ ]] && [ "$sel" -ge 1 ] && [ "$sel" -le "${#files[@]}" ]; then
                local idx=$((sel-1))
                selected_paths="$selected_paths \"${files[$idx]}\""
            else
                echo "Warning: Invalid selection '$sel', ignoring." >&2
            fi
        done
        echo "$selected_paths" | sed 's/^ *//;s/ *$//'
    fi
}

while true; do
    echo "=============================================="
    echo "    Shadowrun 7E Custom Tools - Main Menu     "
    echo "=============================================="
    echo "1) Combat Simulator (CLI Dry-Run)"
    echo "2) Combat Simulator (Pygame UI 1v1)"
    echo "3) Combat Simulator (Squad Combat UI 2v2)"
    echo "4) Module Runner (Hollow Resonance Demo)"
    echo "5) Trade Simulator Demo"
    echo "6) Combat Analyzer (10 iterations)"
    echo "7) NPC Tournament"
    echo "8) Run Data Generators (Balance & XML)"
    echo "9) PDF Generator"
    echo "0) Exit"
    echo "=============================================="
    read -p "Select an option [0-9]: " option

    case $option in
        1)
            team1=$(select_combatants "Select combatant(s) for Team 1")
            team1=${team1:-"npc_templates/Cryptolock.chum5"}
            team2=$(select_combatants "Select combatant(s) for Team 2")
            team2=${team2:-"npc_templates/god_antibody.chum5"}
            echo "Running Combat Simulator (CLI)..."
            eval python scripts/combat_simulator.py --team1 $team1 --team2 $team2 --dry-run
            ;;
        2)
            team1=$(select_combatants "Select combatant(s) for Team 1")
            team1=${team1:-"npc_templates/Cryptolock.chum5"}
            team2=$(select_combatants "Select combatant(s) for Team 2")
            team2=${team2:-"npc_templates/god_antibody.chum5"}
            echo "Running Combat Simulator (Pygame UI)..."
            eval python scripts/combat_simulator.py --team1 $team1 --team2 $team2 --ui --interactive
            ;;
        3)
            team1=$(select_combatants "Select combatants for Team 1 (defaults to Cryptolock and Kyber)")
            team1=${team1:-"npc_templates/Cryptolock.chum5" "npc_templates/Kyber.chum5"}
            team2=$(select_combatants "Select combatants for Team 2 (defaults to god_antibody and wuxing_strike_team)")
            team2=${team2:-"npc_templates/god_antibody.chum5" "npc_templates/wuxing_null_sec_strike_team.chum5"}
            echo "Running Combat Simulator (Squad Combat UI)..."
            eval python scripts/combat_simulator.py --team1 $team1 --team2 $team2 --ui --interactive
            ;;
        4)
            team1=$(select_combatants "Select combatants for Team 1 (defaults to Cryptolock and Kyber)")
            team1=${team1:-"npc_templates/Cryptolock.chum5" "npc_templates/Kyber.chum5"}
            echo "Running Module Runner (Hollow Resonance Demo)..."
            eval python scripts/run_module.py --module campaigns/default/modules/hollow_resonance_part1.json --team1 $team1 --ui --interactive
            ;;
        5)
            buyer=$(select_combatants "Select buyer for Trade Simulator")
            buyer=${buyer:-"npc_templates/Kyber.chum5"}
            read -p "Enter Item Name [Ares Predator]: " item_name
            item_name=${item_name:-Ares Predator}
            read -p "Enter Base Value [350]: " base_val
            base_val=${base_val:-350}
            read -p "Enter Fixer Difficulty (1-6) [1]: " diff
            diff=${diff:-1}
            echo "Running Trade Simulator Demo..."
            # Note: The Trade Simulator strictly takes one buyer string, we'll just use the first if multiple are selected.
            buyer_first=$(echo "$buyer" | awk -F '"' '{if (NF>1) print $2; else print $1}')
            python scripts/combat_simulator.py --trade-simulator "${buyer_first}:$item_name:$base_val:$diff"
            ;;
        6)
            team1=$(select_combatants "Select combatant(s) for Team 1")
            team1=${team1:-"npc_templates/Cryptolock.chum5"}
            team2=$(select_combatants "Select combatant(s) for Team 2")
            team2=${team2:-"npc_templates/god_antibody.chum5"}
            echo "Running Combat Analyzer..."
            eval python scripts/combat_analyzer.py --team1 $team1 --team2 $team2 --iterations 10
            ;;
        7)
            echo "Running NPC Tournament..."
            python scripts/tournament.py
            ;;
        8)
            echo "Running Data Generators (Balance & XML)..."
            python scripts/balance_generator.py
            python scripts/xml_generator.py
            ;;
        9)
            echo "Running PDF Generator..."
            ./scripts/generate_pdf.sh
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid option. Please select a valid number."
            ;;
    esac
    echo ""
done
