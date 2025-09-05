"""Comprehensive Logfire middleware for logging ALL MCP requests and responses."""

import json
import time
from typing import Any
import logfire


class LogfireMiddleware:
    """Middleware to log ALL MCP messages and responses to Logfire."""

    def __init__(self):
        """Initialize Logfire (uses LOGFIRE_TOKEN from environment)."""
        # Only configure if not already configured
        if not hasattr(logfire, "_configured"):
            logfire.configure()
            logfire._configured = True

    def on_message(self, context: Any, call_next: Any) -> Any:
        """Log ALL MCP messages at the protocol level.

        This intercepts every MCP message, including tool calls, initialization,
        and any other MCP protocol messages.

        Args:
            context: MCP context containing message details
            call_next: Function to continue message processing

        Returns:
            The response from message processing
        """
        # Extract message details safely
        message = getattr(context, "message", {})
        method = message.get("method", "unknown")
        params = message.get("params", {})
        message_id = message.get("id", "no-id")

        # Create span for this MCP message
        with logfire.span(f"mcp.message.{method}") as span:
            # Log basic message details
            span.set_attribute("mcp.message.method", method)
            span.set_attribute("mcp.message.id", str(message_id))

            # Log the full message structure (truncated for safety)
            try:
                message_str = json.dumps(message)
                if len(message_str) > 2000:
                    message_str = message_str[:2000] + "..."
                span.set_attribute("mcp.message.full", message_str)
            except (TypeError, ValueError):
                span.set_attribute("mcp.message.full", str(message)[:2000])

            # For tool calls, extract more details
            if method == "tools/call":
                tool_name = params.get("name", "unknown-tool")
                tool_args = params.get("arguments", {})

                span.set_attribute("mcp.tool.name", tool_name)

                # Log tool arguments
                try:
                    args_str = json.dumps(tool_args)
                    if len(args_str) > 1000:
                        args_str = args_str[:1000] + "..."
                    span.set_attribute("mcp.tool.arguments", args_str)
                except (TypeError, ValueError):
                    span.set_attribute("mcp.tool.arguments", str(tool_args)[:1000])

            # Log client info if available
            if hasattr(context, "client_info"):
                client_info = context.client_info
                if hasattr(client_info, "name"):
                    span.set_attribute("mcp.client.name", client_info.name)
                if hasattr(client_info, "version"):
                    span.set_attribute("mcp.client.version", client_info.version)

            start_time = time.time()

            try:
                # Process the message
                response = call_next(context)

                # Log successful response
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("mcp.duration_ms", duration_ms)
                span.set_attribute("mcp.success", True)

                # Log response details
                try:
                    response_str = json.dumps(response)
                    span.set_attribute("mcp.response.size_bytes", len(response_str))

                    # Log response sample (truncated)
                    if len(response_str) <= 1000:
                        span.set_attribute("mcp.response.sample", response_str)
                    else:
                        span.set_attribute(
                            "mcp.response.sample", response_str[:1000] + "..."
                        )

                except (TypeError, ValueError):
                    span.set_attribute("mcp.response.size_bytes", 0)
                    span.set_attribute("mcp.response.sample", str(response)[:1000])

                # Log success message
                if method == "tools/call":
                    tool_name = params.get("name", "unknown-tool")
                    logfire.info(
                        f"Tool call '{tool_name}' completed successfully",
                        method=method,
                        tool=tool_name,
                        duration_ms=duration_ms,
                    )
                else:
                    logfire.info(
                        f"MCP message '{method}' completed successfully",
                        method=method,
                        duration_ms=duration_ms,
                    )

                return response

            except Exception as e:
                # Log ALL errors - this is crucial for debugging failures
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("mcp.duration_ms", duration_ms)
                span.set_attribute("mcp.success", False)
                span.set_attribute("mcp.error.type", type(e).__name__)
                span.set_attribute("mcp.error.message", str(e))
                span.record_exception(e)

                # Detailed error logging
                if method == "tools/call":
                    tool_name = params.get("name", "unknown-tool")
                    logfire.error(
                        f"Tool call '{tool_name}' FAILED",
                        method=method,
                        tool=tool_name,
                        duration_ms=duration_ms,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        full_message=message,
                    )
                else:
                    logfire.error(
                        f"MCP message '{method}' FAILED",
                        method=method,
                        duration_ms=duration_ms,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        full_message=message,
                    )

                # Re-raise the exception so it propagates normally
                raise
