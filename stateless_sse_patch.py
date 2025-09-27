#!/usr/bin/env python3
"""
Stateless SSE Patch for FastMCP

A simpler workaround that makes SSE sessions stateless by default,
avoiding the initialization requirement altogether.

This fixes the "Received request before initialization was complete" error
by making every SSE session self-contained and not requiring initialization.
"""

import logging
from typing import Any
from mcp.server.session import ServerSession
from mcp.server.lowlevel.server import Server as MCPServer

logger = logging.getLogger(__name__)

# Store the original ServerSession __init__
_original_init = ServerSession.__init__


def patched_server_session_init(
    self,
    read_stream: Any,
    write_stream: Any,
    init_options: Any,
    stateless: bool = False,
) -> None:
    """
    Patched ServerSession.__init__ that forces stateless=True for SSE connections.

    This is a workaround for the SSE session persistence issue where
    FastMCP creates a new session for each connection but clients expect
    to reuse the same initialized session.
    """
    # Check if this is being called from SSE context
    import inspect

    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame else None

    # Look for SSE-related calls in the stack
    is_sse_context = False
    while caller_frame and not is_sse_context:
        filename = caller_frame.f_code.co_filename
        function_name = caller_frame.f_code.co_name

        # Check if we're in SSE-related code
        if "sse" in filename.lower() or "sse" in function_name.lower():
            is_sse_context = True
            logger.info("Detected SSE context, forcing stateless mode")

        caller_frame = caller_frame.f_back

    # Force stateless mode for SSE connections
    if is_sse_context:
        stateless = True
        logger.info("Forcing stateless=True for SSE session")

    # Call original init with potentially modified stateless parameter
    _original_init(self, read_stream, write_stream, init_options, stateless)


def apply_stateless_sse_patch():
    """
    Apply the patch to make SSE sessions stateless by default.

    This should be called before creating the FastMCP server.
    """
    ServerSession.__init__ = patched_server_session_init
    logger.info("Applied stateless SSE patch to ServerSession")


def remove_stateless_sse_patch():
    """Remove the patch and restore original behavior."""
    ServerSession.__init__ = _original_init
    logger.info("Removed stateless SSE patch from ServerSession")


# Alternative approach: Patch the MCP Server run method
_original_server_run = MCPServer.run


async def patched_server_run(
    self,
    read_stream: Any,
    write_stream: Any,
    initialization_options: Any,
    _session: Any = None,
) -> None:
    """
    Patched Server.run that creates stateless sessions for SSE.
    """
    import inspect

    # Check if called from SSE context
    is_sse = False
    for frame_info in inspect.stack():
        if "sse" in frame_info.filename.lower():
            is_sse = True
            break

    if is_sse and _session is None:
        # Create a stateless session for SSE
        logger.info("Creating stateless session for SSE transport")
        session = ServerSession(
            read_stream,
            write_stream,
            initialization_options,
            stateless=True,  # Force stateless!
        )
        async with session:
            await session.run()
    else:
        # Use original behavior
        await _original_server_run(
            self, read_stream, write_stream, initialization_options, _session
        )


def apply_server_run_patch():
    """Apply the patch to Server.run for stateless SSE."""
    MCPServer.run = patched_server_run
    logger.info("Applied stateless SSE patch to Server.run")


def remove_server_run_patch():
    """Remove the Server.run patch."""
    MCPServer.run = _original_server_run
    logger.info("Removed stateless SSE patch from Server.run")


if __name__ == "__main__":
    # Test the patch
    logging.basicConfig(level=logging.INFO)

    print("Testing stateless SSE patch...")

    # Apply the patch
    apply_stateless_sse_patch()

    # Your FastMCP server would run here
    # mcp = FastMCP("server")
    # mcp.run(transport="sse")

    print("Patch applied successfully")
