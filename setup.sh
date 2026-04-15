#!/bin/bash

echo "Starting setup for Shadowrun 7E Custom Tools..."

# Check if python3 is installed
if ! command -v python3 > /dev/null 2>&1; then
    echo "Error: python3 could not be found. Please install Python 3 and try again."
else
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "Setup complete! To activate the environment, run:"
    echo "source venv/bin/activate  # On Linux/macOS"
    echo "venv\\Scripts\\activate     # On Windows"
fi
