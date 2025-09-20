#!/usr/bin/env python3

import sys
from anthropic import Anthropic


def extract_trade_players(trade_message: str, api_key: str = None) -> dict:
    """
    Extract player names from a fantasy football trade proposal using Claude.

    Args:
        trade_message: The trade proposal message
        api_key: Anthropic API key (optional, will use ANTHROPIC_API_KEY env var if not provided)

    Returns:
        Dictionary with 'receiving' and 'giving' lists of player names
    """
    client = Anthropic(api_key=api_key)

    prompt = f"""Analyze this fantasy football trade proposal and extract the player names.
Return ONLY a JSON object with two lists:
- "receiving": players being proposed to receive
- "giving": players being proposed to give away

Trade proposal:
{trade_message}

Return JSON only, no other text:"""

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    import json

    result = json.loads(response.content[0].text)
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_trade.py 'trade proposal message'")
        print(
            "Example: python extract_trade.py 'I'll trade you Patrick Mahomes and Travis Kelce for Justin Jefferson and Saquon Barkley'"
        )
        sys.exit(1)

    trade_message = sys.argv[1]

    try:
        result = extract_trade_players(trade_message)
        print(f"Players to receive: {', '.join(result['receiving'])}")
        print(f"Players to give: {', '.join(result['giving'])}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
