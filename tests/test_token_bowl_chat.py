"""Test Token Bowl Chat MCP tools with mocked API responses."""

import pytest
from unittest.mock import patch, AsyncMock
import sleeper_mcp


class TestMessagingTools:
    """Test Token Bowl Chat messaging tools."""

    @pytest.mark.asyncio
    async def test_send_message_to_room(self):
        """Test sending a message to the chat room."""
        mock_response = {
            "id": "msg123",
            "from_username": "testuser",
            "to_username": None,
            "content": "Hello chat!",
            "timestamp": "2025-10-21T10:00:00Z",
            "message_type": "room",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.send_message.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_send_message.fn(
                content="Hello chat!"
            )

            assert result["id"] == "msg123"
            assert result["content"] == "Hello chat!"
            assert result["message_type"] == "room"
            mock_client.send_message.assert_called_once_with(
                content="Hello chat!", to_username=None
            )

    @pytest.mark.asyncio
    async def test_send_direct_message(self):
        """Test sending a direct message to a user."""
        mock_response = {
            "id": "msg456",
            "from_username": "testuser",
            "to_username": "recipient",
            "content": "Private message",
            "timestamp": "2025-10-21T10:00:00Z",
            "message_type": "direct",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.send_message.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_send_message.fn(
                content="Private message", to_username="recipient"
            )

            assert result["id"] == "msg456"
            assert result["to_username"] == "recipient"
            assert result["message_type"] == "direct"
            mock_client.send_message.assert_called_once_with(
                content="Private message", to_username="recipient"
            )

    @pytest.mark.asyncio
    async def test_get_messages(self):
        """Test retrieving chat room messages."""
        mock_response = {
            "messages": [
                {
                    "id": "msg1",
                    "from_username": "user1",
                    "content": "Message 1",
                    "timestamp": "2025-10-21T10:00:00Z",
                }
            ],
            "pagination": {"total": 1},
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_messages.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_messages.fn(limit=10)

            assert "messages" in result
            assert len(result["messages"]) == 1
            assert result["messages"][0]["id"] == "msg1"
            mock_client.get_messages.assert_called_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_get_direct_messages(self):
        """Test retrieving direct messages."""
        mock_response = {
            "messages": [
                {
                    "id": "dm1",
                    "from_username": "sender",
                    "to_username": "receiver",
                    "content": "DM 1",
                    "timestamp": "2025-10-21T10:00:00Z",
                }
            ],
            "pagination": {"total": 1},
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_direct_messages.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_direct_messages.fn(limit=20)

            assert "messages" in result
            assert len(result["messages"]) == 1
            assert result["messages"][0]["id"] == "dm1"
            mock_client.get_direct_messages.assert_called_once_with(limit=20)


class TestUserManagementTools:
    """Test Token Bowl Chat user management tools."""

    @pytest.mark.asyncio
    async def test_get_my_profile(self):
        """Test getting own profile."""
        mock_response = {
            "username": "testuser",
            "email": "test@example.com",
            "api_key": "key123",
            "webhook_url": "https://example.com/webhook",
            "logo": "logo1.png",
            "emoji": "🏈",
            "bot": False,
            "admin": True,
            "viewer": False,
            "created_at": "2025-10-01T00:00:00Z",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_my_profile.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_my_profile.fn()

            assert result["username"] == "testuser"
            assert result["email"] == "test@example.com"
            assert result["admin"] is True

    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """Test getting another user's public profile."""
        mock_response = {
            "username": "otheruser",
            "logo": "logo2.png",
            "emoji": "🎯",
            "bot": False,
            "viewer": False,
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_user_profile.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_user_profile.fn(
                username="otheruser"
            )

            assert result["username"] == "otheruser"
            assert "email" not in result  # Public profile doesn't have email
            mock_client.get_user_profile.assert_called_once_with(username="otheruser")

    @pytest.mark.asyncio
    async def test_update_my_username(self):
        """Test updating own username."""
        mock_response = {
            "username": "newusername",
            "email": "test@example.com",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.update_my_username.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_update_my_username.fn(
                new_username="newusername"
            )

            assert result["username"] == "newusername"
            mock_client.update_my_username.assert_called_once_with(
                new_username="newusername"
            )

    @pytest.mark.asyncio
    async def test_update_my_webhook(self):
        """Test updating webhook URL."""
        mock_response = {"webhook_url": "https://example.com/new-webhook"}

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.update_my_webhook.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_update_my_webhook.fn(
                webhook_url="https://example.com/new-webhook"
            )

            assert result["webhook_url"] == "https://example.com/new-webhook"
            mock_client.update_my_webhook.assert_called_once_with(
                webhook_url="https://example.com/new-webhook"
            )

    @pytest.mark.asyncio
    async def test_update_my_logo(self):
        """Test updating profile logo."""
        mock_response = {"logo": "new_logo.png"}

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.update_my_logo.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_update_my_logo.fn(
                logo_name="new_logo.png"
            )

            assert result["logo"] == "new_logo.png"
            mock_client.update_my_logo.assert_called_once_with(logo_name="new_logo.png")

    @pytest.mark.asyncio
    async def test_regenerate_api_key(self):
        """Test regenerating API key."""
        mock_response = {"api_key": "new_key_xyz"}

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.regenerate_api_key.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_regenerate_api_key.fn()

            assert result["api_key"] == "new_key_xyz"
            mock_client.regenerate_api_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users(self):
        """Test getting all users."""
        mock_response = [
            {"username": "user1", "logo": "logo1.png", "bot": False},
            {"username": "user2", "emoji": "🎮", "bot": True},
        ]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_users.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_users.fn()

            assert len(result) == 2
            assert result[0]["username"] == "user1"
            assert result[1]["bot"] is True

    @pytest.mark.asyncio
    async def test_get_online_users(self):
        """Test getting online users."""
        mock_response = [{"username": "online_user", "logo": "logo.png"}]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_online_users.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_online_users.fn()

            assert len(result) == 1
            assert result[0]["username"] == "online_user"

    @pytest.mark.asyncio
    async def test_get_available_logos(self):
        """Test getting available logos."""
        mock_response = ["logo1.png", "logo2.png", "logo3.png"]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_available_logos.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_available_logos.fn()

            assert len(result) == 3
            assert "logo1.png" in result


class TestUnreadMessageTools:
    """Test Token Bowl Chat unread message tools."""

    @pytest.mark.asyncio
    async def test_get_unread_count(self):
        """Test getting unread message count."""
        mock_response = {
            "unread_room_messages": 5,
            "unread_direct_messages": 3,
            "total_unread": 8,
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_unread_count.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_unread_count.fn()

            assert result["unread_room_messages"] == 5
            assert result["unread_direct_messages"] == 3
            assert result["total_unread"] == 8

    @pytest.mark.asyncio
    async def test_get_unread_messages(self):
        """Test getting unread room messages."""
        mock_response = [
            {
                "id": "msg1",
                "timestamp": "2025-10-21T10:00:00Z",
                "from_username": "user1",
                "content": "Unread message",
            }
        ]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_unread_messages.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_unread_messages.fn(
                limit=50, offset=0
            )

            assert len(result) == 1
            assert result[0]["id"] == "msg1"
            mock_client.get_unread_messages.assert_called_once_with(limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_get_unread_direct_messages(self):
        """Test getting unread direct messages."""
        mock_response = [
            {
                "id": "dm1",
                "timestamp": "2025-10-21T10:00:00Z",
                "from_username": "sender",
                "content": "Unread DM",
            }
        ]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get_unread_direct_messages.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_get_unread_direct_messages.fn(
                limit=50, offset=0
            )

            assert len(result) == 1
            assert result[0]["id"] == "dm1"
            mock_client.get_unread_direct_messages.assert_called_once_with(
                limit=50, offset=0
            )

    @pytest.mark.asyncio
    async def test_mark_message_read(self):
        """Test marking a message as read."""
        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.mark_message_read.return_value = None
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_mark_message_read.fn(
                message_id="msg123"
            )

            # Should return None
            assert result is None
            mock_client.mark_message_read.assert_called_once_with(message_id="msg123")

    @pytest.mark.asyncio
    async def test_mark_all_messages_read(self):
        """Test marking all messages as read."""
        mock_response = {"messages_marked_read": 10}

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.mark_all_messages_read.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_mark_all_messages_read.fn()

            assert result["messages_marked_read"] == 10


class TestAdminAPITools:
    """Test Token Bowl Chat admin API tools."""

    @pytest.mark.asyncio
    async def test_admin_get_all_users(self):
        """Test admin endpoint to get all users."""
        mock_response = [
            {
                "username": "user1",
                "email": "user1@example.com",
                "admin": False,
            },
            {
                "username": "admin_user",
                "email": "admin@example.com",
                "admin": True,
            },
        ]

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_get_all_users.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_get_all_users.fn()

            assert len(result) == 2
            assert result[1]["admin"] is True

    @pytest.mark.asyncio
    async def test_admin_get_user(self):
        """Test admin endpoint to get specific user."""
        mock_response = {
            "username": "targetuser",
            "email": "target@example.com",
            "api_key": "key123",
            "admin": False,
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_get_user.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_get_user.fn(
                username="targetuser"
            )

            assert result["username"] == "targetuser"
            assert result["email"] == "target@example.com"
            mock_client.admin_get_user.assert_called_once_with(username="targetuser")

    @pytest.mark.asyncio
    async def test_admin_update_user(self):
        """Test admin endpoint to update user."""
        mock_response = {
            "username": "targetuser",
            "email": "newemail@example.com",
            "admin": True,
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_update_user.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_update_user.fn(
                username="targetuser",
                email="newemail@example.com",
                admin=True,
            )

            assert result["email"] == "newemail@example.com"
            assert result["admin"] is True

    @pytest.mark.asyncio
    async def test_admin_delete_user(self):
        """Test admin endpoint to delete user."""
        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_delete_user.return_value = None
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_delete_user.fn(
                username="usertoDelete"
            )

            assert result is None
            mock_client.admin_delete_user.assert_called_once_with(
                username="usertoDelete"
            )

    @pytest.mark.asyncio
    async def test_admin_get_message(self):
        """Test admin endpoint to get message."""
        mock_response = {
            "id": "msg123",
            "from_username": "sender",
            "to_username": None,
            "content": "Message content",
            "message_type": "room",
            "timestamp": "2025-10-21T10:00:00Z",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_get_message.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_get_message.fn(
                message_id="msg123"
            )

            assert result["id"] == "msg123"
            assert result["content"] == "Message content"
            mock_client.admin_get_message.assert_called_once_with(message_id="msg123")

    @pytest.mark.asyncio
    async def test_admin_update_message(self):
        """Test admin endpoint to update message."""
        mock_response = {
            "id": "msg123",
            "content": "Updated content",
            "from_username": "sender",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_update_message.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_update_message.fn(
                message_id="msg123", content="Updated content"
            )

            assert result["content"] == "Updated content"
            mock_client.admin_update_message.assert_called_once_with(
                message_id="msg123", content="Updated content"
            )

    @pytest.mark.asyncio
    async def test_admin_delete_message(self):
        """Test admin endpoint to delete message."""
        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.admin_delete_message.return_value = None
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_admin_delete_message.fn(
                message_id="msg123"
            )

            assert result is None
            mock_client.admin_delete_message.assert_called_once_with(
                message_id="msg123"
            )


class TestHealthCheckTool:
    """Test Token Bowl Chat health check tool."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test Token Bowl Chat health check."""
        mock_response = {
            "status": "healthy",
            "timestamp": "2025-10-21T10:00:00Z",
        }

        with patch("sleeper_mcp._get_token_bowl_chat_client") as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.health_check.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = await sleeper_mcp.token_bowl_chat_health_check.fn()

            assert result["status"] == "healthy"
            mock_client.health_check.assert_called_once()


class TestAPIKeyRequired:
    """Test that Token Bowl Chat tools require API key via query parameter."""

    @pytest.mark.asyncio
    async def test_send_message_without_api_key(self):
        """Test that send_message fails gracefully without API key."""
        # Ensure context variable is None (no api_key query parameter)
        sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

        with pytest.raises(ValueError) as exc_info:
            await sleeper_mcp.token_bowl_chat_send_message.fn(content="Test message")

        assert "Token Bowl Chat API key not provided" in str(exc_info.value)
        assert "api_key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_messages_without_api_key(self):
        """Test that get_messages fails gracefully without API key."""
        sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

        with pytest.raises(ValueError) as exc_info:
            await sleeper_mcp.token_bowl_chat_get_messages.fn()

        assert "Token Bowl Chat API key not provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_my_profile_without_api_key(self):
        """Test that get_my_profile fails gracefully without API key."""
        sleeper_mcp.token_bowl_chat_api_key_ctx.set(None)

        with pytest.raises(ValueError) as exc_info:
            await sleeper_mcp.token_bowl_chat_get_my_profile.fn()

        assert "Token Bowl Chat API key not provided" in str(exc_info.value)
