#!/usr/bin/env python
"""
MCP System Diagnostic Tool
Checks all components of the MCP system (server, host, and client)
"""

import asyncio
import subprocess
import sys
import os
import json
import requests
from pepperpymcp import MCPClient
from pepperpymcp.transports import SSETransport

class MCPDiagnostic:
    """Diagnoses the MCP system components"""
    
    def __init__(self):
        self.results = {
            "server": {
                "running": False,
                "port": 8000,
                "url": "http://localhost:8000",
                "details": {}
            },
            "host": {
                "running": False,
                "details": {}
            },
            "client": {
                "available": False,
                "details": {}
            },
            "connections": {
                "server_to_host": False,
                "host_to_client": False
            }
        }
    
    async def check_server(self):
        """Check if MCP server is running"""
        print("\n🔍 Checking MCP Server...")
        
        try:
            # Try to connect to server
            transport = SSETransport(self.results["server"]["url"])
            client = MCPClient(transport)
            
            await client.connect()
            server_info = await client.initialize()
            
            # Get server capabilities
            tools_response = await client.list_tools()
            resources_response = await client.list_resources()
            prompts_response = await client.list_prompts()
            
            # Disconnect
            await client.disconnect()
            
            # Update results
            self.results["server"]["running"] = True
            self.results["server"]["details"] = {
                "info": server_info,
                "tools_count": len(tools_response.get("tools", [])),
                "resources_count": len(resources_response.get("resources", [])),
                "prompts_count": len(prompts_response.get("prompts", []))
            }
            
            print(f"✅ MCP Server is running at {self.results['server']['url']}")
            print(f"   Found {self.results['server']['details']['tools_count']} tools, " +
                  f"{self.results['server']['details']['resources_count']} resources, " +
                  f"{self.results['server']['details']['prompts_count']} prompts")
            
        except Exception as e:
            print(f"❌ MCP Server is not running or not accessible: {str(e)}")
    
    def check_host(self):
        """Check if MCP host processes are running"""
        print("\n🔍 Checking MCP Host Processes...")
        
        try:
            # Check for running MCP host processes
            result = subprocess.run(
                ["pgrep", "-f", "mcp_host.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split("\n")
                self.results["host"]["running"] = True
                self.results["host"]["details"]["pids"] = pids
                
                print(f"✅ MCP Host is running (PIDs: {', '.join(pids)})")
            else:
                print("❌ No MCP Host processes found")
        except Exception as e:
            print(f"❌ Error checking MCP Host: {str(e)}")
    
    def check_client(self):
        """Check if MCP web client is available"""
        print("\n🔍 Checking MCP Web Client...")
        
        # Check for index.html file
        index_path = os.path.abspath("index.html")
        if os.path.exists(index_path):
            self.results["client"]["available"] = True
            self.results["client"]["details"]["path"] = index_path
            
            print(f"✅ MCP Web Client is available at {index_path}")
        else:
            print(f"❌ MCP Web Client not found at {index_path}")
        
        # Check for HTTP server
        try:
            result = subprocess.run(
                ["pgrep", "-f", "http.server"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split("\n")
                self.results["client"]["details"]["http_server_pids"] = pids
                
                print(f"✅ HTTP Server is running (PIDs: {', '.join(pids)})")
            else:
                print("❌ No HTTP Server processes found")
        except Exception as e:
            print(f"❌ Error checking HTTP Server: {str(e)}")
    
    def check_connections(self):
        """Check connections between components"""
        print("\n🔍 Checking Component Connections...")
        
        # Check server-to-host connection
        if self.results["server"]["running"] and self.results["host"]["running"]:
            # We assume if both are running, they can connect
            self.results["connections"]["server_to_host"] = True
            print("✅ Server to Host connection is possible")
        else:
            print("❌ Server to Host connection may not be possible")
        
        # Check host-to-client connection
        if self.results["host"]["running"] and self.results["client"]["available"]:
            # Check if client can access HTTP endpoints
            try:
                if "http_server_pids" in self.results["client"]["details"]:
                    self.results["connections"]["host_to_client"] = True
                    print("✅ Host to Client connection is possible")
                else:
                    print("❌ Host to Client connection may not be possible (HTTP server not running)")
            except:
                print("❌ Host to Client connection status unknown")
        else:
            print("❌ Host to Client connection may not be possible")
    
    def print_summary(self):
        """Print a summary of the diagnostic results"""
        print("\n📊 MCP System Diagnostic Summary")
        print("================================")
        
        # Server
        server_status = "✅ Running" if self.results["server"]["running"] else "❌ Not running"
        print(f"MCP Server: {server_status}")
        
        # Host
        host_status = "✅ Running" if self.results["host"]["running"] else "❌ Not running"
        print(f"MCP Host: {host_status}")
        
        # Client
        client_status = "✅ Available" if self.results["client"]["available"] else "❌ Not available"
        print(f"Web Client: {client_status}")
        
        # Connections
        server_host_conn = "✅ OK" if self.results["connections"]["server_to_host"] else "❌ Issue"
        host_client_conn = "✅ OK" if self.results["connections"]["host_to_client"] else "❌ Issue"
        print(f"Server → Host Connection: {server_host_conn}")
        print(f"Host → Client Connection: {host_client_conn}")
        
        # Overall system status
        overall_status = (
            self.results["server"]["running"] and
            self.results["host"]["running"] and
            self.results["client"]["available"] and
            self.results["connections"]["server_to_host"] and
            self.results["connections"]["host_to_client"]
        )
        
        print("\n🏁 Overall System Status: " + 
              ("✅ FULLY OPERATIONAL" if overall_status else "⚠️ ISSUES DETECTED"))
        
        if not overall_status:
            print("\n🔧 Troubleshooting Recommendations:")
            if not self.results["server"]["running"]:
                print("  • Start the MCP server: cd ../00-hello-world && python server.py")
            if not self.results["host"]["running"]:
                print("  • Start the MCP host: python mcp_host.py --demo --server http://localhost:8000")
            if not self.results["client"]["available"]:
                print("  • Verify index.html exists in the current directory")
            if not "http_server_pids" in self.results["client"]["details"]:
                print("  • Start the HTTP server: python -m http.server 3000")

async def main():
    """Main diagnostic function"""
    print("🚀 Starting MCP System Diagnostic")
    print("================================")
    
    diagnostic = MCPDiagnostic()
    
    # Run checks
    await diagnostic.check_server()
    diagnostic.check_host()
    diagnostic.check_client()
    diagnostic.check_connections()
    
    # Print summary
    diagnostic.print_summary()

if __name__ == "__main__":
    asyncio.run(main()) 