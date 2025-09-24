#!/usr/bin/env python3
"""
Extract trade proposal details from a text string using Claude API.
Returns lists of player Sleeper IDs to give and get, validated against team rosters.
"""

import os
import json
import asyncio
from typing import Dict, Tuple, Optional
import anthropic
import httpx
from dotenv import load_dotenv

load_dotenv()

SLEEPER_API_BASE = "https://api.sleeper.app/v1"
LEAGUE_ID = os.getenv("SLEEPER_LEAGUE_ID", "1266471057523490816")


class TradeProposalExtractor:
    def __init__(self, roster_id: int):
        """Initialize with the roster ID making the trade."""
        self.roster_id = roster_id
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.league_rosters = {}
        self.players_cache = {}

    async def __aenter__(self):
        await self.load_league_data()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    async def load_league_data(self):
        """Load all league rosters and player data."""
        # Get all rosters
        rosters_response = await self.http_client.get(
            f"{SLEEPER_API_BASE}/league/{LEAGUE_ID}/rosters"
        )
        rosters_response.raise_for_status()
        rosters = rosters_response.json()

        # Map roster_id to player lists
        for roster in rosters:
            self.league_rosters[roster["roster_id"]] = roster.get("players", [])

        # Load players cache from Redis or API
        try:
            from players_cache_redis import get_players_from_cache

            self.players_cache = await asyncio.to_thread(get_players_from_cache)
        except Exception as e:
            print(f"Warning: Could not load players cache: {e}")
            # Fallback to API
            players_response = await self.http_client.get(
                f"{SLEEPER_API_BASE}/players/nfl"
            )
            players_response.raise_for_status()
            self.players_cache = players_response.json()

    def parse_trade_with_claude(self, trade_text: str) -> Dict:
        """Use Claude to extract player names and trade structure from text."""
        prompt = f"""Extract the trade proposal details from this text.

Trade text: "{trade_text}"

Identify:
1. Which players are being GIVEN (sent away from roster {self.roster_id})
2. Which players are being RECEIVED (coming to roster {self.roster_id})

Return a JSON object with this exact structure:
{{
    "players_to_give": ["Player Name 1", "Player Name 2"],
    "players_to_get": ["Player Name 3", "Player Name 4"],
    "other_roster_id": null
}}

Notes:
- Use full player names as they appear in the text
- If a specific roster/team is mentioned for the trade partner, try to identify their roster ID (1-10)
- Common phrases: "I give", "I send", "I trade away" = players_to_give
- Common phrases: "I get", "I receive", "for" = players_to_get
"""

        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response
        content = response.content[0].text
        try:
            # Try to parse JSON directly
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content and "}" in content:
                # Find JSON object in response
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
            else:
                raise ValueError("No JSON found in response")

            return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            print(f"Response: {content}")
            raise

    def find_player_by_name(self, name: str) -> Optional[Tuple[str, Dict]]:
        """Find player ID and data by name."""
        name_lower = name.lower().strip()

        # Try exact match first
        for player_id, player_data in self.players_cache.items():
            if not player_data:
                continue

            full_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".lower().strip()
            if full_name == name_lower:
                return player_id, player_data

        # Try last name match
        for player_id, player_data in self.players_cache.items():
            if not player_data:
                continue

            last_name = player_data.get("last_name", "").lower().strip()
            if last_name and last_name in name_lower:
                return player_id, player_data

        # Try fuzzy match on full name
        for player_id, player_data in self.players_cache.items():
            if not player_data:
                continue

            full_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".lower().strip()
            if name_lower in full_name or full_name in name_lower:
                return player_id, player_data

        return None

    def validate_player_on_roster(self, player_id: str, roster_id: int) -> bool:
        """Check if a player is on a specific roster."""
        roster_players = self.league_rosters.get(roster_id, [])
        return player_id in roster_players

    async def extract_trade_proposal(self, trade_text: str) -> Dict:
        """
        Main method to extract and validate trade proposal.

        Returns:
            Dictionary with:
            - players_to_give: List of (sleeper_id, player_name, team, position)
            - players_to_get: List of (sleeper_id, player_name, team, position)
            - validation_errors: List of any validation issues
        """
        # Parse with Claude
        parsed_trade = self.parse_trade_with_claude(trade_text)

        result = {"players_to_give": [], "players_to_get": [], "validation_errors": []}

        # Process players to give
        for player_name in parsed_trade.get("players_to_give", []):
            player_info = self.find_player_by_name(player_name)
            if not player_info:
                result["validation_errors"].append(
                    f"Could not find player: {player_name}"
                )
                continue

            player_id, player_data = player_info

            # Validate player is on our roster
            if not self.validate_player_on_roster(player_id, self.roster_id):
                result["validation_errors"].append(
                    f"{player_name} (ID: {player_id}) is not on roster {self.roster_id}"
                )
                continue

            result["players_to_give"].append(
                {
                    "sleeper_id": player_id,
                    "name": f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                    "team": player_data.get("team", "FA"),
                    "position": player_data.get("position", ""),
                }
            )

        # Process players to get
        other_roster_id = parsed_trade.get("other_roster_id")

        for player_name in parsed_trade.get("players_to_get", []):
            player_info = self.find_player_by_name(player_name)
            if not player_info:
                result["validation_errors"].append(
                    f"Could not find player: {player_name}"
                )
                continue

            player_id, player_data = player_info

            # Try to find which roster has this player if not specified
            if not other_roster_id:
                for roster_id, players in self.league_rosters.items():
                    if roster_id != self.roster_id and player_id in players:
                        other_roster_id = roster_id
                        break

            # Validate player is on the other roster
            if other_roster_id:
                if not self.validate_player_on_roster(player_id, other_roster_id):
                    result["validation_errors"].append(
                        f"{player_name} (ID: {player_id}) is not on roster {other_roster_id}"
                    )
            else:
                # Check if player is on any roster
                on_roster = None
                for roster_id, players in self.league_rosters.items():
                    if player_id in players:
                        on_roster = roster_id
                        break

                if not on_roster:
                    result["validation_errors"].append(
                        f"{player_name} (ID: {player_id}) is not on any roster (free agent?)"
                    )
                elif on_roster == self.roster_id:
                    result["validation_errors"].append(
                        f"{player_name} (ID: {player_id}) is already on your roster {self.roster_id}"
                    )

            result["players_to_get"].append(
                {
                    "sleeper_id": player_id,
                    "name": f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                    "team": player_data.get("team", "FA"),
                    "position": player_data.get("position", ""),
                    "current_roster": other_roster_id or on_roster,
                }
            )

        result["trade_partner_roster_id"] = other_roster_id

        return result


async def main():
    """Example usage of the trade extractor."""

    # Example trade proposals
    example_trades = [
        "I want to trade away Justin Jefferson and James Cook for CeeDee Lamb and Breece Hall",
        "Give: Tyreek Hill, Get: Garrett Wilson and Calvin Ridley",
        "I'll send you Patrick Mahomes for Josh Allen",
    ]

    # Use roster ID 2 (Bill Beliclaude) as example
    my_roster_id = 2

    async with TradeProposalExtractor(my_roster_id) as extractor:
        print(f"Extracting trades for Roster ID: {my_roster_id}\n")
        print("=" * 60)

        for trade_text in example_trades:
            print(f'\nTrade Proposal: "{trade_text}"')
            print("-" * 40)

            try:
                result = await extractor.extract_trade_proposal(trade_text)

                print("\n📤 Players to GIVE:")
                for player in result["players_to_give"]:
                    print(
                        f"  - {player['name']} ({player['position']}, {player['team']}) - ID: {player['sleeper_id']}"
                    )

                print("\n📥 Players to GET:")
                for player in result["players_to_get"]:
                    roster_info = (
                        f" (from roster {player.get('current_roster')})"
                        if player.get("current_roster")
                        else ""
                    )
                    print(
                        f"  - {player['name']} ({player['position']}, {player['team']}) - ID: {player['sleeper_id']}{roster_info}"
                    )

                if result.get("trade_partner_roster_id"):
                    print(
                        f"\n🤝 Trade Partner: Roster {result['trade_partner_roster_id']}"
                    )

                if result["validation_errors"]:
                    print("\n⚠️  Validation Errors:")
                    for error in result["validation_errors"]:
                        print(f"  - {error}")
                else:
                    print("\n✅ All players validated successfully!")

            except Exception as e:
                print(f"❌ Error processing trade: {e}")

            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
