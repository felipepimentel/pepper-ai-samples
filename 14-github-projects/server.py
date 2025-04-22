#!/usr/bin/env python
"""
GitHub Projects Integration MCP Server

This MCP server integrates with GitHub Projects to provide project management
capabilities, analytics, and insights directly in VS Code.
"""

import base64
import io
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from github import Github, GithubException

# Import PepperFastMCP
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.warning(
        "GITHUB_TOKEN environment variable not set. Some features may not work."
    )


# Models
class IssueSearchParams(BaseModel):
    query: str
    sort: Optional[str] = "updated"
    include_metrics: bool = False


class ProjectParams(BaseModel):
    owner: str
    project_number: int
    timeframe: Optional[str] = "last_30_days"


class BoardAnalysisParams(BaseModel):
    board_id: str
    view: Optional[str] = "velocity"
    sprint: Optional[str] = "current"


class TeamMetricsParams(BaseModel):
    team: str
    metrics: List[str] = Field(
        default_factory=lambda: ["pr_velocity", "issue_completion"]
    )
    period: Optional[str] = "last_sprint"


class RecommendationParams(BaseModel):
    context: str
    team: Optional[str] = None
    capacity: Optional[float] = None
    priority: Optional[str] = None
    goals: Optional[List[str]] = None


# Create MCP Server
mcp = PepperFastMCP(
    "GitHub Projects MCP",
    description="Integrates with GitHub Projects for project management and analytics",
)


# GitHub Client
def get_github_client():
    """Returns an authenticated GitHub client."""
    if not GITHUB_TOKEN:
        raise ValueError(
            "GitHub token not provided. Please set GITHUB_TOKEN environment variable."
        )

    return Github(GITHUB_TOKEN)


# Utility functions
def parse_timeframe(timeframe: str) -> tuple[datetime, datetime]:
    """Parse timeframe string to start and end dates."""
    now = datetime.now()

    if timeframe == "last_30_days":
        start_date = now - timedelta(days=30)
    elif timeframe == "last_sprint":
        # Assuming 2-week sprints
        start_date = now - timedelta(days=14)
    elif timeframe == "current_sprint":
        # Assuming 2-week sprints starting on Monday
        days_since_monday = now.weekday()
        days_to_prev_monday = (
            days_since_monday if days_since_monday == 0 else days_since_monday
        )
        start_of_sprint = now - timedelta(days=days_to_prev_monday)
        start_date = start_of_sprint
    elif timeframe == "last_quarter":
        start_date = now - timedelta(days=90)
    else:
        # Default to last 30 days
        start_date = now - timedelta(days=30)

    return start_date, now


async def fetch_graphql(
    query: str, variables: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Fetch data from GitHub GraphQL API."""
    if not GITHUB_TOKEN:
        raise ValueError("GitHub token not provided")

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise ValueError(f"Failed to fetch data: {text}")

            return await response.json()


# Tools
@mcp.tool()
async def search_issues(params: IssueSearchParams) -> Dict[str, Any]:
    """
    Search GitHub issues based on query parameters.

    Args:
        params: Search parameters including query, sort, and metrics options

    Returns:
        Dict with issues and optional metrics
    """
    g = get_github_client()

    try:
        # Execute search query
        issues_results = g.search_issues(params.query, sort=params.sort)

        # Convert to structured data
        issues = []
        for issue in issues_results[:30]:  # Limiting to 30 to avoid rate limits
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": issue.html_url,
                "repository": issue.repository.full_name,
                "labels": [label.name for label in issue.labels],
            }

            if issue.assignee:
                issue_data["assignee"] = issue.assignee.login

            if issue.milestone:
                issue_data["milestone"] = issue.milestone.title

            issues.append(issue_data)

        result = {
            "issues": issues,
            "total_count": issues_results.totalCount,
            "query": params.query,
        }

        # Add metrics if requested
        if params.include_metrics and issues:
            result["metrics"] = {
                "open_issues": len([i for i in issues if i["state"] == "open"]),
                "closed_issues": len([i for i in issues if i["state"] == "closed"]),
                "average_age_days": sum(
                    (
                        datetime.now()
                        - datetime.fromisoformat(i["created_at"].replace("Z", "+00:00"))
                    )
                    for i in issues
                    if i["state"] == "open"
                ).days
                / len(issues),
                "repositories": list(set(i["repository"] for i in issues)),
                "labels_distribution": {},
            }

            # Count label occurrences
            labels_count = {}
            for issue in issues:
                for label in issue["labels"]:
                    labels_count[label] = labels_count.get(label, 0) + 1

            result["metrics"]["labels_distribution"] = labels_count

        return result

    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        return {
            "error": "GitHub API error",
            "message": str(e),
            "issues": [],
            "total_count": 0,
            "query": params.query,
        }
    except Exception as e:
        logger.error(f"Error searching issues: {e}")
        return {
            "error": "Error searching issues",
            "message": str(e),
            "issues": [],
            "total_count": 0,
            "query": params.query,
        }


@mcp.tool()
async def get_project_overview(params: ProjectParams) -> Dict[str, Any]:
    """
    Get an overview of a GitHub Project.

    Args:
        params: Project parameters including owner, project number, and timeframe

    Returns:
        Dict with project overview data
    """
    try:
        # For the GraphQL query to get project data
        project_query = """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) {
              id
              title
              shortDescription
              url
              items(first: 100) {
                nodes {
                  id
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          name
                        }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field {
                          name
                        }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          name
                        }
                      }
                    }
                  }
                  content {
                    ... on Issue {
                      title
                      number
                      repository {
                        name
                      }
                      state
                      createdAt
                      closedAt
                      assignees(first: 5) {
                        nodes {
                          login
                        }
                      }
                      labels(first: 10) {
                        nodes {
                          name
                        }
                      }
                    }
                    ... on PullRequest {
                      title
                      number
                      repository {
                        name
                      }
                      state
                      createdAt
                      closedAt
                      mergedAt
                    }
                  }
                }
              }
            }
          }
        }
        """

        # Use GraphQL API to fetch project data
        try:
            variables = {"owner": params.owner, "number": params.project_number}

            response = await fetch_graphql(project_query, variables)

            if "errors" in response:
                return {
                    "error": "GraphQL error",
                    "message": response["errors"][0]["message"]
                    if response["errors"]
                    else "Unknown GraphQL error",
                }

            project_data = response["data"]["organization"]["projectV2"]

            # Get timeframe dates
            start_date, end_date = parse_timeframe(params.timeframe)

            # Process items to extract data
            items = []
            statuses = {}
            assignees = {}
            issue_count = 0
            pr_count = 0

            for item in project_data["items"]["nodes"]:
                if not item["content"]:
                    continue

                content = item["content"]
                created_at = datetime.fromisoformat(
                    content["createdAt"].replace("Z", "+00:00")
                )

                # Filter by timeframe
                if created_at < start_date or created_at > end_date:
                    continue

                # Get status if available
                status = "No Status"
                for field_value in item["fieldValues"]["nodes"]:
                    if field_value.get("field", {}).get(
                        "name"
                    ) == "Status" and field_value.get("name"):
                        status = field_value["name"]
                        break

                # Count statuses
                statuses[status] = statuses.get(status, 0) + 1

                # Count assignees for issues
                if content.get("assignees"):
                    for assignee in content["assignees"]["nodes"]:
                        login = assignee["login"]
                        assignees[login] = assignees.get(login, 0) + 1

                # Count content types
                if "repository" in content:
                    if "mergedAt" in content:
                        pr_count += 1
                    else:
                        issue_count += 1

                # Add to items list
                items.append(
                    {
                        "title": content["title"],
                        "number": content["number"],
                        "repository": content["repository"]["name"]
                        if "repository" in content
                        else None,
                        "state": content["state"],
                        "created_at": content["createdAt"],
                        "closed_at": content.get("closedAt"),
                        "status": status,
                    }
                )

            # Create overview data
            overview = {
                "project": {
                    "title": project_data["title"],
                    "description": project_data["shortDescription"],
                    "url": project_data["url"],
                },
                "timeframe": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "items": items,
                "metrics": {
                    "total_items": len(items),
                    "issue_count": issue_count,
                    "pr_count": pr_count,
                    "status_distribution": statuses,
                    "assignee_distribution": assignees,
                },
            }

            return overview

        except Exception as e:
            logger.error(f"Error fetching project data: {e}")
            return {
                "error": "Error fetching project data",
                "message": str(e),
            }

    except Exception as e:
        logger.error(f"General error in get_project_overview: {e}")
        return {
            "error": "Failed to get project overview",
            "message": str(e),
        }


@mcp.tool()
async def analyze_board(params: BoardAnalysisParams) -> Dict[str, Any]:
    """
    Analyze a project board and generate metrics based on view type.

    Args:
        params: Board analysis parameters

    Returns:
        Dict with board analysis data and visualizations
    """
    try:
        # For the GraphQL query to get board data with more details
        board_query = """
        query($boardId: ID!) {
          node(id: $boardId) {
            ... on ProjectV2 {
              id
              title
              url
              fields(first: 20) {
                nodes {
                  ... on ProjectV2Field {
                    id
                    name
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
              items(first: 100) {
                nodes {
                  id
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          name
                        }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field {
                          name
                        }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          name
                        }
                      }
                      ... on ProjectV2ItemFieldNumberValue {
                        number
                        field {
                          name
                        }
                      }
                    }
                  }
                  content {
                    ... on Issue {
                      title
                      number
                      repository {
                        name
                      }
                      state
                      createdAt
                      closedAt
                      assignees(first: 5) {
                        nodes {
                          login
                        }
                      }
                      labels(first: 10) {
                        nodes {
                          name
                        }
                      }
                    }
                    ... on PullRequest {
                      title
                      number
                      repository {
                        name
                      }
                      state
                      createdAt
                      closedAt
                      mergedAt
                    }
                  }
                }
              }
            }
          }
        }
        """

        try:
            variables = {"boardId": params.board_id}

            response = await fetch_graphql(board_query, variables)

            if "errors" in response:
                return {
                    "error": "GraphQL error",
                    "message": response["errors"][0]["message"]
                    if response["errors"]
                    else "Unknown GraphQL error",
                }

            board_data = response["data"]["node"]

            # Process based on the view type
            if params.view == "velocity":
                return await _analyze_velocity(board_data, params.sprint)
            elif params.view == "burndown":
                return await _analyze_burndown(board_data, params.sprint)
            else:
                # Default to basic board analysis
                return await _analyze_basic(board_data)

        except Exception as e:
            logger.error(f"Error analyzing board: {e}")
            return {
                "error": "Error analyzing board",
                "message": str(e),
            }

    except Exception as e:
        logger.error(f"General error in analyze_board: {e}")
        return {
            "error": "Failed to analyze board",
            "message": str(e),
        }


async def _analyze_basic(board_data: Dict[str, Any]) -> Dict[str, Any]:
    """Basic board analysis with item counts and status distribution."""
    # Find status field
    status_field = None
    status_options = {}
    for field in board_data["fields"]["nodes"]:
        if field.get("name") == "Status":
            status_field = field
            if "options" in field:
                for option in field["options"]:
                    status_options[option["id"]] = option["name"]
            break

    # Process items
    items_by_status = {}
    items_by_assignee = {}
    items_by_repository = {}
    total_items = 0

    for item in board_data["items"]["nodes"]:
        total_items += 1

        # Get status
        status = "No Status"
        for field_value in item["fieldValues"]["nodes"]:
            if field_value.get("field", {}).get("name") == "Status" and field_value.get(
                "name"
            ):
                status = field_value["name"]
                break

        items_by_status[status] = items_by_status.get(status, 0) + 1

        # Get assignee and repository if it's an issue or PR
        if item["content"]:
            content = item["content"]

            # Assignees for issues
            if content.get("assignees"):
                for assignee in content["assignees"]["nodes"]:
                    login = assignee["login"]
                    items_by_assignee[login] = items_by_assignee.get(login, 0) + 1

            # Repository
            if content.get("repository"):
                repo_name = content["repository"]["name"]
                items_by_repository[repo_name] = (
                    items_by_repository.get(repo_name, 0) + 1
                )

    # Create visualization for status distribution
    if items_by_status:
        fig, ax = plt.subplots(figsize=(10, 6))
        statuses = list(items_by_status.keys())
        counts = list(items_by_status.values())

        ax.bar(statuses, counts)
        ax.set_title("Items by Status")
        ax.set_xlabel("Status")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Save plot to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        status_chart = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()
    else:
        status_chart = None

    return {
        "board": {
            "title": board_data["title"],
            "url": board_data["url"],
        },
        "analysis": {
            "total_items": total_items,
            "items_by_status": items_by_status,
            "items_by_assignee": items_by_assignee,
            "items_by_repository": items_by_repository,
        },
        "visualizations": {
            "status_distribution": f"data:image/png;base64,{status_chart}"
            if status_chart
            else None,
        },
    }


async def _analyze_velocity(board_data: Dict[str, Any], sprint: str) -> Dict[str, Any]:
    """Analyze team velocity based on completed items."""
    # Implementation for velocity analysis would go here
    # This would require historical data across multiple sprints

    # Placeholder implementation
    return {
        "board": {
            "title": board_data["title"],
            "url": board_data["url"],
        },
        "analysis": {
            "message": "Velocity analysis requires historical data tracking. This is a placeholder.",
            "sprint": sprint,
        },
    }


async def _analyze_burndown(board_data: Dict[str, Any], sprint: str) -> Dict[str, Any]:
    """Generate burndown chart for sprint."""
    # Implementation for burndown chart would go here
    # This would require daily completion data

    # Placeholder implementation
    return {
        "board": {
            "title": board_data["title"],
            "url": board_data["url"],
        },
        "analysis": {
            "message": "Burndown analysis requires daily task completion data. This is a placeholder.",
            "sprint": sprint,
        },
    }


@mcp.tool()
async def get_team_metrics(params: TeamMetricsParams) -> Dict[str, Any]:
    """
    Get metrics for a team based on their GitHub activity.

    Args:
        params: Team metrics parameters

    Returns:
        Dict with team metrics
    """
    # This would require team member configuration
    # Placeholder implementation
    return {
        "team": params.team,
        "period": params.period,
        "metrics": {
            metric: "Data collection not implemented yet" for metric in params.metrics
        },
        "message": "Team metrics require team member configuration and historical data.",
    }


@mcp.tool()
async def recommend_issues(params: RecommendationParams) -> Dict[str, Any]:
    """
    Recommend issues based on context, team, and capacity.

    Args:
        params: Recommendation parameters

    Returns:
        Dict with recommended issues
    """
    try:
        g = get_github_client()

        # Build query based on parameters
        query_parts = []

        # Always get open issues
        query_parts.append("is:open")

        # Add team filter if specified (via label or similar)
        if params.team:
            query_parts.append(f"label:{params.team}")

        # Add priority filter if specified
        if params.priority:
            query_parts.append(f"label:{params.priority}")

        # Add other context-specific filters
        if params.context == "sprint_planning":
            query_parts.append("no:assignee")  # Unassigned issues

        # Combine query parts
        query = " ".join(query_parts)

        # Search for issues
        issues_results = g.search_issues(query, sort="created")

        # Convert to structured data
        issues = []
        for issue in issues_results[:20]:  # Limiting to 20 issues
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "url": issue.html_url,
                "repository": issue.repository.full_name,
                "labels": [label.name for label in issue.labels],
            }

            if issue.assignee:
                issue_data["assignee"] = issue.assignee.login

            if issue.milestone:
                issue_data["milestone"] = issue.milestone.title

            issues.append(issue_data)

        # Process recommendations based on context
        if params.context == "sprint_planning":
            # Simple recommendation based on creation date and labels
            recommendations = issues[:10]  # Take top 10 as recommendation

            return {
                "context": params.context,
                "team": params.team,
                "recommended_issues": recommendations,
                "reasoning": "Selected based on priority, age, and team relevance",
            }
        else:
            # Default recommendations
            return {
                "context": params.context,
                "team": params.team,
                "recommended_issues": issues[:5],
                "reasoning": "Selected based on general relevance",
            }

    except Exception as e:
        logger.error(f"Error recommending issues: {e}")
        return {
            "error": "Failed to recommend issues",
            "message": str(e),
            "context": params.context,
            "team": params.team,
            "recommended_issues": [],
        }


@mcp.tool()
async def generate_daily_report(
    blocked_issues: List[Dict],
    pending_reviews: List[Dict],
    include_metrics: bool = True,
) -> Dict[str, Any]:
    """
    Generate a daily status report.

    Args:
        blocked_issues: List of blocked issues
        pending_reviews: List of pending reviews
        include_metrics: Whether to include metrics

    Returns:
        Dict with daily report
    """
    try:
        report = {
            "date": datetime.now().isoformat(),
            "blocked_issues": blocked_issues,
            "pending_reviews": pending_reviews,
            "summary": {
                "blocked_count": len(blocked_issues),
                "pending_reviews_count": len(pending_reviews),
            },
        }

        if include_metrics:
            # Add placeholder metrics
            report["metrics"] = {
                "team_velocity": "Placeholder",
                "burndown_status": "Placeholder",
            }

        return report

    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {
            "error": "Failed to generate daily report",
            "message": str(e),
        }


# HTTP Endpoints
@mcp.http_endpoint("/github/issues/search")
async def http_search_issues(request: IssueSearchParams) -> Dict[str, Any]:
    """HTTP endpoint for issue search."""
    return await search_issues(request)


@mcp.http_endpoint("/github/project/{owner}/{number}")
async def http_get_project(
    owner: str, number: int, timeframe: str = "last_30_days"
) -> Dict[str, Any]:
    """HTTP endpoint for project overview."""
    params = ProjectParams(owner=owner, project_number=number, timeframe=timeframe)
    return await get_project_overview(params)


@mcp.http_endpoint("/github/board/{id}/analysis")
async def http_analyze_board(
    id: str, view: str = "velocity", sprint: str = "current"
) -> Dict[str, Any]:
    """HTTP endpoint for board analysis."""
    params = BoardAnalysisParams(board_id=id, view=view, sprint=sprint)
    return await analyze_board(params)


@mcp.http_endpoint("/github/team/{team}/metrics")
async def http_get_team_metrics(
    team: str,
    metrics: List[str] = ["pr_velocity", "issue_completion"],
    period: str = "last_sprint",
) -> Dict[str, Any]:
    """HTTP endpoint for team metrics."""
    params = TeamMetricsParams(team=team, metrics=metrics, period=period)
    return await get_team_metrics(params)


@mcp.http_endpoint("/github/issues/recommend")
async def http_recommend_issues(request: RecommendationParams) -> Dict[str, Any]:
    """HTTP endpoint for issue recommendations."""
    return await recommend_issues(request)


# Setup and add web client
mcp.add_web_client()

# Main
if __name__ == "__main__":
    # Check if token is configured
    if not GITHUB_TOKEN:
        logger.warning(
            "GITHUB_TOKEN environment variable not set. "
            "Please set it to use GitHub API features."
        )

    # Run the MCP server
    mcp.run(host="0.0.0.0", port=8000)
