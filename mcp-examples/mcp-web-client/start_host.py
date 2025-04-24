#!/usr/bin/env python
"""
Script to start the MCP host with web interface
"""

import asyncio
import subprocess
import sys
import os
import time
import webbrowser
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("host.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("start_host")

async def start_mcp_host(server_url="http://localhost:8000", use_stdio=False):
    """Start the MCP host in demo mode"""
    logger.info(f"Starting MCP host, connecting to server at {server_url}")
    
    # Build the command to start the MCP host
    cmd = [sys.executable, "mcp_host.py", "--demo"]
    
    if use_stdio:
        cmd.extend(["--stdio"])
        # Start the server process if using stdio
        logger.info("Starting MCP server in stdio mode")
        server_process = subprocess.Popen(
            [sys.executable, "../00-hello-world/server.py", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"MCP server started with stdio mode, PID {server_process.pid}")
    else:
        cmd.extend(["--server", server_url])
    
    # Start the process
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for the host to start
        time.sleep(2)
        
        if process.poll() is not None:
            logger.error(f"Failed to start MCP host: process exited with code {process.poll()}")
            stderr_data = process.stderr.read() if process.stderr else "No error output"
            logger.error(f"Error: {stderr_data}")
            return None
        
        logger.info(f"MCP host started with PID {process.pid}")
    except Exception as e:
        logger.error(f"Failed to start MCP host: {e}")
        return None
    
    # Start the HTTP server for the web client
    logger.info("Starting HTTP server for web client")
    try:
        http_server_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000"],
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if http_server_process.poll() is not None:
            logger.error(f"Failed to start HTTP server: process exited with code {http_server_process.poll()}")
            stderr_data = http_server_process.stderr.read() if http_server_process.stderr else "No error output"
            logger.error(f"Error: {stderr_data}")
            if 'process' in locals():
                process.terminate()
            return None
        
        logger.info(f"HTTP server started with PID {http_server_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        if 'process' in locals():
            process.terminate()
        return None
    
    # Open the web client in a browser
    logger.info("Opening web client in browser")
    index_path = Path(os.getcwd()) / "index.html"
    try:
        webbrowser.open(f"http://localhost:3000")
        logger.info(f"Web client opened at http://localhost:3000")
    except Exception as e:
        logger.error(f"Failed to open web client: {e}")
    
    logger.info("All components started. Press Ctrl+C to stop.")
    
    if use_stdio:
        return process, http_server_process, server_process
    return process, http_server_process

async def main():
    parser = argparse.ArgumentParser(description="Start MCP host with web interface")
    parser.add_argument("--stdio", action="store_true", help="Use stdio transport (will start server)")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL to connect to")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    try:
        processes = await start_mcp_host(server_url=args.server, use_stdio=args.stdio)
        
        if not processes:
            logger.error("Failed to start one or more components")
            return
        
        # Keep running until Ctrl+C
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all components...")
        # Clean up processes
        if processes:
            for process in processes:
                if process and process.poll() is None:
                    process.terminate()
                    logger.info(f"Terminated process with PID {process.pid}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 