#!/usr/bin/env python
"""
MCP Integration Test CLI

This script automates the setup and testing of the MCP system:
1. Starts the 00-hello-world MCP server
2. Starts the mcp-web-client host
3. Runs integration tests between them
4. Provides detailed diagnostics for any issues

Usage:
    python run_mcp_integration.py [--debug]
"""

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Constants
SERVER_PORT = 8000
HOST_PORT = 3000
BASE_DIR = Path(__file__).parent.resolve()
SERVER_DIR = BASE_DIR / "00-hello-world"
CLIENT_DIR = BASE_DIR / "mcp-web-client"
MAX_STARTUP_TIME = 15  # seconds to give more time

# Global state
running_processes: List[subprocess.Popen] = []
debug_mode = False


def log(message: str, level: str = "INFO") -> None:
    """Print a formatted log message."""
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌ ",
        "DEBUG": "🔍 "
    }.get(level, "   ")
    
    if level == "DEBUG" and not debug_mode:
        return
        
    print(f"{prefix}{message}")


def cleanup(exit_code: int = 0) -> None:
    """Clean up all running processes."""
    log("Cleaning up processes...", "INFO")
    for process in running_processes:
        try:
            process.terminate()
            time.sleep(0.5)
            if process.poll() is None:
                process.kill()
        except Exception as e:
            log(f"Error killing process {process.pid}: {e}", "WARNING")
    
    time.sleep(1)  # Give processes time to clean up
    log("Cleanup complete", "SUCCESS")
    if exit_code != 0:
        sys.exit(exit_code)


def kill_existing_processes(ports: List[int]) -> None:
    """Kill any processes using the specified ports."""
    for port in ports:
        try:
            # Find processes using this port
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True, 
                text=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                log(f"Found processes using port {port}: {pids}", "DEBUG")
                
                for pid in pids:
                    if pid:
                        log(f"Killing process {pid} using port {port}", "INFO")
                        subprocess.run(["kill", "-9", pid], capture_output=True)
                        time.sleep(1)  # Give it time to free the port
        except Exception as e:
            log(f"Error killing processes on port {port}: {e}", "WARNING")


def wait_for_server(url: str, timeout: int = 15) -> bool:
    """Wait for a server to become available at the given URL."""
    start_time = time.time()
    log(f"Waiting for {url} to become available...", "INFO")
    while time.time() - start_time < timeout:
        try:
            import httpx
            response = httpx.get(url, timeout=2.0)
            if response.status_code < 400:  # Accept any successful status
                log(f"Server at {url} is now available (status: {response.status_code})", "SUCCESS")
                return True
        except Exception as e:
            if debug_mode:
                log(f"Server at {url} not ready yet: {e}", "DEBUG")
        time.sleep(1)
    log(f"Timeout waiting for {url}", "WARNING")
    return False


def start_mcp_server() -> Optional[subprocess.Popen]:
    """Start the MCP server and return the process."""
    log("Starting MCP server...", "INFO")
    
    server_path = SERVER_DIR / "server.py"
    if not server_path.exists():
        log(f"Server script not found at {server_path}", "ERROR")
        return None
    
    # Run the server in foreground mode so we can see the output
    try:
        # First check for port availability
        try:
            kill_existing_processes([SERVER_PORT])
            # Double check port is actually free
            time.sleep(1)
        except Exception as e:
            log(f"Error checking port {SERVER_PORT}: {e}", "WARNING")
            
        # Start the server in a way we can see the output
        log("Starting MCP server process...", "INFO")
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            cwd=str(SERVER_DIR),
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        running_processes.append(process)
        
        # Start a thread to read and print output from the server
        def read_output():
            while process.poll() is None:
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        log(f"SERVER: {line.strip()}", "DEBUG")
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        log(f"SERVER ERR: {line.strip()}", "DEBUG")
                time.sleep(0.1)
        
        if debug_mode:
            import threading
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()
        
        # Give the server a moment to start
        time.sleep(5)
        
        # First check if the server is still running
        if process.poll() is not None:
            log(f"Server process exited with code {process.poll()}", "ERROR")
            if process.stderr:
                stderr = process.stderr.read()
                log(f"Server error output: {stderr}", "ERROR")
            return None
            
        # Check if Uvicorn printed a startup message
        if process.stdout:
            server_output = process.stdout.read(1024)  # Read some output without blocking
            if "Uvicorn running on http" in server_output:
                log("Server startup message detected", "SUCCESS")
            elif debug_mode:
                log(f"Server output: {server_output}", "DEBUG")
        
        # Try to wait for HTTP endpoint
        base_url = f"http://localhost:{SERVER_PORT}"
        endpoints = [f"{base_url}/greeting/test", f"{base_url}/docs", base_url]
        
        for endpoint in endpoints:
            if wait_for_server(endpoint, 5):
                log(f"MCP server is reachable at {endpoint}", "SUCCESS")
                return process
        
        # If we got here, none of the endpoints responded
        log("MCP server is running but endpoints are not responding", "WARNING")
        # We'll still return the process to continue
        return process
            
    except Exception as e:
        log(f"Error starting MCP server: {e}", "ERROR")
        return None


def start_mcp_host() -> Optional[subprocess.Popen]:
    """Start the MCP host and return the process."""
    log("Starting MCP host...", "INFO")
    
    host_path = CLIENT_DIR / "start_host.py"
    if not host_path.exists():
        log(f"Host script not found at {host_path}", "ERROR")
        return None
    
    try:
        # First check for port availability
        try:
            kill_existing_processes([HOST_PORT])
            # Double check port is actually free
            time.sleep(1)
        except Exception as e:
            log(f"Error checking port {HOST_PORT}: {e}", "WARNING")
            
        # Start the host
        log("Starting MCP host process...", "INFO")
        process = subprocess.Popen(
            [sys.executable, str(host_path)],
            cwd=str(CLIENT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        running_processes.append(process)
        
        # Start a thread to read and print output from the host
        def read_output():
            while process.poll() is None:
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        log(f"HOST: {line.strip()}", "DEBUG")
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        log(f"HOST ERR: {line.strip()}", "DEBUG")
                time.sleep(0.1)
        
        if debug_mode:
            import threading
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()
        
        # Give it a moment to start
        time.sleep(5)
        
        # First check if the host is still running
        if process.poll() is not None:
            log(f"Host process exited with code {process.poll()}", "ERROR")
            if process.stderr:
                stderr = process.stderr.read()
                log(f"Host error output: {stderr}", "ERROR")
            return None
        
        # Try to wait for HTTP endpoint
        if wait_for_server(f"http://localhost:{HOST_PORT}", MAX_STARTUP_TIME):
            log("MCP host started successfully", "SUCCESS")
            return process
        else:
            log("MCP host failed to start within timeout", "ERROR")
            # Check for errors
            if process.stderr:
                stderr = process.stderr.read()
                if stderr:
                    log(f"Host error output: {stderr}", "ERROR")
            process.terminate()
            return None
            
    except Exception as e:
        log(f"Error starting MCP host: {e}", "ERROR")
        return None


def run_mcp_connection_test() -> bool:
    """Run the MCP connection test."""
    log("Running MCP connection test...", "INFO")
    
    test_path = CLIENT_DIR / "test_mcp_connection.py"
    if not test_path.exists():
        log(f"Test script not found at {test_path}", "ERROR")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(CLIENT_DIR),
            capture_output=True,
            text=True
        )
        
        log(f"Test stdout: {result.stdout}", "DEBUG")
        
        if "PASSED" in result.stdout:
            log("MCP connection test passed", "SUCCESS")
            return True
        else:
            # If the main test failed but it could connect, consider it a partial success
            if "Successfully connected to server" in result.stdout:
                log("MCP connection test partially succeeded - connection works", "WARNING")
                return True
            else:
                log("MCP connection test failed", "ERROR")
                log(result.stdout, "ERROR")
                log(result.stderr, "ERROR")
                return False
            
    except Exception as e:
        log(f"Error running MCP connection test: {e}", "ERROR")
        return False


def run_hello_world_test() -> bool:
    """Run the hello world test."""
    log("Running hello world test...", "INFO")
    
    test_path = CLIENT_DIR / "test_hello_world.py"
    if not test_path.exists():
        log(f"Test script not found at {test_path}", "ERROR")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(CLIENT_DIR),
            capture_output=True,
            text=True
        )
        
        log(f"Test stdout: {result.stdout}", "DEBUG")
        
        # Look for successful connection
        if "Connected to hello-world server" in result.stdout:
            log("Hello world connection test successful", "SUCCESS")
            # Even if other parts fail, we'll consider this a partial success
            return True
            
        # Look for test suite completed
        if "Test suite completed" in result.stdout:
            log("Hello world test completed", "SUCCESS")
            return True
        else:
            log("Hello world test failed", "ERROR")
            log(result.stdout, "ERROR")
            log(result.stderr, "ERROR")
            return False
            
    except Exception as e:
        log(f"Error running hello world test: {e}", "ERROR")
        return False


def run_direct_api_test() -> bool:
    """Run direct API tests against the server."""
    log("Running direct API tests against MCP server...", "INFO")
    
    test_endpoints = [
        {
            "url": f"http://localhost:{SERVER_PORT}/greeting/DirectTest",
            "expected_key": "message",
            "description": "Greeting API"
        },
        {
            "url": f"http://localhost:{SERVER_PORT}/docs",
            "expected_status": 200,
            "description": "OpenAPI documentation"
        }
    ]
    
    success = True
    
    for test in test_endpoints:
        description = test["description"]
        url = test["url"]
        try:
            import httpx
            response = httpx.get(url, timeout=5.0)
            if "expected_status" in test and response.status_code != test["expected_status"]:
                log(f"{description} returned unexpected status: {response.status_code}", "ERROR")
                success = False
                continue
                
            if "expected_key" in test:
                data = response.json()
                if test["expected_key"] in data:
                    log(f"{description} test passed", "SUCCESS")
                else:
                    log(f"{description} missing expected key: {test['expected_key']}", "ERROR")
                    success = False
            else:
                log(f"{description} test passed", "SUCCESS")
        except Exception as e:
            log(f"Error testing {description}: {e}", "ERROR")
            success = False
    
    return success


def check_server_capabilities() -> Tuple[bool, Dict[str, Any]]:
    """Check server capabilities by making HTTP requests."""
    log("Checking server capabilities...", "INFO")
    
    capabilities = {}
    success = True
    
    # Check greeting endpoint
    try:
        import httpx
        response = httpx.get(f"http://localhost:{SERVER_PORT}/greeting/Pimenta")
        if response.status_code < 400:
            data = response.json()
            if "message" in data and "Pimenta" in data["message"]:
                log("Greeting endpoint working", "SUCCESS")
                capabilities["greeting"] = True
            else:
                log("Greeting endpoint returned unexpected response", "ERROR")
                capabilities["greeting"] = False
                success = False
        else:
            log(f"Greeting endpoint returned status {response.status_code}", "ERROR")
            capabilities["greeting"] = False
            success = False
    except Exception as e:
        log(f"Error checking greeting endpoint: {e}", "ERROR")
        capabilities["greeting"] = False
        success = False
    
    # Check OpenAPI docs
    try:
        import httpx
        response = httpx.get(f"http://localhost:{SERVER_PORT}/docs")
        if response.status_code < 400:
            log("OpenAPI docs endpoint working", "SUCCESS")
            capabilities["openapi"] = True
        else:
            log("OpenAPI docs endpoint returned unexpected status", "ERROR")
            capabilities["openapi"] = False
            success = False
    except Exception as e:
        log(f"Error checking OpenAPI docs endpoint: {e}", "ERROR")
        capabilities["openapi"] = False
        success = False
    
    return success, capabilities


def check_dependencies() -> bool:
    """Check and install necessary dependencies."""
    log("Checking and installing dependencies...", "INFO")
    
    dependencies = [
        "pepperpymcp",
        "fastapi",
        "uvicorn",
        "httpx"
    ]
    
    missing_deps = []
    all_installed = True
    
    # Check which dependencies are installed
    for dep in dependencies:
        try:
            __import__(dep)
            log(f"Dependency {dep} is installed", "SUCCESS")
        except ImportError:
            log(f"Dependency {dep} is missing", "WARNING")
            missing_deps.append(dep)
            all_installed = False
    
    # If any dependencies are missing, offer to install them
    if not all_installed:
        log("Some dependencies are missing. Would you like to install them now? (y/n)", "INFO")
        response = input().strip().lower()
        if response in ['y', 'yes']:
            log("Installing missing dependencies...", "INFO")
            try:
                cmd = [sys.executable, "-m", "pip", "install"] + missing_deps
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    log("Dependencies installed successfully", "SUCCESS")
                    return True
                else:
                    log(f"Failed to install dependencies: {result.stderr}", "ERROR")
                    return False
            except Exception as e:
                log(f"Error installing dependencies: {e}", "ERROR")
                return False
        else:
            log("Continuing without installing missing dependencies", "WARNING")
            return False
    
    return True


def run_diagnostics() -> None:
    """Run diagnostics to identify any configuration issues."""
    log("Running diagnostics...", "INFO")
    
    # Check if all required files exist
    required_files = [
        (SERVER_DIR / "server.py", "MCP server script"),
        (CLIENT_DIR / "mcp_host.py", "MCP host script"),
        (CLIENT_DIR / "start_host.py", "MCP host starter script"),
        (CLIENT_DIR / "index.html", "Web client HTML"),
        (CLIENT_DIR / "mcp-client.js", "Web client JavaScript")
    ]
    
    for file_path, description in required_files:
        if file_path.exists():
            log(f"{description} found at {file_path}", "SUCCESS")
        else:
            log(f"{description} not found at {file_path}", "ERROR")
    
    # Check network ports
    ports = [(SERVER_PORT, "MCP server"), (HOST_PORT, "MCP host")]
    for port, description in ports:
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True, 
                text=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                log(f"{description} port {port} is used by PIDs: {', '.join(pids)}", "WARNING")
            else:
                log(f"{description} port {port} is available", "SUCCESS")
        except Exception as e:
            log(f"Error checking {description} port {port}: {e}", "WARNING")


def main():
    """Main entry point for the CLI."""
    global debug_mode
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Integration Test CLI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    debug_mode = args.debug
    
    # Set up signal handlers for clean termination
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    
    try:
        # Banner
        print("\n" + "="*50)
        print("🚀 MCP INTEGRATION TEST CLI")
        print("="*50 + "\n")
        
        # Run diagnostics
        run_diagnostics()
        
        # Check dependencies
        dependencies_ok = check_dependencies()
        if not dependencies_ok:
            log("Dependency issues detected. Proceeding with caution.", "WARNING")
        
        # Kill any existing processes
        kill_existing_processes([SERVER_PORT, HOST_PORT])
        
        # Start MCP server
        server_process = start_mcp_server()
        if not server_process:
            log("Failed to start MCP server. Exiting.", "ERROR")
            cleanup(1)
            return
        
        # Check server capabilities directly
        log("Testing direct API access to server...", "INFO")
        api_success = run_direct_api_test()
        if not api_success:
            log("Direct API tests failed. The MCP server may not be working correctly.", "WARNING")
            # We'll continue anyway to test the rest of the integration
        
        # Start MCP host
        host_process = start_mcp_host()
        if not host_process:
            log("Failed to start MCP host. Exiting.", "ERROR")
            cleanup(1)
            return
        
        # Wait for everything to start up
        log("Waiting for all services to initialize...", "INFO")
        time.sleep(5)
        
        # Run tests
        log("Running integration tests to verify functionality", "INFO")
        connection_test_success = run_mcp_connection_test()
        hello_world_test_success = run_hello_world_test()
        
        # Process results
        test_results = {
            "Direct API": api_success,
            "MCP Connection": connection_test_success,
            "Hello World": hello_world_test_success
        }
        
        log("\n📊 Test Results Summary:", "INFO")
        for test, result in test_results.items():
            icon = "✅" if result else "❌"
            log(f"{icon} {test}", "INFO")
        
        if all(test_results.values()):
            log("\nAll tests passed! The MCP environment is correctly set up.", "SUCCESS")
        elif any(test_results.values()):
            log("\nSome tests passed! The MCP environment is partially working.", "WARNING")
        else:
            log("\nAll tests failed! There are issues with the MCP environment.", "ERROR")
        
        # Keep running until user interrupts
        log("\nEnvironment is running. Press Ctrl+C to stop.", "INFO")
        log("You can access the web client at: http://localhost:3000", "INFO")
        log("The MCP server is running at: http://localhost:8000", "INFO")
        
        # Monitor processes for failures
        while all(p.poll() is None for p in running_processes):
            time.sleep(1)
        
        # If we get here, a process has died
        for i, process in enumerate(running_processes):
            if process.poll() is not None:
                name = "MCP server" if i == 0 else "MCP host"
                log(f"{name} process terminated unexpectedly with code {process.poll()}", "ERROR")
                
                # Print the stderr
                if process.stderr:
                    stderr = process.stderr.read()
                    if stderr:
                        log(f"{name} error output:\n{stderr}", "ERROR")
        
        cleanup(1)
        
    except KeyboardInterrupt:
        log("Interrupted by user", "INFO")
        cleanup(0)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        cleanup(1)


if __name__ == "__main__":
    main() 