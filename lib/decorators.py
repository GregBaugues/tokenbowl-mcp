"""Decorators for MCP tools.

This module provides decorators that add common functionality to MCP tools,
such as logging, error handling, and observability integration.
"""

import logging
from functools import wraps
import logfire

logger = logging.getLogger(__name__)


def log_mcp_tool(func):
    """Decorator to automatically log MCP tool calls with parameters and responses.

    This decorator adds comprehensive logging and observability to MCP tools:
    - Logs tool invocations with parameters
    - Creates Logfire spans for distributed tracing
    - Handles errors defensively
    - Serializes parameters safely (with truncation)
    - Logs success/failure with context

    The decorator is designed to be defensive - if any logging operation fails,
    the tool execution continues without disruption.

    Args:
        func: Async function to wrap (MCP tool)

    Returns:
        Wrapped async function with logging
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__

        # Prepare parameters for logging (serialize to JSON-safe format) with error handling
        params = {}
        try:
            if args:
                params["args"] = [str(arg)[:200] for arg in args]  # Limit arg length
            if kwargs:
                params["kwargs"] = {
                    k: str(v)[:200] if v is not None else None
                    for k, v in kwargs.items()
                }
        except Exception as e:
            logger.warning(f"Error preparing params for {tool_name}: {e}")
            params = {"error": "Could not serialize parameters"}

        # Create span with defensive error handling
        span = None
        try:
            span = logfire.span(
                f"mcp_tool.{tool_name}",
                tool_name=tool_name,
                parameters=params,
                _tags=["mcp_tool", tool_name],
            )
            span.__enter__()
        except (TypeError, AttributeError) as e:
            # If span creation fails, log the error and continue without span tracking
            logger.error(
                f"Error creating logfire span for {tool_name}: {type(e).__name__}: {e}"
            )
            # Execute function without span tracking
            try:
                result = await func(*args, **kwargs)
                logger.info(f"MCP Tool Called (no span): {tool_name}")
                return result
            except Exception as func_error:
                logger.error(
                    f"MCP Tool Exception (no span): {tool_name} - {type(func_error).__name__}: {func_error}",
                    exc_info=True,
                )
                raise

        # Normal execution with span tracking
        try:
            try:
                # Log the tool invocation
                logger.info(f"MCP Tool Called: {tool_name} with params: {params}")

                # Execute the actual function
                result = await func(*args, **kwargs)

                # Check if result indicates an error
                if isinstance(result, dict) and "error" in result:
                    if span:
                        span.set_attribute("success", False)
                        span.set_attribute("error_message", result["error"])
                    logger.warning(
                        f"MCP Tool Error Response: {tool_name} - {result['error']}"
                    )
                else:
                    if span:
                        span.set_attribute("success", True)

                    # Log response summary (avoid logging huge responses)
                    response_summary = None
                    if isinstance(result, list):
                        response_summary = f"List with {len(result)} items"
                    elif isinstance(result, dict):
                        response_summary = f"Dict with keys: {list(result.keys())[:10]}"
                    else:
                        response_summary = str(type(result))

                    if span:
                        span.set_attribute("response_type", response_summary)

                    logger.info(f"MCP Tool Success: {tool_name} - {response_summary}")

                return result

            except Exception as e:
                if span:
                    span.set_attribute("success", False)
                    span.set_attribute("error_type", type(e).__name__)
                    span.set_attribute("error_message", str(e))

                logger.error(
                    f"MCP Tool Exception: {tool_name} - {type(e).__name__}: {str(e)}",
                    exc_info=True,
                )

                # Re-raise the exception to maintain original behavior
                raise
        finally:
            # Safely exit the span if it was created
            if span:
                try:
                    span.__exit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing span for {tool_name}: {e}")

    return wrapper
