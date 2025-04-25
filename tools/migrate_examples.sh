#!/bin/bash

# Script to migrate examples to new structure

# Create main directories if they don't exist
mkdir -p examples/{mcp,a2a,integrated}

# Function to migrate an example
migrate_example() {
    local src=$1
    local dst=$2
    
    echo "Migrating $src to $dst"
    
    # Create destination directory
    mkdir -p "$dst"
    
    # Move files
    mv "$src"/* "$dst"/ 2>/dev/null || true
    
    # Create src directory if it doesn't exist
    mkdir -p "$dst/src"
    
    # Move server.py to src if it exists at root
    if [ -f "$dst/server.py" ]; then
        mv "$dst/server.py" "$dst/src/"
    fi
    
    # Ensure README exists
    if [ ! -f "$dst/README.md" ]; then
        echo "# $(basename "$dst")" > "$dst/README.md"
        echo "" >> "$dst/README.md"
        echo "## Concept" >> "$dst/README.md"
        echo "TODO: Add concept description" >> "$dst/README.md"
        echo "" >> "$dst/README.md"
        echo "## Prerequisites" >> "$dst/README.md"
        echo "TODO: Add prerequisites" >> "$dst/README.md"
        echo "" >> "$dst/README.md"
        echo "## Tutorial" >> "$dst/README.md"
        echo "TODO: Add step-by-step tutorial" >> "$dst/README.md"
        echo "" >> "$dst/README.md"
        echo "## Exercises" >> "$dst/README.md"
        echo "TODO: Add suggested exercises" >> "$dst/README.md"
    fi
    
    # Ensure pyproject.toml exists
    if [ ! -f "$dst/pyproject.toml" ]; then
        echo "[build-system]" > "$dst/pyproject.toml"
        echo "requires = [\"hatchling\"]" >> "$dst/pyproject.toml"
        echo "build-backend = \"hatchling.build\"" >> "$dst/pyproject.toml"
        echo "" >> "$dst/pyproject.toml"
        echo "[project]" >> "$dst/pyproject.toml"
        echo "name = \"$(basename "$dst")\"" >> "$dst/pyproject.toml"
        echo "version = \"0.1.0\"" >> "$dst/pyproject.toml"
        echo "description = \"$(basename "$dst") example\"" >> "$dst/pyproject.toml"
    fi
}

# Migrate MCP examples
for example in mcp-examples/*; do
    if [ -d "$example" ]; then
        name=$(basename "$example")
        migrate_example "$example" "examples/mcp/$name"
    fi
done

# Migrate A2A examples
for example in a2a-examples/*; do
    if [ -d "$example" ]; then
        name=$(basename "$example")
        migrate_example "$example" "examples/a2a/$name"
    fi
done

# Migrate integrated examples
for example in a2a-mcp-examples/*; do
    if [ -d "$example" ]; then
        name=$(basename "$example")
        migrate_example "$example" "examples/integrated/$name"
    fi
done

echo "Migration complete!" 