"""Test APIKeyMiddleware for Token Bowl Chat authentication."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from starlette.responses import Response
import sleeper_mcp


class TestAPIKeyMiddleware:
    """Test the APIKeyMiddleware for proper API key handling."""

    @pytest.mark.asyncio
    async def test_api_key_extracted_from_query_params(self):
        """Test that API key is extracted from query parameters."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Mock request with api_key query parameter
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"api_key": "test_api_key_123"}
        mock_request.url.path = "/some-endpoint"

        # Mock call_next to return a response
        async def mock_call_next(request):
            # Verify API key is set in context during request processing
            api_key = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
            assert api_key == "test_api_key_123"
            return Response(content="OK", status_code=200)

        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Verify response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_key_persists_for_sse_endpoint(self):
        """Test that API key persists for SSE endpoints (not reset after request)."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Mock SSE request with api_key query parameter
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"api_key": "sse_api_key_456"}
        mock_request.url.path = "/sse"

        # Track whether API key is set during and after the request
        api_key_during_request = None
        api_key_after_request = None

        # Mock call_next to return a response
        async def mock_call_next(request):
            nonlocal api_key_during_request
            api_key_during_request = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
            return Response(content="OK", status_code=200)

        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Check API key after middleware completes
        api_key_after_request = sleeper_mcp.token_bowl_chat_api_key_ctx.get()

        # Verify API key was set during request
        assert api_key_during_request == "sse_api_key_456"

        # Verify API key persists after request for SSE endpoint
        assert (
            api_key_after_request == "sse_api_key_456"
        ), "API key should persist for SSE endpoints"

        # Clean up - reset the context for other tests
        sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

    @pytest.mark.asyncio
    async def test_api_key_reset_for_non_sse_endpoint(self):
        """Test that API key is reset after non-SSE requests."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Mock non-SSE request with api_key query parameter
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"api_key": "temp_api_key_789"}
        mock_request.url.path = "/api/some-endpoint"

        # Track whether API key is set during and after the request
        api_key_during_request = None
        api_key_after_request = None

        # Mock call_next to return a response
        async def mock_call_next(request):
            nonlocal api_key_during_request
            api_key_during_request = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
            return Response(content="OK", status_code=200)

        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Check API key after middleware completes
        api_key_after_request = sleeper_mcp.token_bowl_chat_api_key_ctx.get()

        # Verify API key was set during request
        assert api_key_during_request == "temp_api_key_789"

        # Verify API key is reset after request for non-SSE endpoint
        assert (
            api_key_after_request is None
        ), "API key should be reset for non-SSE endpoints"

    @pytest.mark.asyncio
    async def test_no_api_key_in_query_params(self):
        """Test that middleware proceeds normally when no API key is provided."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Mock request without api_key query parameter
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {}
        mock_request.url.path = "/some-endpoint"

        # Track API key during request
        api_key_during_request = None

        # Mock call_next to return a response
        async def mock_call_next(request):
            nonlocal api_key_during_request
            api_key_during_request = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
            return Response(content="OK", status_code=200)

        # Execute middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Verify no API key was set
        assert api_key_during_request is None

        # Verify response still succeeds
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sse_path_variations(self):
        """Test that SSE path detection works for various SSE endpoint variations."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Test various SSE paths
        sse_paths = ["/sse", "/sse/", "/sse/subscribe", "/sse?foo=bar"]

        for path in sse_paths:
            # Reset context before each test
            sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

            # Mock SSE request
            mock_request = MagicMock(spec=Request)
            mock_request.query_params = {"api_key": f"key_for_{path}"}
            mock_request.url.path = path

            # Mock call_next
            async def mock_call_next(request):
                return Response(content="OK", status_code=200)

            # Execute middleware
            await middleware.dispatch(mock_request, mock_call_next)

            # Verify API key persists for all SSE path variations
            api_key_after = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
            assert (
                api_key_after is not None
            ), f"API key should persist for SSE path: {path}"

        # Clean up
        sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self):
        """Test that middleware properly handles exceptions in call_next."""
        # Create middleware instance
        middleware = sleeper_mcp.APIKeyMiddleware(app=AsyncMock())

        # Mock request with api_key
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"api_key": "exception_test_key"}
        mock_request.url.path = "/api/endpoint"

        # Mock call_next to raise an exception
        async def mock_call_next_with_error(request):
            raise ValueError("Test exception")

        # Execute middleware and expect exception
        with pytest.raises(ValueError, match="Test exception"):
            await middleware.dispatch(mock_request, mock_call_next_with_error)

        # Verify API key was still reset even after exception
        api_key_after = sleeper_mcp.token_bowl_chat_api_key_ctx.get()
        assert (
            api_key_after is None
        ), "API key should be reset even when exception occurs"
