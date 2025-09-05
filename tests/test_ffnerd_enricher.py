"""Tests for Fantasy Nerds player data enrichment."""

import time
from unittest.mock import Mock, AsyncMock
import pytest

from ffnerd.enricher import (
    PlayerEnricher,
    EnrichmentMetrics,
    validate_enrichment_data,
    normalize_team_abbreviation,
    merge_injury_data,
)


@pytest.fixture
def mock_mapper():
    """Create a mock PlayerMapper."""
    mapper = Mock()
    mapper.get_ffnerd_id = Mock(
        side_effect=lambda sleeper_id: {
            "4046": 1823,  # Patrick Mahomes
            "6786": 2234,  # Jonathan Taylor
            "4984": 2145,  # Calvin Ridley
            "unmapped": None,  # Player without mapping
        }.get(sleeper_id)
    )
    return mapper


@pytest.fixture
def mock_cache():
    """Create a mock FantasyNerdsCache."""
    cache = Mock()
    cache.get_player_enrichment = AsyncMock(
        return_value={
            "projections": {
                "week": 1,
                "points": 24.5,
                "passing_yards": 298,
                "passing_tds": 2,
            },
            "injury": {
                "status": "Healthy",
                "description": None,
                "last_update": "2025-01-05",
            },
            "news": [
                {
                    "headline": "Mahomes ready for season",
                    "date": "2025-01-04",
                    "link": "https://example.com",
                }
            ],
            "rankings": {"overall": 2, "position": 1},
        }
    )
    return cache


@pytest.fixture
def enricher(mock_mapper, mock_cache):
    """Create a PlayerEnricher with mocked dependencies."""
    return PlayerEnricher(mapper=mock_mapper, cache=mock_cache)


@pytest.fixture
def sample_sleeper_player():
    """Create sample Sleeper player data."""
    return {
        "player_id": "4046",
        "full_name": "Patrick Mahomes",
        "first_name": "Patrick",
        "last_name": "Mahomes",
        "team": "KC",
        "position": "QB",
        "age": 28,
        "status": "Active",
        "injury_status": None,
    }


class TestEnrichmentMetrics:
    """Test suite for EnrichmentMetrics class."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = EnrichmentMetrics()
        assert metrics.total_processed == 0
        assert metrics.successful_enrichments == 0
        assert metrics.missing_mappings == 0
        assert metrics.confidence_scores == []
        assert metrics.processing_times == []

    def test_record_successful_enrichment(self):
        """Test recording a successful enrichment."""
        metrics = EnrichmentMetrics()
        metrics.record_enrichment(
            success=True, confidence=0.85, time_ms=15.5, cache_hit=True
        )

        assert metrics.total_processed == 1
        assert metrics.successful_enrichments == 1
        assert metrics.failed_enrichments == 0
        assert metrics.confidence_scores == [0.85]
        assert metrics.processing_times == [15.5]
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 0

    def test_record_failed_enrichment(self):
        """Test recording a failed enrichment."""
        metrics = EnrichmentMetrics()
        metrics.record_enrichment(success=False, cache_hit=False)

        assert metrics.total_processed == 1
        assert metrics.successful_enrichments == 0
        assert metrics.failed_enrichments == 1
        assert metrics.confidence_scores == []
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 1

    def test_record_missing_mapping(self):
        """Test recording a missing mapping."""
        metrics = EnrichmentMetrics()
        metrics.record_missing_mapping()

        assert metrics.total_processed == 1
        assert metrics.missing_mappings == 1
        assert metrics.successful_enrichments == 0

    def test_get_summary(self):
        """Test getting metrics summary."""
        metrics = EnrichmentMetrics()
        metrics.start_tracking()

        # Record various operations
        metrics.record_enrichment(True, 0.9, 10.0, True)
        metrics.record_enrichment(True, 0.8, 12.0, True)
        metrics.record_enrichment(False, cache_hit=False)
        metrics.record_missing_mapping()

        summary = metrics.get_summary()

        assert summary["total_processed"] == 4
        assert summary["successful_enrichments"] == 2
        assert summary["failed_enrichments"] == 1
        assert summary["missing_mappings"] == 1
        assert summary["success_rate"] == 50.0
        assert summary["average_confidence"] == 0.85
        assert summary["average_time_ms"] == 11.0
        assert summary["cache_hit_rate"] == 66.67
        assert summary["elapsed_time_seconds"] is not None


class TestPlayerEnricher:
    """Test suite for PlayerEnricher class."""

    def test_initialization_default(self):
        """Test enricher initialization with defaults."""
        enricher = PlayerEnricher()
        assert enricher.mapper is not None
        assert enricher.cache is not None
        assert isinstance(enricher.metrics, EnrichmentMetrics)

    def test_initialization_with_dependencies(self, mock_mapper, mock_cache):
        """Test enricher initialization with provided dependencies."""
        enricher = PlayerEnricher(mapper=mock_mapper, cache=mock_cache)
        assert enricher.mapper is mock_mapper
        assert enricher.cache is mock_cache

    def test_calculate_confidence_no_data(self, enricher, sample_sleeper_player):
        """Test confidence calculation with no enrichment data."""
        confidence = enricher.calculate_confidence(sample_sleeper_player, None)
        assert confidence == 0.0

    def test_calculate_confidence_full_data(self, enricher, sample_sleeper_player):
        """Test confidence calculation with full enrichment data."""
        ffnerd_data = {
            "projections": {"points": 24.5},
            "injury": {"status": "Healthy"},
            "news": [{"headline": "News"}],
            "rankings": {"overall": 2},
            "ffnerd_id": 1823,
        }

        confidence = enricher.calculate_confidence(sample_sleeper_player, ffnerd_data)
        assert confidence > 0.9  # Should be high with all data present

    def test_calculate_confidence_partial_data(self, enricher, sample_sleeper_player):
        """Test confidence calculation with partial enrichment data."""
        ffnerd_data = {
            "projections": {"points": 24.5},
            "injury": None,
            "news": [],
            "rankings": {"overall": 2},
        }

        confidence = enricher.calculate_confidence(sample_sleeper_player, ffnerd_data)
        assert 0.3 < confidence < 0.7  # Should be moderate with partial data

    def test_calculate_confidence_skill_position_boost(self, enricher):
        """Test confidence boost for skill position players."""
        qb_player = {"position": "QB", "player_id": "123"}
        k_player = {"position": "K", "player_id": "456"}

        ffnerd_data = {"projections": {"points": 10}}

        qb_confidence = enricher.calculate_confidence(qb_player, ffnerd_data)
        k_confidence = enricher.calculate_confidence(k_player, ffnerd_data)

        # Kickers should get more lenient scoring
        assert k_confidence > qb_confidence

    @pytest.mark.asyncio
    async def test_enrich_player_success(self, enricher, sample_sleeper_player):
        """Test successful player enrichment."""
        enriched = await enricher.enrich_player(sample_sleeper_player)

        assert "ffnerd_data" in enriched
        assert enriched["ffnerd_data"]["projections"]["points"] == 24.5
        assert enriched["ffnerd_data"]["confidence"] > 0
        assert "enriched_at" in enriched["ffnerd_data"]
        assert enriched["ffnerd_data"]["ffnerd_id"] == 1823

        # Original data should be preserved
        assert enriched["full_name"] == "Patrick Mahomes"
        assert enriched["team"] == "KC"

    @pytest.mark.asyncio
    async def test_enrich_player_no_mapping(self, enricher):
        """Test enrichment with no Fantasy Nerds mapping."""
        unmapped_player = {
            "player_id": "unmapped",
            "full_name": "Unknown Player",
            "position": "RB",
        }

        enriched = await enricher.enrich_player(unmapped_player)

        assert "ffnerd_data" not in enriched
        assert enriched["full_name"] == "Unknown Player"
        assert enricher.metrics.missing_mappings == 1

    @pytest.mark.asyncio
    async def test_enrich_player_missing_id(self, enricher):
        """Test enrichment with missing player_id."""
        player_no_id = {"full_name": "No ID Player", "position": "WR"}

        enriched = await enricher.enrich_player(player_no_id)

        assert "ffnerd_data" not in enriched
        assert enricher.metrics.failed_enrichments == 1

    @pytest.mark.asyncio
    async def test_enrich_player_cache_error(self, enricher, sample_sleeper_player):
        """Test enrichment when cache throws an error."""
        enricher.cache.get_player_enrichment = AsyncMock(
            side_effect=Exception("Cache error")
        )

        enriched = await enricher.enrich_player(sample_sleeper_player)

        assert "ffnerd_data" not in enriched
        assert enriched["full_name"] == "Patrick Mahomes"
        assert enricher.metrics.failed_enrichments == 1

    @pytest.mark.asyncio
    async def test_enrich_players_bulk(self, enricher):
        """Test bulk player enrichment."""
        players = {
            "4046": {
                "player_id": "4046",
                "full_name": "Patrick Mahomes",
                "position": "QB",
            },
            "6786": {
                "player_id": "6786",
                "full_name": "Jonathan Taylor",
                "position": "RB",
            },
            "unmapped": {
                "player_id": "unmapped",
                "full_name": "Unknown Player",
                "position": "WR",
            },
        }

        enriched = await enricher.enrich_players(players)

        assert len(enriched) == 3
        assert "ffnerd_data" in enriched["4046"]
        assert "ffnerd_data" in enriched["6786"]
        assert "ffnerd_data" not in enriched["unmapped"]

        metrics = enricher.get_metrics()
        assert metrics["total_processed"] == 3
        assert metrics["successful_enrichments"] == 2
        assert metrics["missing_mappings"] == 1

    @pytest.mark.asyncio
    async def test_enrich_players_concurrency_limit(self, enricher):
        """Test that bulk enrichment respects concurrency limits."""
        # Create many players to test concurrency
        players = {
            str(i): {
                "player_id": "4046" if i % 2 == 0 else "unmapped",
                "full_name": f"Player {i}",
                "position": "QB",
            }
            for i in range(100)
        }

        start_time = time.time()
        enriched = await enricher.enrich_players(players, max_concurrent=10)
        elapsed = time.time() - start_time

        assert len(enriched) == 100
        # Should complete reasonably quickly with concurrency
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_enrich_players_with_exceptions(self, enricher):
        """Test bulk enrichment handles individual exceptions gracefully."""
        players = {
            "4046": {
                "player_id": "4046",
                "full_name": "Patrick Mahomes",
                "position": "QB",
            },
            "bad": {
                "player_id": "bad",
                "full_name": "Bad Player",
                # Missing position to potentially cause issues
            },
        }

        # Make one call fail
        original_get = enricher.cache.get_player_enrichment

        async def failing_get(sleeper_id, ffnerd_id):
            if sleeper_id == "bad":
                raise Exception("Test error")
            return await original_get(sleeper_id=sleeper_id, ffnerd_id=ffnerd_id)

        enricher.cache.get_player_enrichment = failing_get
        enricher.mapper.get_ffnerd_id = Mock(return_value=123)  # All mapped

        enriched = await enricher.enrich_players(players)

        # Should still return results for successful enrichments
        assert len(enriched) == 2
        assert "ffnerd_data" in enriched["4046"]

    def test_get_metrics(self, enricher):
        """Test getting enrichment metrics."""
        enricher.metrics.record_enrichment(True, 0.85, 10.0, True)

        metrics = enricher.get_metrics()
        assert metrics["total_processed"] == 1
        assert metrics["successful_enrichments"] == 1

    def test_reset_metrics(self, enricher):
        """Test resetting enrichment metrics."""
        enricher.metrics.record_enrichment(True, 0.85, 10.0, True)
        assert enricher.metrics.total_processed == 1

        enricher.reset_metrics()
        assert enricher.metrics.total_processed == 0


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_validate_enrichment_data_valid(self):
        """Test validation of valid enrichment data."""
        valid_data = {"projections": {"points": 20}, "injury": {"status": "Healthy"}}
        assert validate_enrichment_data(valid_data) is True

    def test_validate_enrichment_data_invalid(self):
        """Test validation of invalid enrichment data."""
        assert validate_enrichment_data(None) is False
        assert validate_enrichment_data([]) is False
        assert validate_enrichment_data({}) is False
        assert validate_enrichment_data({"other": "data"}) is False

    def test_normalize_team_abbreviation(self):
        """Test team abbreviation normalization."""
        assert normalize_team_abbreviation("ARI") == "ARZ"
        assert normalize_team_abbreviation("ARZ") == "ARI"
        assert normalize_team_abbreviation("WSH") == "WAS"
        assert normalize_team_abbreviation("WAS") == "WSH"
        assert normalize_team_abbreviation("JAX") == "JAC"
        assert normalize_team_abbreviation("JAC") == "JAX"
        assert normalize_team_abbreviation("LA") == "LAR"
        assert normalize_team_abbreviation("KC") == "KC"  # No change
        assert normalize_team_abbreviation("gb") == "GB"  # Case normalized

    def test_merge_injury_data_both_present(self):
        """Test merging injury data when both sources have data."""
        sleeper_injury = {"status": "Questionable", "body_part": "knee"}
        ffnerd_injury = {
            "status": "Doubtful",
            "description": "Knee sprain",
            "last_update": "2025-01-05",
        }

        merged = merge_injury_data(sleeper_injury, ffnerd_injury)

        # Sleeper takes priority
        assert merged["status"] == "Questionable"
        assert merged["body_part"] == "knee"
        # But Fantasy Nerds adds extra info
        assert merged["ffnerd_description"] == "Knee sprain"
        assert merged["ffnerd_last_update"] == "2025-01-05"

    def test_merge_injury_data_only_sleeper(self):
        """Test merging when only Sleeper has injury data."""
        sleeper_injury = {"status": "Out", "body_part": "ankle"}

        merged = merge_injury_data(sleeper_injury, None)

        assert merged == sleeper_injury

    def test_merge_injury_data_only_ffnerd(self):
        """Test merging when only Fantasy Nerds has injury data."""
        ffnerd_injury = {"status": "Questionable", "description": "Hamstring strain"}

        merged = merge_injury_data(None, ffnerd_injury)

        assert merged == ffnerd_injury

    def test_merge_injury_data_both_none(self):
        """Test merging when neither has injury data."""
        merged = merge_injury_data(None, None)
        assert merged is None


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Integration tests for realistic enrichment scenarios."""

    async def test_performance_bulk_enrichment(self):
        """Test that bulk enrichment meets performance requirements."""
        # Create 1000+ players as specified in requirements
        mapper = Mock()
        mapper.get_ffnerd_id = Mock(return_value=123)

        cache = Mock()
        cache.get_player_enrichment = AsyncMock(
            return_value={"projections": {"points": 15}, "rankings": {"overall": 50}}
        )

        enricher = PlayerEnricher(mapper=mapper, cache=cache)

        players = {
            str(i): {
                "player_id": str(i),
                "full_name": f"Player {i}",
                "position": "RB" if i % 2 == 0 else "WR",
            }
            for i in range(1200)
        }

        start_time = time.time()
        enriched = await enricher.enrich_players(players)
        elapsed = time.time() - start_time

        # Requirement: Process 1000+ players in < 1 second
        assert len(enriched) == 1200
        assert elapsed < 1.0

        metrics = enricher.get_metrics()
        assert metrics["total_processed"] == 1200
        assert metrics["successful_enrichments"] == 1200
