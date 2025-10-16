#!/bin/bash
# Convenience script to run the Product Ideation System

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "Error: Please run this script from the project root directory"
    echo "Current directory: $(pwd)"
    echo "Expected files: src/main.py, config/settings.yaml"
    exit 1
fi

# Run the main module with all arguments passed through
uv run python -m src.main "$@"
