"""
System Orchestrator Module

Manages the lifecycle of AI agents and coordinates system-wide activities.
"""

from typing import Dict, List, Optional
import asyncio
from .base_agent import AgentRole, Message
from .agent import Agent
from .memory_manager import MemoryManager
from .knowledge_base import KnowledgeBase
from .decision_engine import DecisionEngine

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
        # Inject shared components if they are using defaults
        # Note: In a real system we might force sharing, but here we just register
        self.agents[agent.state.agent_id] = agent
        return agent.state.agent_id

    def create_agent(self, role: AgentRole, config: Optional[Dict] = None) -> Agent:
        """Create and register a new agent"""
        agent = Agent(
            role=role,
            config=config,
            knowledge_base=self.knowledge_base,
            decision_engine=self.decision_engine
            # We give them their own memory manager, but share knowledge and decisions
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
                # Handle agent response (e.g. log it, or re-broadcast if needed)
                # For now, we just print it
                print(f"Agent {response.sender_id} replied: {response.content}")

    async def start(self):
        """Start the orchestration loop"""
        self.active = True
        print("System Orchestrator started.")
        # In a real app, this might start a background loop

    async def stop(self):
        """Stop the orchestration loop"""
        self.active = False
        print("System Orchestrator stopped.")

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
                pass

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

                # We could inject a "thought" into the agent to prompt them to speak
                # await speaker.process_message(Message(..., content="SYSTEM: It's quiet..."))

                self.last_activity_time = now # Reset timer

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
