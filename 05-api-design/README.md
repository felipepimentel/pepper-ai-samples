# API Design Assistant MCP Server

This MCP server helps with API design, validation, and best practices. It provides tools for validating OpenAPI specifications, suggesting RESTful endpoints, generating data models, and analyzing API design patterns.

## Features

1. OpenAPI Specification Validation
   - Validate OpenAPI/Swagger specs
   - Check for compliance with standards
   - Identify potential issues

2. RESTful Endpoint Suggestions
   - Generate endpoint suggestions based on resources
   - Follow REST best practices
   - Include common CRUD operations

3. Data Model Generation
   - Generate code models from OpenAPI specs
   - Support multiple programming languages
   - Type-safe model generation

4. API Design Analysis
   - Check for common API design issues
   - Suggest improvements
   - Score API design quality

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## Usage Examples

1. Validate OpenAPI Specification
```python
result = await client.call_tool("validate_openapi", {
    "spec": {
        "openapi": "3.0.0",
        "info": {"title": "My API", "version": "1.0.0"},
        "paths": {...}
    }
})
```

2. Get Endpoint Suggestions
```python
result = await client.call_tool("suggest_endpoints", {
    "resource": "users",
    "actions": ["list", "create", "get", "update", "delete"]
})
```

3. Generate Data Models
```python
result = await client.call_tool("generate_models", {
    "spec": {
        "openapi": "3.0.0",
        "components": {
            "schemas": {...}
        }
    }
})
```

4. Analyze API Design
```python
result = await client.call_tool("analyze_api_design", {
    "spec": {
        "openapi": "3.0.0",
        "paths": {...}
    }
})
```

## Example Questions

1. API Design
   - "Suggest endpoints for a user management API"
   - "What's the best way to version this API?"
   - "How should I structure this resource hierarchy?"

2. Validation
   - "Is this OpenAPI spec valid?"
   - "What issues exist in my API design?"
   - "Are there any security concerns in this spec?"

3. Best Practices
   - "How can I improve my API's consistency?"
   - "What's the recommended way to handle errors?"
   - "Should I use query parameters or path parameters here?"

4. Code Generation
   - "Generate Python models for this API spec"
   - "What's the best way to implement these endpoints?"
   - "How should I structure the response objects?"

## HTTP Endpoints

```bash
# Validate OpenAPI spec
POST /validate
Content-Type: application/json
{
    "spec": {...}
}

# Get endpoint suggestions
POST /suggest
Content-Type: application/json
{
    "resource": "users",
    "actions": ["list", "create"]
}

# Generate models
POST /generate
Content-Type: application/json
{
    "spec": {...}
}

# Analyze API design
POST /analyze
Content-Type: application/json
{
    "spec": {...}
}
``` 