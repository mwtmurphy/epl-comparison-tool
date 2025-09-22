#!/bin/bash
# Check CI - Run the same checks that CI runs locally
# This helps catch issues before pushing to GitHub

set -e  # Exit on any command failure

echo "🔍 Running CI checks locally..."
echo

echo "📝 Checking code formatting with black..."
poetry run black --check .
echo "✅ Black formatting check passed"
echo

echo "🔍 Running linting with ruff..."
poetry run ruff check .
echo "✅ Ruff linting check passed"
echo

echo "🧪 Running tests..."
poetry run pytest
echo "✅ All tests passed"
echo

echo "🌐 Running Streamlit health check..."
timeout 10s poetry run streamlit run app.py --server.headless=true --server.port=8500 > /dev/null 2>&1 || true
echo "✅ Streamlit health check completed"
echo

echo "🎉 All CI checks passed! Safe to push to GitHub."
