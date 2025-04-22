#!/usr/bin/env python3
"""Performance Profiling MCP Server."""

import asyncio
import os
from typing import Dict, Optional

import psutil
import py_spy
from fastapi import FastAPI
from line_profiler import LineProfiler
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel


class ProfileRequest(BaseModel):
    """Profile request model."""

    target_file: str
    function_name: Optional[str] = None
    duration: Optional[int] = 30


class MemorySnapshot(BaseModel):
    """Memory snapshot model."""

    timestamp: float
    rss: int  # Resident Set Size
    vms: int  # Virtual Memory Size
    cpu_percent: float


# Initialize MCP server
mcp = PepperFastMCP(
    "Performance Profiler",
    description="Analyzes and profiles Python code performance",
)


@mcp.tool()
async def cpu_profile(request: ProfileRequest) -> Dict:
    """Profile CPU usage of a Python process or function."""
    try:
        # Use py-spy for CPU profiling
        profiler = py_spy.PySpyClient()
        profile_data = await profiler.collect_profile(
            request.target_file, duration=request.duration
        )

        return {
            "success": True,
            "profile": profile_data,
            "hotspots": profile_data.get_hotspots(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def memory_usage(request: ProfileRequest) -> Dict:
    """Monitor memory usage of a Python process."""
    try:
        process = psutil.Process(os.getpid())
        snapshots = []

        # Take memory snapshots
        for _ in range(10):  # Take 10 snapshots
            memory_info = process.memory_info()
            snapshots.append(
                MemorySnapshot(
                    timestamp=process.create_time(),
                    rss=memory_info.rss,
                    vms=memory_info.vms,
                    cpu_percent=process.cpu_percent(),
                )
            )
            await asyncio.sleep(1)

        return {
            "success": True,
            "snapshots": [s.dict() for s in snapshots],
            "summary": {
                "avg_rss": sum(s.rss for s in snapshots) / len(snapshots),
                "max_rss": max(s.rss for s in snapshots),
                "avg_cpu": sum(s.cpu_percent for s in snapshots) / len(snapshots),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def line_profile(request: ProfileRequest) -> Dict:
    """Profile execution time of specific lines in a function."""
    try:
        if not request.function_name:
            return {"success": False, "error": "Function name is required"}

        # Set up line profiler
        profiler = LineProfiler()

        # Load and profile the function
        with open(request.target_file) as f:
            exec(f.read())

        # Profile the specified function
        profiler.add_function(locals()[request.function_name])
        profiler.enable()

        try:
            # Run the function
            locals()[request.function_name]()
        finally:
            profiler.disable()

        # Get profiling results
        stats = profiler.get_stats()
        return {
            "success": True,
            "line_stats": {
                "timings": stats.timings,
                "unit": stats.unit,
                "total_time": stats.total_time,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_performance(request: ProfileRequest) -> Dict:
    """Comprehensive performance analysis of a Python file or function."""
    results = {
        "cpu_profile": await cpu_profile(request),
        "memory_usage": await memory_usage(request),
    }

    if request.function_name:
        results["line_profile"] = await line_profile(request)

    # Generate recommendations
    recommendations = []

    # CPU recommendations
    if results["cpu_profile"]["success"]:
        hotspots = results["cpu_profile"]["profile"]["hotspots"]
        for hotspot in hotspots:
            recommendations.append(
                f"High CPU usage in {hotspot['function']}: Consider optimization"
            )

    # Memory recommendations
    if results["memory_usage"]["success"]:
        memory_summary = results["memory_usage"]["summary"]
        if memory_summary["max_rss"] > 1e9:  # More than 1GB
            recommendations.append(
                "High memory usage detected: Consider memory optimization"
            )

    results["recommendations"] = recommendations
    return results


# Add FastAPI integration
app = FastAPI(title="Performance Profiler")
mcp.add_web_client()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8006, reload=True)
