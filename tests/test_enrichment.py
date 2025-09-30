"""Unit tests for lib/enrichment.py player enrichment utilities."""

import pytest
from unittest.mock import AsyncMock

from lib.enrichment import (
    enrich_player_basic,
    enrich_player_stats,
    enrich_player_injury_news,
    enrich_player_full,
    enrich_player_minimal,
    get_trending_data_map,
    get_recent_drops_set,
    add_trending_data,
    mark_recent_drops,
    organize_roster_by_position,
)


class TestEnrichPlayerBasic:
    """Tests for enrich_player_basic()."""

    def test_basic_player_info(self):
        """Test basic player info extraction."""
        player_data = {
            "full_name": "Patrick Mahomes",
            "position": "QB",
            "team": "KC",
            "status": "Active",
        }
        result = enrich_player_basic("4046", player_data)

        assert result["player_id"] == "4046"
        assert result["name"] == "Patrick Mahomes"
        assert result["position"] == "QB"
        assert result["team"] == "KC"
        assert result["status"] == "Active"

    def test_defense_handling(self):
        """Test that team defenses are handled correctly."""
        player_data = {"full_name": "Kansas City Chiefs", "position": "DEF"}
        result = enrich_player_basic("KC", player_data)

        assert result["player_id"] == "KC"
        assert result["name"] == "KC Defense"
        assert result["position"] == "DEF"
        assert result["team"] == "KC"

    def test_missing_player_name(self):
        """Test fallback for missing player name."""
        player_data = {"position": "RB", "team": "SF"}
        result = enrich_player_basic("9999", player_data)

        assert result["player_id"] == "9999"
        assert result["name"] == "9999 (Unknown)"
        assert result["position"] == "RB"

    def test_empty_player_data(self):
        """Test with empty player data."""
        result = enrich_player_basic("1234", {})

        assert result["player_id"] == "1234"
        assert result["name"] == "1234 (Unknown)"
        assert result["position"] is None
        assert result["team"] is None
        assert result["status"] is None


class TestEnrichPlayerStats:
    """Tests for enrich_player_stats()."""

    def test_projected_stats(self):
        """Test extraction of projected stats."""
        player_data = {
            "stats": {
                "projected": {
                    "fantasy_points": 22.5,
                    "fantasy_points_low": 18.2,
                    "fantasy_points_high": 26.8,
                }
            }
        }
        result = enrich_player_stats(player_data)

        assert result["projected"]["fantasy_points"] == 22.5
        assert result["projected"]["fantasy_points_low"] == 18.2
        assert result["projected"]["fantasy_points_high"] == 26.8

    def test_ros_projected_stats_qb(self):
        """Test ROS projected stats for QB with position-specific data."""
        player_data = {
            "position": "QB",
            "stats": {
                "ros_projected": {
                    "fantasy_points": 285.6,
                    "season": "2024",
                    "passing_yards": 4200,
                    "passing_touchdowns": 32,
                    "rushing_yards": 250,
                    "rushing_touchdowns": 2,
                }
            },
        }
        result = enrich_player_stats(player_data, include_position_stats=True)

        assert result["ros_projected"]["fantasy_points"] == 285.6
        assert result["ros_projected"]["season"] == "2024"
        assert result["ros_projected"]["passing_yards"] == 4200
        assert result["ros_projected"]["passing_touchdowns"] == 32
        assert result["ros_projected"]["rushing_yards"] == 250
        assert result["ros_projected"]["rushing_touchdowns"] == 2

    def test_ros_projected_stats_rb(self):
        """Test ROS projected stats for RB with position-specific data."""
        player_data = {
            "position": "RB",
            "stats": {
                "ros_projected": {
                    "fantasy_points": 195.4,
                    "season": "2024",
                    "rushing_yards": 1200,
                    "receiving_yards": 400,
                    "receptions": 45,
                    "total_touchdowns": 12,
                }
            },
        }
        result = enrich_player_stats(player_data, include_position_stats=True)

        assert result["ros_projected"]["fantasy_points"] == 195.4
        assert result["ros_projected"]["rushing_yards"] == 1200
        assert result["ros_projected"]["receiving_yards"] == 400
        assert result["ros_projected"]["receptions"] == 45
        assert result["ros_projected"]["total_touchdowns"] == 12

    def test_ros_projected_stats_without_position_stats(self):
        """Test ROS projected stats without position-specific data."""
        player_data = {
            "position": "QB",
            "stats": {
                "ros_projected": {
                    "fantasy_points": 285.6,
                    "season": "2024",
                    "passing_yards": 4200,
                }
            },
        }
        result = enrich_player_stats(player_data, include_position_stats=False)

        assert result["ros_projected"]["fantasy_points"] == 285.6
        assert result["ros_projected"]["season"] == "2024"
        # Position-specific stats should not be included
        assert "passing_yards" not in result["ros_projected"]

    def test_actual_stats(self):
        """Test extraction of actual game stats."""
        player_data = {
            "stats": {
                "actual": {
                    "fantasy_points": 24.8,
                    "game_status": "Final",
                    "game_stats": {"passing_yards": 320, "passing_touchdowns": 3},
                }
            }
        }
        result = enrich_player_stats(player_data)

        assert result["actual"]["fantasy_points"] == 24.8
        assert result["actual"]["game_status"] == "Final"
        assert result["actual"]["game_stats"]["passing_yards"] == 320

    def test_no_stats_available(self):
        """Test when no stats are available."""
        player_data = {"position": "QB"}
        result = enrich_player_stats(player_data)

        assert result["projected"] is None
        assert result["ros_projected"] is None
        assert result["actual"] is None

    def test_partial_stats(self):
        """Test with only some stats available."""
        player_data = {
            "stats": {
                "projected": {"fantasy_points": 15.2},
                # No ros_projected or actual
            }
        }
        result = enrich_player_stats(player_data)

        assert result["projected"]["fantasy_points"] == 15.2
        assert result["ros_projected"] is None
        assert result["actual"] is None


class TestEnrichPlayerInjuryNews:
    """Tests for enrich_player_injury_news()."""

    def test_injury_info(self):
        """Test extraction of injury information."""
        player_data = {
            "data": {
                "injury": {
                    "game_status": "Questionable",
                    "injury": "Ankle",
                    "last_update": "2024-01-15",
                }
            }
        }
        result = enrich_player_injury_news(player_data)

        assert result["injury"]["status"] == "Questionable"
        assert result["injury"]["description"] == "Ankle"
        assert result["injury"]["last_update"] == "2024-01-15"

    def test_news_items(self):
        """Test extraction of news items."""
        player_data = {
            "data": {
                "news": [
                    {"title": "News 1", "date": "2024-01-15"},
                    {"title": "News 2", "date": "2024-01-14"},
                    {"title": "News 3", "date": "2024-01-13"},
                    {"title": "News 4", "date": "2024-01-12"},
                ]
            }
        }
        result = enrich_player_injury_news(player_data, max_news=3)

        assert len(result["news"]) == 3
        assert result["news"][0]["title"] == "News 1"
        assert result["news"][2]["title"] == "News 3"

    def test_no_injury_or_news(self):
        """Test when no injury or news data exists."""
        player_data = {"data": {}}
        result = enrich_player_injury_news(player_data)

        assert "injury" not in result
        assert "news" not in result

    def test_no_data_section(self):
        """Test when data section doesn't exist."""
        player_data = {"position": "QB"}
        result = enrich_player_injury_news(player_data)

        assert result == {}


class TestEnrichPlayerFull:
    """Tests for enrich_player_full()."""

    def test_full_enrichment(self):
        """Test complete player enrichment."""
        player_data = {
            "full_name": "Patrick Mahomes",
            "position": "QB",
            "team": "KC",
            "status": "Active",
            "stats": {
                "projected": {"fantasy_points": 22.5},
                "ros_projected": {"fantasy_points": 285.6, "season": "2024"},
            },
            "data": {
                "injury": {"game_status": "Healthy"},
                "news": [{"title": "Latest news"}],
            },
        }
        result = enrich_player_full("4046", player_data)

        # Check basic info
        assert result["player_id"] == "4046"
        assert result["name"] == "Patrick Mahomes"
        assert result["position"] == "QB"

        # Check stats
        assert result["stats"]["projected"]["fantasy_points"] == 22.5
        assert result["stats"]["ros_projected"]["fantasy_points"] == 285.6

        # Check injury/news
        assert result["injury"]["status"] == "Healthy"
        assert len(result["news"]) == 1

    def test_minimal_data_enrichment(self):
        """Test enrichment with minimal player data."""
        player_data = {"full_name": "Unknown Player"}
        result = enrich_player_full("9999", player_data)

        assert result["player_id"] == "9999"
        assert result["name"] == "Unknown Player"
        assert result["stats"]["projected"] is None


class TestEnrichPlayerMinimal:
    """Tests for enrich_player_minimal()."""

    def test_minimal_player_data(self):
        """Test minimal player data extraction."""
        player_data = {
            "full_name": "Justin Jefferson",
            "position": "WR",
            "team": "MIN",
            "status": "Active",
            "injury_status": None,
            "stats": {"projected": {"fantasy_points": 18.5}},
        }
        result = enrich_player_minimal("7528", player_data)

        assert result["player_id"] == "7528"
        assert result["full_name"] == "Justin Jefferson"
        assert result["position"] == "WR"
        assert result["team"] == "MIN"
        assert result["status"] == "Active"
        assert result["projected_points"] == 18.5

    def test_minimal_with_ros_projected(self):
        """Test minimal data includes ROS projected points."""
        player_data = {
            "full_name": "Player Name",
            "stats": {
                "projected": {"fantasy_points": 15.0},
                "ros_projected": {"fantasy_points": 200.0},
            },
        }
        result = enrich_player_minimal("1234", player_data)

        assert result["projected_points"] == 15.0
        assert result["ros_projected_points"] == 200.0

    def test_minimal_backward_compatibility(self):
        """Test fallback to old stat location."""
        player_data = {
            "full_name": "Player Name",
            "data": {"projections": {"proj_pts": 12.5}},
        }
        result = enrich_player_minimal("1234", player_data)

        assert result["projected_points"] == 12.5

    def test_minimal_no_projections(self):
        """Test minimal data without projections."""
        player_data = {
            "full_name": "Player Name",
            "position": "TE",
        }
        result = enrich_player_minimal("1234", player_data)

        assert result["player_id"] == "1234"
        assert result["full_name"] == "Player Name"
        assert "projected_points" not in result


class TestGetTrendingDataMap:
    """Tests for get_trending_data_map()."""

    @pytest.mark.asyncio
    async def test_trending_data_map(self):
        """Test fetching and mapping trending data."""
        mock_fn = AsyncMock(
            return_value=[
                {"player_id": "4046", "count": 150},
                {"player_id": "7528", "count": 120},
            ]
        )

        result = await get_trending_data_map(mock_fn, txn_type="add")

        assert result == {"4046": 150, "7528": 120}
        mock_fn.assert_called_once_with(type="add")

    @pytest.mark.asyncio
    async def test_trending_data_map_error(self):
        """Test graceful error handling."""
        mock_fn = AsyncMock(side_effect=Exception("API error"))

        result = await get_trending_data_map(mock_fn, txn_type="add")

        assert result == {}


class TestGetRecentDropsSet:
    """Tests for get_recent_drops_set()."""

    @pytest.mark.asyncio
    async def test_recent_drops_set(self):
        """Test fetching recently dropped players."""
        mock_fn = AsyncMock(
            return_value=[
                {"drops": {"4046": {"player_id": "4046"}, "7528": {"player_id": "7528"}}},
                {"drops": {"9999": {"player_id": "9999"}}},
            ]
        )

        result = await get_recent_drops_set(mock_fn, days_back=7)

        assert result == {"4046", "7528", "9999"}
        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_recent_drops_set_no_drops(self):
        """Test when no transactions have drops."""
        mock_fn = AsyncMock(return_value=[{"adds": {"4046": {"player_id": "4046"}}}])

        result = await get_recent_drops_set(mock_fn, days_back=7)

        assert result == set()

    @pytest.mark.asyncio
    async def test_recent_drops_set_error(self):
        """Test graceful error handling."""
        mock_fn = AsyncMock(side_effect=Exception("API error"))

        result = await get_recent_drops_set(mock_fn, days_back=7)

        assert result == set()


class TestAddTrendingData:
    """Tests for add_trending_data()."""

    def test_add_trending_counts(self):
        """Test adding trending counts to players."""
        players = [
            {"player_id": "4046", "name": "Patrick Mahomes"},
            {"player_id": "7528", "name": "Justin Jefferson"},
            {"player_id": "9999", "name": "Unknown Player"},
        ]
        trending_map = {"4046": 150, "7528": 120}

        result = add_trending_data(players, trending_map)

        assert result[0]["trending_add_count"] == 150
        assert result[1]["trending_add_count"] == 120
        assert "trending_add_count" not in result[2]

    def test_add_trending_empty_map(self):
        """Test with empty trending map."""
        players = [{"player_id": "4046"}]
        result = add_trending_data(players, {})

        assert "trending_add_count" not in result[0]


class TestMarkRecentDrops:
    """Tests for mark_recent_drops()."""

    def test_mark_recently_dropped(self):
        """Test marking recently dropped players."""
        players = [
            {"player_id": "4046", "name": "Patrick Mahomes"},
            {"player_id": "7528", "name": "Justin Jefferson"},
            {"player_id": "9999", "name": "Unknown Player"},
        ]
        recent_drops = {"4046", "9999"}

        result = mark_recent_drops(players, recent_drops)

        assert result[0]["recently_dropped"] is True
        assert "recently_dropped" not in result[1]
        assert result[2]["recently_dropped"] is True

    def test_mark_recent_drops_empty_set(self):
        """Test with empty drops set."""
        players = [{"player_id": "4046"}]
        result = mark_recent_drops(players, set())

        assert "recently_dropped" not in result[0]


class TestOrganizeRosterByPosition:
    """Tests for organize_roster_by_position()."""

    def test_organize_roster(self):
        """Test organizing players into roster categories."""
        players = [
            {"player_id": "4046", "name": "Patrick Mahomes"},
            {"player_id": "7528", "name": "Justin Jefferson"},
            {"player_id": "9999", "name": "Bench Player"},
            {"player_id": "8888", "name": "Taxi Player"},
            {"player_id": "7777", "name": "IR Player"},
        ]
        starters_ids = ["4046", "7528"]
        taxi_ids = ["8888"]
        reserve_ids = ["7777"]

        result = organize_roster_by_position(
            players, starters_ids, taxi_ids, reserve_ids
        )

        assert len(result["starters"]) == 2
        assert len(result["bench"]) == 1
        assert len(result["taxi"]) == 1
        assert len(result["reserve"]) == 1

        assert result["starters"][0]["player_id"] == "4046"
        assert result["bench"][0]["player_id"] == "9999"
        assert result["taxi"][0]["player_id"] == "8888"
        assert result["reserve"][0]["player_id"] == "7777"

    def test_organize_roster_all_bench(self):
        """Test when all players are on bench."""
        players = [
            {"player_id": "1"},
            {"player_id": "2"},
            {"player_id": "3"},
        ]
        result = organize_roster_by_position(players, [], [], [])

        assert len(result["starters"]) == 0
        assert len(result["bench"]) == 3
        assert len(result["taxi"]) == 0
        assert len(result["reserve"]) == 0

    def test_organize_roster_empty(self):
        """Test with empty player list."""
        result = organize_roster_by_position([], [], [], [])

        assert len(result["starters"]) == 0
        assert len(result["bench"]) == 0
        assert len(result["taxi"]) == 0
        assert len(result["reserve"]) == 0