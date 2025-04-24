#!/bin/bash
# MCP Architecture Demo Launcher
# This script runs the MCP architecture demonstration

# Stop running processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Set up color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}     MCP Architecture Demo Launcher    ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed${NC}"
    exit 1
fi

# Check if the script exists
SCRIPT_PATH="$(dirname "$0")/standalone_demo.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}Error: Demo script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# Make sure the parent directory is in PYTHONPATH
export PYTHONPATH="$(dirname $(dirname "$0")):$PYTHONPATH"

echo -e "${GREEN}Starting MCP Architecture Demo...${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""

# Run the demo
python "$SCRIPT_PATH"

# Check exit status
STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}Demo completed successfully${NC}"
elif [ $STATUS -eq 130 ]; then
    echo -e "${YELLOW}Demo was interrupted by user${NC}"
else
    echo -e "${RED}Demo exited with error code $STATUS${NC}"
fi

echo -e "${BLUE}=======================================${NC}"
echo "Thank you for trying the MCP architecture demo!"
echo -e "${BLUE}=======================================${NC}" 