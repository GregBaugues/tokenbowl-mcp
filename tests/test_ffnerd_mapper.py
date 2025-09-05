"""Unit tests for player ID mapper."""

import json
import pytest
from pathlib import Path
from ffnerd.mapper import PlayerMapper


@pytest.fixture
def mapper():
    """Create a PlayerMapper instance."""
    return PlayerMapper()


@pytest.fixture
def sample_sleeper_players():
    """Sample Sleeper player data."""
    return {
        "4046": {
            "player_id": "4046",
            "full_name": "Patrick Mahomes",
            "first_name": "Patrick",
            "last_name": "Mahomes",
            "team": "KC",
            "position": "QB",
            "status": "Active",
        },
        "4988": {
            "player_id": "4988",
            "full_name": "Justin Jefferson",
            "first_name": "Justin",
            "last_name": "Jefferson",
            "team": "MIN",
            "position": "WR",
            "status": "Active",
        },
        "2374": {
            "player_id": "2374",
            "full_name": "Odell Beckham Jr.",
            "first_name": "Odell",
            "last_name": "Beckham",
            "team": "MIA",
            "position": "WR",
            "status": "Active",
        },
        "KC": {
            "player_id": "KC",
            "full_name": "Kansas City Chiefs",
            "team": "KC",
            "position": "DEF",
            "status": "Active",
        },
    }


@pytest.fixture
def sample_ffnerd_players():
    """Sample Fantasy Nerds player data."""
    return [
        {"playerId": 1823, "name": "Patrick Mahomes", "team": "KC", "position": "QB"},
        {"playerId": 2456, "name": "Justin Jefferson", "team": "MIN", "position": "WR"},
        {
            "playerId": 987,
            "name": "Odell Beckham",  # Missing "Jr."
            "team": "MIA",
            "position": "WR",
        },
        {"playerId": 5001, "name": "Kansas City", "team": "KC", "position": "DST"},
    ]


class TestPlayerMapper:
    """Test PlayerMapper functionality."""

    def test_init(self, mapper):
        """Test mapper initialization."""
        assert mapper.sleeper_to_ffnerd == {}
        assert mapper.ffnerd_to_sleeper == {}
        assert mapper.confidence_scores == {}

    def test_normalize_name(self, mapper):
        """Test name normalization."""
        assert mapper.normalize_name("Patrick Mahomes") == "patrick mahomes"
        assert mapper.normalize_name("Odell Beckham Jr.") == "odell beckham"
        assert mapper.normalize_name("Robert Griffin III") == "robert griffin"
        assert mapper.normalize_name("Le'Veon Bell") == "leveon bell"
        assert mapper.normalize_name("JuJu Smith-Schuster") == "juju smithschuster"
        assert mapper.normalize_name("  John   Doe  ") == "john doe"
        assert mapper.normalize_name("") == ""
        assert mapper.normalize_name(None) == ""

    def test_normalize_team(self, mapper):
        """Test team abbreviation normalization."""
        assert mapper.normalize_team("KC") == "KC"
        assert mapper.normalize_team("kc") == "KC"
        assert mapper.normalize_team("ARI") == "ARZ"
        assert mapper.normalize_team("ARZ") == "ARI"
        assert mapper.normalize_team("WSH") == "WAS"
        assert mapper.normalize_team("WAS") == "WSH"
        assert mapper.normalize_team("JAX") == "JAC"
        assert mapper.normalize_team("JAC") == "JAX"
        assert mapper.normalize_team("LA") == "LAR"
        assert mapper.normalize_team("LAR") == "LA"
        assert mapper.normalize_team("") == ""
        assert mapper.normalize_team(None) == ""

    def test_calculate_similarity(self, mapper):
        """Test string similarity calculation."""
        assert mapper.calculate_similarity("patrick", "patrick") == 1.0
        assert mapper.calculate_similarity("patrick", "patrik") > 0.8
        assert mapper.calculate_similarity("mahomes", "mahones") > 0.8
        assert mapper.calculate_similarity("john", "jane") <= 0.5  # john/jane has exactly 0.5 similarity
        assert mapper.calculate_similarity("", "") == 1.0

    def test_match_player_exact(self, mapper):
        """Test exact player matching."""
        sleeper = {"full_name": "Patrick Mahomes", "team": "KC", "position": "QB"}
        ffnerd = {"name": "Patrick Mahomes", "team": "KC", "position": "QB"}

        is_match, confidence = mapper.match_player(sleeper, ffnerd)
        assert is_match is True
        assert confidence == 1.0

    def test_match_player_with_suffix(self, mapper):
        """Test matching players with name suffixes."""
        sleeper = {"full_name": "Odell Beckham Jr.", "team": "MIA", "position": "WR"}
        ffnerd = {"name": "Odell Beckham", "team": "MIA", "position": "WR"}

        is_match, confidence = mapper.match_player(sleeper, ffnerd)
        assert is_match is True
        assert confidence >= 0.85

    def test_match_player_team_change(self, mapper):
        """Test matching players who changed teams."""
        sleeper = {"full_name": "Calvin Ridley", "team": "TEN", "position": "WR"}
        ffnerd = {
            "name": "Calvin Ridley",
            "team": "",  # Free agent
            "position": "WR",
        }

        is_match, confidence = mapper.match_player(sleeper, ffnerd)
        assert is_match is True
        assert confidence >= 0.9

    def test_match_player_defense(self, mapper):
        """Test matching team defenses."""
        sleeper = {"full_name": "Kansas City Chiefs", "team": "KC", "position": "DEF"}
        ffnerd = {"name": "Kansas City", "team": "KC", "position": "DST"}

        is_match, confidence = mapper.match_player(sleeper, ffnerd)
        assert is_match is True
        assert confidence == 1.0

    def test_match_player_no_match(self, mapper):
        """Test non-matching players."""
        sleeper = {"full_name": "Patrick Mahomes", "team": "KC", "position": "QB"}
        ffnerd = {"name": "Josh Allen", "team": "BUF", "position": "QB"}

        is_match, confidence = mapper.match_player(sleeper, ffnerd)
        assert is_match is False
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_build_mapping(
        self, mapper, sample_sleeper_players, sample_ffnerd_players
    ):
        """Test building player mappings."""
        stats = await mapper.build_mapping(
            sample_sleeper_players, sample_ffnerd_players
        )

        # Check statistics
        assert stats["total_sleeper_players"] == 4
        assert stats["active_sleeper_players"] == 4
        assert stats["total_ffnerd_players"] == 4
        assert stats["mapped_count"] >= 3  # At least Mahomes, Jefferson, and Chiefs
        assert stats["mapping_rate"] >= 0.75

        # Check specific mappings
        assert mapper.get_ffnerd_id("4046") == 1823  # Mahomes
        assert mapper.get_ffnerd_id("4988") == 2456  # Jefferson
        assert mapper.get_sleeper_id(1823) == "4046"
        assert mapper.get_sleeper_id(2456) == "4988"

        # Check confidence scores
        assert mapper.get_confidence("4046") == 1.0  # Exact match
        assert mapper.get_confidence("4988") == 1.0  # Exact match

    def test_add_manual_mapping(self, mapper):
        """Test adding manual mapping overrides."""
        mapper.add_manual_mapping("9999", 8888, confidence=0.9)

        assert mapper.get_ffnerd_id("9999") == 8888
        assert mapper.get_sleeper_id(8888) == "9999"
        assert mapper.get_confidence("9999") == 0.9

    def test_save_and_load_mapping(self, mapper, tmp_path):
        """Test saving and loading mappings to/from JSON."""
        # Add some mappings
        mapper.add_manual_mapping("1234", 5678, 0.95)
        mapper.add_manual_mapping("2345", 6789, 1.0)

        # Save to file
        output_file = tmp_path / "test_mapping.json"
        mapper.save_mapping(str(output_file))

        # Verify file exists and contains correct data
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)

        assert "1234" in data
        assert data["1234"]["ffnerd_id"] == 5678
        assert data["1234"]["confidence"] == 0.95
        assert data["2345"]["ffnerd_id"] == 6789

        # Create new mapper and load the file
        new_mapper = PlayerMapper(str(output_file))
        assert new_mapper.get_ffnerd_id("1234") == 5678
        assert new_mapper.get_confidence("1234") == 0.95

    def test_load_mapping_file_not_found(self, mapper):
        """Test loading from non-existent file."""
        mapper.mapping_file = Path("/nonexistent/file.json")
        mapper.load_mapping()  # Should not raise, just log warning
        assert mapper.sleeper_to_ffnerd == {}

    def test_save_mapping_no_file_specified(self, mapper):
        """Test saving without output file specified."""
        with pytest.raises(ValueError, match="No output file specified"):
            mapper.save_mapping()

    def test_get_nonexistent_ids(self, mapper):
        """Test getting IDs that don't exist."""
        assert mapper.get_ffnerd_id("nonexistent") is None
        assert mapper.get_sleeper_id(99999) is None
        assert mapper.get_confidence("nonexistent") == 0.0

    @pytest.mark.asyncio
    async def test_build_mapping_inactive_players(self, mapper):
        """Test that inactive players are skipped in mapping."""
        sleeper_players = {
            "1": {
                "player_id": "1",
                "full_name": "Active Player",
                "team": "KC",
                "position": "QB",
                "status": "Active",
            },
            "2": {
                "player_id": "2",
                "full_name": "Retired Player",
                "team": "",
                "position": "RB",
                "status": "Inactive",
            },
        }

        ffnerd_players = [
            {"playerId": 101, "name": "Active Player", "team": "KC", "position": "QB"},
            {"playerId": 102, "name": "Retired Player", "team": "", "position": "RB"},
        ]

        stats = await mapper.build_mapping(sleeper_players, ffnerd_players)

        # Only active player should be mapped
        assert stats["active_sleeper_players"] == 1
        assert stats["mapped_count"] <= 1
        assert mapper.get_ffnerd_id("1") == 101
        assert mapper.get_ffnerd_id("2") is None  # Inactive, not mapped

    @pytest.mark.asyncio
    async def test_build_mapping_special_characters(self, mapper):
        """Test mapping players with special characters in names."""
        sleeper_players = {
            "1": {
                "player_id": "1",
                "full_name": "JuJu Smith-Schuster",
                "team": "NE",
                "position": "WR",
                "status": "Active",
            }
        }

        ffnerd_players = [
            {
                "playerId": 201,
                "name": "JuJu Smith Schuster",
                "team": "NE",
                "position": "WR",
            }
        ]

        stats = await mapper.build_mapping(sleeper_players, ffnerd_players)

        assert stats["mapped_count"] == 1
        assert mapper.get_ffnerd_id("1") == 201
