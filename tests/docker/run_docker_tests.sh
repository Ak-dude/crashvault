#!/bin/bash
# Run crashvault tests in Docker containers across multiple Python versions
#
# Usage:
#   ./run_docker_tests.sh              # Run all Docker tests
#   ./run_docker_tests.sh 3.11         # Run tests on specific Python version
#   ./run_docker_tests.sh --compose    # Use docker-compose for parallel testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}CrashVault Docker Test Runner${NC}"
echo "================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    exit 1
fi

# Parse arguments
USE_COMPOSE=false
PYTHON_VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12" "3.13")

while [[ $# -gt 0 ]]; do
    case $1 in
        --compose)
            USE_COMPOSE=true
            shift
            ;;
        3.*)
            PYTHON_VERSIONS=("$1")
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--compose] [python_version]"
            exit 1
            ;;
    esac
done

if [ "$USE_COMPOSE" = true ]; then
    echo -e "${YELLOW}Running tests with docker-compose (parallel)...${NC}"
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    docker-compose -f docker-compose.test.yml down -v
else
    # Run tests sequentially for each Python version
    FAILED_VERSIONS=()

    for VERSION in "${PYTHON_VERSIONS[@]}"; do
        echo ""
        echo -e "${YELLOW}Testing on Python ${VERSION}...${NC}"
        echo "----------------------------------------"

        IMAGE_TAG="crashvault-test:py${VERSION//./}"

        # Build image
        echo "Building Docker image..."
        if docker build \
            --build-arg PYTHON_VERSION="$VERSION" \
            -t "$IMAGE_TAG" \
            -f "$SCRIPT_DIR/Dockerfile.test" \
            "$PROJECT_ROOT" > /dev/null 2>&1; then
            echo -e "${GREEN}Image built successfully${NC}"
        else
            echo -e "${RED}Failed to build image for Python ${VERSION}${NC}"
            FAILED_VERSIONS+=("$VERSION")
            continue
        fi

        # Run tests
        echo "Running tests..."
        if docker run --rm \
            -e CRASHVAULT_HOME=/tmp/crashvault-test \
            "$IMAGE_TAG" \
            pytest tests/ -v --tb=short -x; then
            echo -e "${GREEN}✓ Python ${VERSION} passed${NC}"
        else
            echo -e "${RED}✗ Python ${VERSION} failed${NC}"
            FAILED_VERSIONS+=("$VERSION")
        fi

        # Cleanup
        docker rmi -f "$IMAGE_TAG" > /dev/null 2>&1 || true
    done

    # Summary
    echo ""
    echo "================================"
    echo "Test Summary"
    echo "================================"

    if [ ${#FAILED_VERSIONS[@]} -eq 0 ]; then
        echo -e "${GREEN}All Python versions passed!${NC}"
        exit 0
    else
        echo -e "${RED}Failed versions: ${FAILED_VERSIONS[*]}${NC}"
        exit 1
    fi
fi