"""Unit tests for lib.decorators module."""

import pytest
from unittest.mock import patch, MagicMock
from lib.decorators import log_mcp_tool


class TestLogMcpTool:
    """Tests for log_mcp_tool decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success_basic(self):
        """Test decorator with successful function execution."""

        @log_mcp_tool
        async def sample_tool(param1: str, param2: int):
            return {"result": "success", "param1": param1, "param2": param2}

        result = await sample_tool("test", 42)
        assert result == {"result": "success", "param1": "test", "param2": 42}

    @pytest.mark.asyncio
    async def test_decorator_with_exception(self):
        """Test decorator with function that raises exception."""

        @log_mcp_tool
        async def failing_tool():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_tool()

    @pytest.mark.asyncio
    async def test_decorator_with_error_response(self):
        """Test decorator with error response dict."""

        @log_mcp_tool
        async def error_tool():
            return {"error": "Something went wrong", "details": "test"}

        result = await error_tool()
        assert "error" in result
        assert result["error"] == "Something went wrong"

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function metadata."""

        @log_mcp_tool
        async def my_tool():
            return {"ok": True}

        assert my_tool.__name__ == "my_tool"

    @pytest.mark.asyncio
    async def test_decorator_with_args_and_kwargs(self):
        """Test decorator with mixed args and kwargs."""

        @log_mcp_tool
        async def tool_with_params(pos_arg, keyword_arg="default"):
            return {"pos": pos_arg, "kw": keyword_arg}

        result = await tool_with_params("value1", keyword_arg="value2")
        assert result == {"pos": "value1", "kw": "value2"}

    @pytest.mark.asyncio
    async def test_decorator_with_none_values(self):
        """Test decorator handles None parameter values."""

        @log_mcp_tool
        async def tool_with_none(param1, param2=None):
            return {"param1": param1, "param2": param2}

        result = await tool_with_none("test", param2=None)
        assert result["param1"] == "test"
        assert result["param2"] is None

    @pytest.mark.asyncio
    async def test_decorator_with_list_result(self):
        """Test decorator with list result."""

        @log_mcp_tool
        async def list_tool():
            return [1, 2, 3, 4, 5]

        result = await list_tool()
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_decorator_with_dict_result(self):
        """Test decorator with dict result (non-error)."""

        @log_mcp_tool
        async def dict_tool():
            return {"key1": "value1", "key2": "value2", "status": "ok"}

        result = await dict_tool()
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_decorator_with_string_result(self):
        """Test decorator with string result."""

        @log_mcp_tool
        async def string_tool():
            return "simple string result"

        result = await string_tool()
        assert result == "simple string result"

    @pytest.mark.asyncio
    @patch("lib.decorators.logger")
    async def test_decorator_logs_success(self, mock_logger):
        """Test that decorator logs successful execution."""

        @log_mcp_tool
        async def success_tool():
            return {"result": "ok"}

        await success_tool()

        # Check that info was logged
        assert mock_logger.info.called

    @pytest.mark.asyncio
    @patch("lib.decorators.logger")
    async def test_decorator_logs_error_response(self, mock_logger):
        """Test that decorator logs error responses."""

        @log_mcp_tool
        async def error_tool():
            return {"error": "Failed"}

        await error_tool()

        # Check that warning was logged for error response
        assert mock_logger.warning.called

    @pytest.mark.asyncio
    @patch("lib.decorators.logger")
    async def test_decorator_logs_exception(self, mock_logger):
        """Test that decorator logs exceptions."""

        @log_mcp_tool
        async def exception_tool():
            raise RuntimeError("Something broke")

        with pytest.raises(RuntimeError):
            await exception_tool()

        # Check that error was logged
        assert mock_logger.error.called

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_creates_span(self, mock_logfire):
        """Test that decorator creates Logfire span."""
        mock_span = MagicMock()
        mock_logfire.span.return_value = mock_span

        @log_mcp_tool
        async def span_tool():
            return {"ok": True}

        await span_tool()

        # Check that span was created
        mock_logfire.span.assert_called_once()
        mock_span.__enter__.assert_called_once()
        mock_span.__exit__.assert_called_once()

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_handles_span_creation_failure(self, mock_logfire):
        """Test that decorator handles span creation failures gracefully."""
        # Make span creation fail
        mock_logfire.span.side_effect = TypeError("Span creation failed")

        @log_mcp_tool
        async def resilient_tool():
            return {"result": "ok"}

        # Tool should still work despite span failure
        result = await resilient_tool()
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_sets_span_attributes_on_success(self, mock_logfire):
        """Test that decorator sets success attributes on span."""
        mock_span = MagicMock()
        mock_logfire.span.return_value = mock_span

        @log_mcp_tool
        async def success_tool():
            return {"data": "test"}

        await success_tool()

        # Check that success attribute was set
        mock_span.set_attribute.assert_any_call("success", True)

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_sets_span_attributes_on_error_response(self, mock_logfire):
        """Test that decorator sets error attributes for error responses."""
        mock_span = MagicMock()
        mock_logfire.span.return_value = mock_span

        @log_mcp_tool
        async def error_tool():
            return {"error": "Failed operation"}

        await error_tool()

        # Check that error attributes were set
        mock_span.set_attribute.assert_any_call("success", False)
        mock_span.set_attribute.assert_any_call("error_message", "Failed operation")

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_sets_span_attributes_on_exception(self, mock_logfire):
        """Test that decorator sets error attributes for exceptions."""
        mock_span = MagicMock()
        mock_logfire.span.return_value = mock_span

        @log_mcp_tool
        async def exception_tool():
            raise ValueError("Test exception")

        with pytest.raises(ValueError):
            await exception_tool()

        # Check that error attributes were set
        mock_span.set_attribute.assert_any_call("success", False)
        mock_span.set_attribute.assert_any_call("error_type", "ValueError")

    @pytest.mark.asyncio
    async def test_decorator_with_very_long_parameters(self):
        """Test that decorator truncates very long parameter values."""
        long_string = "x" * 300  # Longer than 200 char limit

        @log_mcp_tool
        async def long_param_tool(data):
            return {"received_length": len(data)}

        result = await long_param_tool(long_string)
        assert result["received_length"] == 300

    @pytest.mark.asyncio
    @patch("lib.decorators.logger")
    async def test_decorator_handles_parameter_serialization_failure(self, mock_logger):
        """Test that decorator handles parameter serialization failures."""

        # Create an object that can't be easily serialized
        class UnserializableObject:
            def __str__(self):
                raise RuntimeError("Cannot serialize")

        @log_mcp_tool
        async def tool_with_bad_param(param):
            return {"ok": True}

        # Should still work despite serialization failure
        result = await tool_with_bad_param(UnserializableObject())
        assert result == {"ok": True}

    @pytest.mark.asyncio
    @patch("lib.decorators.logfire")
    async def test_decorator_handles_span_exit_failure(self, mock_logfire):
        """Test that decorator handles span exit failures gracefully."""
        mock_span = MagicMock()
        mock_span.__exit__.side_effect = Exception("Exit failed")
        mock_logfire.span.return_value = mock_span

        @log_mcp_tool
        async def span_exit_fail_tool():
            return {"result": "ok"}

        # Tool should still work despite span exit failure
        result = await span_exit_fail_tool()
        assert result == {"result": "ok"}
