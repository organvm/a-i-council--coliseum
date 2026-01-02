"""
API Dependencies

Provides dependency injection for API routes.
"""

from typing import Optional
from functools import lru_cache
from ..ai_agents.orchestrator import SystemOrchestrator
from ..ai_agents.agent import Agent, AgentRole

# Global singleton instance
_orchestrator_instance: Optional[SystemOrchestrator] = None

def get_orchestrator() -> SystemOrchestrator:
    """Dependency to get the global system orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SystemOrchestrator()
    return _orchestrator_instance

async def initialize_orchestrator():
    """Initialize the orchestrator with default agents on startup"""
    orchestrator = get_orchestrator()
    if not orchestrator.agents:
        # Spawn initial council members
        roles = [
            (AgentRole.MODERATOR, "Atlas"),
            (AgentRole.DEBATER, "Socrates"),
            (AgentRole.DEBATER, "Machiavelli"),
            (AgentRole.ANALYST, "Athena"),
        ]

        for role, name in roles:
            agent = Agent(role=role, config={"name": name})
            orchestrator.add_agent(agent)

        await orchestrator.start()
