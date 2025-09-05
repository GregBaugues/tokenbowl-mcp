"""Lightweight Logfire middleware for logging MCP requests and responses."""

import json
import time
from typing import Any
import logfire


class LogfireMiddleware:
    """Middleware to log MCP requests and responses to Logfire."""

    def __init__(self):
        """Initialize Logfire (uses LOGFIRE_TOKEN from environment)."""
        # Only configure if not already configured
        if not hasattr(logfire, "_configured"):
            logfire.configure()
            logfire._configured = True

    async def __call__(self, method: str, params: Any, next_handler) -> Any:
        """Log MCP request and response.

        Args:
            method: The MCP method/tool name being called
            params: The parameters passed to the tool
            next_handler: The next handler in the middleware chain

        Returns:
            The response from the tool
        """
        # Log the request and response with timing
        with logfire.span(f"mcp.{method}") as span:
            # Log request details
            span.set_attribute("mcp.tool", method)

            # Safely serialize params
            try:
                params_str = json.dumps(params) if params else "{}"
                # Truncate large params to keep logs lightweight
                if len(params_str) > 1000:
                    params_str = params_str[:1000] + "..."
                span.set_attribute("mcp.request.params", params_str)
            except (TypeError, ValueError):
                span.set_attribute("mcp.request.params", str(params)[:1000])

            start_time = time.time()

            try:
                # Call the actual tool
                response = await next_handler(method, params)

                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("mcp.duration_ms", duration_ms)
                span.set_attribute("mcp.success", True)

                # Log response size (not full content to keep it lightweight)
                try:
                    response_str = json.dumps(response)
                    span.set_attribute("mcp.response.size_bytes", len(response_str))

                    # Log a sample of the response for debugging (first 500 chars)
                    if len(response_str) <= 500:
                        span.set_attribute("mcp.response.sample", response_str)
                    else:
                        span.set_attribute(
                            "mcp.response.sample", response_str[:500] + "..."
                        )
                except (TypeError, ValueError):
                    span.set_attribute("mcp.response.size_bytes", 0)
                    span.set_attribute("mcp.response.sample", str(response)[:500])

                logfire.info(
                    f"MCP {method} completed",
                    duration_ms=duration_ms,
                )

                return response

            except Exception as e:
                # Log error details
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("mcp.duration_ms", duration_ms)
                span.set_attribute("mcp.success", False)
                span.set_attribute("mcp.error.type", type(e).__name__)
                span.set_attribute("mcp.error.message", str(e))
                span.record_exception(e)

                logfire.error(
                    f"MCP {method} failed",
                    duration_ms=duration_ms,
                    error=str(e),
                )

                raise
