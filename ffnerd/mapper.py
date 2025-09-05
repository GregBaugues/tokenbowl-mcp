"""Player ID mapping between Sleeper and Fantasy Nerds APIs."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class PlayerMapper:
    """Maps between Sleeper and Fantasy Nerds player IDs."""

    # Team abbreviation variations between APIs
    TEAM_ALIASES = {
        "ARI": "ARZ",
        "ARZ": "ARI",
        "WSH": "WAS",
        "WAS": "WSH",
        "JAX": "JAC",
        "JAC": "JAX",
        "LA": "LAR",  # Rams
        "LAR": "LA",
    }

    # Name suffixes to normalize (check longer suffixes first to avoid partial matches)
    NAME_SUFFIXES = ["iii", "iv", "ii", "jr.", "sr.", "jr", "sr"]

    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize player mapper.

        Args:
            mapping_file: Path to JSON file containing player mappings.
        """
        self.mapping_file = Path(mapping_file) if mapping_file else None
        self.sleeper_to_ffnerd: Dict[str, int] = {}
        self.ffnerd_to_sleeper: Dict[int, str] = {}
        self.confidence_scores: Dict[str, float] = {}

        if self.mapping_file and self.mapping_file.exists():
            self.load_mapping()

    def load_mapping(self) -> None:
        """Load mapping from JSON file."""
        if not self.mapping_file or not self.mapping_file.exists():
            logger.warning(f"Mapping file not found: {self.mapping_file}")
            return

        try:
            with open(self.mapping_file, "r") as f:
                data = json.load(f)

            for sleeper_id, mapping_data in data.items():
                ffnerd_id = mapping_data.get("ffnerd_id")
                if ffnerd_id:
                    self.sleeper_to_ffnerd[sleeper_id] = ffnerd_id
                    self.ffnerd_to_sleeper[ffnerd_id] = sleeper_id
                    self.confidence_scores[sleeper_id] = mapping_data.get(
                        "confidence", 1.0
                    )

            logger.info(f"Loaded {len(self.sleeper_to_ffnerd)} player mappings")
        except Exception as e:
            logger.error(f"Failed to load mapping file: {e}")

    def save_mapping(self, output_file: Optional[str] = None) -> None:
        """
        Save mapping to JSON file.

        Args:
            output_file: Path to save mapping file. Uses self.mapping_file if not provided.
        """
        save_path = Path(output_file) if output_file else self.mapping_file
        if not save_path:
            raise ValueError("No output file specified")

        mapping_data = {}
        for sleeper_id, ffnerd_id in self.sleeper_to_ffnerd.items():
            mapping_data[sleeper_id] = {
                "ffnerd_id": ffnerd_id,
                "confidence": self.confidence_scores.get(sleeper_id, 0.0),
            }

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(mapping_data, f, indent=2)

        logger.info(f"Saved {len(mapping_data)} mappings to {save_path}")

    def normalize_name(self, name: str) -> str:
        """
        Normalize player name for matching.

        Args:
            name: Player name to normalize.

        Returns:
            Normalized name string.
        """
        if not name:
            return ""

        # Convert to lowercase
        normalized = name.lower()

        # Remove suffixes
        for suffix in self.NAME_SUFFIXES:
            normalized = normalized.replace(suffix.lower(), "")

        # Remove special characters and extra spaces
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

    def normalize_team(self, team: str) -> str:
        """
        Normalize team abbreviation.

        Args:
            team: Team abbreviation.

        Returns:
            Normalized team abbreviation.
        """
        if not team:
            return ""
        team = team.upper()
        return self.TEAM_ALIASES.get(team, team)

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity score between 0 and 1.
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def match_player(
        self, sleeper_player: Dict[str, Any], ffnerd_player: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """
        Check if two players match and return confidence score.

        Args:
            sleeper_player: Sleeper player data.
            ffnerd_player: Fantasy Nerds player data.

        Returns:
            Tuple of (is_match, confidence_score).
        """
        # Extract player data
        sleeper_name = self.normalize_name(
            sleeper_player.get("full_name", "")
            or f"{sleeper_player.get('first_name', '')} {sleeper_player.get('last_name', '')}"
        )
        ffnerd_name = self.normalize_name(ffnerd_player.get("name", ""))

        sleeper_team = self.normalize_team(sleeper_player.get("team", ""))
        ffnerd_team = self.normalize_team(ffnerd_player.get("team", ""))

        sleeper_pos = (sleeper_player.get("position") or "").upper()
        ffnerd_pos = (ffnerd_player.get("position") or "").upper()

        # Calculate name similarity
        name_similarity = self.calculate_similarity(sleeper_name, ffnerd_name)

        # Exact match (name + team + position)
        if (
            name_similarity >= 0.95
            and sleeper_team == ffnerd_team
            and sleeper_pos == ffnerd_pos
        ):
            return True, 1.0

        # Very high name similarity with matching position
        if name_similarity >= 0.9 and sleeper_pos == ffnerd_pos:
            # Check if team matches or if one is empty (free agent)
            if sleeper_team == ffnerd_team or not sleeper_team or not ffnerd_team:
                return True, 0.95

        # High name similarity with fuzzy team matching
        if name_similarity >= 0.85 and sleeper_pos == ffnerd_pos:
            # Allow for team changes or aliases
            if sleeper_team == ffnerd_team or not sleeper_team or not ffnerd_team:
                return True, 0.85
            # Check team aliases
            if self.normalize_team(sleeper_team) == self.normalize_team(ffnerd_team):
                return True, 0.85

        # Defense/Special Teams matching
        if sleeper_pos == "DEF" and ffnerd_pos in ["DEF", "DST"]:
            # For defenses, match on team name
            if sleeper_team == ffnerd_team:
                return True, 1.0

        return False, 0.0

    async def build_mapping(
        self, sleeper_players: Dict[str, Any], ffnerd_players: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build mapping between Sleeper and Fantasy Nerds players.

        Args:
            sleeper_players: Dictionary of Sleeper players (player_id -> player data).
            ffnerd_players: List of Fantasy Nerds players.

        Returns:
            Dictionary containing mapping statistics.
        """
        mapped_count = 0
        unmapped_sleeper = []
        unmapped_ffnerd = list(ffnerd_players)
        confidence_distribution = {"1.0": 0, "0.95": 0, "0.85": 0}

        # Create Fantasy Nerds lookup by normalized name for efficiency
        ffnerd_by_name = {}
        for ffn_player in ffnerd_players:
            name = self.normalize_name(ffn_player.get("name", ""))
            if name:
                if name not in ffnerd_by_name:
                    ffnerd_by_name[name] = []
                ffnerd_by_name[name].append(ffn_player)

        # Match each Sleeper player
        for sleeper_id, sleeper_player in sleeper_players.items():
            # Skip inactive players
            if sleeper_player.get("status") not in ["Active", "Injured Reserve"]:
                continue

            best_match = None
            best_confidence = 0.0

            # Try to find matching Fantasy Nerds player
            sleeper_name = self.normalize_name(
                sleeper_player.get("full_name", "")
                or f"{sleeper_player.get('first_name', '')} {sleeper_player.get('last_name', '')}"
            )

            # First try exact name matches
            potential_matches = ffnerd_by_name.get(sleeper_name, [])

            # Then try all players if no exact name match
            if not potential_matches:
                potential_matches = ffnerd_players

            for ffn_player in potential_matches:
                is_match, confidence = self.match_player(sleeper_player, ffn_player)
                if is_match and confidence > best_confidence:
                    best_match = ffn_player
                    best_confidence = confidence
                    if confidence == 1.0:
                        break  # Perfect match found

            if best_match:
                ffnerd_id = best_match.get("playerId")
                if ffnerd_id:
                    self.sleeper_to_ffnerd[sleeper_id] = ffnerd_id
                    self.ffnerd_to_sleeper[ffnerd_id] = sleeper_id
                    self.confidence_scores[sleeper_id] = best_confidence

                    mapped_count += 1

                    # Track confidence distribution
                    if best_confidence == 1.0:
                        confidence_distribution["1.0"] += 1
                    elif best_confidence >= 0.95:
                        confidence_distribution["0.95"] += 1
                    else:
                        confidence_distribution["0.85"] += 1

                    # Remove from unmapped list
                    if best_match in unmapped_ffnerd:
                        unmapped_ffnerd.remove(best_match)
            else:
                unmapped_sleeper.append(
                    {
                        "id": sleeper_id,
                        "name": sleeper_player.get("full_name", ""),
                        "team": sleeper_player.get("team", ""),
                        "position": sleeper_player.get("position", ""),
                    }
                )

        # Generate statistics
        active_sleeper_count = sum(
            1
            for p in sleeper_players.values()
            if p.get("status") in ["Active", "Injured Reserve"]
        )

        return {
            "total_sleeper_players": len(sleeper_players),
            "active_sleeper_players": active_sleeper_count,
            "total_ffnerd_players": len(ffnerd_players),
            "mapped_count": mapped_count,
            "mapping_rate": mapped_count / active_sleeper_count
            if active_sleeper_count > 0
            else 0,
            "confidence_distribution": confidence_distribution,
            "unmapped_sleeper_count": len(unmapped_sleeper),
            "unmapped_ffnerd_count": len(unmapped_ffnerd),
            "sample_unmapped_sleeper": unmapped_sleeper[:10],  # First 10 unmapped
        }

    def get_ffnerd_id(self, sleeper_id: str) -> Optional[int]:
        """
        Get Fantasy Nerds ID for a Sleeper player.

        Args:
            sleeper_id: Sleeper player ID.

        Returns:
            Fantasy Nerds player ID or None if not mapped.
        """
        return self.sleeper_to_ffnerd.get(sleeper_id)

    def get_sleeper_id(self, ffnerd_id: int) -> Optional[str]:
        """
        Get Sleeper ID for a Fantasy Nerds player.

        Args:
            ffnerd_id: Fantasy Nerds player ID.

        Returns:
            Sleeper player ID or None if not mapped.
        """
        return self.ffnerd_to_sleeper.get(ffnerd_id)

    def get_confidence(self, sleeper_id: str) -> float:
        """
        Get confidence score for a player mapping.

        Args:
            sleeper_id: Sleeper player ID.

        Returns:
            Confidence score between 0 and 1.
        """
        return self.confidence_scores.get(sleeper_id, 0.0)

    def add_manual_mapping(
        self, sleeper_id: str, ffnerd_id: int, confidence: float = 1.0
    ) -> None:
        """
        Add manual player mapping override.

        Args:
            sleeper_id: Sleeper player ID.
            ffnerd_id: Fantasy Nerds player ID.
            confidence: Confidence score for mapping.
        """
        self.sleeper_to_ffnerd[sleeper_id] = ffnerd_id
        self.ffnerd_to_sleeper[ffnerd_id] = sleeper_id
        self.confidence_scores[sleeper_id] = confidence
        logger.info(
            f"Added manual mapping: {sleeper_id} -> {ffnerd_id} (confidence: {confidence})"
        )
