# Issue #28: Integrate Logfire for Request/Response Logging

**Issue URL:** https://github.com/GregBaugues/sleeper-mcp/issues/28

## Problem Statement

Integrate Logfire (Pydantic's observability platform) into the FastMCP server to log all MCP requests and responses. The LOGFIRE_TOKEN is already configured in both local `.env` and Render deployment.

## Prior Art & Context

1. **Previous Monitoring Attempt**: PR #10 implemented a monitoring dashboard that was later reverted. It used:
   - FastAPI wrapper approach 
   - In-memory circular buffer for request storage
   - Dashboard UI at root URL
   - API endpoints for logs and stats

2. **Current Setup**:
   - FastMCP server with 20 tools for Sleeper API
   - Uses `httpx` for API calls to Sleeper
   - Redis caching layer for player data
   - Environment-aware transport (HTTP/SSE for web, STDIO for Claude Desktop)

## Technical Approach

### 1. Logfire Integration Strategy

Based on FastMCP's middleware capabilities and Logfire's design, we'll:

1. **Install Logfire**: Add `logfire` to dependencies
2. **Create Custom Middleware**: Implement a FastMCP middleware that:
   - Captures all tool calls (requests and responses)
   - Logs them to Logfire with proper spans and context
   - Includes timing, errors, and metadata
3. **Instrument HTTPX**: Add Logfire instrumentation for outbound API calls
4. **Environment Configuration**: Use LOGFIRE_TOKEN from environment

### 2. Implementation Details

#### A. Dependencies
```python
# pyproject.toml
dependencies = [
    ...,
    "logfire>=1.0.0",
]
```

#### B. Middleware Implementation
```python
# logfire_middleware.py
import logfire
from fastmcp.server.middleware import Middleware, MiddlewareContext
import time
import json

class LogfireMiddleware(Middleware):
    def __init__(self):
        # Initialize Logfire (uses LOGFIRE_TOKEN from env)
        logfire.configure()
        
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log tool calls with request/response data"""
        tool_name = context.method
        params = context.message.get("params", {})
        
        with logfire.span(f"mcp.tool.{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.params", json.dumps(params))
            
            start_time = time.time()
            try:
                result = await call_next(context)
                duration = time.time() - start_time
                
                span.set_attribute("tool.duration_ms", duration * 1000)
                span.set_attribute("tool.success", True)
                span.set_attribute("tool.response_size", len(json.dumps(result)))
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("tool.duration_ms", duration * 1000)
                span.set_attribute("tool.success", False)
                span.set_attribute("tool.error", str(e))
                span.record_exception(e)
                raise
```

#### C. HTTPX Instrumentation
```python
# In sleeper_mcp.py
import logfire

# Configure Logfire once at startup
logfire.configure()

# Instrument HTTPX clients
async with logfire.instrument_httpx().AsyncClient() as client:
    # All HTTP calls will be automatically traced
    response = await client.get(url)
```

#### D. Integration Points

1. **sleeper_mcp.py**: 
   - Initialize Logfire at startup
   - Add LogfireMiddleware to MCP server
   - Wrap httpx clients with instrumentation

2. **Environment Variables**:
   - LOGFIRE_TOKEN (already set)
   - Optional: LOGFIRE_PROJECT_NAME, LOGFIRE_SERVICE_NAME

### 3. Testing Strategy

1. **Unit Tests**: Mock Logfire to verify middleware behavior
2. **Integration Tests**: Verify logging works with actual tool calls
3. **Local Testing**: Run server locally and check Logfire dashboard
4. **Production Validation**: Deploy to Render and verify logs appear

### 4. Rollout Plan

1. Create feature branch
2. Add logfire dependency
3. Implement middleware
4. Update sleeper_mcp.py to use middleware
5. Add HTTPX instrumentation
6. Test locally with LOGFIRE_TOKEN
7. Run existing test suite
8. Deploy to staging/production
9. Verify in Logfire dashboard

### 5. Success Criteria

- [ ] All MCP tool calls are logged to Logfire
- [ ] Request parameters and responses are captured
- [ ] Timing information is recorded
- [ ] Errors are properly tracked with stack traces
- [ ] HTTPX calls to Sleeper API are instrumented
- [ ] No performance degradation
- [ ] Existing tests pass
- [ ] Logs visible in Logfire dashboard

### 6. Risks & Mitigations

- **Risk**: Performance impact from logging
  - **Mitigation**: Logfire is async and designed for production use
  
- **Risk**: Sensitive data exposure
  - **Mitigation**: Review what data is logged, exclude sensitive fields if needed

- **Risk**: Breaking existing functionality
  - **Mitigation**: Comprehensive testing, gradual rollout

## Next Steps

1. Create feature branch for issue #28
2. Install logfire package
3. Implement LogfireMiddleware
4. Integrate with FastMCP server
5. Test and validate
6. Create PR for review