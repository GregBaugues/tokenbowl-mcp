#!/usr/bin/env python3
"""FastAPI wrapper for Token Bowl MCP Server with monitoring dashboard"""

import os
import sys
import json
import time
import asyncio
from typing import Optional
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from request_logger import RequestLogger
import sleeper_mcp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger_module = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Token Bowl MCP Monitor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize request logger
logger = RequestLogger(maxlen=1000)

# Dashboard HTML (embedded)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token Bowl MCP Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: #1e293b;
            padding: 20px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #38bdf8;
            font-size: 2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        
        .stat-label {
            color: #94a3b8;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .stat-value {
            color: #38bdf8;
            font-size: 2em;
            font-weight: bold;
        }
        
        .filters {
            background: #1e293b;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        select, input {
            background: #334155;
            color: #e2e8f0;
            border: 1px solid #475569;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
        }
        
        button {
            background: #38bdf8;
            color: #0f172a;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        
        button:hover {
            background: #0284c7;
        }
        
        .logs-container {
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .log-header {
            background: #334155;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .log-list {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .log-entry {
            border-bottom: 1px solid #334155;
            padding: 15px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .log-entry:hover {
            background: #334155;
        }
        
        .log-entry.error {
            border-left: 3px solid #ef4444;
        }
        
        .log-entry.success {
            border-left: 3px solid #10b981;
        }
        
        .log-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .log-tool {
            color: #38bdf8;
            font-weight: 500;
        }
        
        .log-time {
            color: #94a3b8;
            font-size: 0.9em;
        }
        
        .log-details {
            display: none;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #475569;
        }
        
        .log-details.expanded {
            display: block;
        }
        
        .log-params, .log-response {
            background: #0f172a;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .error-message {
            color: #ef4444;
            margin-top: 10px;
        }
        
        .duration {
            color: #fbbf24;
        }
        
        .chart-container {
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            height: 300px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .refresh-indicator {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <div class="container">
            <h1>🏈 Token Bowl MCP Monitor</h1>
        </div>
    </header>
    
    <div class="container">
        <!-- Statistics Cards -->
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="stat-label">Total Requests</div>
                <div class="stat-value" id="totalRequests">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value" id="successRate">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Response Time</div>
                <div class="stat-value" id="avgResponse">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Uptime</div>
                <div class="stat-value" id="uptime">-</div>
            </div>
        </div>
        
        <!-- Tool Usage Chart -->
        <div class="chart-container">
            <canvas id="toolChart"></canvas>
        </div>
        
        <!-- Filters -->
        <div class="filters">
            <select id="toolFilter">
                <option value="">All Tools</option>
            </select>
            
            <select id="statusFilter">
                <option value="">All Status</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
            </select>
            
            <input type="text" id="searchFilter" placeholder="Search in logs...">
            
            <button onclick="clearLogs()">Clear Logs</button>
            <button onclick="exportLogs()">Export JSON</button>
            
            <div class="auto-refresh">
                <input type="checkbox" id="autoRefresh" checked>
                <label for="autoRefresh">Auto-refresh</label>
                <div class="refresh-indicator"></div>
            </div>
        </div>
        
        <!-- Logs -->
        <div class="logs-container">
            <div class="log-header">
                <h2>Request Logs</h2>
                <span id="logCount">0 logs</span>
            </div>
            <div class="log-list" id="logList">
                <div class="loading">Loading logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        let logs = [];
        let stats = {};
        let autoRefreshInterval = null;
        let toolChart = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            loadData();
            setupAutoRefresh();
            setupFilters();
        });
        
        function initChart() {
            const ctx = document.getElementById('toolChart').getContext('2d');
            toolChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Tool Usage',
                        data: [],
                        backgroundColor: '#38bdf8',
                        borderColor: '#0284c7',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Tool Usage Statistics',
                            color: '#e2e8f0'
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: '#334155'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: '#334155'
                            }
                        }
                    }
                }
            });
        }
        
        async function loadData() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/stats');
                stats = await statsResponse.json();
                updateStats(stats);
                updateChart(stats);
                
                // Load logs
                const logsResponse = await fetch('/api/logs?limit=100');
                logs = await logsResponse.json();
                updateLogs(logs);
                updateToolFilter(stats);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function updateStats(stats) {
            document.getElementById('totalRequests').textContent = stats.total_requests || '0';
            document.getElementById('successRate').textContent = (stats.success_rate || 0) + '%';
            document.getElementById('avgResponse').textContent = (stats.avg_response_time_ms || 0).toFixed(1) + 'ms';
            
            // Format uptime
            const uptime = stats.uptime_seconds || 0;
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            document.getElementById('uptime').textContent = `${hours}h ${minutes}m`;
        }
        
        function updateChart(stats) {
            if (!stats.tools_usage) return;
            
            const tools = Object.keys(stats.tools_usage);
            const counts = tools.map(tool => stats.tools_usage[tool].count);
            
            toolChart.data.labels = tools;
            toolChart.data.datasets[0].data = counts;
            toolChart.update();
        }
        
        function updateLogs(logs) {
            const logList = document.getElementById('logList');
            const logCount = document.getElementById('logCount');
            
            if (logs.length === 0) {
                logList.innerHTML = '<div class="loading">No logs yet</div>';
                logCount.textContent = '0 logs';
                return;
            }
            
            logCount.textContent = `${logs.length} logs`;
            
            logList.innerHTML = logs.map(log => `
                <div class="log-entry ${log.status}" onclick="toggleDetails(this)">
                    <div class="log-meta">
                        <span class="log-tool">${log.tool}</span>
                        <span class="log-time">${formatTime(log.timestamp)}</span>
                    </div>
                    <div>
                        <span class="duration">⚡ ${log.duration_ms}ms</span>
                        ${log.status === 'error' ? '<span style="color: #ef4444; margin-left: 10px;">❌ Error</span>' : ''}
                    </div>
                    <div class="log-details">
                        ${log.params ? `
                            <div>
                                <strong>Parameters:</strong>
                                <div class="log-params">${JSON.stringify(log.params, null, 2)}</div>
                            </div>
                        ` : ''}
                        ${log.response ? `
                            <div>
                                <strong>Response:</strong>
                                <div class="log-response">${typeof log.response === 'string' ? log.response : JSON.stringify(log.response, null, 2)}</div>
                            </div>
                        ` : ''}
                        ${log.error ? `
                            <div class="error-message">
                                <strong>Error:</strong> ${log.error}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function updateToolFilter(stats) {
            const toolFilter = document.getElementById('toolFilter');
            const currentValue = toolFilter.value;
            
            if (!stats.tools_usage) return;
            
            const tools = Object.keys(stats.tools_usage);
            toolFilter.innerHTML = '<option value="">All Tools</option>' + 
                tools.map(tool => `<option value="${tool}">${tool}</option>`).join('');
            
            toolFilter.value = currentValue;
        }
        
        function toggleDetails(element) {
            const details = element.querySelector('.log-details');
            details.classList.toggle('expanded');
        }
        
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) {
                return `${Math.floor(diff / 1000)}s ago`;
            } else if (diff < 3600000) {
                return `${Math.floor(diff / 60000)}m ago`;
            } else {
                return date.toLocaleTimeString();
            }
        }
        
        function setupAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            
            const startRefresh = () => {
                autoRefreshInterval = setInterval(loadData, 5000);
            };
            
            const stopRefresh = () => {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            };
            
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    startRefresh();
                } else {
                    stopRefresh();
                }
            });
            
            if (checkbox.checked) {
                startRefresh();
            }
        }
        
        function setupFilters() {
            const toolFilter = document.getElementById('toolFilter');
            const statusFilter = document.getElementById('statusFilter');
            const searchFilter = document.getElementById('searchFilter');
            
            const applyFilters = async () => {
                let url = '/api/logs?limit=100';
                
                if (toolFilter.value) {
                    url += `&tool=${encodeURIComponent(toolFilter.value)}`;
                }
                
                if (statusFilter.value) {
                    url += `&status=${encodeURIComponent(statusFilter.value)}`;
                }
                
                const response = await fetch(url);
                let filteredLogs = await response.json();
                
                // Apply search filter client-side
                if (searchFilter.value) {
                    const search = searchFilter.value.toLowerCase();
                    filteredLogs = filteredLogs.filter(log => 
                        log.tool.toLowerCase().includes(search) ||
                        JSON.stringify(log.params).toLowerCase().includes(search) ||
                        JSON.stringify(log.response).toLowerCase().includes(search)
                    );
                }
                
                updateLogs(filteredLogs);
            };
            
            toolFilter.addEventListener('change', applyFilters);
            statusFilter.addEventListener('change', applyFilters);
            searchFilter.addEventListener('input', applyFilters);
        }
        
        async function clearLogs() {
            if (confirm('Clear all logs? This cannot be undone.')) {
                await fetch('/api/logs', { method: 'DELETE' });
                loadData();
            }
        }
        
        function exportLogs() {
            const dataStr = JSON.stringify(logs, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = `mcp-logs-${new Date().toISOString()}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the monitoring dashboard"""
    return DASHBOARD_HTML


@app.get("/api/logs")
async def get_logs(
    limit: Optional[int] = 100, tool: Optional[str] = None, status: Optional[str] = None
):
    """Get request/response logs with optional filtering"""
    return logger.get_logs(limit=limit, tool=tool, status=status)


@app.delete("/api/logs")
async def clear_logs():
    """Clear all logs from memory"""
    logger.clear()
    return {"message": "Logs cleared"}


@app.get("/api/stats")
async def get_stats():
    """Get aggregated statistics"""
    return logger.get_stats()


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "tokenbowl-mcp"}


@app.get("/sse")
async def handle_sse(request: Request):
    """Handle Server-Sent Events for MCP communication"""

    async def event_generator():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"

        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.post("/sse")
async def handle_mcp_request(request: Request):
    """Handle MCP JSON-RPC requests and log them"""
    start_time = time.time()

    try:
        # Get request body
        body = await request.body()
        request_data = json.loads(body) if body else {}

        # Extract method and parameters
        method = request_data.get("method", "unknown")
        params = request_data.get("params", {})
        request_id = request_data.get("id")

        # Extract tool name for logging
        tool_name = method
        if method == "tools/call" and "name" in params:
            tool_name = params["name"]

        # Handle different MCP methods
        if method == "initialize":
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {"tools": {}, "prompts": {}},
                    "serverInfo": {"name": "tokenbowl-mcp", "version": "1.0.0"},
                },
            }
        elif method == "tools/list":
            # List of available tools (hardcoded for now)
            tools = [
                {
                    "name": "get_league_info",
                    "description": "Get comprehensive information about the Token Bowl fantasy football league",
                },
                {
                    "name": "get_league_rosters",
                    "description": "Get all team rosters in the Token Bowl league with player assignments",
                },
                {
                    "name": "get_league_users",
                    "description": "Get all users (team owners) participating in the Token Bowl league",
                },
                {
                    "name": "get_league_matchups",
                    "description": "Get head-to-head matchups for a specific week in the Token Bowl league",
                },
                {
                    "name": "get_league_transactions",
                    "description": "Get recent transactions in the Token Bowl league",
                },
                {
                    "name": "get_league_traded_picks",
                    "description": "Get information about traded draft picks in the Token Bowl league",
                },
                {
                    "name": "get_league_drafts",
                    "description": "Get all drafts associated with the Token Bowl league",
                },
                {
                    "name": "get_playoffs_bracket",
                    "description": "Get the current playoff bracket for the Token Bowl league",
                },
                {
                    "name": "get_user",
                    "description": "Get detailed information about a specific Sleeper user",
                },
                {
                    "name": "get_user_leagues",
                    "description": "Get all leagues a user is participating in for a specific season",
                },
                {
                    "name": "get_user_drafts",
                    "description": "Get all drafts a user is participating in for a specific season",
                },
                {
                    "name": "get_all_nfl_players",
                    "description": "Get comprehensive data for all NFL players (cached in Redis)",
                },
                {
                    "name": "get_trending_players_add",
                    "description": "Get NFL players trending up (being added to rosters)",
                },
                {
                    "name": "get_trending_players_drop",
                    "description": "Get NFL players trending down (being dropped from rosters)",
                },
                {
                    "name": "search_player_by_name",
                    "description": "Search for NFL players by name (uses cached data)",
                },
                {
                    "name": "search_player_by_id",
                    "description": "Get NFL player details by player ID (uses cached data)",
                },
                {
                    "name": "get_players_cache_status",
                    "description": "Get status information about the NFL players cache",
                },
                {
                    "name": "refresh_players_cache",
                    "description": "Force refresh of the NFL players cache from Sleeper API",
                },
                {
                    "name": "get_draft",
                    "description": "Get comprehensive information about a specific fantasy draft",
                },
                {
                    "name": "get_draft_picks",
                    "description": "Get all player selections from a completed or in-progress draft",
                },
                {
                    "name": "get_draft_traded_picks",
                    "description": "Get information about draft picks that were traded before or during a draft",
                },
            ]
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools},
            }
        elif method == "tools/call":
            # Call the actual tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            # Try to get the tool function from sleeper_mcp module
            if hasattr(sleeper_mcp, tool_name):
                # Execute the tool
                try:
                    tool_obj = getattr(sleeper_mcp, tool_name)
                    # If it's a FunctionTool object, get the underlying function
                    if hasattr(tool_obj, "fn"):
                        result = await tool_obj.fn(**tool_args)
                    else:
                        result = await tool_obj(**tool_args)

                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, default=str),
                                }
                            ]
                        },
                    }
                except Exception as tool_error:
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution error: {str(tool_error)}",
                        },
                    }
            else:
                response_data = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}",
                    },
                }
        else:
            # Unknown method
            response_data = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        # Log the request
        duration = time.time() - start_time
        is_error = "error" in response_data

        logger.log_request(
            tool_name=tool_name,
            params=params,
            response=response_data.get("result", response_data.get("error")),
            duration=duration,
            status="error" if is_error else "success",
            error=response_data.get("error", {}).get("message") if is_error else None,
        )

        return JSONResponse(content=response_data)

    except Exception as e:
        # Log error
        duration = time.time() - start_time
        logger.log_request(
            tool_name="unknown",
            params={},
            response=str(e),
            duration=duration,
            status="error",
            error=str(e),
        )

        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if "request_data" in locals() else None,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }

        return JSONResponse(content=error_response, status_code=500)


def main():
    """Main entry point for the application"""
    # Check for environment variable or command line argument
    if os.getenv("RENDER") or (len(sys.argv) > 1 and sys.argv[1] == "http"):
        # Use PORT env variable (required by Render) or command line arg
        port = int(os.getenv("PORT", 8000))
        if len(sys.argv) > 2:
            port = int(sys.argv[2])

        # Bind to 0.0.0.0 for external access (required for cloud deployment)
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Default to localhost for local development
        uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
