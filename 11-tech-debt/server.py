#!/usr/bin/env python3
"""Technical Debt Analyzer MCP Server."""

from typing import Dict, List, Optional

import lizard
import radon.complexity as radon_cc
from fastapi import FastAPI
from git import Repo
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel


class CodeAnalysisRequest(BaseModel):
    """Code analysis request model."""

    repo_path: str
    file_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class TechDebtItem(BaseModel):
    """Technical debt item model."""

    file: str
    line: Optional[int]
    type: str
    severity: str
    description: str
    effort: str
    suggestion: str


# Initialize MCP server
mcp = PepperFastMCP(
    "Technical Debt Analyzer",
    description="Analyzes and tracks technical debt in codebases",
)


@mcp.tool()
async def analyze_code_quality(request: CodeAnalysisRequest) -> Dict:
    """Analyze code quality using multiple metrics."""
    try:
        analysis = {"complexity": [], "maintainability": [], "code_smells": []}

        # Use lizard for complexity analysis
        file_analyzer = lizard.analyze(
            paths=[request.repo_path], exclude_pattern=request.exclude_patterns
        )

        for file_info in file_analyzer:
            # Analyze function complexity
            for func in file_info.function_list:
                if func.cyclomatic_complexity > 10:
                    analysis["complexity"].append(
                        {
                            "file": file_info.filename,
                            "function": func.name,
                            "complexity": func.cyclomatic_complexity,
                            "lines": func.length,
                            "tokens": func.token_count,
                        }
                    )

        # Use radon for maintainability index
        for file_path in file_analyzer.filenames:
            try:
                with open(file_path) as f:
                    code = f.read()
                    mi_visit = radon_cc.mi_visit(code, multi=True)
                    if mi_visit < 65:  # Low maintainability
                        analysis["maintainability"].append(
                            {
                                "file": file_path,
                                "maintainability_index": mi_visit,
                                "status": "poor" if mi_visit < 50 else "warning",
                            }
                        )
            except Exception:
                continue

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_git_history(request: CodeAnalysisRequest) -> Dict:
    """Analyze git history for technical debt indicators."""
    try:
        repo = Repo(request.repo_path)
        analysis = {"hotspots": [], "churn": [], "ownership": []}

        # Analyze file changes
        for commit in repo.iter_commits():
            for file in commit.stats.files:
                if any(
                    file.endswith(pat)
                    for pat in request.file_patterns or [".py", ".js", ".java"]
                ):
                    analysis["churn"].append(
                        {
                            "file": file,
                            "changes": commit.stats.files[file]["lines"],
                            "date": commit.committed_datetime.isoformat(),
                        }
                    )

        # Identify hotspots (frequently changed files)
        file_changes = {}
        for churn in analysis["churn"]:
            file = churn["file"]
            file_changes[file] = file_changes.get(file, 0) + churn["changes"]

        analysis["hotspots"] = [
            {"file": file, "changes": changes}
            for file, changes in sorted(
                file_changes.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

        # Analyze code ownership
        ownership = {}
        for commit in repo.iter_commits():
            for file in commit.stats.files:
                if file not in ownership:
                    ownership[file] = {}
                author = commit.author.email
                ownership[file][author] = ownership[file].get(author, 0) + 1

        analysis["ownership"] = [
            {
                "file": file,
                "authors": len(authors),
                "primary_author": max(authors.items(), key=lambda x: x[1])[0],
            }
            for file, authors in ownership.items()
        ]

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_dependencies(request: CodeAnalysisRequest) -> Dict:
    """Analyze project dependencies for potential issues."""
    try:
        analysis = {"outdated": [], "security": [], "compatibility": []}

        # Check Python dependencies
        try:
            import pkg_resources

            for dist in pkg_resources.working_set:
                name = dist.key
                version = dist.version
                # Check if package has known security issues
                # This would typically use a security advisory database
                analysis["security"].append(
                    {
                        "package": name,
                        "version": version,
                        "type": "python",
                        "status": "check_needed",
                    }
                )
        except Exception:
            pass

        # Check JavaScript dependencies (if package.json exists)
        package_json = os.path.join(request.repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    for name, version in deps.items():
                        analysis["outdated"].append(
                            {
                                "package": name,
                                "version": version,
                                "type": "node",
                                "status": "check_needed",
                            }
                        )
            except Exception:
                pass

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_debt_report(request: CodeAnalysisRequest) -> Dict:
    """Generate a comprehensive technical debt report."""
    try:
        # Gather all analyses
        code_quality = await analyze_code_quality(request)
        git_history = await analyze_git_history(request)
        dependencies = await analyze_dependencies(request)

        report = {
            "summary": {
                "total_debt_items": 0,
                "critical_items": 0,
                "effort_estimate": "0h",
            },
            "debt_items": [],
            "priorities": [],
            "recommendations": [],
        }

        # Process code quality issues
        if code_quality["success"]:
            for item in code_quality["analysis"]["complexity"]:
                report["debt_items"].append(
                    TechDebtItem(
                        file=item["file"],
                        type="complexity",
                        severity="high" if item["complexity"] > 15 else "medium",
                        description=f"High complexity in function {item['function']}",
                        effort="4h",
                        suggestion="Break down complex function into smaller, more manageable pieces",
                    ).dict()
                )

        # Process git history insights
        if git_history["success"]:
            for hotspot in git_history["analysis"]["hotspots"][:5]:
                report["debt_items"].append(
                    TechDebtItem(
                        file=hotspot["file"],
                        type="churn",
                        severity="medium",
                        description=f"High churn file with {hotspot['changes']} changes",
                        effort="8h",
                        suggestion="Consider refactoring frequently changed code into more stable components",
                    ).dict()
                )

        # Process dependency issues
        if dependencies["success"]:
            for security_item in dependencies["analysis"]["security"]:
                report["debt_items"].append(
                    TechDebtItem(
                        file="requirements.txt",
                        type="security",
                        severity="critical",
                        description=f"Security check needed for {security_item['package']}",
                        effort="2h",
                        suggestion="Update package and verify no breaking changes",
                    ).dict()
                )

        # Calculate summary
        report["summary"]["total_debt_items"] = len(report["debt_items"])
        report["summary"]["critical_items"] = len(
            [item for item in report["debt_items"] if item["severity"] == "critical"]
        )

        # Calculate total effort
        total_hours = sum(
            int(item["effort"].rstrip("h")) for item in report["debt_items"]
        )
        report["summary"]["effort_estimate"] = f"{total_hours}h"

        # Prioritize items
        report["priorities"] = sorted(
            report["debt_items"],
            key=lambda x: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]],
                int(x["effort"].rstrip("h")),
            ),
        )

        # Generate recommendations
        if report["summary"]["critical_items"] > 0:
            report["recommendations"].append("Focus on critical security issues first")

        if any(item["type"] == "complexity" for item in report["debt_items"]):
            report["recommendations"].append(
                "Plan regular refactoring sessions for complex code"
            )

        if any(item["type"] == "churn" for item in report["debt_items"]):
            report["recommendations"].append(
                "Review and stabilize frequently changing components"
            )

        return {"success": True, "report": report}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add FastAPI integration
app = FastAPI(title="Technical Debt Analyzer")
mcp.add_web_client()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8011, reload=True)
