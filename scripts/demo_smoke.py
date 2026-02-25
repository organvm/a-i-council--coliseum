#!/usr/bin/env python3
"""
Lightweight smoke test for demo recording readiness.

Checks:
- backend health + readiness
- bootstrap endpoint
- websocket connect
- Director Mode scenario start (optional)
- arrival of demo/combat/vote websocket events within timeout
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

import httpx
import websockets


async def require_ok(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    url = str(client.base_url.join(path))
    resp = await client.get(path, timeout=5.0)
    print(f"[smoke] GET {url} -> {resp.status_code}")
    resp.raise_for_status()
    return resp.json()


async def wait_for_http_ready(
    client: httpx.AsyncClient,
    path: str,
    startup_timeout: float,
) -> dict[str, Any]:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + startup_timeout
    last_error: Exception | None = None
    while loop.time() < deadline:
        try:
            return await require_ok(client, path)
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.5)
    if last_error:
        raise last_error
    raise RuntimeError("Timed out waiting for HTTP readiness")


async def start_scenario(
    client: httpx.AsyncClient,
    scenario: str,
    speed_multiplier: float,
) -> None:
    path = f"/api/demo/scenarios/{scenario}/start"
    resp = await client.post(
        path,
        json={"restart_if_running": True, "speed_multiplier": speed_multiplier},
        timeout=10.0,
    )
    print(f"[smoke] POST {path} -> {resp.status_code}")
    resp.raise_for_status()
    payload = resp.json()
    status = payload.get("director", {})
    print(
        "[smoke] director status:",
        {
            "status": status.get("status"),
            "scenario": status.get("scenario"),
            "run_id": status.get("run_id"),
        },
    )


async def wait_for_events(ws_url: str, timeout_seconds: float) -> list[str]:
    interesting = {"demo_marker", "combat_update", "vote_update", "system_status"}
    seen: list[str] = []

    print(f"[smoke] WS connect {ws_url}")
    async with websockets.connect(ws_url, open_timeout=5.0) as ws:
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while asyncio.get_event_loop().time() < deadline:
            remaining = max(0.1, deadline - asyncio.get_event_loop().time())
            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
            payload = json.loads(raw)
            event_type = payload.get("type")
            if event_type in interesting:
                seen.append(str(event_type))
                print(f"[smoke] WS event: {event_type}")
            if {"system_status", "demo_marker"}.issubset(set(seen)) and (
                "combat_update" in seen or "vote_update" in seen
            ):
                return seen

    return seen


async def amain(args: argparse.Namespace) -> int:
    async with httpx.AsyncClient(base_url=args.api_url) as client:
        health = await wait_for_http_ready(client, "/health", args.startup_timeout)
        ready = await require_ok(client, "/health/ready")
        bootstrap = await require_ok(client, "/api/state/bootstrap")

        if health.get("status") != "healthy":
            print("[smoke] unexpected /health status", health, file=sys.stderr)
            return 1
        if ready.get("status") not in {"ready", "degraded"}:
            print("[smoke] unexpected /health/ready status", ready, file=sys.stderr)
            return 1
        if "agents" not in bootstrap:
            print("[smoke] bootstrap missing agents payload", file=sys.stderr)
            return 1

        if not args.skip_scenario_start:
            await start_scenario(client, args.scenario, args.speed_multiplier)

    seen = await wait_for_events(args.ws_url, args.ws_timeout)
    seen_set = set(seen)
    if "system_status" not in seen_set:
        print("[smoke] missing websocket system_status event", file=sys.stderr)
        return 1
    if "demo_marker" not in seen_set:
        print("[smoke] missing demo_marker event", file=sys.stderr)
        return 1
    if "combat_update" not in seen_set and "vote_update" not in seen_set:
        print("[smoke] missing combat_update/vote_update event", file=sys.stderr)
        return 1

    print("[smoke] PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--ws-url", default="ws://localhost:8000/ws")
    parser.add_argument("--scenario", default="ars_submission_showcase")
    parser.add_argument("--speed-multiplier", type=float, default=4.0)
    parser.add_argument("--ws-timeout", type=float, default=12.0)
    parser.add_argument("--startup-timeout", type=float, default=20.0)
    parser.add_argument("--skip-scenario-start", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
