#!/bin/bash
# Linkora v3.5 - Test & Archive SOP Runner
# Usage: ./scripts/test_sop.sh

PROJECT_ROOT=$(pwd)
TIMESTAMP=$(date +"%Y%m%d_%H%M")
ARCHIVE_DIR="$PROJECT_ROOT/docs/qa/archives"
RESULT_FILE="$ARCHIVE_DIR/TEST_RESULT_$TIMESTAMP.log"

# 1. Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

echo "🧪 Starting Linkora v3.5 Compliance Testing..."
echo "Timestamp: $TIMESTAMP"

# 2. Run tests and capture both stdout and stderr
export APP_ENV="test"
export PYTHONPATH="$PROJECT_ROOT/backend"

# Run pytest on the compliance suite
# Using -v for verbose output
pytest backend/tests/test_sa_compliance.py -v > "$RESULT_FILE" 2>&1
TEST_EXIT_CODE=$?

# 3. Handle results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Tests PASSED!"
    echo "Result saved to: $RESULT_FILE"
    
    # Update Manifest
    echo "- [$TIMESTAMP] ✅ PASSED - [View Log](file://$RESULT_FILE)" >> "$PROJECT_ROOT/docs/qa/TEST_HISTORY.md"
else
    echo "❌ Tests FAILED (Exit Code: $TEST_EXIT_CODE)"
    echo "Check error details in: $RESULT_FILE"
    
    # Update Manifest
    echo "- [$TIMESTAMP] ❌ FAILED - [View Log](file://$RESULT_FILE)" >> "$PROJECT_ROOT/docs/qa/TEST_HISTORY.md"
fi

# 4. Final summary for CLI
tail -n 5 "$RESULT_FILE"

exit $TEST_EXIT_CODE
