#!/usr/bin/env python
import asyncio
import httpx
import json

LEAGUE_ID = "1266471057523490816"
BASE_URL = "https://api.sleeper.app/v1"


async def fetch_data():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get league info
        league_resp = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}")
        league_info = league_resp.json()

        # Get Week 3 matchups
        matchups_resp = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/matchups/3")
        matchups = matchups_resp.json()

        # Get rosters
        rosters_resp = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/rosters")
        rosters = rosters_resp.json()

        # Get users
        users_resp = await client.get(f"{BASE_URL}/league/{LEAGUE_ID}/users")
        users = users_resp.json()

        # Get transactions for Week 3
        transactions_resp = await client.get(
            f"{BASE_URL}/league/{LEAGUE_ID}/transactions/3"
        )
        transactions = transactions_resp.json()

        # Get trending players
        trending_resp = await client.get(f"{BASE_URL}/players/nfl/trending/add")
        trending = trending_resp.json()

        return {
            "league": league_info,
            "matchups": matchups,
            "rosters": rosters,
            "users": users,
            "transactions": transactions,
            "trending": trending,
        }


async def main():
    data = await fetch_data()

    print(f"Week: {data['league'].get('current_matchup_week', 3)}")
    print(f"Season: {data['league']['season']}")
    print(f"League: {data['league']['name']}")

    # Process matchups
    matchup_groups = {}
    for team in data["matchups"]:
        matchup_id = team["matchup_id"]
        if matchup_id not in matchup_groups:
            matchup_groups[matchup_id] = []
        matchup_groups[matchup_id].append(team)

    print(f"\nFound {len(matchup_groups)} matchups")

    # Map roster_id to user/team names
    roster_to_user = {}
    for roster in data["rosters"]:
        roster_id = roster["roster_id"]
        owner_id = roster["owner_id"]

        # Find user
        for user in data["users"]:
            if user["user_id"] == owner_id:
                roster_to_user[roster_id] = {
                    "display_name": user.get("display_name", "Unknown"),
                    "team_name": user.get("metadata", {}).get(
                        "team_name", user.get("display_name", "Unknown")
                    ),
                    "wins": roster.get("settings", {}).get("wins", 0),
                    "losses": roster.get("settings", {}).get("losses", 0),
                }
                break

    print("\nMatchups Summary:")
    for matchup_id, teams in matchup_groups.items():
        if len(teams) == 2:
            team1, team2 = teams
            user1 = roster_to_user.get(team1["roster_id"], {})
            user2 = roster_to_user.get(team2["roster_id"], {})

            print(f"\nMatchup {matchup_id}:")
            print(f"  {user1.get('team_name', 'Unknown')} ({team1['points']:.2f})")
            print("  vs")
            print(f"  {user2.get('team_name', 'Unknown')} ({team2['points']:.2f})")
            print(
                f"  Winner: {'Team 1' if team1['points'] > team2['points'] else 'Team 2'} by {abs(team1['points'] - team2['points']):.2f}"
            )

    # Save full data for reference
    with open("week3_data.json", "w") as f:
        json.dump(data, f, indent=2)

    print("\nFull data saved to week3_data.json")
    print(f"Trending players count: {len(data['trending'])}")
    print(f"Transactions count: {len(data['transactions'])}")


if __name__ == "__main__":
    asyncio.run(main())
