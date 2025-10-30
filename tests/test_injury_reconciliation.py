"""Test injury status reconciliation from issue #119."""

import pytest
from unittest.mock import patch, MagicMock
from build_cache import enrich_and_filter_players


class TestInjuryReconciliation:
    """Test that conflicting injury statuses are properly reconciled."""

    def test_ffnerd_injury_overrides_sleeper_when_out(self):
        """When FFNerd says 'Out', Sleeper injury_status should be overridden."""
        sleeper_players = {
            "5927": {
                "player_id": "5927",
                "full_name": "Terry McLaurin",
                "position": "WR",
                "team": "WAS",
                "injury_status": "Questionable",  # Sleeper says Questionable
                "injury_body_part": "Ankle",
                "status": "Active",
                "age": 30,
                "first_name": "Terry",
                "last_name": "McLaurin",
            }
        }

        mapping = {"5927": 1234}

        ffnerd_data = {
            "1234": {
                "projections": None,
                "ros_projections": None,
                "injury": {
                    "game_status": "Out For Week 9",  # FFNerd says Out
                    "injury": "Quadriceps",
                    "last_update": "2025-10-29",
                    "team": "WAS",
                    "position": "WR",
                },
                "news": [],
            }
        }

        stats_data = {}
        bye_weeks_map = {"WAS": 12}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        # Verify the injury_status was updated to match FFNerd
        assert result["5927"]["injury_status"] == "Out"
        # Verify injury_body_part was updated from FFNerd
        assert result["5927"]["injury_body_part"] == "Quadriceps"
        # Verify FFNerd data is still preserved
        assert result["5927"]["data"]["injury"]["game_status"] == "Out For Week 9"

    def test_ffnerd_questionable_overrides_sleeper_out(self):
        """When FFNerd says 'Questionable', it should override Sleeper's 'Out'."""
        sleeper_players = {
            "1234": {
                "player_id": "1234",
                "full_name": "Test Player",
                "position": "RB",
                "team": "NYG",
                "injury_status": "Out",  # Sleeper says Out
                "status": "Active",
                "first_name": "Test",
                "last_name": "Player",
            }
        }

        mapping = {"1234": 5678}

        ffnerd_data = {
            "5678": {
                "injury": {
                    "game_status": "Questionable For Week 9 Vs. Seattle",
                    "injury": "Hamstring",
                    "last_update": "2025-10-29",
                },
                "news": [],
            }
        }

        stats_data = {}
        bye_weeks_map = {}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        # FFNerd should override Sleeper
        assert result["1234"]["injury_status"] == "Questionable"
        assert result["1234"]["injury_body_part"] == "Hamstring"

    def test_sleeper_injury_preserved_when_no_ffnerd_data(self):
        """When FFNerd has no injury data, preserve Sleeper's injury_status."""
        sleeper_players = {
            "9999": {
                "player_id": "9999",
                "full_name": "No Match Player",
                "position": "WR",
                "team": "DAL",
                "injury_status": "Doubtful",
                "injury_body_part": "Knee",
                "status": "Active",
                "first_name": "No",
                "last_name": "Match",
            }
        }

        mapping = {}  # No mapping to FFNerd
        ffnerd_data = {}
        stats_data = {}
        bye_weeks_map = {}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        # Sleeper injury data should be preserved
        assert result["9999"]["injury_status"] == "Doubtful"
        assert result["9999"]["injury_body_part"] == "Knee"
        # No FFNerd data should be present
        assert "data" not in result["9999"]

    def test_healthy_player_clears_injury_status(self):
        """When FFNerd indicates healthy, injury_status should be cleared."""
        sleeper_players = {
            "7777": {
                "player_id": "7777",
                "full_name": "Healthy Player",
                "position": "QB",
                "team": "BUF",
                "injury_status": "Questionable",  # Old injury in Sleeper
                "status": "Active",
                "first_name": "Healthy",
                "last_name": "Player",
            }
        }

        mapping = {"7777": 3333}

        ffnerd_data = {
            "3333": {
                "injury": {
                    "game_status": "Healthy",  # Player is now healthy
                    "injury": None,
                    "last_update": "2025-10-29",
                },
                "news": [],
            }
        }

        stats_data = {}
        bye_weeks_map = {}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        # injury_status should be cleared
        assert result["7777"]["injury_status"] is None

    def test_ir_status_properly_mapped(self):
        """Test that IR status is properly mapped from FFNerd."""
        sleeper_players = {
            "8888": {
                "player_id": "8888",
                "full_name": "IR Player",
                "position": "RB",
                "team": "SF",
                "injury_status": None,
                "status": "Active",
                "first_name": "IR",
                "last_name": "Player",
            }
        }

        mapping = {"8888": 4444}

        ffnerd_data = {
            "4444": {
                "injury": {
                    "game_status": "Injured Reserve",
                    "injury": "ACL",
                    "last_update": "2025-10-29",
                },
                "news": [],
            }
        }

        stats_data = {}
        bye_weeks_map = {}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        assert result["8888"]["injury_status"] == "IR"
        assert result["8888"]["injury_body_part"] == "ACL"

    def test_injury_without_game_status_marked_questionable(self):
        """Test that injuries without specific game_status are marked Questionable."""
        sleeper_players = {
            "6666": {
                "player_id": "6666",
                "full_name": "Injury No Status",
                "position": "TE",
                "team": "KC",
                "injury_status": None,
                "status": "Active",
                "first_name": "Injury",
                "last_name": "No Status",
            }
        }

        mapping = {"6666": 2222}

        ffnerd_data = {
            "2222": {
                "injury": {
                    "game_status": "",  # No specific game status
                    "injury": "Shoulder",  # But has an injury
                    "last_update": "2025-10-29",
                },
                "news": [],
            }
        }

        stats_data = {}
        bye_weeks_map = {}

        result = enrich_and_filter_players(
            sleeper_players, mapping, ffnerd_data, stats_data, bye_weeks_map
        )

        # Should default to Questionable when injured but no specific status
        assert result["6666"]["injury_status"] == "Questionable"
        assert result["6666"]["injury_body_part"] == "Shoulder"