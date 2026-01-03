"""
Concrete Agent Implementation

This module provides the concrete implementation of the AI agent,
integrating memory, knowledge, NLP, and decision-making capabilities.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent, AgentRole, Message
from .memory_manager import MemoryManager
from .knowledge_base import KnowledgeBase
from .nlp_module import NLPProcessor
from .decision_engine import DecisionEngine


class Agent(BaseAgent):
    """
    Concrete implementation of an AI agent.

    Integrates:
    - MemoryManager: For short-term and long-term memory
    - KnowledgeBase: For accessing static knowledge
    - NLPProcessor: For language understanding and generation
    - DecisionEngine: For making choices and voting
    """

    def __init__(
        self,
        role: AgentRole,
        config: Optional[Dict[str, Any]] = None,
        memory_manager: Optional[MemoryManager] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        nlp_processor: Optional[NLPProcessor] = None,
        decision_engine: Optional[DecisionEngine] = None
    ):
        super().__init__(role, config)

        # Initialize modules
        self.memory_manager = memory_manager or MemoryManager()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.decision_engine = decision_engine or DecisionEngine()

        # Agent personality/system prompt
        self.system_prompt = config.get("system_prompt", f"You are an AI agent acting as a {role}.")
        self.name = config.get("name", f"{role.capitalize()} Agent")

    async def process_message(self, message: Message) -> Optional[Message]:
        """
        Process incoming message and optionally return a response.

        1. Add message to memory
        2. Analyze sentiment/content
        3. Decide whether to respond
        4. Generate response if needed
        """
        self.update_state(last_active=datetime.utcnow())

        # 1. Add to short-term memory
        self.memory_manager.add_short_term({
            "type": "message",
            "content": message.model_dump()
        })
        self.message_history.append(message)

        # Ignore own messages
        if message.sender_id == self.state.agent_id:
            return None

        # 2. Analyze content
        # Check if direct message or broadcast
        is_direct = message.recipient_id == self.state.agent_id

        # If it's a direct message, we almost always want to respond
        should_respond = is_direct

        # For broadcast, we might respond if it's relevant or we are mentioned
        if not should_respond:
            # Simple keyword check for now, could be more sophisticated
            if self.name.lower() in message.content.lower():
                should_respond = True

            # Or if role dictates participation (e.g., DEBATER)
            if self.state.role == AgentRole.DEBATER and self.state.current_topic:
                 # Check if message is relevant to current topic (simplified)
                 should_respond = True

        if should_respond:
            # 3. Generate Response
            response_text = await self.generate_response(
                prompt=message.content,
                context={
                    "sender_id": message.sender_id,
                    "message_type": message.message_type,
                    "previous_messages": self.memory_manager.get_short_term(limit=5)
                }
            )

            return Message(
                sender_id=self.state.agent_id,
                recipient_id=message.sender_id if is_direct else None,
                content=response_text,
                metadata={"reply_to": message.message_id}
            )

        return None

    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a decision using the DecisionEngine or internal logic.
        """
        decision_type = context.get("type", "internal")

        if decision_type == "vote":
            decision_id = context.get("decision_id")
            if not decision_id:
                return {"error": "No decision_id provided for vote"}

            # Logic to determine vote would go here, possibly using NLP and KnowledgeBase
            # For now, we simulate a random or default choice
            choice = context.get("default_choice", "yes")

            try:
                self.decision_engine.cast_vote(
                    decision_id=decision_id,
                    agent_id=self.state.agent_id,
                    choice=choice,
                    reasoning="Automated decision based on role configuration"
                )
                return {"status": "voted", "choice": choice}
            except ValueError as e:
                return {"error": str(e)}

        return {"status": "skipped", "reason": "Unknown decision type"}

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response using NLP processor.
        """
        # Since NLPProcessor currently lacks generation, we use summarization as a proxy
        # or a simple template. In a real scenario, this would call an LLM.

        # Use NLP Processor generate if available, else summarize or heuristic
        if self.nlp_processor.client:
            return await self.nlp_processor.generate(
                system=self.system_prompt,
                prompt=prompt,
                context=context
            )

        # Fallback
        summary = await self.nlp_processor.summarize(prompt, max_length=50)

        role_prefixes = {
            AgentRole.MODERATOR: "As a moderator, I note:",
            AgentRole.DEBATER: "I argue that:",
            AgentRole.ANALYST: "Analysis shows:",
            AgentRole.FACT_CHECKER: "Fact check:",
        }

        prefix = role_prefixes.get(self.state.role, "Response:")
        return f"{prefix} {summary} (processed by {self.state.agent_id})"
