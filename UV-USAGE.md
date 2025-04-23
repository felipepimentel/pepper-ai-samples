# Using UV with MCP and A2A Examples

This project standardizes on [UV](https://github.com/astral-sh/uv) for Python package management and script execution. UV offers significantly faster dependency resolution and installation compared to pip.

## Installation

Install UV by following the instructions at https://github.com/astral-sh/uv

```bash
# Install UV with the official installer
curl -sSf https://astral.sh/uv/install.sh | bash
```

## Creating Virtual Environments

Create virtual environments using UV:

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# OR
# .venv\Scripts\activate   # Windows
```

## Installing Dependencies

Install project dependencies using UV:

```bash
# Install from pyproject.toml
uv sync

# OR

# Install development dependencies
uv pip install -e ".[dev]"
```

## Running Examples

All examples in this project have been updated to work with UV directly:

```bash
# Navigate to an example directory
cd mcp-examples/00-hello-world

# Run the server
uv run server.py
```

## Development Tasks

UV simplifies common development tasks:

```bash
# Add a production dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest

# Lock dependencies
uv lock

# Run tests
uv run -m pytest
```

## Notes for Contributors

When contributing to this project:

1. The `PepperFastMCP` class now handles the proper execution with UV compatibility internally. Simply use:

```python
if __name__ == "__main__":
    mcp.run()
```

2. For cleanup operations, use a try-finally block:

```python
if __name__ == "__main__":
    try:
        mcp.run()
    finally:
        # Your cleanup code here
        cleanup_resources()
```

3. Always lock dependencies with `uv lock` to ensure consistent environments
4. Document the UV usage in your example's README.md

## Migrating Examples

If you find examples that still use a custom server.py implementation with direct uvicorn+asyncio calls, please simplify them to just use `mcp.run()`. 