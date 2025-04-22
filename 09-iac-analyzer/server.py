#!/usr/bin/env python3
"""Infrastructure as Code Analyzer MCP Server."""

from typing import Dict, Optional

import hcl2
from ansible_lint import rules as ansible_rules
from cfnlint.core import get_rules, get_template_rules
from checkov.main import Runner as CheckovRunner
from fastapi import FastAPI
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel


class IaCFile(BaseModel):
    """Infrastructure as Code file model."""

    path: str
    type: str  # terraform, cloudformation, ansible
    content: str


class SecurityCheck(BaseModel):
    """Security check result model."""

    resource: str
    check_id: str
    severity: str
    message: str
    fix_suggestion: Optional[str] = None


# Initialize MCP server
mcp = PepperFastMCP(
    "IaC Analyzer",
    description="Analyzes Infrastructure as Code for best practices and security",
)


@mcp.tool()
async def analyze_terraform(file: IaCFile) -> Dict:
    """Analyze Terraform configuration files."""
    try:
        # Parse HCL
        with open(file.path, "r") as f:
            tf_dict = hcl2.load(f)

        analysis = {"resources": [], "variables": [], "outputs": [], "issues": []}

        # Analyze resources
        if "resource" in tf_dict:
            for resource_type, instances in tf_dict["resource"].items():
                for instance in instances:
                    analysis["resources"].append(
                        {
                            "type": resource_type,
                            "name": list(instance.keys())[0],
                            "config": instance[list(instance.keys())[0]],
                        }
                    )

        # Check for security issues
        runner = CheckovRunner()
        report = runner.run(files=[file.path])

        for record in report.failed_checks:
            analysis["issues"].append(
                {
                    "severity": record.severity,
                    "check_id": record.check_id,
                    "message": record.check_name,
                    "resource": record.resource,
                }
            )

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_cloudformation(file: IaCFile) -> Dict:
    """Analyze CloudFormation templates."""
    try:
        analysis = {"resources": [], "parameters": [], "outputs": [], "issues": []}

        # Get CloudFormation rules
        rules = get_rules()
        template_rules = get_template_rules()

        # Run linting
        matches = []
        for rule in rules:
            matches.extend(rule.matchall(file.content))

        # Process results
        for match in matches:
            analysis["issues"].append(
                {
                    "rule": match.rule.id,
                    "message": match.message,
                    "severity": match.rule.severity,
                    "location": match.location,
                }
            )

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_ansible(file: IaCFile) -> Dict:
    """Analyze Ansible playbooks."""
    try:
        analysis = {"tasks": [], "roles": [], "variables": [], "issues": []}

        # Run ansible-lint
        for rule in ansible_rules.RulesCollection():
            result = rule.matchplay(file.content)
            if result:
                analysis["issues"].append(
                    {
                        "rule_id": rule.id,
                        "description": rule.description,
                        "severity": rule.severity,
                        "match": str(result),
                    }
                )

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def suggest_improvements(file: IaCFile) -> Dict:
    """Suggest improvements for IaC files."""
    try:
        suggestions = []

        if file.type == "terraform":
            analysis = await analyze_terraform(file)
            if analysis["success"]:
                # Check for common improvements
                for resource in analysis["analysis"]["resources"]:
                    # Check for missing tags
                    if "tags" not in resource["config"]:
                        suggestions.append(
                            {
                                "type": "best_practice",
                                "resource": resource["name"],
                                "suggestion": "Add tags for better resource management",
                            }
                        )

                    # Check for hardcoded values
                    for key, value in resource["config"].items():
                        if isinstance(value, str) and not value.startswith("${"):
                            suggestions.append(
                                {
                                    "type": "improvement",
                                    "resource": resource["name"],
                                    "suggestion": f"Consider using variables for '{key}' instead of hardcoded values",
                                }
                            )

        elif file.type == "cloudformation":
            analysis = await analyze_cloudformation(file)
            if analysis["success"]:
                for issue in analysis["analysis"]["issues"]:
                    suggestions.append(
                        {
                            "type": "fix",
                            "resource": issue["location"],
                            "suggestion": f"Fix {issue['rule']}: {issue['message']}",
                        }
                    )

        elif file.type == "ansible":
            analysis = await analyze_ansible(file)
            if analysis["success"]:
                for issue in analysis["analysis"]["issues"]:
                    suggestions.append(
                        {
                            "type": "improvement",
                            "rule": issue["rule_id"],
                            "suggestion": issue["description"],
                        }
                    )

        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add FastAPI integration
app = FastAPI(title="IaC Analyzer")
mcp.add_web_client()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8009, reload=True)
