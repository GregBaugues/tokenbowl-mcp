# Issue #6: Add MCP Request/Response Monitoring Dashboard

**GitHub Issue:** https://github.com/GregBaugues/sleeper-mcp/issues/6

## Problem Statement
The MCP server currently runs without visibility into request/response traffic. We need a monitoring dashboard to track tool usage, performance metrics, and error rates.

## Implementation Plan

### Architecture Overview

Since FastMCP doesn't natively support custom HTTP routes alongside the MCP server, we'll need to:
1. Run a separate FastAPI application on the same port
2. Use FastAPI to handle both the dashboard routes AND proxy MCP requests 
3. Implement request/response logging in the proxy layer
4. Store logs in memory using collections.deque (circular buffer)

### Step-by-Step Implementation

#### 1. Restructure the Application
- Create a new file `app.py` that combines FastAPI with the MCP server
- FastAPI will handle:
  - `/` - Dashboard HTML page
  - `/api/logs` - JSON endpoint for log data
  - `/api/stats` - Aggregated statistics
  - `/sse` - Proxy to MCP server (existing endpoint)
- The MCP server will run as a subprocess or be integrated directly

#### 2. Request/Response Logging System
```python
from collections import deque
from datetime import datetime
import json

class RequestLogger:
    def __init__(self, maxlen=1000):
        self.logs = deque(maxlen=maxlen)
    
    def log_request(self, tool_name, params, response, duration, status):
        self.logs.append({
            'timestamp': datetime.utcnow().isoformat(),
            'tool': tool_name,
            'params': params,
            'response': response,
            'duration_ms': duration * 1000,
            'status': status,
            'error': None if status == 'success' else response
        })
```

#### 3. Dashboard Backend (FastAPI Routes)
```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return dashboard_html  # Single-page HTML with embedded CSS/JS

@app.get("/api/logs")
async def get_logs(limit: int = 100, tool: str = None):
    # Return filtered logs as JSON
    
@app.get("/api/stats")
async def get_stats():
    # Return aggregated statistics
    
@app.post("/sse")  
async def proxy_mcp_request(request):
    # Log the request
    # Forward to MCP server
    # Log the response
    # Return response
```

#### 4. Dashboard Frontend Design
Single HTML file with:
- **Header:** Token Bowl MCP Monitor
- **Stats Cards:** Total requests, error rate, avg response time
- **Request Timeline:** Scrollable list with expandable details
- **Tool Usage Chart:** Bar chart showing tool frequency
- **Filters:** Tool name, time range, status (success/error)
- **Search:** Full-text search in request/response data
- **Auto-refresh:** Poll `/api/logs` every 5 seconds

#### 5. Implementation Steps

**Phase 1: Create FastAPI wrapper**
- [ ] Create `app.py` with FastAPI application
- [ ] Move MCP server initialization to app.py
- [ ] Set up basic routes (/, /api/logs, /api/stats)
- [ ] Implement MCP proxy at /sse endpoint

**Phase 2: Add logging middleware**
- [ ] Create RequestLogger class with deque storage
- [ ] Intercept MCP requests in proxy layer
- [ ] Extract tool name, params from requests
- [ ] Measure response time and status
- [ ] Store in circular buffer

**Phase 3: Build dashboard backend**
- [ ] Implement /api/logs with filtering
- [ ] Calculate statistics for /api/stats
- [ ] Add pagination support
- [ ] Add export functionality

**Phase 4: Create dashboard UI**
- [ ] Design responsive HTML layout
- [ ] Add CSS styling (embedded)
- [ ] Implement JavaScript for:
  - Fetching and displaying logs
  - Filtering and search
  - Auto-refresh
  - Expandable details
- [ ] Add charts using Chart.js (CDN)

**Phase 5: Testing and Polish**
- [ ] Test with various MCP tool calls
- [ ] Verify memory usage stays bounded
- [ ] Add error handling
- [ ] Performance optimization
- [ ] Mobile responsiveness

### Technical Considerations

1. **Memory Management:** Use deque with maxlen=1000 to limit memory usage
2. **Performance:** Ensure logging doesn't slow down MCP responses
3. **Deployment:** Update render.yaml to use app.py instead of sleeper_mcp.py
4. **Backwards Compatibility:** Ensure /sse endpoint still works for Claude
5. **Security:** Consider adding basic auth in future iteration

### Alternative Approach (if FastAPI integration proves complex)

Run two separate processes:
1. MCP server on port 8001 (internal)
2. FastAPI dashboard on port 8000 (public)
3. Dashboard proxies MCP requests and logs them

This would require process management but might be simpler.

### Files to Create/Modify

1. **New Files:**
   - `app.py` - Main FastAPI application with dashboard
   - `request_logger.py` - Logging and storage logic
   - `dashboard.html` - Embedded in app.py as string

2. **Modified Files:**
   - `sleeper_mcp.py` - Refactor to be importable
   - `render.yaml` - Update start command
   - `pyproject.toml` - Add FastAPI dependency

### Testing Strategy

1. Unit tests for RequestLogger class
2. Integration tests for API endpoints
3. Manual testing of dashboard UI
4. Load testing to verify performance
5. Memory usage monitoring

### Success Criteria

- [ ] Dashboard accessible at root URL
- [ ] All MCP requests logged and visible
- [ ] Performance metrics displayed
- [ ] Search and filter functionality works
- [ ] No impact on MCP server performance
- [ ] Memory usage stays within limits