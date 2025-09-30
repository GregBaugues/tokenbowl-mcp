"""Parameter validation utilities for MCP tools.

This module provides reusable validation functions for common parameter types
used across MCP tools. All validation functions follow a consistent pattern:
- Accept a parameter value (possibly of wrong type)
- Perform type conversion if needed
- Validate constraints (range, enum, format, etc.)
- Raise ValueError with descriptive message on failure
- Return validated value on success

MCP tools should wrap these functions in try/except blocks and use
create_error_response() to format errors consistently.
"""

import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def validate_roster_id(roster_id: Union[int, str]) -> int:
    """Validate roster ID parameter.

    Args:
        roster_id: Roster ID to validate (1-10)

    Returns:
        int: Validated roster ID

    Raises:
        ValueError: If roster_id is not a valid integer or out of range
    """
    try:
        roster_id_int = int(roster_id)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Roster ID must be an integer between 1 and 10, got {type(roster_id).__name__}: {roster_id}"
        ) from e

    if not 1 <= roster_id_int <= 10:
        raise ValueError(f"Roster ID must be between 1 and 10, got {roster_id_int}")

    return roster_id_int


def validate_week(week: Union[int, str]) -> int:
    """Validate NFL week parameter.

    Args:
        week: Week number to validate (1-18 for regular season + playoffs)

    Returns:
        int: Validated week number

    Raises:
        ValueError: If week is not a valid integer or out of range
    """
    try:
        week_int = int(week)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Week must be an integer between 1 and 18, got {type(week).__name__}: {week}"
        ) from e

    if not 1 <= week_int <= 18:
        raise ValueError(f"Week must be between 1 and 18, got {week_int}")

    return week_int


def validate_position(position: Optional[str]) -> Optional[str]:
    """Validate position parameter.

    Args:
        position: Position code to validate (QB, RB, WR, TE, DEF, K) or None

    Returns:
        Optional[str]: Validated position in uppercase, or None if input was None

    Raises:
        ValueError: If position is not a valid position code
    """
    if position is None:
        return None

    valid_positions = ["QB", "RB", "WR", "TE", "DEF", "K"]
    position_upper = str(position).upper()

    if position_upper not in valid_positions:
        raise ValueError(f"Position must be one of {valid_positions}, got {position}")

    return position_upper


def validate_limit(limit: Union[int, str], max_value: int = 200) -> int:
    """Validate limit parameter with optional max cap.

    Args:
        limit: Limit to validate (must be positive)
        max_value: Maximum allowed value (default: 200)

    Returns:
        int: Validated limit, capped at max_value

    Raises:
        ValueError: If limit is not a valid positive integer
    """
    try:
        limit_int = int(limit)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Limit must be a positive integer, got {type(limit).__name__}: {limit}"
        ) from e

    if limit_int < 1:
        raise ValueError(f"Limit must be a positive integer, got {limit_int}")

    # Cap at max_value
    return min(limit_int, max_value)


def validate_non_empty_string(value: str, param_name: str) -> str:
    """Validate that a string parameter is not empty after stripping whitespace.

    Args:
        value: String value to validate
        param_name: Name of the parameter (for error messages)

    Returns:
        str: Validated string (stripped of whitespace)

    Raises:
        ValueError: If value is empty or contains only whitespace
    """
    try:
        value_str = str(value).strip()
    except (TypeError, AttributeError) as e:
        raise ValueError(
            f"{param_name} must be a non-empty string, got {type(value).__name__}"
        ) from e

    if not value_str:
        raise ValueError(f"{param_name} cannot be empty")

    return value_str


def validate_days_back(
    days_back: Union[int, str], min_value: int = 1, max_value: int = 30
) -> int:
    """Validate days_back parameter for historical queries.

    Args:
        days_back: Number of days to look back
        min_value: Minimum allowed value (default: 1)
        max_value: Maximum allowed value (default: 30)

    Returns:
        int: Validated days_back value

    Raises:
        ValueError: If days_back is not a valid integer or out of range
    """
    try:
        days_back_int = int(days_back)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"days_back must be an integer between {min_value} and {max_value}, "
            f"got {type(days_back).__name__}: {days_back}"
        ) from e

    if not min_value <= days_back_int <= max_value:
        raise ValueError(
            f"days_back must be between {min_value} and {max_value}, got {days_back_int}"
        )

    return days_back_int


def create_error_response(message: str, **context) -> Dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        message: Error message
        **context: Additional context fields to include in the response

    Returns:
        Dict with error message and context fields
    """
    return {"error": message, **context}
