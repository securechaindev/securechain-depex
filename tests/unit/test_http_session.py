"""Unit tests for http_session module."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from aiohttp import ClientSession

from app.http_session import HTTPSessionManager


class TestHTTPSessionManager:
    """Test suite for HTTPSessionManager."""

    @pytest.mark.asyncio
    async def test_get_session_creates_new_session(self):
        """Test that get_session creates a new session when none exists."""
        manager = HTTPSessionManager()
        
        session = await manager.get_session()
        
        assert session is not None
        assert isinstance(session, ClientSession)
        assert not session.closed
        
        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_get_session_returns_existing_session(self):
        """Test that get_session returns existing session if still open."""
        manager = HTTPSessionManager()
        
        session1 = await manager.get_session()
        session2 = await manager.get_session()
        
        assert session1 is session2
        assert not session1.closed
        
        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_get_session_creates_new_after_closed(self):
        """Test that get_session creates new session after previous was closed."""
        manager = HTTPSessionManager()
        
        session1 = await manager.get_session()
        await manager.close()
        
        session2 = await manager.get_session()
        
        assert session1 is not session2
        assert session1.closed
        assert not session2.closed
        
        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_close_closes_open_session(self):
        """Test that close properly closes an open session."""
        manager = HTTPSessionManager()
        
        session = await manager.get_session()
        assert not session.closed
        
        await manager.close()
        
        assert session.closed
        assert manager._session is None

    @pytest.mark.asyncio
    async def test_close_when_no_session(self):
        """Test that close works when no session exists."""
        manager = HTTPSessionManager()
        
        # Should not raise any exception
        await manager.close()
        
        assert manager._session is None

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self):
        """Test that close works when session is already closed."""
        manager = HTTPSessionManager()
        
        session = await manager.get_session()
        await manager.close()
        
        # Close again should not raise exception
        await manager.close()
        
        assert session.closed
        assert manager._session is None

    @pytest.mark.asyncio
    async def test_multiple_get_close_cycles(self):
        """Test multiple cycles of getting and closing sessions."""
        manager = HTTPSessionManager()
        
        for _ in range(3):
            session = await manager.get_session()
            assert not session.closed
            
            await manager.close()
            assert session.closed
            assert manager._session is None

    @pytest.mark.asyncio
    async def test_session_state_after_external_close(self):
        """Test behavior when session is closed externally."""
        manager = HTTPSessionManager()
        
        session1 = await manager.get_session()
        # Simulate external close
        await session1.close()
        
        # Should create new session since previous is closed
        session2 = await manager.get_session()
        
        assert session1 is not session2
        assert session1.closed
        assert not session2.closed
        
        # Cleanup
        await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_get_session_calls(self):
        """Test that concurrent get_session calls handle properly."""
        manager = HTTPSessionManager()
        
        # Get session twice "concurrently" (in async context)
        import asyncio
        sessions = await asyncio.gather(
            manager.get_session(),
            manager.get_session()
        )
        
        # Both should get the same session (or handle race conditions safely)
        assert all(isinstance(s, ClientSession) for s in sessions)
        assert all(not s.closed for s in sessions)
        
        # Cleanup
        await manager.close()
