"""Fantasy Nerds API client for fetching NFL player data and projections."""

import os
from typing import Dict, List, Optional, Any
import httpx
import logging

logger = logging.getLogger(__name__)


class FantasyNerdsClient:
    """Async client for Fantasy Nerds API."""

    BASE_URL = "https://api.fantasynerds.com/v1/nfl"
    TIMEOUT = 30.0

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Fantasy Nerds client.

        Args:
            api_key: Fantasy Nerds API key. If not provided, will look for FFNERD_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FFNERD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Fantasy Nerds API key required. Set FFNERD_API_KEY environment variable."
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {"Accept": "application/json"}

    async def get_players(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch all NFL players from Fantasy Nerds.

        Args:
            include_inactive: Whether to include inactive players (default: False)

        Returns:
            List of player dictionaries with Fantasy Nerds player data.
        """
        url = f"{self.BASE_URL}/players"
        params = {"apikey": self.api_key}
        if include_inactive:
            params["include_inactive"] = "1"

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # API returns a list directly, not a dict with "players" key
            return data if isinstance(data, list) else []

    async def get_weekly_projections(
        self, week: Optional[int] = None, position: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch weekly fantasy projections.

        Args:
            week: NFL week number (1-18). If None, gets current week.
            position: Filter by position (QB, RB, WR, TE, K, DST). If None, gets all.

        Returns:
            Dictionary containing projections data.
        """
        url = f"{self.BASE_URL}/projections"
        params = {"apikey": self.api_key}
        if week:
            params["week"] = week
        if position:
            params["position"] = position.upper()

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()

    async def get_injuries(self, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch current NFL injury reports.

        Args:
            week: NFL week number. If None, gets most recent.

        Returns:
            List of injury report dictionaries.
        """
        url = f"{self.BASE_URL}/injuries"
        params = {"apikey": self.api_key}
        if week:
            params["week"] = week

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # API returns injuries nested in teams structure
            if isinstance(data, dict) and "teams" in data:
                injuries = []
                for team_data in data.get("teams", []):
                    if "players" in team_data:
                        injuries.extend(team_data["players"])
                return injuries
            return []

    async def get_news(
        self, player_id: Optional[int] = None, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent player news.

        Args:
            player_id: Fantasy Nerds player ID to filter news for specific player.
            days: Number of days of news to retrieve (default: 7).

        Returns:
            List of news article dictionaries.
        """
        url = f"{self.BASE_URL}/news"
        params = {"apikey": self.api_key, "days": days}
        if player_id:
            params["player_id"] = player_id

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # API returns news as a list directly
            return data if isinstance(data, list) else []

    async def get_rankings(
        self,
        scoring_type: str = "PPR",
        position: Optional[str] = None,
        week: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch expert consensus rankings.

        Args:
            scoring_type: Scoring format - "PPR", "HALF", or "STD" (default: "PPR").
            position: Filter by position (QB, RB, WR, TE, K, DST). If None, gets overall.
            week: NFL week number. If None, gets season rankings.

        Returns:
            List of player ranking dictionaries.
        """
        url = f"{self.BASE_URL}/rankings"
        params = {"apikey": self.api_key, "scoring": scoring_type.upper()}
        if position:
            params["position"] = position.upper()
        if week:
            params["week"] = week

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # Check for error in response
            if isinstance(data, dict) and "error" in data:
                logger.error(f"Rankings API error: {data['error']}")
                return []
            # API may return rankings as list or in a dict
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "rankings" in data:
                return data["rankings"]
            return []

    async def get_adp(
        self, scoring_type: str = "PPR", mock_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Fetch Average Draft Position data.

        Args:
            scoring_type: Scoring format - "PPR", "HALF", or "STD" (default: "PPR").
            mock_type: Draft type - "all", "mock", or "real" (default: "all").

        Returns:
            List of player ADP dictionaries.
        """
        url = f"{self.BASE_URL}/adp"
        params = {
            "apikey": self.api_key,
            "scoring": scoring_type.upper(),
            "type": mock_type.lower(),
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # API may return ADP as list or in a dict
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "adp" in data:
                return data["adp"]
            return []

    async def get_schedule(self, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch NFL game schedule.

        Args:
            week: NFL week number. If None, gets full season schedule.

        Returns:
            List of game dictionaries.
        """
        url = f"{self.BASE_URL}/schedule"
        params = {"apikey": self.api_key}
        if week:
            params["week"] = week

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            # API may return schedule as list or in a dict
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "schedule" in data:
                return data["schedule"]
            return []

    async def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            players = await self.get_players(include_inactive=False)
            return len(players) > 0
        except Exception as e:
            logger.error(f"Failed to connect to Fantasy Nerds API: {e}")
            return False
