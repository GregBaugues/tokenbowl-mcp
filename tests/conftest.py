import pytest
import vcr
from pathlib import Path
import fakeredis.aioredis as fakeredis
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure VCR
vcr_config = vcr.VCR(
    serializer="yaml",
    cassette_library_dir=str(Path(__file__).parent / "cassettes"),
    record_mode="once",  # 'once' for initial recording, 'none' for replay only
    match_on=["uri", "method"],
    filter_headers=["authorization"],
)


@pytest.fixture
def vcr_cassette():
    """Fixture to use VCR with custom configuration."""
    return vcr_config


@pytest.fixture
async def mock_redis():
    """Mock Redis client using fakeredis."""
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    yield redis_client
    await redis_client.close()


@pytest.fixture
def mock_mcp_server():
    """Mock FastMCP server for testing tools."""
    from fastmcp import FastMCP

    # Create a test MCP server
    mcp = FastMCP("sleeper-test")
    return mcp


@pytest.fixture
def league_id():
    """Test league ID."""
    return "1266471057523490816"


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "123456789"


@pytest.fixture
def test_draft_id():
    """Test draft ID."""
    return "987654321"
