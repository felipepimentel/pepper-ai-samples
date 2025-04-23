# Code Review MCP Server

This MCP server provides automated code review capabilities, helping developers identify issues, enforce best practices, and improve code quality. It combines static analysis, style checking, security scanning, and best practice recommendations.

## Features

1. Static Analysis
   - Type checking
   - Code complexity metrics
   - Dead code detection
   - Dependency analysis

2. Style Checking
   - PEP 8 compliance
   - Code formatting
   - Documentation coverage
   - Naming conventions

3. Security Scanning
   - Vulnerability detection
   - Dependency auditing
   - Secret detection
   - OWASP compliance

4. Best Practices
   - Design pattern suggestions
   - Performance improvements
   - Error handling review
   - Testing coverage analysis

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## Usage Examples

1. Code Analysis
```python
result = await client.call_tool("analyze_code", {
    "file_path": "app/main.py",
    "checks": ["style", "security", "complexity"]
})
```

2. Security Scan
```python
result = await client.call_tool("security_scan", {
    "directory": "app/",
    "include_deps": True
})
```

3. Best Practice Review
```python
result = await client.call_tool("review_practices", {
    "file_path": "app/models.py",
    "focus": ["patterns", "performance"]
})
```

4. Documentation Check
```python
result = await client.call_tool("check_docs", {
    "directory": "app/",
    "min_coverage": 80
})
```

## Example Questions

1. Code Quality
   - "Review this file for potential issues"
   - "Check if this code follows PEP 8"
   - "Analyze code complexity in this module"

2. Security
   - "Scan this codebase for vulnerabilities"
   - "Check for exposed secrets or credentials"
   - "Audit dependencies for security issues"

3. Best Practices
   - "Suggest improvements for this function"
   - "Review error handling practices"
   - "Check for anti-patterns in this code"

4. Documentation
   - "Check documentation coverage"
   - "Review docstring quality"
   - "Suggest documentation improvements"

## HTTP Endpoints

```bash
# Analyze code
POST /analyze
Content-Type: application/json
{
    "file_path": "app/main.py",
    "checks": ["style", "security", "complexity"]
}

# Security scan
POST /security
Content-Type: application/json
{
    "directory": "app/",
    "include_deps": true
}

# Review practices
POST /review
Content-Type: application/json
{
    "file_path": "app/models.py",
    "focus": ["patterns", "performance"]
}

# Check documentation
POST /docs
Content-Type: application/json
{
    "directory": "app/",
    "min_coverage": 80
} 