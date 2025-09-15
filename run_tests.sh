#!/bin/bash
# run_tests.sh - Fast test runner with coverage for DocPivot

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}DocPivot Test Suite${NC}"
echo -e "${YELLOW}================================${NC}"

START=$(date +%s)

# Run tests with coverage, skip covered lines in report
echo -e "\n${GREEN}Running tests with coverage...${NC}\n"

pytest tests/ \
    --cov=docpivot \
    --cov-report=term:skip-covered \
    --cov-report=term-missing:skip-covered \
    --tb=short \
    -q \
    || TEST_FAILED=1

END=$(date +%s)
RUNTIME=$((END-START))

echo ""
echo -e "${YELLOW}================================${NC}"

if [ -z "$TEST_FAILED" ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo -e "Test runtime: ${RUNTIME}s (Target: <120s)"

# Check if tests are running fast enough
if [ $RUNTIME -gt 120 ]; then
    echo -e "${RED}❌ Tests exceeded 120s limit!${NC}"
    echo -e "${YELLOW}Consider removing slow tests or using pytest-xdist for parallel execution${NC}"
    exit 1
elif [ $RUNTIME -gt 60 ]; then
    echo -e "${YELLOW}⚠️  Tests taking ${RUNTIME}s - approaching 120s limit${NC}"
else
    echo -e "${GREEN}✓ Tests completed quickly (${RUNTIME}s)${NC}"
fi

echo -e "${YELLOW}================================${NC}"

# Exit with failure if tests failed
if [ ! -z "$TEST_FAILED" ]; then
    exit 1
fi