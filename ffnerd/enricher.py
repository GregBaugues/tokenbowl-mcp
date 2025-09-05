"""Player data enrichment logic for merging Sleeper and Fantasy Nerds data."""

import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Tuple
from .mapper import PlayerMapper
from .cache import FantasyNerdsCache

logger = logging.getLogger(__name__)


class EnrichmentMetrics:
    """Track metrics for enrichment operations."""

    def __init__(self):
        """Initialize metrics tracking."""
        self.total_processed = 0
        self.successful_enrichments = 0
        self.missing_mappings = 0
        self.failed_enrichments = 0
        self.confidence_scores = []
        self.processing_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.start_time = None

    def record_enrichment(
        self,
        success: bool,
        confidence: float = 0.0,
        time_ms: float = 0.0,
        cache_hit: bool = False,
    ) -> None:
        """
        Record metrics for a single enrichment operation.

        Args:
            success: Whether enrichment was successful
            confidence: Confidence score for the enrichment (0-1)
            time_ms: Processing time in milliseconds
            cache_hit: Whether data came from cache
        """
        self.total_processed += 1

        if success:
            self.successful_enrichments += 1
            self.confidence_scores.append(confidence)
        else:
            self.failed_enrichments += 1

        if time_ms > 0:
            self.processing_times.append(time_ms)

        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_missing_mapping(self) -> None:
        """Record a missing player mapping."""
        self.missing_mappings += 1
        self.total_processed += 1

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of enrichment metrics.

        Returns:
            Dictionary containing metrics summary
        """
        avg_confidence = (
            sum(self.confidence_scores) / len(self.confidence_scores)
            if self.confidence_scores
            else 0.0
        )
        avg_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times
            else 0.0
        )
        success_rate = (
            self.successful_enrichments / self.total_processed
            if self.total_processed > 0
            else 0.0
        )
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0.0
        )

        elapsed_time = None
        if self.start_time:
            elapsed_time = time.time() - self.start_time

        return {
            "total_processed": self.total_processed,
            "successful_enrichments": self.successful_enrichments,
            "failed_enrichments": self.failed_enrichments,
            "missing_mappings": self.missing_mappings,
            "success_rate": round(success_rate * 100, 2),
            "average_confidence": round(avg_confidence, 3),
            "average_time_ms": round(avg_time, 2),
            "cache_hit_rate": round(cache_hit_rate * 100, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "elapsed_time_seconds": round(elapsed_time, 2) if elapsed_time else None,
        }

    def start_tracking(self) -> None:
        """Start tracking elapsed time."""
        self.start_time = time.time()


class PlayerEnricher:
    """Enriches Sleeper player data with Fantasy Nerds information."""

    def __init__(
        self,
        mapper: Optional[PlayerMapper] = None,
        cache: Optional[FantasyNerdsCache] = None,
    ):
        """
        Initialize the player enricher.

        Args:
            mapper: PlayerMapper instance for ID mapping
            cache: FantasyNerdsCache instance for data retrieval
        """
        self.mapper = mapper or PlayerMapper()
        self.cache = cache or FantasyNerdsCache()
        self.metrics = EnrichmentMetrics()

    def calculate_confidence(
        self, player_data: Dict[str, Any], ffnerd_data: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for enrichment quality.

        Args:
            player_data: Original Sleeper player data
            ffnerd_data: Fantasy Nerds enrichment data

        Returns:
            Confidence score between 0 and 1
        """
        if not ffnerd_data:
            return 0.0

        score = 0.0
        weights = {
            "projections": 0.35,
            "injury": 0.20,
            "news": 0.15,
            "rankings": 0.20,
            "ffnerd_id": 0.10,
        }

        # Check for presence and quality of each data type
        for field, weight in weights.items():
            if field in ffnerd_data and ffnerd_data[field]:
                if field == "projections":
                    # Check if projections have actual values
                    proj = ffnerd_data[field]
                    if isinstance(proj, dict) and proj.get("points", 0) > 0:
                        score += weight
                elif field == "news":
                    # Check if news is recent and non-empty
                    news = ffnerd_data[field]
                    if isinstance(news, list) and len(news) > 0:
                        score += weight
                elif field == "rankings":
                    # Check if rankings exist and are valid
                    rankings = ffnerd_data[field]
                    if isinstance(rankings, dict) and rankings.get("overall"):
                        score += weight
                else:
                    # For other fields, just check presence
                    score += weight

        # Adjust confidence based on player importance
        position = player_data.get("position", "").upper()
        if position in ["QB", "RB", "WR", "TE"]:
            # Skill positions should have higher data availability
            score = score * 1.1  # Boost up to 10%
        elif position in ["K", "DEF"]:
            # Kickers and defenses may have less data
            score = score * 1.2  # More lenient scoring

        # Cap at 1.0
        return min(score, 1.0)

    async def enrich_player(
        self, sleeper_player: Dict[str, Any], skip_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Enrich a single Sleeper player with Fantasy Nerds data.

        Args:
            sleeper_player: Original Sleeper player data
            skip_cache: Whether to skip cache and fetch fresh data

        Returns:
            Enriched player data with ffnerd_data field added
        """
        start_time = time.time()

        # Make a copy to avoid modifying original
        enriched_player = sleeper_player.copy()

        # Get Sleeper player ID
        sleeper_id = sleeper_player.get("player_id")
        if not sleeper_id:
            logger.warning("Player missing player_id field")
            self.metrics.record_enrichment(success=False)
            return enriched_player

        # Map to Fantasy Nerds ID
        ffnerd_id = self.mapper.get_ffnerd_id(sleeper_id)
        if not ffnerd_id:
            logger.debug(f"No Fantasy Nerds mapping for Sleeper ID: {sleeper_id}")
            self.metrics.record_missing_mapping()
            return enriched_player

        try:
            # Get enrichment data from cache
            ffnerd_data = await self.cache.get_player_enrichment(
                sleeper_id=sleeper_id, ffnerd_id=ffnerd_id
            )

            cache_hit = ffnerd_data is not None

            if ffnerd_data:
                # Add metadata to enrichment
                ffnerd_data["ffnerd_id"] = ffnerd_id
                ffnerd_data["enriched_at"] = datetime.now(timezone.utc).isoformat()

                # Calculate and add confidence score
                confidence = self.calculate_confidence(sleeper_player, ffnerd_data)
                ffnerd_data["confidence"] = round(confidence, 3)

                # Add enrichment to player data
                enriched_player["ffnerd_data"] = ffnerd_data

                # Record metrics
                elapsed_ms = (time.time() - start_time) * 1000
                self.metrics.record_enrichment(
                    success=True,
                    confidence=confidence,
                    time_ms=elapsed_ms,
                    cache_hit=cache_hit,
                )

                logger.debug(
                    f"Enriched player {sleeper_player.get('full_name', 'Unknown')} "
                    f"(confidence: {confidence:.2f})"
                )
            else:
                # No enrichment data available
                self.metrics.record_enrichment(success=False, cache_hit=False)
                logger.debug(
                    f"No enrichment data for player {sleeper_player.get('full_name', 'Unknown')}"
                )

        except Exception as e:
            logger.error(f"Error enriching player {sleeper_id}: {str(e)}")
            self.metrics.record_enrichment(success=False)

        return enriched_player

    async def enrich_players(
        self, players: Dict[str, Dict[str, Any]], max_concurrent: int = 50
    ) -> Dict[str, Dict[str, Any]]:
        """
        Enrich multiple players efficiently with concurrent operations.

        Args:
            players: Dictionary of player_id -> player data
            max_concurrent: Maximum number of concurrent enrichment operations

        Returns:
            Dictionary of enriched players
        """
        self.metrics.start_tracking()
        logger.info(f"Starting bulk enrichment for {len(players)} players")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_semaphore(
            player_id: str, player_data: Dict
        ) -> Tuple[str, Dict]:
            """Enrich a player with semaphore control."""
            async with semaphore:
                enriched = await self.enrich_player(player_data)
                return player_id, enriched

        # Create tasks for all players
        tasks = [
            enrich_with_semaphore(player_id, player_data)
            for player_id, player_data in players.items()
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        enriched_players = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in bulk enrichment: {result}")
            else:
                player_id, enriched_data = result
                enriched_players[player_id] = enriched_data

        # Log summary
        summary = self.metrics.get_summary()
        logger.info(
            f"Bulk enrichment completed: "
            f"{summary['successful_enrichments']}/{summary['total_processed']} successful "
            f"({summary['success_rate']}% success rate, "
            f"{summary['average_confidence']} avg confidence, "
            f"{summary['elapsed_time_seconds']}s elapsed)"
        )

        return enriched_players

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current enrichment metrics.

        Returns:
            Dictionary containing metrics summary
        """
        return self.metrics.get_summary()

    def reset_metrics(self) -> None:
        """Reset metrics tracking."""
        self.metrics = EnrichmentMetrics()


# Utility functions for data validation and normalization


def validate_enrichment_data(data: Dict[str, Any]) -> bool:
    """
    Validate that enrichment data meets expected schema.

    Args:
        data: Enrichment data to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    # Check for at least one data field
    data_fields = ["projections", "injury", "news", "rankings"]
    has_data = any(field in data for field in data_fields)

    return has_data


def normalize_team_abbreviation(team: str) -> str:
    """
    Normalize team abbreviations between different APIs.

    Args:
        team: Team abbreviation

    Returns:
        Normalized team abbreviation
    """
    team_map = {
        "ARI": "ARZ",
        "ARZ": "ARI",
        "WSH": "WAS",
        "WAS": "WSH",
        "JAX": "JAC",
        "JAC": "JAX",
        "LA": "LAR",
    }

    return team_map.get(team.upper(), team.upper())


def merge_injury_data(
    sleeper_injury: Optional[Dict], ffnerd_injury: Optional[Dict]
) -> Optional[Dict]:
    """
    Merge injury data from both sources, prioritizing Sleeper.

    Args:
        sleeper_injury: Injury data from Sleeper
        ffnerd_injury: Injury data from Fantasy Nerds

    Returns:
        Merged injury data
    """
    if not ffnerd_injury:
        return sleeper_injury

    if not sleeper_injury:
        return ffnerd_injury

    # Sleeper takes priority, but we can add Fantasy Nerds details
    merged = sleeper_injury.copy()

    # Add Fantasy Nerds specific fields if not present
    if "description" in ffnerd_injury and "description" not in merged:
        merged["ffnerd_description"] = ffnerd_injury["description"]

    if "last_update" in ffnerd_injury:
        merged["ffnerd_last_update"] = ffnerd_injury["last_update"]

    return merged
