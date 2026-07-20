#!/bin/bash

# Define paths
TEMPLATE="scripts/template.tex"
FILTER="scripts/multicols.lua"

# Ensure pandoc is available
if ! command -v pandoc &> /dev/null
then
    echo "Pandoc could not be found. Please ensure pandoc and LaTeX are installed."
    echo "You can run ./setup.sh to install dependencies."
    exit 1
fi

echo "Generating PDFs for novellas via Pandoc..."

NOVELLAS=(
    "GM Notes/Cold Storage a Novella.md"
    "GM Notes/Hollow Resonance a Novella.md"
)

for MD_FILE in "${NOVELLAS[@]}"; do
    if [ ! -f "$MD_FILE" ]; then
        echo "File $MD_FILE not found."
        continue
    fi

    BASENAME=$(basename "$MD_FILE" .md)
    PDF_FILE="GM Notes/${BASENAME}.pdf"

    echo "Processing $MD_FILE -> $PDF_FILE"

    pandoc "$MD_FILE" \
        -o "$PDF_FILE" \
        --template="$TEMPLATE" \
        --lua-filter="$FILTER" \
        --pdf-engine=pdflatex \
        -V geometry:margin=0.75in \
        -V documentclass=article \
        -V classoption=oneside \
        --columns=50 \
        -V linkcolor:blue \
        -V urlcolor:blue \
        -V toccolor:blue \
        -s

    if [ $? -eq 0 ]; then
        echo "Successfully generated $PDF_FILE"
    else
        echo "Failed to generate $PDF_FILE"
    fi
done
