#!/bin/bash
# Set up a single virtual environment for all MCP examples

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  uv venv
else
  echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies for all examples
echo "Installing dependencies for all examples..."

# Install each example's dependencies
for dir in [0-9][0-9]-*; do
  if [ -f "$dir/pyproject.toml" ]; then
    echo "Installing dependencies for $dir..."
    (cd "$dir" && uv pip install -e .)
  fi
done

echo ""
echo "Environment setup complete. To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run an example, navigate to its directory and run the server:"
echo "  cd 00-hello-world"
echo "  python src/server.py"
echo ""
echo "Or use UV directly:"
echo "  cd 00-hello-world"
echo "  uv run --active src/server.py" 