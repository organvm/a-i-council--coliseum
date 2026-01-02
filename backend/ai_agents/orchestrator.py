"""
System Orchestrator Module

Manages the lifecycle of AI agents and the main event loop of the council.
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
import logging
import random

from .agent import Agent
from .communication import AgentCommunicationProtocol
from .decision_engine import DecisionEngine
from ..event_pipeline.ingestion import EventIngestionSystem
from ..voting.voting_engine import VotingEngine

logger = logging.getLogger(__name__)

class SystemOrchestrator:
    """
    The central nervous system of the AI Council.

    Responsibilities:
    - Manage agent lifecycles (spawn, kill, pause)
    - Run the main "tick" loop for continuous operation
    - Coordinate between Agents, Event Pipeline, and Voting Engine
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.is_running = False
        self.tick_rate = 1.0  # Seconds between ticks
        self.loop_task: Optional[asyncio.Task] = None
        self.last_activity_time = datetime.utcnow()
        self.silence_threshold_seconds = 30  # Trigger conversation after 30s of silence

        # Initialize Subsystems
        self.communication_protocol = AgentCommunicationProtocol()
        self.event_system = EventIngestionSystem()
        self.voting_engine = VotingEngine()
        self.decision_engine = DecisionEngine()

    def add_agent(self, agent: Agent) -> None:
        """Register a new agent with the system"""
        self.agents[agent.state.agent_id] = agent
        self.communication_protocol.register_agent(agent)
        logger.info(f"Agent {agent.name} ({agent.state.role}) added.")

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the system"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self.communication_protocol.unregister_agent(agent_id)
            del self.agents[agent_id]
            logger.info(f"Agent {agent.name} removed.")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    async def start(self) -> None:
        """Start the orchestrator and main loop"""
        if self.is_running:
            return

        self.is_running = True

        # Start communication protocol
        asyncio.create_task(self.communication_protocol.start())

        # Start main loop
        self.loop_task = asyncio.create_task(self._main_loop())
        logger.info("System Orchestrator started.")

    async def stop(self) -> None:
        """Stop the orchestrator"""
        self.is_running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                logger.debug("Main loop task cancelled during orchestrator shutdown.")

        await self.communication_protocol.stop()
        logger.info("System Orchestrator stopped.")

    async def _main_loop(self) -> None:
        """Main system loop"""
        while self.is_running:
            try:
                await self._tick()
                await asyncio.sleep(self.tick_rate)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

    async def _tick(self) -> None:
        """
        Single system tick.

        1. Process pending messages (handled by comms protocol)
        2. Allow agents to reflect/act based on new events
        3. Check for silence and trigger conversation
        """
        # Update last activity based on message queue?
        # Ideally communication protocol would track last message time.
        # For now, let's assume if there are agents, we check for silence.

        if not self.agents:
            return

        now = datetime.utcnow()
        time_since_activity = (now - self.last_activity_time).total_seconds()

        if time_since_activity > self.silence_threshold_seconds:
            # Pick a random agent to say something
            active_agents = [a for a in self.agents.values() if a.state.is_active]
            if active_agents:
                speaker = random.choice(active_agents)
                # Trigger a thought/message
                # In a real system, we'd prompt "It's quiet, start a topic"
                # For now, just a placeholder log or message
                logger.info(f"Silence detected. Triggering {speaker.name}...")

                # Send an actual system event so that real communication occurs
                # and last_activity_time is updated by the communication flow.
                await self.broadcast_event(
                    event_content="SYSTEM: It's quiet. Please start a new topic."
                )

    async def broadcast_event(self, event_content: str) -> None:
        """
        Manually inject an event/message to all agents
        """
        # Create a system message
        await self.communication_protocol.broadcast_message(
            sender_id="SYSTEM",
            content=event_content
        )
        self.last_activity_time = datetime.utcnow()
