#!/bin/bash

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

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
            echo "Running Combat Simulator (CLI)..."
            python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5 --dry-run
            ;;
        2)
            echo "Running Combat Simulator (Pygame UI)..."
            python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5 --ui --interactive
            ;;
        3)
            echo "Running Combat Simulator (Squad Combat UI)..."
            python scripts/combat_simulator.py --team1 npc_templates/Cryptolock.chum5 npc_templates/Kyber.chum5 --team2 npc_templates/god_antibody.chum5 npc_templates/wuxing_null_sec_strike_team.chum5 --ui --interactive
            ;;
        4)
            echo "Running Module Runner (Hollow Resonance Demo)..."
            python scripts/run_module.py --module campaigns/default/modules/hollow_resonance_part1.json --team1 npc_templates/Cryptolock.chum5 npc_templates/Kyber.chum5 --ui --interactive
            ;;
        5)
            echo "Running Trade Simulator Demo..."
            python scripts/combat_simulator.py --trade-simulator "npc_templates/Kyber.chum5:Ares Predator:350:1"
            ;;
        6)
            echo "Running Combat Analyzer..."
            python scripts/combat_analyzer.py --team1 npc_templates/Cryptolock.chum5 --team2 npc_templates/god_antibody.chum5 --iterations 10
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
