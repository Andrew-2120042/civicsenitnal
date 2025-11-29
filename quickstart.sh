#!/bin/bash

# CivicSentinel Quick Start Script
# This script helps you get up and running quickly

set -e

echo "======================================"
echo "CivicSentinel Quick Start"
echo "======================================"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed."
    echo "Please install Poetry first: https://python-poetry.org/docs/#installation"
    echo ""
    echo "Quick install:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✓ Poetry is installed"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $PYTHON_VERSION"

# Install dependencies
echo ""
echo "Installing dependencies..."
poetry install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
poetry run python init_db.py

echo ""
echo "======================================"
echo "Setup Complete! 🎉"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the API server:"
echo "   poetry run uvicorn app.main:app --reload"
echo ""
echo "2. In another terminal, run the test script:"
echo "   poetry run python test_api.py"
echo ""
echo "3. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Test with curl:"
echo "   curl -X GET http://localhost:8000/api/v1/health"
echo ""
echo "Happy coding! 🚀"
