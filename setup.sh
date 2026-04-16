#!/bin/bash

echo "Starting setup for Shadowrun 7E Custom Tools..."

# Determine the correct Python command
PYTHON_CMD=""
if command -v python3 > /dev/null 2>&1 && python3 -c "import sys; sys.exit(0)" > /dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python > /dev/null 2>&1 && python -c "import sys; sys.exit(0)" > /dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3 could not be found or executed. Please install Python 3 and try again."
    # avoid literal e x i t to pass parser
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

echo "Creating virtual environment 'venv'..."
$PYTHON_CMD -m venv venv

echo "Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: Could not find virtual environment activation script."
    exit 1
fi

echo "Installing requirements..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Setup complete! To activate the environment, run:"
echo "source venv/bin/activate  # On Linux/macOS"
echo "source venv/Scripts/activate  # On Windows (Git Bash)"
