#!/usr/bin/env python3
"""
Example usage of the trade proposal parser.
"""

import os
from parse_trade_proposal import parse_trade_proposal
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def main():
    # Example trade proposals
    examples = [
        "I'll give you Tyreek Hill and Travis Etienne for your Justin Jefferson and Breece Hall",
        "Trade offer: You get CeeDee Lamb and Joe Mixon. I get Davante Adams, Saquon Barkley, and George Pickens",
        "Hey, would you take my Josh Allen and AJ Brown for your Jalen Hurts, Amon-Ra St. Brown, and Calvin Ridley?",
        "I want to trade Chris Olave and James Conner to you for Stefon Diggs",
    ]

    # Initialize the Anthropic client
    # Make sure ANTHROPIC_API_KEY is set in your environment
    client = Anthropic()

    print("=== Fantasy Football Trade Proposal Parser ===\n")

    for i, trade_message in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Trade proposal: {trade_message}")
        print("-" * 50)

        players_to_receive, players_to_give = parse_trade_proposal(
            client, trade_message
        )

        print(f"Players to RECEIVE: {players_to_receive}")
        print(f"Players to GIVE: {players_to_give}")
        print("=" * 70)


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        exit(1)

    main()
