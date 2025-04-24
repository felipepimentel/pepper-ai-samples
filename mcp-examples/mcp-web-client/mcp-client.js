/**
 * MCP Web Client
 * 
 * This client implements the Model Context Protocol to communicate with MCP servers
 * using Server-Sent Events (SSE).
 */

class MCPClient {
    constructor() {
        this.serverUrl = '';
        this.eventSource = null;
        this.serverInfo = null;
        this.tools = [];
        this.resources = [];
        this.prompts = [];
        this.pendingRequests = new Map();
        this.requestId = 1;
        this.isConnected = false;
        this.connectionCallbacks = [];

        // Initialize UI elements
        this.initUI();
    }

    initUI() {
        // Connection handling
        document.getElementById('connectButton').addEventListener('click', () => this.connect());
        document.getElementById('serverSelect').addEventListener('change', (e) => {
            document.getElementById('customServer').value = e.target.value;
        });

        // Tool execution
        document.getElementById('toolSelect').addEventListener('change', (e) => this.onToolSelected(e.target.value));
        document.getElementById('executeTool').addEventListener('click', () => this.executeTool());

        // Resource fetching
        document.getElementById('resourcePattern').addEventListener('change', (e) => this.onResourceSelected(e.target.value));
        document.getElementById('fetchResource').addEventListener('click', () => this.fetchResource());

        // Prompt generation
        document.getElementById('promptSelect').addEventListener('change', (e) => this.onPromptSelected(e.target.value));
        document.getElementById('generatePrompt').addEventListener('click', () => this.generatePrompt());
    }

    async connect() {
        // First, disconnect if already connected
        if (this.isConnected) {
            this.disconnect();
        }

        // Get server URL
        const serverUrl = document.getElementById('customServer').value.trim();
        if (!serverUrl) {
            alert('Please enter a server URL');
            return;
        }

        this.serverUrl = serverUrl;

        // Check if we're using stdio transport
        if (serverUrl === 'stdio') {
            alert('To use stdio transport, please run the MCP host with:\npython mcp_host.py --demo --stdio');
            this.updateConnectionStatus('Connect via terminal', false);
            return;
        }

        this.updateConnectionStatus('Connecting...', false);
        this.updateFlowDiagram('Connecting...', 'Establishing connection');

        try {
            await this.initialize();
            this.updateConnectionStatus('Connected', true);
            this.setupSSEConnection();
            this.updateServerCapabilities();
            this.populateToolSelect();
            this.populateResourceSelect();
            this.populatePromptSelect();

            // Update UI for connected state
            this.isConnected = true;
            this.connectionCallbacks.forEach(callback => callback(true));
        } catch (error) {
            console.error('Connection error:', error);
            this.updateConnectionStatus('Connection failed', false);
            alert(`Failed to connect: ${error.message}`);
        }
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        this.isConnected = false;
        this.updateConnectionStatus('Disconnected', false);
        this.connectionCallbacks.forEach(callback => callback(false));
    }

    async initialize() {
        // Initialize connection to the server
        const response = await fetch(`${this.serverUrl}/mcp/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        this.serverInfo = data;
        return data;
    }

    setupSSEConnection() {
        // Create a new SSE connection to receive events from the server
        const url = `${this.serverUrl}/mcp/sse`;
        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
            console.log('SSE connection established');
        };

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleServerMessage(data);
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.disconnect();
        };
    }

    handleServerMessage(data) {
        console.log('Message from server:', data);

        // Check if this is a response to a pending request
        if (data.id && this.pendingRequests.has(data.id)) {
            const { resolve, reject } = this.pendingRequests.get(data.id);
            this.pendingRequests.delete(data.id);

            if (data.error) {
                reject(new Error(data.error.message || 'Unknown error'));
            } else {
                resolve(data.result);
            }
        }
    }

    async sendRequest(method, params = {}) {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }

        const id = this.requestId++;

        // Update the flow diagram
        this.updateFlowDiagram(`Request: ${method}`, `MCP ${method}`);

        // Create a promise that will be resolved when we receive a response
        const requestPromise = new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });

            // Set a timeout to fail the request if it takes too long
            setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error('Request timed out'));
                }
            }, 30000); // 30 second timeout
        });

        // Send the request to the server
        const response = await fetch(`${this.serverUrl}/mcp/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id,
                method,
                params
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        // Wait for the response from the server
        const result = await requestPromise;
        return result;
    }

    async listTools() {
        try {
            const result = await this.sendRequest('mcp.list_tools');
            this.tools = result.tools || [];
            return this.tools;
        } catch (error) {
            console.error('Error listing tools:', error);
            throw error;
        }
    }

    async listResources() {
        try {
            const result = await this.sendRequest('mcp.list_resources');
            this.resources = result.resources || [];
            return this.resources;
        } catch (error) {
            console.error('Error listing resources:', error);
            throw error;
        }
    }

    async listPrompts() {
        try {
            const result = await this.sendRequest('mcp.list_prompts');
            this.prompts = result.prompts || [];
            return this.prompts;
        } catch (error) {
            console.error('Error listing prompts:', error);
            throw error;
        }
    }

    async callTool(name, params = {}) {
        try {
            const result = await this.sendRequest('mcp.call_tool', {
                name,
                params
            });
            return result;
        } catch (error) {
            console.error(`Error calling tool ${name}:`, error);
            throw error;
        }
    }

    async getResource(uri) {
        try {
            const result = await this.sendRequest('mcp.get_resource', {
                uri
            });
            return result;
        } catch (error) {
            console.error(`Error getting resource ${uri}:`, error);
            throw error;
        }
    }

    async callPrompt(name, params = {}) {
        try {
            const result = await this.sendRequest('mcp.call_prompt', {
                name,
                params
            });
            return result;
        } catch (error) {
            console.error(`Error calling prompt ${name}:`, error);
            throw error;
        }
    }

    // UI update functions
    updateConnectionStatus(status, isConnected = false) {
        const statusEl = document.getElementById('connectionStatus');
        statusEl.textContent = status;

        if (isConnected) {
            statusEl.classList.remove('status-disconnected');
            statusEl.classList.add('status-connected');
        } else {
            statusEl.classList.remove('status-connected');
            statusEl.classList.add('status-disconnected');
        }
    }

    updateFlowDiagram(requestMsg, mcpRequestMsg) {
        document.getElementById('requestMessage').textContent = requestMsg;
        document.getElementById('mcpRequestMessage').textContent = mcpRequestMsg;
    }

    updateServerCapabilities() {
        const serverInfoDiv = document.getElementById('serverCapabilities');
        const serverName = this.serverInfo?.name || 'Unknown Server';
        const serverDesc = this.serverInfo?.description || 'No description available';

        let toolsCount = 0;
        let resourcesCount = 0;
        let promptsCount = 0;

        // Get counts asynchronously
        Promise.all([
            this.listTools().then(tools => { toolsCount = tools.length; }),
            this.listResources().then(resources => { resourcesCount = resources.length; }),
            this.listPrompts().then(prompts => { promptsCount = prompts.length; })
        ]).then(() => {
            serverInfoDiv.innerHTML = `
                <h5>${serverName}</h5>
                <p>${serverDesc}</p>
                <div class="list-group mt-3">
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        Tools
                        <span class="badge bg-primary rounded-pill">${toolsCount}</span>
                    </div>
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        Resources
                        <span class="badge bg-primary rounded-pill">${resourcesCount}</span>
                    </div>
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        Prompts
                        <span class="badge bg-primary rounded-pill">${promptsCount}</span>
                    </div>
                </div>
            `;
        });
    }

    async populateToolSelect() {
        const tools = await this.listTools();
        const select = document.getElementById('toolSelect');

        // Clear existing options
        select.innerHTML = '<option value="">Select a tool...</option>';

        // Add options for each tool
        tools.forEach(tool => {
            const option = document.createElement('option');
            option.value = tool.name;
            option.textContent = `${tool.name} - ${tool.description || 'No description'}`;
            select.appendChild(option);
        });
    }

    async populateResourceSelect() {
        const resources = await this.listResources();
        const select = document.getElementById('resourcePattern');

        // Clear existing options
        select.innerHTML = '<option value="">Select a resource pattern...</option>';

        // Add options for each resource
        resources.forEach(resource => {
            const option = document.createElement('option');
            option.value = resource.pattern;
            option.textContent = `${resource.pattern} - ${resource.description || 'No description'}`;
            select.appendChild(option);
        });
    }

    async populatePromptSelect() {
        const prompts = await this.listPrompts();
        const select = document.getElementById('promptSelect');

        // Clear existing options
        select.innerHTML = '<option value="">Select a prompt...</option>';

        // Add options for each prompt
        prompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt.name;
            option.textContent = `${prompt.name} - ${prompt.description || 'No description'}`;
            select.appendChild(option);
        });
    }

    onToolSelected(toolName) {
        const tool = this.tools.find(t => t.name === toolName);
        const paramsDiv = document.getElementById('toolParams');

        if (!tool) {
            paramsDiv.innerHTML = '';
            return;
        }

        // Create input fields for each parameter
        let paramInputs = '';
        if (tool.parameters && Array.isArray(tool.parameters)) {
            tool.parameters.forEach(param => {
                paramInputs += `
                    <div class="mb-2">
                        <label for="tool-param-${param.name}" class="form-label">
                            ${param.name} ${param.required ? '<span class="text-danger">*</span>' : ''}
                        </label>
                        <input type="${param.type === 'number' ? 'number' : 'text'}" 
                            class="form-control" 
                            id="tool-param-${param.name}" 
                            placeholder="${param.description || param.name}"
                            ${param.default ? `value="${param.default}"` : ''}
                            ${param.required ? 'required' : ''}>
                        ${param.description ? `<div class="form-text">${param.description}</div>` : ''}
                    </div>
                `;
            });
        }

        paramsDiv.innerHTML = paramInputs || '<p class="text-muted">No parameters required</p>';
    }

    onResourceSelected(pattern) {
        const resource = this.resources.find(r => r.pattern === pattern);
        const paramsDiv = document.getElementById('resourceParams');

        if (!resource) {
            paramsDiv.innerHTML = '';
            return;
        }

        // Extract parameter names from the URI pattern
        const params = [];
        const paramRegex = /{([^}]+)}/g;
        let match;

        while ((match = paramRegex.exec(pattern)) !== null) {
            params.push(match[1]);
        }

        // Create input fields for each parameter
        let paramInputs = '';
        if (params.length > 0) {
            params.forEach(param => {
                paramInputs += `
                    <div class="mb-2">
                        <label for="resource-param-${param}" class="form-label">${param}</label>
                        <input type="text" class="form-control" id="resource-param-${param}" 
                            placeholder="Enter ${param}" required>
                    </div>
                `;
            });
        }

        paramsDiv.innerHTML = paramInputs || '<p class="text-muted">No parameters required</p>';
    }

    onPromptSelected(promptName) {
        const prompt = this.prompts.find(p => p.name === promptName);
        const paramsDiv = document.getElementById('promptParams');

        if (!prompt) {
            paramsDiv.innerHTML = '';
            return;
        }

        // Create input fields for each parameter
        let paramInputs = '';
        if (prompt.parameters && Array.isArray(prompt.parameters)) {
            prompt.parameters.forEach(param => {
                paramInputs += `
                    <div class="mb-2">
                        <label for="prompt-param-${param.name}" class="form-label">
                            ${param.name} ${param.required ? '<span class="text-danger">*</span>' : ''}
                        </label>
                        <input type="${param.type === 'number' ? 'number' : 'text'}" 
                            class="form-control" 
                            id="prompt-param-${param.name}" 
                            placeholder="${param.description || param.name}"
                            ${param.default ? `value="${param.default}"` : ''}
                            ${param.required ? 'required' : ''}>
                        ${param.description ? `<div class="form-text">${param.description}</div>` : ''}
                    </div>
                `;
            });
        }

        paramsDiv.innerHTML = paramInputs || '<p class="text-muted">No parameters required</p>';
    }

    async executeTool() {
        const toolName = document.getElementById('toolSelect').value;

        if (!toolName) {
            alert('Please select a tool');
            return;
        }

        // Collect parameter values
        const params = {};
        const tool = this.tools.find(t => t.name === toolName);

        if (tool && tool.parameters) {
            for (const param of tool.parameters) {
                const input = document.getElementById(`tool-param-${param.name}`);

                if (input) {
                    const value = input.value;

                    // Skip optional parameters with empty values
                    if (!param.required && value === '') {
                        continue;
                    }

                    // Convert to number if needed
                    if (param.type === 'number') {
                        params[param.name] = parseFloat(value);
                    } else {
                        params[param.name] = value;
                    }
                }
            }
        }

        // Execute the tool
        try {
            const result = await this.callTool(toolName, params);

            // Display the result
            const responseEl = document.getElementById('toolResponse');
            responseEl.innerHTML = typeof result === 'object'
                ? `<pre>${JSON.stringify(result, null, 2)}</pre>`
                : `<p>${result}</p>`;
        } catch (error) {
            console.error(`Error executing tool ${toolName}:`, error);

            // Display the error
            const responseEl = document.getElementById('toolResponse');
            responseEl.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
    }

    async fetchResource() {
        const patternValue = document.getElementById('resourcePattern').value;

        if (!patternValue) {
            alert('Please select a resource pattern');
            return;
        }

        // Construct URI by replacing parameters in the pattern
        let uri = patternValue;
        const paramRegex = /{([^}]+)}/g;
        let match;

        while ((match = paramRegex.exec(patternValue)) !== null) {
            const paramName = match[1];
            const input = document.getElementById(`resource-param-${paramName}`);

            if (input && input.value) {
                uri = uri.replace(`{${paramName}}`, encodeURIComponent(input.value));
            } else {
                alert(`Please enter a value for ${paramName}`);
                return;
            }
        }

        // Fetch the resource
        try {
            const result = await this.getResource(uri);

            // Display the result
            const responseEl = document.getElementById('resourceResponse');

            // Try to detect if content is JSON or plain text
            if (typeof result === 'object') {
                responseEl.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            } else if (typeof result === 'string') {
                // Check if it's a stringified JSON
                try {
                    const parsed = JSON.parse(result);
                    responseEl.innerHTML = `<pre>${JSON.stringify(parsed, null, 2)}</pre>`;
                } catch {
                    // It's plain text, check if it might be markdown
                    if (result.includes('#') || result.includes('*') || result.includes('```')) {
                        responseEl.innerHTML = marked.parse(result);
                    } else {
                        responseEl.innerHTML = `<p>${result}</p>`;
                    }
                }
            } else {
                responseEl.innerHTML = `<p>${result}</p>`;
            }
        } catch (error) {
            console.error(`Error fetching resource ${uri}:`, error);

            // Display the error
            const responseEl = document.getElementById('resourceResponse');
            responseEl.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
    }

    async generatePrompt() {
        const promptName = document.getElementById('promptSelect').value;

        if (!promptName) {
            alert('Please select a prompt');
            return;
        }

        // Collect parameter values
        const params = {};
        const prompt = this.prompts.find(p => p.name === promptName);

        if (prompt && prompt.parameters) {
            for (const param of prompt.parameters) {
                const input = document.getElementById(`prompt-param-${param.name}`);

                if (input) {
                    const value = input.value;

                    // Skip optional parameters with empty values
                    if (!param.required && value === '') {
                        continue;
                    }

                    // Convert to number if needed
                    if (param.type === 'number') {
                        params[param.name] = parseFloat(value);
                    } else {
                        params[param.name] = value;
                    }
                }
            }
        }

        // Generate from the prompt
        try {
            const result = await this.callPrompt(promptName, params);

            // Display the result
            const responseEl = document.getElementById('promptResponse');

            if (Array.isArray(result)) {
                // Handle conversation format
                let conversation = '';
                result.forEach(message => {
                    const role = message.role.charAt(0).toUpperCase() + message.role.slice(1);
                    conversation += `<div class="p-2 ${message.role === 'assistant' ? 'bg-light' : ''}">
                        <strong>${role}:</strong> ${message.content}
                    </div>`;
                });
                responseEl.innerHTML = conversation;
            } else if (typeof result === 'object') {
                responseEl.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            } else if (typeof result === 'string') {
                // Check if it might be markdown
                if (result.includes('#') || result.includes('*') || result.includes('```')) {
                    responseEl.innerHTML = marked.parse(result);
                } else {
                    responseEl.innerHTML = `<p>${result}</p>`;
                }
            } else {
                responseEl.innerHTML = `<p>${result}</p>`;
            }
        } catch (error) {
            console.error(`Error generating from prompt ${promptName}:`, error);

            // Display the error
            const responseEl = document.getElementById('promptResponse');
            responseEl.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
    }

    // Register a callback to be called when connection status changes
    onConnectionChange(callback) {
        this.connectionCallbacks.push(callback);
    }
}

// Initialize the client when the page loads
const mcpClient = new MCPClient(); 