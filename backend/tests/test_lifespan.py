"""Lifespan tests for one-time startup/shutdown orchestration."""

from fastapi.testclient import TestClient

import backend.main as main_module


def test_app_lifespan_initializes_and_stops_once(monkeypatch):
    calls = {"initialize": 0, "start": 0, "stop": 0}

    class StubOrchestrator:
        agents = {}

        async def start(self):
            calls["start"] += 1

        async def stop(self):
            calls["stop"] += 1

        async def broadcast_message(self, message):
            pass

    async def fake_initialize():
        calls["initialize"] += 1

    stub = StubOrchestrator()
    monkeypatch.setattr(main_module, "initialize_orchestrator", fake_initialize)
    monkeypatch.setattr(main_module, "get_orchestrator", lambda: stub)

    with TestClient(main_module.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200

    assert calls["initialize"] == 1
    assert calls["start"] == 1
    assert calls["stop"] == 1

