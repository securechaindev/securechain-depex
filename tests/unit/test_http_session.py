import pytest
from aiohttp import ClientSession

from app.http_session import HTTPSessionManager


class TestHTTPSessionManager:
    @pytest.mark.asyncio
    async def test_get_session_creates_new_session(self):
        manager = HTTPSessionManager()

        session = await manager.get_session()

        assert session is not None
        assert isinstance(session, ClientSession)
        assert not session.closed

        await manager.close()

    @pytest.mark.asyncio
    async def test_get_session_returns_existing_session(self):
        manager = HTTPSessionManager()

        session1 = await manager.get_session()
        session2 = await manager.get_session()

        assert session1 is session2
        assert not session1.closed

        await manager.close()

    @pytest.mark.asyncio
    async def test_get_session_creates_new_after_closed(self):
        manager = HTTPSessionManager()

        session1 = await manager.get_session()
        await manager.close()

        session2 = await manager.get_session()

        assert session1 is not session2
        assert session1.closed
        assert not session2.closed

        await manager.close()

    @pytest.mark.asyncio
    async def test_close_closes_open_session(self):
        manager = HTTPSessionManager()

        session = await manager.get_session()
        assert not session.closed

        await manager.close()

        assert session.closed
        assert manager.session is None

    @pytest.mark.asyncio
    async def test_close_when_no_session(self):
        manager = HTTPSessionManager()

        await manager.close()

        assert manager.session is None

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self):
        manager = HTTPSessionManager()

        session = await manager.get_session()
        await manager.close()

        await manager.close()

        assert session.closed
        assert manager.session is None

    @pytest.mark.asyncio
    async def test_multiple_get_close_cycles(self):
        manager = HTTPSessionManager()

        for _ in range(3):
            session = await manager.get_session()
            assert not session.closed

            await manager.close()
            assert session.closed
            assert manager.session is None

    @pytest.mark.asyncio
    async def test_session_state_after_external_close(self):
        manager = HTTPSessionManager()

        session1 = await manager.get_session()
        await session1.close()

        session2 = await manager.get_session()

        assert session1 is not session2
        assert session1.closed
        assert not session2.closed

        await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_get_session_calls(self):
        manager = HTTPSessionManager()

        import asyncio
        sessions = await asyncio.gather(
            manager.get_session(),
            manager.get_session()
        )

        assert all(isinstance(s, ClientSession) for s in sessions)
        assert all(not s.closed for s in sessions)

        await manager.close()
