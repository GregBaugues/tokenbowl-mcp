"""Tests for the Monday Night Emergency waiver tool."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sleeper_mcp import its_monday_night_and_i_need_a


@pytest.mark.asyncio
async def test_its_monday_night_emergency_valid_position():
    """Test the Monday night emergency tool with valid position."""

    # Mock the current time to be Monday night
    mock_current_time = datetime(2025, 10, 13, 18, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))

    # Mock schedule data with some games not yet played
    mock_schedule = {
        "season": 2025,
        "current_week": 6,
        "requested_week": 6,
        "games": [
            # Sunday games (already played)
            {
                "home_team": "KC",
                "away_team": "BUF",
                "game_date": "2025-10-12 13:00:00",
                "tv": "CBS"
            },
            # Monday night game (not played yet)
            {
                "home_team": "NYG",
                "away_team": "DAL",
                "game_date": "2025-10-13 20:15:00",  # 8:15 PM ET = 5:15 PM PT
                "tv": "ESPN"
            }
        ]
    }

    # Mock waiver wire players
    mock_waiver_players = {
        "total_available": 50,
        "filtered_count": 10,
        "players": [
            {
                "player_id": "1234",
                "full_name": "Dak Prescott",
                "position": "QB",
                "team": "DAL",
                "projected_points": 18.5,
                "recently_dropped": False,
                "trending_add_count": 5
            },
            {
                "player_id": "5678",
                "full_name": "Daniel Jones",
                "position": "QB",
                "team": "NYG",
                "projected_points": 15.2,
                "recently_dropped": True,
                "trending_add_count": 2
            },
            {
                "player_id": "9999",
                "full_name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
                "projected_points": 25.0,
                "recently_dropped": False,
                "trending_add_count": 0
            }
        ]
    }

    with patch('sleeper_mcp.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_current_time
        mock_datetime.strptime = datetime.strptime

        with patch('sleeper_mcp.httpx.AsyncClient') as mock_client:
            # Mock Sleeper state API
            mock_state_response = MagicMock()
            mock_state_response.json.return_value = {"week": 6, "season": 2025}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_state_response

            with patch('sleeper_mcp.get_nfl_schedule.fn', new_callable=AsyncMock) as mock_schedule_fn:
                mock_schedule_fn.return_value = mock_schedule

                with patch('sleeper_mcp.get_waiver_wire_players.fn', new_callable=AsyncMock) as mock_waiver_fn:
                    mock_waiver_fn.return_value = mock_waiver_players

                    # Call the function
                    result = await its_monday_night_and_i_need_a.fn("QB")

                    # Verify results - should only include DAL and NYG players (top 2)
                    assert len(result) == 2
                    assert result[0]["name"] == "Dak Prescott"
                    assert result[0]["team"] == "DAL"
                    assert result[0]["proj"] == 18.5

                    assert result[1]["name"] == "Daniel Jones"
                    assert result[1]["team"] == "NYG"
                    assert result[1]["proj"] == 15.2

                    # Mahomes should not be included (KC already played)
                    assert not any(p["name"] == "Patrick Mahomes" for p in result)


@pytest.mark.asyncio
async def test_its_monday_night_emergency_invalid_position():
    """Test the Monday night emergency tool with invalid position."""
    result = await its_monday_night_and_i_need_a.fn("INVALID")

    # Should return an error
    assert len(result) == 1
    assert "error" in result[0]
    assert "Invalid position" in result[0]["error"]


@pytest.mark.asyncio
async def test_its_monday_night_emergency_all_teams_played():
    """Test when all teams have already played."""

    # Mock current time to be Tuesday
    mock_current_time = datetime(2025, 10, 14, 10, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))

    # All games in the past
    mock_schedule = {
        "season": 2025,
        "current_week": 6,
        "requested_week": 6,
        "games": [
            {
                "home_team": "KC",
                "away_team": "BUF",
                "game_date": "2025-10-12 13:00:00",
                "tv": "CBS"
            },
            {
                "home_team": "NYG",
                "away_team": "DAL",
                "game_date": "2025-10-13 20:15:00",
                "tv": "ESPN"
            }
        ]
    }

    with patch('sleeper_mcp.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_current_time
        mock_datetime.strptime = datetime.strptime

        with patch('sleeper_mcp.httpx.AsyncClient') as mock_client:
            mock_state_response = MagicMock()
            mock_state_response.json.return_value = {"week": 6, "season": 2025}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_state_response

            with patch('sleeper_mcp.get_nfl_schedule.fn', new_callable=AsyncMock) as mock_schedule_fn:
                mock_schedule_fn.return_value = mock_schedule

                result = await its_monday_night_and_i_need_a.fn("RB")

                # Should return empty list since all teams have played
                assert result == []


@pytest.mark.asyncio
async def test_its_monday_night_emergency_no_available_players():
    """Test when no players are available at the position."""

    mock_current_time = datetime(2025, 10, 13, 18, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))

    mock_schedule = {
        "season": 2025,
        "current_week": 6,
        "requested_week": 6,
        "games": [
            {
                "home_team": "NYG",
                "away_team": "DAL",
                "game_date": "2025-10-13 20:15:00",
                "tv": "ESPN"
            }
        ]
    }

    # Empty waiver wire
    mock_waiver_players = {
        "total_available": 0,
        "filtered_count": 0,
        "players": []
    }

    with patch('sleeper_mcp.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_current_time
        mock_datetime.strptime = datetime.strptime

        with patch('sleeper_mcp.httpx.AsyncClient') as mock_client:
            mock_state_response = MagicMock()
            mock_state_response.json.return_value = {"week": 6, "season": 2025}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_state_response

            with patch('sleeper_mcp.get_nfl_schedule.fn', new_callable=AsyncMock) as mock_schedule_fn:
                mock_schedule_fn.return_value = mock_schedule

                with patch('sleeper_mcp.get_waiver_wire_players.fn', new_callable=AsyncMock) as mock_waiver_fn:
                    mock_waiver_fn.return_value = mock_waiver_players

                    result = await its_monday_night_and_i_need_a.fn("TE")

                    # Should return empty list
                    assert result == []


@pytest.mark.asyncio
async def test_its_monday_night_emergency_sorting():
    """Test that results are properly sorted by projected points."""

    mock_current_time = datetime(2025, 10, 13, 18, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))

    mock_schedule = {
        "season": 2025,
        "current_week": 6,
        "requested_week": 6,
        "games": [
            {
                "home_team": "NYG",
                "away_team": "DAL",
                "game_date": "2025-10-13 20:15:00",
                "tv": "ESPN"
            }
        ]
    }

    mock_waiver_players = {
        "total_available": 10,
        "filtered_count": 5,
        "players": [
            {
                "player_id": "1",
                "full_name": "Player Low",
                "position": "WR",
                "team": "DAL",
                "projected_points": 5.0,
                "recently_dropped": False,
                "trending_add_count": 0
            },
            {
                "player_id": "2",
                "full_name": "Player High",
                "position": "WR",
                "team": "NYG",
                "projected_points": 20.0,
                "recently_dropped": False,
                "trending_add_count": 0
            },
            {
                "player_id": "3",
                "full_name": "Player Mid",
                "position": "WR",
                "team": "DAL",
                "projected_points": 12.5,
                "recently_dropped": False,
                "trending_add_count": 0
            }
        ]
    }

    with patch('sleeper_mcp.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_current_time
        mock_datetime.strptime = datetime.strptime

        with patch('sleeper_mcp.httpx.AsyncClient') as mock_client:
            mock_state_response = MagicMock()
            mock_state_response.json.return_value = {"week": 6, "season": 2025}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_state_response

            with patch('sleeper_mcp.get_nfl_schedule.fn', new_callable=AsyncMock) as mock_schedule_fn:
                mock_schedule_fn.return_value = mock_schedule

                with patch('sleeper_mcp.get_waiver_wire_players.fn', new_callable=AsyncMock) as mock_waiver_fn:
                    mock_waiver_fn.return_value = mock_waiver_players

                    result = await its_monday_night_and_i_need_a.fn("WR")

                    # Verify sorting by projected points (highest first) - only top 3
                    assert len(result) == 3
                    assert result[0]["name"] == "Player High"
                    assert result[0]["proj"] == 20.0
                    assert result[1]["name"] == "Player Mid"
                    assert result[1]["proj"] == 12.5
                    assert result[2]["name"] == "Player Low"
                    assert result[2]["proj"] == 5.0