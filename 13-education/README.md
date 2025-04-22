# Education Assistant MCP Server

This MCP server transforms VS Code into an interactive learning platform by generating exercises, tracking progress, and providing contextual learning materials. It adapts to different learning styles and skill levels.

## Features

1. Exercise Generation
   - Create coding challenges
   - Generate practice problems
   - Build mini-projects
   - Custom difficulty levels

2. Learning Path Creation
   - Personalized learning tracks
   - Skill gap analysis
   - Progress tracking
   - Achievement system

3. Interactive Tutorials
   - In-editor code walkthroughs
   - Real-time feedback
   - Contextual hints
   - Live coding examples

4. Knowledge Assessment
   - Skill level evaluation
   - Progress tracking
   - Performance analytics
   - Learning recommendations

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## Usage Examples

1. Generate Exercise
```python
result = await client.call_tool("generate_exercise", {
    "topic": "async/await",
    "difficulty": "intermediate",
    "time_estimate": "30min"
})
```

2. Create Learning Path
```python
result = await client.call_tool("create_path", {
    "goal": "Full Stack Development",
    "current_level": "beginner",
    "time_available": "10h/week"
})
```

3. Start Tutorial
```python
result = await client.call_tool("start_tutorial", {
    "topic": "React Hooks",
    "interactive": True,
    "with_examples": True
})
```

4. Assess Knowledge
```python
result = await client.call_tool("assess_skills", {
    "topics": ["Python", "APIs", "Testing"],
    "depth": "detailed"
})
```

## Example Questions

1. Learning Content
   - "Create an exercise about async programming"
   - "Generate a project idea for practicing APIs"
   - "What should I learn next for web development?"

2. Skill Assessment
   - "Test my Python knowledge"
   - "What are my weak areas in testing?"
   - "Am I ready for advanced topics?"

3. Tutorial Help
   - "Walk me through creating a REST API"
   - "Explain this code pattern with examples"
   - "Show me best practices for this"

4. Progress Tracking
   - "How am I progressing in backend development?"
   - "What skills have I mastered?"
   - "Generate a learning report"

## HTTP Endpoints

```bash
# Generate exercise
POST /education/exercise
Content-Type: application/json
{
    "topic": "async/await",
    "difficulty": "intermediate"
}

# Create learning path
POST /education/path
Content-Type: application/json
{
    "goal": "Full Stack Development",
    "current_level": "beginner"
}

# Start tutorial
POST /education/tutorial
Content-Type: application/json
{
    "topic": "React Hooks",
    "interactive": true
}

# Assess skills
POST /education/assess
Content-Type: application/json
{
    "topics": ["Python", "APIs", "Testing"]
} 