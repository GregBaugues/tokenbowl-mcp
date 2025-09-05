"""Request/Response logging system for MCP monitoring dashboard"""

from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


class RequestLogger:
    """Circular buffer for storing MCP request/response logs"""

    def __init__(self, maxlen: int = 1000):
        """Initialize logger with specified buffer size

        Args:
            maxlen: Maximum number of logs to store (oldest are dropped)
        """
        self.logs = deque(maxlen=maxlen)
        self.start_time = datetime.utcnow()

    def log_request(
        self,
        tool_name: str,
        params: Dict[str, Any],
        response: Any,
        duration: float,
        status: str = "success",
        error: Optional[str] = None,
    ) -> None:
        """Log a single MCP request/response

        Args:
            tool_name: Name of the MCP tool called
            params: Parameters passed to the tool
            response: Response from the tool (or error message)
            duration: Time taken in seconds
            status: "success" or "error"
            error: Error message if status is "error"
        """
        log_entry = {
            "id": len(self.logs) + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool": tool_name,
            "params": params,
            "response": self._truncate_response(response),
            "duration_ms": round(duration * 1000, 2),
            "status": status,
            "error": error,
        }
        self.logs.append(log_entry)

    def _truncate_response(self, response: Any, max_length: int = 1000) -> Any:
        """Truncate response to avoid excessive memory usage

        Args:
            response: Response data to truncate
            max_length: Maximum string length for response

        Returns:
            Truncated response
        """
        if isinstance(response, str) and len(response) > max_length:
            return response[:max_length] + "... (truncated)"
        elif isinstance(response, (dict, list)):
            # Convert to string and truncate if too long
            response_str = json.dumps(response)
            if len(response_str) > max_length:
                return response_str[:max_length] + "... (truncated)"
        return response

    def get_logs(
        self,
        limit: Optional[int] = None,
        tool: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve logs with optional filtering

        Args:
            limit: Maximum number of logs to return
            tool: Filter by tool name
            status: Filter by status ("success" or "error")
            since: Only return logs after this timestamp

        Returns:
            List of log entries matching criteria
        """
        logs = list(self.logs)

        # Apply filters
        if tool:
            logs = [log for log in logs if log["tool"] == tool]

        if status:
            logs = [log for log in logs if log["status"] == status]

        if since:
            since_str = since.isoformat() + "Z"
            logs = [log for log in logs if log["timestamp"] > since_str]

        # Apply limit (return most recent)
        if limit:
            logs = logs[-limit:]

        # Reverse to show most recent first
        return list(reversed(logs))

    def get_stats(self) -> Dict[str, Any]:
        """Calculate aggregate statistics from logs

        Returns:
            Dictionary containing various statistics
        """
        if not self.logs:
            return {
                "total_requests": 0,
                "success_rate": 0,
                "error_rate": 0,
                "avg_response_time_ms": 0,
                "tools_usage": {},
                "recent_errors": [],
                "uptime_seconds": 0,
            }

        logs = list(self.logs)
        total = len(logs)
        successes = sum(1 for log in logs if log["status"] == "success")
        errors = total - successes

        # Calculate average response time
        response_times = [log["duration_ms"] for log in logs]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Count tool usage
        tool_counts = {}
        for log in logs:
            tool = log["tool"]
            if tool not in tool_counts:
                tool_counts[tool] = {"count": 0, "errors": 0, "avg_ms": 0}
            tool_counts[tool]["count"] += 1
            if log["status"] == "error":
                tool_counts[tool]["errors"] += 1

        # Calculate average response time per tool
        for tool_name in tool_counts:
            tool_logs = [log for log in logs if log["tool"] == tool_name]
            tool_times = [log["duration_ms"] for log in tool_logs]
            tool_counts[tool_name]["avg_ms"] = round(
                sum(tool_times) / len(tool_times) if tool_times else 0, 2
            )

        # Get recent errors
        recent_errors = [
            {
                "timestamp": log["timestamp"],
                "tool": log["tool"],
                "error": log.get("error", "Unknown error"),
            }
            for log in logs[-10:]
            if log["status"] == "error"
        ]

        # Calculate uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "total_requests": total,
            "success_rate": round((successes / total * 100) if total > 0 else 0, 2),
            "error_rate": round((errors / total * 100) if total > 0 else 0, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "tools_usage": tool_counts,
            "recent_errors": recent_errors,
            "uptime_seconds": round(uptime),
            "buffer_size": self.logs.maxlen,
            "buffer_used": len(self.logs),
        }

    def clear(self) -> None:
        """Clear all logs from the buffer"""
        self.logs.clear()
