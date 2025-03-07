#!/bin/bash

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
if [ -d ".venv" ]; then
    echo "Virtual environment already exists. Activating..."
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies if they are not installed
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found. Please create it first."
else
# Check if the --verbose flag is passed
    VERBOSE=false
    for arg in "$@"; do
        if [[ "$arg" == "--verbose" ]]; then
            VERBOSE=true
            break
        fi
    done

    echo "Installing dependencies..."
    if [ "$VERBOSE" = true ]; then
        $PIP_CMD install -r requirements.txt &
    else
        $PIP_CMD install -r requirements.txt > /dev/null 2>&1 &
        # Get the process ID
        PID=$!

        # Loading animation
        SPINNER="/-\|"
        i=0

        # Show a loading spinner while pip install is running
        while kill -0 $PID 2>/dev/null; do
            printf "\rRunning installation... %s" "${SPINNER:i++%${#SPINNER}:1}"
            sleep 0.2
        done

        # Clear the spinner line
        printf "\r\033[K"
    fi

    wait $PID
    INSTALL_STATUS=$?

    # Check exit status of pip install
    if [ $INSTALL_STATUS -eq 0 ]; then
        echo "Installation successful!"
    else
        echo "Installation failed! Use --verbose flag to see the output."
    fi

fi


