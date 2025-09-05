#!/usr/bin/env python
"""Script to build player ID mapping between Sleeper and Fantasy Nerds APIs."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ffnerd.client import FantasyNerdsClient
from ffnerd.mapper import PlayerMapper
from players_cache_redis import get_all_players

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_sleeper_players() -> Dict[str, Any]:
    """
    Fetch all Sleeper players from cache or API.

    Returns:
        Dictionary of Sleeper players.
    """
    try:
        logger.info("Fetching Sleeper players from cache...")
        players = await get_all_players()
        logger.info(f"Retrieved {len(players)} Sleeper players")
        return players
    except Exception as e:
        logger.error(f"Failed to fetch Sleeper players: {e}")
        # Fallback to direct API call if cache fails
        import httpx

        logger.info("Attempting direct API call to Sleeper...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.sleeper.app/v1/players/nfl")
            response.raise_for_status()
            players = response.json()
            logger.info(f"Retrieved {len(players)} players from Sleeper API")
            return players


async def fetch_ffnerd_players(client: FantasyNerdsClient) -> list:
    """
    Fetch all Fantasy Nerds players.

    Args:
        client: Fantasy Nerds API client.

    Returns:
        List of Fantasy Nerds players.
    """
    try:
        logger.info("Fetching Fantasy Nerds players...")
        players = await client.get_players(include_inactive=False)
        logger.info(f"Retrieved {len(players)} Fantasy Nerds players")
        return players
    except Exception as e:
        logger.error(f"Failed to fetch Fantasy Nerds players: {e}")
        raise


async def generate_mapping_report(stats: Dict[str, Any], output_dir: Path) -> None:
    """
    Generate a detailed mapping report.

    Args:
        stats: Mapping statistics from PlayerMapper.
        output_dir: Directory to save report.
    """
    report_file = output_dir / "mapping_report.txt"

    report_lines = [
        "=" * 60,
        "Player ID Mapping Report",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 60,
        "",
        "SUMMARY STATISTICS",
        "-" * 40,
        f"Total Sleeper Players: {stats['total_sleeper_players']}",
        f"Active Sleeper Players: {stats['active_sleeper_players']}",
        f"Total Fantasy Nerds Players: {stats['total_ffnerd_players']}",
        f"Successfully Mapped: {stats['mapped_count']}",
        f"Mapping Rate: {stats['mapping_rate']:.2%}",
        "",
        "CONFIDENCE DISTRIBUTION",
        "-" * 40,
        f"Perfect Matches (1.0): {stats['confidence_distribution']['1.0']}",
        f"High Confidence (0.95): {stats['confidence_distribution']['0.95']}",
        f"Good Confidence (0.85): {stats['confidence_distribution']['0.85']}",
        "",
        "UNMAPPED PLAYERS",
        "-" * 40,
        f"Unmapped Sleeper Players: {stats['unmapped_sleeper_count']}",
        f"Unmapped Fantasy Nerds Players: {stats['unmapped_ffnerd_count']}",
        "",
    ]

    if stats.get("sample_unmapped_sleeper"):
        report_lines.extend(["Sample Unmapped Sleeper Players (Top 10):", "-" * 40])
        for player in stats["sample_unmapped_sleeper"]:
            report_lines.append(
                f"  - {player['name']} ({player['position']}, {player['team']})"
            )

    report_lines.extend(["", "=" * 60])

    report_content = "\n".join(report_lines)

    with open(report_file, "w") as f:
        f.write(report_content)

    logger.info(f"Report saved to {report_file}")
    print("\n" + report_content)


async def export_unmapped_for_review(stats: Dict[str, Any], output_dir: Path) -> None:
    """
    Export unmapped players to CSV for manual review.

    Args:
        stats: Mapping statistics containing unmapped players.
        output_dir: Directory to save CSV file.
    """
    if not stats.get("sample_unmapped_sleeper"):
        return

    csv_file = output_dir / "unmapped_players.csv"

    # Simple CSV format for easy review
    csv_lines = ["Sleeper ID,Name,Position,Team"]
    for player in stats.get("sample_unmapped_sleeper", []):
        csv_lines.append(
            f"{player['id']},{player['name']},{player['position']},{player['team']}"
        )

    with open(csv_file, "w") as f:
        f.write("\n".join(csv_lines))

    logger.info(f"Unmapped players exported to {csv_file}")


async def main():
    """Main function to build player mapping."""
    # Check for API key
    if not os.getenv("FFNERD_API_KEY"):
        logger.error(
            "FFNERD_API_KEY environment variable not set. "
            "Please set it in your .env file or environment."
        )
        sys.exit(1)

    # Setup output directory
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    mapping_file = output_dir / "player_mapping.json"

    try:
        # Initialize Fantasy Nerds client
        ffnerd_client = FantasyNerdsClient()

        # Test connection
        logger.info("Testing Fantasy Nerds API connection...")
        if not await ffnerd_client.test_connection():
            logger.error("Failed to connect to Fantasy Nerds API")
            sys.exit(1)
        logger.info("Connection successful!")

        # Fetch players from both APIs
        sleeper_players = await fetch_sleeper_players()
        ffnerd_players = await fetch_ffnerd_players(ffnerd_client)

        # Initialize mapper and build mappings
        logger.info("Building player mappings...")
        mapper = PlayerMapper()
        stats = await mapper.build_mapping(sleeper_players, ffnerd_players)

        # Save mapping to file
        logger.info(f"Saving mappings to {mapping_file}...")
        mapper.save_mapping(str(mapping_file))

        # Generate report
        await generate_mapping_report(stats, output_dir)

        # Export unmapped players for review
        await export_unmapped_for_review(stats, output_dir)

        # Success summary
        logger.info("=" * 60)
        logger.info("MAPPING GENERATION COMPLETE!")
        logger.info(f"Mapping file: {mapping_file}")
        logger.info(
            f"Mapped {stats['mapped_count']} of {stats['active_sleeper_players']} active players"
        )
        logger.info(f"Success rate: {stats['mapping_rate']:.2%}")
        logger.info("=" * 60)

        # Exit with appropriate code
        if stats["mapping_rate"] < 0.9:
            logger.warning(
                "Mapping rate below 90%. Manual review recommended for unmapped players."
            )
            sys.exit(2)  # Warning exit code
        else:
            logger.info("Mapping rate meets target (>90%). Success!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Failed to generate mapping: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
