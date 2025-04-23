# Documentation Writer MCP Server

This MCP server helps create and maintain high-quality documentation in multiple languages, with support for various formats and styles. It combines natural language processing with code analysis to generate comprehensive documentation.

## Features

1. Multi-language Documentation
   - Generate docs in multiple languages
   - Maintain consistent terminology
   - Cultural adaptation of examples
   - Region-specific formatting

2. Visual Documentation
   - Generate architecture diagrams
   - Create sequence diagrams from code
   - Build user flow diagrams
   - Export diagrams in multiple formats

3. Code Documentation
   - Generate docstrings and comments
   - Create API documentation
   - Write usage examples
   - Generate test documentation

4. Rich Content Creation
   - Write technical blog posts
   - Create presentation slides
   - Generate video scripts
   - Write release notes

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## Usage Examples

1. Generate Documentation
```python
result = await client.call_tool("generate_docs", {
    "source_file": "app/main.py",
    "languages": ["en", "pt", "es"],
    "format": "markdown"
})
```

2. Create Diagrams
```python
result = await client.call_tool("create_diagram", {
    "source_dir": "app/",
    "diagram_type": "architecture",
    "output_format": "svg"
})
```

3. Write Blog Post
```python
result = await client.call_tool("write_blog", {
    "topic": "New Features in v2.0",
    "code_changes": ["app/features/", "app/api/"],
    "target_audience": "developers"
})
```

4. Generate Release Notes
```python
result = await client.call_tool("generate_release_notes", {
    "version": "2.0.0",
    "changes": ["commits", "issues"],
    "format": "markdown"
})
```

## Example Questions

1. Documentation Generation
   - "Generate API documentation for this module"
   - "Create a user guide for this feature"
   - "Write installation instructions in Spanish"

2. Visual Content
   - "Create an architecture diagram for this system"
   - "Generate a sequence diagram for this workflow"
   - "Make a flowchart for this algorithm"

3. Content Creation
   - "Write a blog post about our new feature"
   - "Create slides for a technical presentation"
   - "Generate a script for a demo video"

4. Maintenance
   - "Update docs to reflect recent changes"
   - "Find outdated documentation"
   - "Suggest improvements for clarity"

## HTTP Endpoints

```bash
# Generate documentation
POST /docs/generate
Content-Type: application/json
{
    "source": "app/main.py",
    "languages": ["en", "pt", "es"]
}

# Create diagram
POST /docs/diagram
Content-Type: application/json
{
    "source": "app/",
    "type": "architecture"
}

# Write content
POST /docs/content
Content-Type: application/json
{
    "type": "blog",
    "topic": "New Features"
}

# Generate release notes
POST /docs/release
Content-Type: application/json
{
    "version": "2.0.0",
    "format": "markdown"
} 