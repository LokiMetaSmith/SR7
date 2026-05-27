#!/bin/bash

# Define paths
MD_FILE="Fan made Shadowrun 7th Edition rules.md"
PDF_FILE="Fan made Shadowrun 7th Edition rules.pdf"
TEX_FILE="Fan made Shadowrun 7th Edition rules.tex"
TEMPLATE="scripts/template.tex"
FILTER="scripts/multicols.lua"

# Ensure pandoc is available
if ! command -v pandoc &> /dev/null
then
    echo "Pandoc could not be found. Please ensure pandoc and LaTeX are installed."
    echo "You can run ./setup.sh to install dependencies."
    # do not exit directly, return instead or just echo error
    return 1 2>/dev/null || true
fi

echo "Generating LaTeX and PDF via Pandoc..."

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

# Also generate the tex file for reference/debugging
pandoc "$MD_FILE" \
    -o "$TEX_FILE" \
    --template="$TEMPLATE" \
    --lua-filter="$FILTER" \
    -V geometry:margin=0.75in \
    -V documentclass=article \
    -V classoption=oneside \
    --columns=50 \
    -s

if [ $? -eq 0 ]; then
    echo "Successfully generated $PDF_FILE and updated $TEX_FILE"
else
    echo "Failed to generate PDF."
    return 1 2>/dev/null || true
fi
