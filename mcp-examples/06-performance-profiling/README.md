# Performance Profiling MCP Server

This MCP server provides tools for profiling and analyzing Python code performance. It includes CPU profiling, memory usage monitoring, line-by-line profiling, and performance analysis with optimization recommendations.

## Features

1. CPU Profiling
   - Profile CPU usage of Python processes
   - Identify performance hotspots
   - Generate flame graphs

2. Memory Usage Monitoring
   - Track memory consumption
   - Detect memory leaks
   - Monitor RSS and CPU percentage

3. Line Profiling
   - Profile specific functions line by line
   - Measure execution time per line
   - Identify bottlenecks

4. Performance Analysis
   - Comprehensive performance reports
   - Optimization recommendations
   - Resource usage patterns

## Setup

```bash
# Install dependencies
uv pip install -e .

# Run the server
python server.py
```

## Usage Examples

1. CPU Profiling
```python
result = await client.call_tool("cpu_profile", {
    "pid": 1234,  # or
    "function_name": "my_function"
})
```

2. Memory Usage Monitoring
```python
result = await client.call_tool("memory_usage", {
    "pid": 1234,
    "duration": 60  # seconds
})
```

3. Line Profiling
```python
result = await client.call_tool("line_profile", {
    "function_name": "process_data",
    "module_path": "app/processing.py"
})
```

4. Performance Analysis
```python
result = await client.call_tool("analyze_performance", {
    "pid": 1234,
    "function_name": "process_data",  # optional
    "duration": 300  # seconds
})
```

## Example Questions

1. CPU Performance
   - "What's causing high CPU usage in my application?"
   - "Which functions are the most CPU intensive?"
   - "How can I optimize this slow function?"

2. Memory Usage
   - "Is my application leaking memory?"
   - "What's the memory usage pattern over time?"
   - "Which processes are using the most memory?"

3. Code Optimization
   - "Profile this function line by line"
   - "What are the performance bottlenecks?"
   - "How can I improve the execution time?"

4. Resource Analysis
   - "Generate a complete performance report"
   - "What's the resource usage trend?"
   - "Identify optimization opportunities"

## HTTP Endpoints

```bash
# Profile CPU usage
POST /profile/cpu
Content-Type: application/json
{
    "pid": 1234
}

# Monitor memory usage
POST /profile/memory
Content-Type: application/json
{
    "pid": 1234,
    "duration": 60
}

# Profile specific lines
POST /profile/line
Content-Type: application/json
{
    "function_name": "process_data",
    "module_path": "app/processing.py"
}

# Analyze performance
POST /analyze
Content-Type: application/json
{
    "pid": 1234,
    "duration": 300
} 