"""Targeted tests for websocket connection management behavior."""

from __future__ import annotations

import pytest

from backend.main import ConnectionManager


class _HealthyWebSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, payload):
        self.messages.append(payload)


class _FailingWebSocket:
    async def send_json(self, payload):
        raise RuntimeError("socket write failed")


@pytest.mark.asyncio
async def test_connection_manager_broadcast_prunes_failed_connections():
    manager = ConnectionManager()
    healthy = _HealthyWebSocket()
    failing = _FailingWebSocket()
    manager.active_connections = [healthy, failing]

    await manager.broadcast({"type": "combat_update", "data": {"damage": 3}})

    assert healthy.messages == [{"type": "combat_update", "data": {"damage": 3}}]
    assert healthy in manager.active_connections
    assert failing not in manager.active_connections


def test_connection_manager_disconnect_is_idempotent():
    manager = ConnectionManager()
    ws = object()
    manager.active_connections = [ws]

    manager.disconnect(ws)
    manager.disconnect(ws)

    assert manager.active_connections == []
