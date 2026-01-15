"""
System Orchestrator Module

Manages the lifecycle of AI agents and coordinates system-wide activities.
"""

from typing import Dict, List, Optional
import asyncio
import logging
from .base_agent import AgentRole, Message
from .agent import Agent
from .memory_manager import MemoryManager
from .knowledge_base import KnowledgeBase
from .decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

class SystemOrchestrator:
    """
    Orchestrates the AI Council system.
    Manages agents, distributes messages, and coordinates activities.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.agents: Dict[str, Agent] = {}
        self.active = False
        self.memory_manager = MemoryManager()
        self.knowledge_base = KnowledgeBase()
        self.decision_engine = DecisionEngine()
        self._initialized = True

    def register_agent(self, agent: Agent) -> str:
        """Register a new agent with the system"""
        self.agents[agent.state.agent_id] = agent
        return agent.state.agent_id

    # Alias for compatibility if needed (tests used add_agent)
    add_agent = register_agent

    def create_agent(self, role: AgentRole, config: Optional[Dict] = None) -> Agent:
        """Create and register a new agent"""
        agent = Agent(
            role=role,
            config=config,
            knowledge_base=self.knowledge_base,
            decision_engine=self.decision_engine
        )
        self.register_agent(agent)
        return agent

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the system"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    async def broadcast_message(self, message: Message) -> None:
        """Broadcast a message to all active agents"""
        tasks = []
        for agent in self.agents.values():
            if agent.state.is_active:
                tasks.append(agent.process_message(message))

        # Gather responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses (if any agents replied)
        for response in responses:
            if isinstance(response, Message):
                # Handle agent response
                print(f"Agent {response.sender_id} replied: {response.content}")

    async def start(self):
        """Start the orchestration loop"""
        self.active = True
        logger.info("System Orchestrator started.")

    async def stop(self):
        """Stop the orchestration loop"""
        self.active = False
        logger.info("System Orchestrator stopped.")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
