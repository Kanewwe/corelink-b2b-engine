#!/bin/bash

# Linkora Backend Test Runner for macOS/Linux
# Usage: ./scripts/test.sh

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧪 Running Linkora Backend Unit Tests (macOS)...${NC}"

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

if [ ! -d "$PROJECT_ROOT/backend" ]; then
    echo -e "${RED}Error: Must run from project root or scripts directory.${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# Add backend to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/backend"
# Set APP_ENV to test (allows database.py to use SQLite fallback)
export APP_ENV="test"
# Ensure DATABASE_URL is UNSET for full SQLite verification
unset DATABASE_URL

# Run pytest
# Using python3 specifically for macOS convention
python3 -m pytest backend/tests -v

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Tests failed. Please check the output above.${NC}"
    exit 1
fi
