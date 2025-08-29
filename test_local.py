#!/usr/bin/env python3
"""Local testing script for the composed MCP server"""

import asyncio
import os
import sys
from main_mcp import main_mcp
from sleeper_mcp import mcp as sleeper_server
from ffnerds_mcp import mcp as ffnerds_server


async def test_composition():
    """Test that servers compose correctly"""
    print("=" * 60)
    print("Testing Server Composition")
    print("=" * 60)
    
    # Import servers
    await main_mcp.import_server(sleeper_server)
    await main_mcp.import_server(ffnerds_server, prefix="ffnerds")
    
    # Get all tools
    tools = await main_mcp.get_tools()
    
    print(f"✓ Total tools available: {len(tools)}")
    
    # Count by category
    sleeper_tools = [t for t in tools if not t.startswith('ffnerds')]
    ffnerds_tools = [t for t in tools if t.startswith('ffnerds')]
    
    print(f"✓ Sleeper tools: {len(sleeper_tools)}")
    print(f"✓ Fantasy Nerds tools: {len(ffnerds_tools)}")
    
    return tools


async def test_sleeper_tools(tools):
    """Test a few Sleeper API tools"""
    print("\n" + "=" * 60)
    print("Testing Sleeper API Tools")
    print("=" * 60)
    
    # Test get_league_info
    try:
        print("\n1. Testing get_league_info...")
        # Call the tool directly through the composed server
        from sleeper_mcp import get_league_info
        result = await get_league_info()
        if result and 'name' in result:
            print(f"   ✓ League: {result['name']}")
            print(f"   ✓ Season: {result.get('season', 'N/A')}")
        else:
            print("   ✓ Tool executed (no league data)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test get_players_cache_status
    try:
        print("\n2. Testing get_players_cache_status...")
        from sleeper_mcp import get_players_cache_status
        result = await get_players_cache_status()
        if result:
            if 'error' in result:
                print(f"   ✓ Cache not available: {result['error']}")
            else:
                print(f"   ✓ Cache status retrieved")
                if 'last_updated' in result:
                    print(f"   ✓ Last updated: {result['last_updated']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")


async def test_ffnerds_tools(tools):
    """Test Fantasy Nerds API tools"""
    print("\n" + "=" * 60)
    print("Testing Fantasy Nerds API Tools")
    print("=" * 60)
    
    if not os.getenv("FANTASY_NERDS_API_KEY"):
        print("⚠️  FANTASY_NERDS_API_KEY not set - tools will return error")
        print("   Set it with: export FANTASY_NERDS_API_KEY='your_key_here'")
    
    # Test get_bye_weeks (doesn't require parameters)
    try:
        print("\n1. Testing ffnerds_get_bye_weeks...")
        from ffnerds_mcp import get_bye_weeks
        result = await get_bye_weeks()
        if 'error' in result:
            print(f"   ✓ Expected error (no API key): {result['error']}")
        else:
            print(f"   ✓ Bye weeks data retrieved")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test get_nfl_teams
    try:
        print("\n2. Testing ffnerds_get_nfl_teams...")
        from ffnerds_mcp import get_nfl_teams
        result = await get_nfl_teams()
        if 'error' in result:
            print(f"   ✓ Expected error (no API key): {result['error']}")
        else:
            print(f"   ✓ NFL teams data retrieved")
    except Exception as e:
        print(f"   ✗ Error: {e}")


async def list_all_tools():
    """List all available tools"""
    print("\n" + "=" * 60)
    print("All Available Tools")
    print("=" * 60)
    
    tools = await main_mcp.get_tools()
    
    print("\nSleeper Tools:")
    print("-" * 40)
    sleeper_tools = sorted([t for t in tools if not t.startswith('ffnerds')])
    for i, tool in enumerate(sleeper_tools, 1):
        print(f"  {i:2}. {tool}")
    
    print("\nFantasy Nerds Tools:")
    print("-" * 40)
    ffnerds_tools = sorted([t for t in tools if t.startswith('ffnerds')])
    for i, tool in enumerate(ffnerds_tools, 1):
        print(f"  {i:2}. {tool}")


async def main():
    """Run all tests"""
    print("\n🚀 Testing Composed MCP Server Locally\n")
    
    # Test composition
    tools = await test_composition()
    
    # Test Sleeper tools
    await test_sleeper_tools(tools)
    
    # Test Fantasy Nerds tools
    await test_ffnerds_tools(tools)
    
    # List all tools
    if "--list" in sys.argv:
        await list_all_tools()
    else:
        print("\n💡 Tip: Run with --list flag to see all available tools")
    
    print("\n✅ Local testing complete!")
    print("\nTo test the HTTP server:")
    print("  1. Set API key: export FANTASY_NERDS_API_KEY='your_key'")
    print("  2. Run server:  uv run python main_mcp.py http 8000")
    print("  3. Test at:     http://localhost:8000/sse")


if __name__ == "__main__":
    asyncio.run(main())