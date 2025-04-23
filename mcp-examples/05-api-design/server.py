#!/usr/bin/env python3
"""API Design Assistant MCP Server."""

from typing import Dict, List, Optional

from datamodel_code_generator import InputFileType, generate
from fastapi import FastAPI
from openapi_spec_validator import validate_spec
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel


class APISpec(BaseModel):
    """OpenAPI specification model."""

    spec: Dict
    version: str = "3.0.0"


class EndpointSuggestion(BaseModel):
    """Endpoint suggestion model."""

    path: str
    method: str
    description: str
    parameters: Optional[List[Dict]] = None
    responses: Optional[Dict] = None


# Initialize MCP server
mcp = PepperFastMCP(
    "API Design Assistant",
    description="Assists with API design, validation, and best practices",
)


@mcp.tool()
async def validate_openapi(spec: APISpec) -> Dict:
    """Validate OpenAPI specification."""
    try:
        validate_spec(spec.spec)
        return {"valid": True, "errors": None}
    except Exception as e:
        return {"valid": False, "errors": str(e)}


@mcp.tool()
async def suggest_endpoints(
    resource: str, actions: List[str]
) -> List[EndpointSuggestion]:
    """Suggest RESTful endpoints for a resource."""
    suggestions = []
    base_path = f"/{resource.lower()}"

    common_patterns = {
        "list": {"method": "GET", "path": base_path},
        "create": {"method": "POST", "path": base_path},
        "get": {"method": "GET", "path": f"{base_path}/{{id}}"},
        "update": {"method": "PUT", "path": f"{base_path}/{{id}}"},
        "delete": {"method": "DELETE", "path": f"{base_path}/{{id}}"},
        "patch": {"method": "PATCH", "path": f"{base_path}/{{id}}"},
    }

    for action in actions:
        if action in common_patterns:
            pattern = common_patterns[action]
            suggestions.append(
                EndpointSuggestion(
                    path=pattern["path"],
                    method=pattern["method"],
                    description=f"{action.capitalize()} {resource}",
                    parameters=[{"name": "id", "in": "path"}]
                    if "id" in pattern["path"]
                    else None,
                )
            )

    return suggestions


@mcp.tool()
async def generate_models(spec: APISpec) -> Dict[str, str]:
    """Generate data models from OpenAPI spec."""
    try:
        output = generate(
            spec.spec, input_file_type=InputFileType.OpenAPI, output="models.py"
        )
        return {"success": True, "models": output}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_api_design(spec: APISpec) -> Dict:
    """Analyze API design for best practices."""
    analysis = {"issues": [], "suggestions": [], "score": 100}

    # Check for common issues
    if "paths" in spec.spec:
        for path, methods in spec.spec["paths"].items():
            # Check if path uses versioning
            if not path.startswith("/v"):
                analysis["suggestions"].append(
                    f"Consider adding API versioning to path: {path}"
                )
                analysis["score"] -= 5

            # Check for proper error responses
            for method, details in methods.items():
                if "responses" in details:
                    if "400" not in details["responses"]:
                        analysis["issues"].append(
                            f"Missing 400 error response in {method} {path}"
                        )
                        analysis["score"] -= 3
                    if "500" not in details["responses"]:
                        analysis["issues"].append(
                            f"Missing 500 error response in {method} {path}"
                        )
                        analysis["score"] -= 3

    return analysis


# Add FastAPI integration
app = FastAPI(title="API Design Assistant")
mcp.add_web_client()

if __name__ == "__main__":
    try:
        import uvicorn
        mcp.run()
    finally:
        # Cleanup code 
        pass

