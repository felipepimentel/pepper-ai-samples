# GitHub Projects Integration MCP Server

This MCP server integrates with GitHub Projects to provide advanced project management capabilities, analytics, and insights directly in VS Code. It helps track issues, milestones, project boards, and team performance.

## Features

1. Project Analytics
   - Sprint velocity tracking
   - Burndown charts
   - Team performance metrics
   - Issue aging analysis

2. Issue Management
   - Smart issue search
   - Issue templates
   - Automated labeling
   - Duplicate detection

3. Project Board Integration
   - Board status overview
   - Card movement tracking
   - Automated updates
   - Custom workflow automation

4. Team Insights
   - Contribution analytics
   - Review statistics
   - Response time metrics
   - Workload distribution

## Setup

```bash
# Install dependencies
uv pip install -e .

# Configure GitHub token
export GITHUB_TOKEN="your_token_here"

# Run the server
python server.py
```

## Usage Examples

1. Get Project Overview
```python
result = await client.call_tool("get_project_overview", {
    "owner": "organization",
    "project_number": 1,
    "timeframe": "last_30_days"
})
```

2. Search Issues
```python
result = await client.call_tool("search_issues", {
    "query": "label:bug status:open assignee:pimenta",
    "sort": "priority",
    "include_metrics": True
})
```

3. Board Analysis
```python
result = await client.call_tool("analyze_board", {
    "board_id": "PROJECT_ID",
    "view": "velocity",
    "sprint": "current"
})
```

4. Team Metrics
```python
result = await client.call_tool("get_team_metrics", {
    "team": "backend",
    "metrics": ["pr_velocity", "issue_completion", "review_time"],
    "period": "last_sprint"
})
```

## Example Questions

1. Project Status
   - "Show me the current sprint progress"
   - "What issues are blocking the team?"
   - "Generate a sprint report"
   - "What's our velocity this month?"

2. Issue Analysis
   - "Find all high-priority bugs assigned to me"
   - "Which issues are getting stale?"
   - "Show issues needing review"
   - "List issues by effort estimate"

3. Team Performance
   - "How's the PR review distribution?"
   - "What's our average time to close issues?"
   - "Show team workload balance"
   - "Who needs help with their tasks?"

4. Project Planning
   - "Suggest next sprint capacity"
   - "Identify risks in current sprint"
   - "Generate milestone timeline"
   - "Analyze resource allocation"

## HTTP Endpoints

```bash
# Get project overview
GET /github/project/{owner}/{number}
{
    "timeframe": "last_30_days",
    "include_metrics": true
}

# Search issues
POST /github/issues/search
Content-Type: application/json
{
    "query": "label:bug status:open",
    "sort": "priority"
}

# Analyze board
GET /github/board/{id}/analysis
{
    "view": "velocity",
    "sprint": "current"
}

# Get team metrics
GET /github/team/{team}/metrics
{
    "metrics": ["pr_velocity", "review_time"],
    "period": "last_sprint"
}

# Get issue recommendations
POST /github/issues/recommend
Content-Type: application/json
{
    "context": "sprint_planning",
    "team": "backend"
}
```

## Tips for Better Results

1. Project Setup
   - Configure GitHub token with appropriate permissions
   - Set up project board columns to match your workflow
   - Define labels for better categorization
   - Configure team members and roles

2. Best Practices
   - Keep issues updated with relevant labels
   - Use project board automations
   - Add effort estimates to issues
   - Link related issues and PRs

3. Common Workflows

Sprint Planning:
```python
# 1. Get team capacity
capacity = await client.call_tool("get_team_metrics", {
    "team": "backend",
    "metrics": ["capacity"],
    "period": "next_sprint"
})

# 2. Get recommended issues
issues = await client.call_tool("recommend_issues", {
    "capacity": capacity,
    "priority": "high",
    "team": "backend"
})

# 3. Generate sprint plan
plan = await client.call_tool("generate_sprint_plan", {
    "issues": issues,
    "capacity": capacity,
    "goals": ["reduce_bugs", "improve_performance"]
})
```

Daily Updates:
```python
# 1. Get blocked issues
blocked = await client.call_tool("find_blocked_issues", {
    "team": "all",
    "sprint": "current"
})

# 2. Get PR review status
reviews = await client.call_tool("get_review_status", {
    "team": "all",
    "status": "pending"
})

# 3. Generate daily report
report = await client.call_tool("generate_daily_report", {
    "blocked_issues": blocked,
    "pending_reviews": reviews,
    "include_metrics": True
})
``` 