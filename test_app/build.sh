#!/bin/bash

# Exit on error
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Building Docker image for test app..."
docker build -t daystar-test-app:latest .

echo "Build complete."
