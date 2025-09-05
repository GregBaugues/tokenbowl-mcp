"""Unit tests for Fantasy Nerds API client."""

import os
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from ffnerd.client import FantasyNerdsClient


@pytest.fixture
def client():
    """Create a Fantasy Nerds client with test API key."""
    with patch.dict(os.environ, {"FFNERD_API_KEY": "test_api_key"}):
        return FantasyNerdsClient()


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = AsyncMock(spec=httpx.Response)
    response.raise_for_status = AsyncMock()
    return response


class TestFantasyNerdsClient:
    """Test Fantasy Nerds API client methods."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = FantasyNerdsClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_init_from_env(self):
        """Test client initialization from environment variable."""
        with patch.dict(os.environ, {"FFNERD_API_KEY": "env_key"}):
            client = FantasyNerdsClient()
            assert client.api_key == "env_key"

    def test_init_missing_api_key(self):
        """Test client initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Fantasy Nerds API key required"):
                FantasyNerdsClient()

    def test_get_headers(self, client):
        """Test header generation for API requests."""
        headers = client._get_headers()
        assert headers["Accept"] == "application/json"
        # API key is now passed as query param, not header

    @pytest.mark.asyncio
    async def test_get_players(self, client, mock_response):
        """Test fetching players from API."""
        # API returns a list directly, not a dict with "players" key
        mock_response.json.return_value = [
            {
                "playerId": 1,
                "name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
            },
            {
                "playerId": 2,
                "name": "Justin Jefferson",
                "position": "WR",
                "team": "MIN",
            },
        ]

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            players = await client.get_players()

            assert len(players) == 2
            assert players[0]["name"] == "Patrick Mahomes"
            mock_get.assert_called_once()

            # Check URL and params
            call_args = mock_get.call_args
            assert "players" in str(call_args[0][0])
            assert call_args[1]["params"]["apikey"] == "test_api_key"

    @pytest.mark.asyncio
    async def test_get_players_include_inactive(self, client, mock_response):
        """Test fetching all players including inactive."""
        mock_response.json.return_value = []  # API returns list directly

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            await client.get_players(include_inactive=True)

            # Should include include_inactive param when including inactive
            call_args = mock_get.call_args
            assert "params" in call_args[1]
            assert call_args[1]["params"]["apikey"] == "test_api_key"
            assert call_args[1]["params"]["include_inactive"] == "1"

    @pytest.mark.asyncio
    async def test_get_weekly_projections(self, client, mock_response):
        """Test fetching weekly projections."""
        mock_response.json.return_value = {
            "projections": [
                {"playerId": 1, "points": 25.5},
                {"playerId": 2, "points": 18.3},
            ]
        }

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            projections = await client.get_weekly_projections(week=1, position="QB")

            assert "projections" in projections
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["week"] == 1
            assert call_args[1]["params"]["position"] == "QB"

    @pytest.mark.asyncio
    async def test_get_injuries(self, client, mock_response):
        """Test fetching injury reports."""
        # API returns injuries nested in teams structure
        mock_response.json.return_value = {
            "season": "2025",
            "week": "1",
            "teams": [
                {
                    "team": "KC",
                    "players": [
                        {"playerId": 1, "injury": "Ankle", "status": "Questionable"},
                        {"playerId": 2, "injury": "Hamstring", "status": "Out"},
                    ]
                }
            ]
        }

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            injuries = await client.get_injuries(week=5)

            assert len(injuries) == 2
            assert injuries[0]["injury"] == "Ankle"
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["week"] == 5

    @pytest.mark.asyncio
    async def test_get_news(self, client, mock_response):
        """Test fetching player news."""
        # API returns news as a list directly
        mock_response.json.return_value = [
            {"playerId": 1, "title": "Player Update", "body": "News content"},
            {"playerId": 1, "title": "Injury Report", "body": "More news"},
        ]

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            news = await client.get_news(player_id=1, days=3)

            assert len(news) == 2
            assert news[0]["title"] == "Player Update"
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["player_id"] == 1
            assert call_args[1]["params"]["days"] == 3

    @pytest.mark.asyncio
    async def test_get_rankings(self, client, mock_response):
        """Test fetching expert rankings."""
        # API may return rankings as list or dict
        mock_response.json.return_value = [
            {"playerId": 1, "rank": 1, "name": "Player One"},
            {"playerId": 2, "rank": 2, "name": "Player Two"},
        ]

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            rankings = await client.get_rankings(
                scoring_type="PPR", position="RB", week=10
            )

            assert len(rankings) == 2
            assert rankings[0]["rank"] == 1
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["scoring"] == "PPR"
            assert call_args[1]["params"]["position"] == "RB"
            assert call_args[1]["params"]["week"] == 10

    @pytest.mark.asyncio
    async def test_get_adp(self, client, mock_response):
        """Test fetching ADP data."""
        # API may return ADP as list or dict
        mock_response.json.return_value = [
            {"playerId": 1, "adp": 1.5, "name": "Top Player"},
            {"playerId": 2, "adp": 5.3, "name": "Good Player"},
        ]

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            adp_data = await client.get_adp(scoring_type="HALF", mock_type="real")

            assert len(adp_data) == 2
            assert adp_data[0]["adp"] == 1.5
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["scoring"] == "HALF"
            assert call_args[1]["params"]["type"] == "real"

    @pytest.mark.asyncio
    async def test_get_schedule(self, client, mock_response):
        """Test fetching NFL schedule."""
        # API may return schedule as list or dict
        mock_response.json.return_value = [
            {"week": 1, "home": "KC", "away": "DET"},
            {"week": 1, "home": "GB", "away": "CHI"},
        ]

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            schedule = await client.get_schedule(week=1)

            assert len(schedule) == 2
            assert schedule[0]["home"] == "KC"
            mock_get.assert_called_once()

            # Check params
            call_args = mock_get.call_args
            assert call_args[1]["params"]["week"] == 1

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client, mock_response):
        """Test successful API connection test."""
        # API returns list of players directly
        mock_response.json.return_value = [{"playerId": 1, "name": "Test Player"}]

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await client.test_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client):
        """Test failed API connection test."""
        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection error")):
            result = await client.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test handling of API errors."""
        error_response = AsyncMock(spec=httpx.Response)
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=AsyncMock(), response=AsyncMock()
        )

        with patch("httpx.AsyncClient.get", return_value=error_response):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_players()

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, client, mock_response):
        """Test that timeout is properly configured."""
        mock_response.json.return_value = []  # API returns list directly

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_class.return_value = mock_client_instance

            await client.get_players()

            # Check that AsyncClient was created with correct timeout
            mock_client_class.assert_called_with(timeout=30.0)
