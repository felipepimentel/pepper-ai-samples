#!/usr/bin/env python3
"""Architecture Analysis MCP Server."""

import os
from typing import Dict, List, Optional

import astroid
import networkx as nx
import radon.complexity as radon_cc
from fastapi import FastAPI
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel
from pylint import lint


class AnalysisRequest(BaseModel):
    """Analysis request model."""

    target_path: str
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class DependencyNode(BaseModel):
    """Dependency graph node model."""

    name: str
    type: str
    dependencies: List[str]


# Initialize MCP server
mcp = PepperFastMCP(
    "Architecture Analyzer",
    description="Analyzes code architecture and suggests improvements",
)


@mcp.tool()
async def analyze_dependencies(request: AnalysisRequest) -> Dict:
    """Analyze module dependencies and create a dependency graph."""
    try:
        # Create dependency graph
        graph = nx.DiGraph()

        # Parse Python files and build dependency graph
        for root, _, files in os.walk(request.target_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    module = astroid.parse(open(filepath).read())

                    # Add node for current module
                    module_name = os.path.splitext(file)[0]
                    graph.add_node(module_name)

                    # Add edges for imports
                    for import_node in module.nodes_of_class(astroid.Import):
                        for name, _ in import_node.names:
                            graph.add_edge(module_name, name)

        # Calculate metrics
        metrics = {
            "cyclic_dependencies": list(nx.simple_cycles(graph)),
            "centrality": nx.degree_centrality(graph),
            "coupling_score": len(graph.edges()) / len(graph.nodes())
            if graph.nodes()
            else 0,
        }

        return {"success": True, "graph": nx.node_link_data(graph), "metrics": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_code_quality(request: AnalysisRequest) -> Dict:
    """Analyze code quality using various metrics."""
    try:
        results = {"complexity": [], "maintainability": [], "code_smells": []}

        for root, _, files in os.walk(request.target_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)

                    # Calculate cyclomatic complexity
                    with open(filepath) as f:
                        code = f.read()
                        complexity = radon_cc.cc_visit(code)
                        results["complexity"].append(
                            {
                                "file": filepath,
                                "complexity": [c._asdict() for c in complexity],
                            }
                        )

                    # Run pylint for code quality
                    pylint_output = lint.Run([filepath], do_exit=False)
                    results["code_smells"].extend(
                        [
                            {
                                "file": filepath,
                                "line": msg.line,
                                "message": msg.msg,
                                "type": msg.symbol,
                            }
                            for msg in pylint_output.linter.reporter.messages
                        ]
                    )

        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_architecture_patterns(request: AnalysisRequest) -> Dict:
    """Identify and analyze architectural patterns in the codebase."""
    try:
        patterns = {
            "mvc": {"found": False, "confidence": 0},
            "repository": {"found": False, "confidence": 0},
            "factory": {"found": False, "confidence": 0},
            "singleton": {"found": False, "confidence": 0},
        }

        for root, _, files in os.walk(request.target_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    module = astroid.parse(open(filepath).read())

                    # Check for MVC pattern
                    if any(
                        c.name.endswith("Controller")
                        for c in module.nodes_of_class(astroid.ClassDef)
                    ):
                        patterns["mvc"]["found"] = True
                        patterns["mvc"]["confidence"] += 0.3

                    # Check for Repository pattern
                    if any(
                        c.name.endswith("Repository")
                        for c in module.nodes_of_class(astroid.ClassDef)
                    ):
                        patterns["repository"]["found"] = True
                        patterns["repository"]["confidence"] += 0.3

                    # Check for Factory pattern
                    if any(
                        c.name.endswith("Factory")
                        for c in module.nodes_of_class(astroid.ClassDef)
                    ):
                        patterns["factory"]["found"] = True
                        patterns["factory"]["confidence"] += 0.3

                    # Check for Singleton pattern
                    for cls in module.nodes_of_class(astroid.ClassDef):
                        if any(m.name == "__new__" for m in cls.methods()):
                            patterns["singleton"]["found"] = True
                            patterns["singleton"]["confidence"] += 0.3

        return {"success": True, "patterns": patterns}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def suggest_improvements(request: AnalysisRequest) -> Dict:
    """Suggest architectural improvements based on analysis."""
    try:
        # Gather all analysis results
        dependencies = await analyze_dependencies(request)
        code_quality = await analyze_code_quality(request)
        patterns = await analyze_architecture_patterns(request)

        suggestions = []

        # Check for cyclic dependencies
        if dependencies["success"] and dependencies["metrics"]["cyclic_dependencies"]:
            suggestions.append(
                {
                    "type": "critical",
                    "issue": "Cyclic dependencies detected",
                    "suggestion": "Consider breaking cyclic dependencies using dependency inversion",
                }
            )

        # Check complexity
        if code_quality["success"]:
            complex_functions = [
                c
                for result in code_quality["results"]["complexity"]
                for c in result["complexity"]
                if c["complexity"] > 10
            ]
            if complex_functions:
                suggestions.append(
                    {
                        "type": "warning",
                        "issue": f"Found {len(complex_functions)} complex functions",
                        "suggestion": "Consider breaking down complex functions into smaller, more manageable pieces",
                    }
                )

        # Check architectural patterns
        if patterns["success"]:
            if not any(p["found"] for p in patterns["patterns"].values()):
                suggestions.append(
                    {
                        "type": "info",
                        "issue": "No clear architectural patterns detected",
                        "suggestion": "Consider implementing well-known patterns like MVC or Repository pattern",
                    }
                )

        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add FastAPI integration
app = FastAPI(title="Architecture Analyzer")
mcp.add_web_client()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8007, reload=True)
