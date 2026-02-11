"""
API Dependencies.

Provides dependency injection and startup initialization for API routes.
"""

from __future__ import annotations

from typing import Optional

try:
    from ..ai_agents.agent import Agent, AgentRole
    from ..ai_agents.orchestrator import SystemOrchestrator
except ImportError:
    from ai_agents.agent import Agent, AgentRole
    from ai_agents.orchestrator import SystemOrchestrator

_orchestrator_instance: Optional[SystemOrchestrator] = None


def get_orchestrator() -> SystemOrchestrator:
    """Return the shared orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SystemOrchestrator()
    return _orchestrator_instance


async def initialize_orchestrator() -> None:
    """Populate default agents once. Does not start the orchestrator loop."""
    orchestrator = get_orchestrator()
    if orchestrator.agents:
        return

    roles = [
        (AgentRole.MODERATOR, "Atlas"),
        (AgentRole.DEBATER, "Socrates"),
        (AgentRole.DEBATER, "Machiavelli"),
        (AgentRole.ANALYST, "Athena"),
    ]

    for role, name in roles:
        agent = Agent(role=role, config={"name": name})
        orchestrator.add_agent(agent)
