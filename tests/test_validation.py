"""Unit tests for lib.validation module."""

import pytest
from lib.validation import (
    validate_roster_id,
    validate_week,
    validate_position,
    validate_limit,
    validate_non_empty_string,
    validate_days_back,
    create_error_response,
)


class TestValidateRosterId:
    """Tests for validate_roster_id function."""

    def test_valid_roster_id_int(self):
        """Test with valid integer roster ID."""
        assert validate_roster_id(5) == 5

    def test_valid_roster_id_string(self):
        """Test with valid string roster ID."""
        assert validate_roster_id("5") == 5

    def test_roster_id_boundary_lower(self):
        """Test lower boundary (1)."""
        assert validate_roster_id(1) == 1

    def test_roster_id_boundary_upper(self):
        """Test upper boundary (10)."""
        assert validate_roster_id(10) == 10

    def test_roster_id_too_low(self):
        """Test roster ID below valid range."""
        with pytest.raises(ValueError, match="between 1 and 10"):
            validate_roster_id(0)

    def test_roster_id_too_high(self):
        """Test roster ID above valid range."""
        with pytest.raises(ValueError, match="between 1 and 10"):
            validate_roster_id(11)

    def test_roster_id_negative(self):
        """Test negative roster ID."""
        with pytest.raises(ValueError, match="between 1 and 10"):
            validate_roster_id(-1)

    def test_roster_id_invalid_type(self):
        """Test with non-numeric string."""
        with pytest.raises(ValueError, match="integer"):
            validate_roster_id("invalid")

    def test_roster_id_float(self):
        """Test with float value (should convert to int)."""
        assert validate_roster_id(5.0) == 5
        # String floats should fail (use int() not float())
        with pytest.raises(ValueError, match="integer"):
            validate_roster_id("5.7")


class TestValidateWeek:
    """Tests for validate_week function."""

    def test_valid_week_int(self):
        """Test with valid integer week."""
        assert validate_week(1) == 1
        assert validate_week(10) == 10

    def test_valid_week_string(self):
        """Test with valid string week."""
        assert validate_week("15") == 15

    def test_week_boundary_lower(self):
        """Test lower boundary (1)."""
        assert validate_week(1) == 1

    def test_week_boundary_upper(self):
        """Test upper boundary (18)."""
        assert validate_week(18) == 18

    def test_week_too_low(self):
        """Test week below valid range."""
        with pytest.raises(ValueError, match="between 1 and 18"):
            validate_week(0)

    def test_week_too_high(self):
        """Test week above valid range."""
        with pytest.raises(ValueError, match="between 1 and 18"):
            validate_week(19)

    def test_week_invalid_type(self):
        """Test with non-numeric string."""
        with pytest.raises(ValueError, match="integer"):
            validate_week("week1")


class TestValidatePosition:
    """Tests for validate_position function."""

    def test_valid_positions(self):
        """Test all valid positions."""
        assert validate_position("QB") == "QB"
        assert validate_position("RB") == "RB"
        assert validate_position("WR") == "WR"
        assert validate_position("TE") == "TE"
        assert validate_position("DEF") == "DEF"
        assert validate_position("K") == "K"

    def test_position_lowercase(self):
        """Test position conversion to uppercase."""
        assert validate_position("qb") == "QB"
        assert validate_position("rb") == "RB"

    def test_position_mixed_case(self):
        """Test mixed case position."""
        assert validate_position("Qb") == "QB"
        assert validate_position("dEf") == "DEF"

    def test_position_none(self):
        """Test None position (optional parameter)."""
        assert validate_position(None) is None

    def test_invalid_position(self):
        """Test invalid position code."""
        with pytest.raises(ValueError, match="must be one of"):
            validate_position("XX")

    def test_invalid_position_empty(self):
        """Test empty string position."""
        with pytest.raises(ValueError, match="must be one of"):
            validate_position("")


class TestValidateLimit:
    """Tests for validate_limit function."""

    def test_valid_limit_int(self):
        """Test with valid integer limit."""
        assert validate_limit(50) == 50

    def test_valid_limit_string(self):
        """Test with valid string limit."""
        assert validate_limit("100") == 100

    def test_limit_default_max(self):
        """Test default max value (200)."""
        assert validate_limit(150) == 150
        assert validate_limit(200) == 200
        assert validate_limit(250) == 200  # Capped at max

    def test_limit_custom_max(self):
        """Test with custom max value."""
        assert validate_limit(50, max_value=100) == 50
        assert validate_limit(150, max_value=100) == 100  # Capped

    def test_limit_boundary_lower(self):
        """Test lower boundary (1)."""
        assert validate_limit(1) == 1

    def test_limit_zero(self):
        """Test zero limit (invalid)."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_limit(0)

    def test_limit_negative(self):
        """Test negative limit."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_limit(-10)

    def test_limit_invalid_type(self):
        """Test with non-numeric string."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_limit("many")


class TestValidateNonEmptyString:
    """Tests for validate_non_empty_string function."""

    def test_valid_string(self):
        """Test with valid non-empty string."""
        assert validate_non_empty_string("test", "param") == "test"

    def test_string_with_whitespace(self):
        """Test string with leading/trailing whitespace (should be stripped)."""
        assert validate_non_empty_string("  test  ", "param") == "test"

    def test_empty_string(self):
        """Test empty string."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_non_empty_string("", "test_param")

    def test_whitespace_only(self):
        """Test string with only whitespace."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_non_empty_string("   ", "test_param")

    def test_string_with_param_name_in_error(self):
        """Test that parameter name appears in error message."""
        with pytest.raises(ValueError, match="search_term"):
            validate_non_empty_string("", "search_term")


class TestValidateDaysBack:
    """Tests for validate_days_back function."""

    def test_valid_days_back_int(self):
        """Test with valid integer days_back."""
        assert validate_days_back(7) == 7

    def test_valid_days_back_string(self):
        """Test with valid string days_back."""
        assert validate_days_back("14") == 14

    def test_days_back_default_range(self):
        """Test default range (1-30)."""
        assert validate_days_back(1) == 1
        assert validate_days_back(30) == 30

    def test_days_back_custom_range(self):
        """Test custom min/max range."""
        assert validate_days_back(5, min_value=1, max_value=10) == 5

    def test_days_back_below_min_default(self):
        """Test below default minimum."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            validate_days_back(0)

    def test_days_back_above_max_default(self):
        """Test above default maximum."""
        with pytest.raises(ValueError, match="between 1 and 30"):
            validate_days_back(31)

    def test_days_back_below_min_custom(self):
        """Test below custom minimum."""
        with pytest.raises(ValueError, match="between 5 and 20"):
            validate_days_back(4, min_value=5, max_value=20)

    def test_days_back_above_max_custom(self):
        """Test above custom maximum."""
        with pytest.raises(ValueError, match="between 5 and 20"):
            validate_days_back(21, min_value=5, max_value=20)

    def test_days_back_invalid_type(self):
        """Test with non-numeric string."""
        with pytest.raises(ValueError, match="integer"):
            validate_days_back("last week")


class TestCreateErrorResponse:
    """Tests for create_error_response function."""

    def test_basic_error_response(self):
        """Test basic error response with just message."""
        result = create_error_response("Something went wrong")
        assert result == {"error": "Something went wrong"}

    def test_error_response_with_context(self):
        """Test error response with additional context."""
        result = create_error_response(
            "Invalid parameter", value_received="abc", expected="integer"
        )
        assert result == {
            "error": "Invalid parameter",
            "value_received": "abc",
            "expected": "integer",
        }

    def test_error_response_with_multiple_context_fields(self):
        """Test error response with multiple context fields."""
        result = create_error_response(
            "Range error", value=15, min=1, max=10, parameter="limit"
        )
        assert result == {
            "error": "Range error",
            "value": 15,
            "min": 1,
            "max": 10,
            "parameter": "limit",
        }

    def test_error_response_empty_context(self):
        """Test error response with no context fields."""
        result = create_error_response("Error message")
        assert "error" in result
        assert len(result) == 1
