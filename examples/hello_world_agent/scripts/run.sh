#!/bin/bash
WORKING_DIR=$(pwd)
echo "Working directory: $WORKING_DIR"

# Check if 'python' or 'python3' is available
if command -v python &> /dev/null; then
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "Error: Python is not installed. Please install Python and try again."
    exit 1
fi

# Check if 'pip' or 'pip3' is available
if command -v pip &> /dev/null; then
    PIP_CMD=pip
elif command -v pip3 &> /dev/null; then
    PIP_CMD=pip3
else
    echo "Error: pip is not installed. Please install pip and try again."
    exit 1
fi

# Check if the virtual environment directory exists
if [ -d "$WORKING_DIR/.venv" ]; then
    echo "Virtual environment already exists. Activating..."
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $WORKING_DIR/.venv
fi

# Activate the virtual environment
source $WORKING_DIR/.venv/bin/activate

# Run the Python script
$PYTHON_CMD main.py

# Deactivate the virtual environment
deactivate