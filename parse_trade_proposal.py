#!/usr/bin/env python3
"""
Parse fantasy football trade proposals using Claude SDK.
Extracts lists of players being received and given in a trade.
"""

import argparse
import json
import os
from typing import List, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def parse_trade_proposal(
    client: Anthropic, message: str
) -> Tuple[List[str], List[str]]:
    """
    Parse a trade proposal message using Claude to extract player names.

    Args:
        client: Anthropic client instance
        message: The trade proposal text

    Returns:
        Tuple of (players_to_receive, players_to_give)
    """

    prompt = f"""Extract the player names from the following fantasy football trade proposal.
Return ONLY a JSON object with two arrays:
- "receiving": players being proposed to receive
- "giving": players being proposed to give away

Trade proposal:
{message}

Return only valid JSON with player names as strings."""

    response = client.messages.create(
        model="claude-3.5-sonnet-4.1-20250805",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the text content from the response
    content = response.content[0].text

    try:
        # Parse the JSON response
        result = json.loads(content)
        players_to_receive = result.get("receiving", [])
        players_to_give = result.get("giving", [])

        return players_to_receive, players_to_give
    except json.JSONDecodeError as e:
        print(f"Error parsing Claude's response as JSON: {e}")
        print(f"Response: {content}")
        return [], []


def main():
    parser = argparse.ArgumentParser(
        description="Parse fantasy football trade proposals"
    )
    parser.add_argument("message", help="The trade proposal message to parse")
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
        default=None,
    )

    args = parser.parse_args()

    # Initialize the Anthropic client
    # Will use ANTHROPIC_API_KEY env var if api_key is not provided
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: No API key provided. Set ANTHROPIC_API_KEY environment variable or use --api-key"
        )
        return

    client = Anthropic(api_key=api_key)

    # Parse the trade proposal
    players_to_receive, players_to_give = parse_trade_proposal(client, args.message)

    # Display results
    print("\n=== Trade Proposal Analysis ===")
    print(f"\nPlayers to RECEIVE: {players_to_receive}")
    print(f"Players to GIVE: {players_to_give}")

    # Also output as JSON for programmatic use
    result = {"receiving": players_to_receive, "giving": players_to_give}
    print(f"\nJSON output:\n{json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
