#!/bin/bash
# MCP Example Runner
# This script helps with running the MCP examples

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Function to print success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info messages
info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Function to print error messages
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i:$1 &>/dev/null
    return $?
}

# Function to start a server in the background
start_server() {
    local example_dir=$1
    local port=$2
    local server_name=$3
    
    cd "../$example_dir" || { error "Could not find directory $example_dir"; return 1; }
    
    if is_port_in_use $port; then
        error "Port $port is already in use. Cannot start $server_name server."
        return 1
    fi
    
    info "Starting $server_name server on port $port..."
    uv run server.py --port $port &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 2
    
    if ! is_port_in_use $port; then
        error "Failed to start $server_name server."
        return 1
    fi
    
    success "$server_name server started on port $port (PID: $SERVER_PID)"
    cd - > /dev/null
    return 0
}

# Function to stop all servers
stop_servers() {
    section "Stopping Servers"
    
    # Kill any started servers
    if [ -n "$SERVER_PIDS" ]; then
        for pid in $SERVER_PIDS; do
            info "Stopping server with PID $pid..."
            kill $pid 2>/dev/null
        done
        success "All servers stopped."
    else
        info "No servers were started."
    fi
}

# Handle Ctrl+C
trap stop_servers EXIT INT TERM

# Main menu
main_menu() {
    SERVER_PIDS=""
    
    while true; do
        section "MCP Example Runner"
        echo "1. Start Hello World server (port 8000)"
        echo "2. Start File Explorer server (port 8001)"
        echo "3. Start Web Search server (port 8002)"
        echo "4. Start Database Query server (port 8003)"
        echo "5. Start Web Client"
        echo "6. Start MCP Host Demo"
        echo "7. Start MCP Host Interactive Mode"
        echo "8. Stop all servers"
        echo "9. Exit"
        
        read -p "Enter your choice: " choice
        
        case $choice in
            1)
                section "Starting Hello World Server"
                if start_server "00-hello-world" 8000 "Hello World"; then
                    SERVER_PIDS="$SERVER_PIDS $SERVER_PID"
                fi
                ;;
            2)
                section "Starting File Explorer Server"
                if start_server "01-file-explorer" 8001 "File Explorer"; then
                    SERVER_PIDS="$SERVER_PIDS $SERVER_PID"
                fi
                ;;
            3)
                section "Starting Web Search Server"
                if start_server "02-web-search" 8002 "Web Search"; then
                    SERVER_PIDS="$SERVER_PIDS $SERVER_PID"
                fi
                ;;
            4)
                section "Starting Database Query Server"
                if start_server "03-database-query" 8003 "Database Query"; then
                    SERVER_PIDS="$SERVER_PIDS $SERVER_PID"
                fi
                ;;
            5)
                section "Starting Web Client"
                info "Opening web client in your default browser..."
                
                # Try to open browser based on OS
                if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    xdg-open index.html &>/dev/null
                elif [[ "$OSTYPE" == "darwin"* ]]; then
                    open index.html
                elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
                    start index.html
                else
                    python -m http.server 3000 &
                    SERVER_PIDS="$SERVER_PIDS $!"
                    info "Web client running at http://localhost:3000"
                fi
                
                success "Web client started"
                ;;
            6)
                section "Starting MCP Host Demo"
                read -p "Enter server URL (e.g., http://localhost:8000): " server_url
                
                if [ -z "$server_url" ]; then
                    error "Server URL is required"
                    continue
                fi
                
                info "Running MCP Host demo with server $server_url..."
                uv run mcp_host.py --demo --server "$server_url"
                success "Demo completed"
                ;;
            7)
                section "Starting MCP Host Interactive Mode"
                info "Running MCP Host in interactive mode..."
                uv run mcp_host.py --interactive
                success "Interactive mode exited"
                ;;
            8)
                stop_servers
                SERVER_PIDS=""
                ;;
            9)
                section "Exiting"
                info "Cleaning up..."
                exit 0
                ;;
            *)
                error "Invalid choice. Please try again."
                ;;
        esac
        
        echo -e "\nPress Enter to continue..."
        read
    done
}

# Check if Python is installed
if ! command -v python &>/dev/null; then
    error "Python is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Start the main menu
main_menu 