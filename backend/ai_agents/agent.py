"""
Concrete Agent Implementation.

Integrates memory, knowledge, NLP, and decision-making capabilities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from .base_agent import AgentRole, BaseAgent, Message
from .decision_engine import DecisionEngine
from .knowledge_base import KnowledgeBase
from .memory_manager import MemoryManager
from .nlp_module import NLPProcessor


class Agent(BaseAgent):
    """Concrete implementation of an AI agent."""

    def __init__(
        self,
        role: AgentRole,
        config: Optional[Dict[str, Any]] = None,
        memory_manager: Optional[MemoryManager] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        nlp_processor: Optional[NLPProcessor] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ):
        super().__init__(role, config)

        cfg = config or {}
        self.memory_manager = memory_manager or MemoryManager()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.decision_engine = decision_engine or DecisionEngine()

        self.system_prompt = cfg.get(
            "system_prompt", f"You are an AI agent acting as a {role.value}."
        )
        self.name = cfg.get("name", f"{role.value.capitalize()} Agent")

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message and optionally return a response."""
        self.update_state(last_active=datetime.utcnow())
        self.memory_manager.add_short_term({"type": "message", "content": message.model_dump()})
        self.message_history.append(message)

        if message.sender_id == self.state.agent_id:
            return None

        is_direct = message.recipient_id == self.state.agent_id
        should_respond = is_direct

        if not should_respond:
            content_lower = message.content.lower()
            if self.name.lower() in content_lower:
                should_respond = True
            elif message.recipient_id is None and self.state.is_active:
                # Debaters are expected to participate in open discussion.
                should_respond = self.state.role == AgentRole.DEBATER

        if not should_respond:
            return None

        sentiment = await self.nlp_processor.analyze_sentiment(message.content)
        topics = await self.nlp_processor.classify_topic(message.content)
        self.add_to_memory("last_sentiment", sentiment)
        self.add_to_memory("last_topics", topics)
        
        # Save to episodic/semantic memory for long-term recall
        await self.memory_manager.add_semantic_memory(
            text=f"Interaction context: {message.content}",
            agent_id=self.state.agent_id,
            metadata={
                "sender_id": message.sender_id,
                "message_id": message.message_id,
                "sentiment": sentiment,
                "topics": topics
            }
        )

        # Save state to DB

        response_text = await self.generate_response(
            prompt=message.content,
            context={
                "sender_id": message.sender_id,
                "message_type": message.message_type,
                "previous_messages": self.memory_manager.get_short_term(limit=5),
            },
        )

        return Message(
            sender_id=self.state.agent_id,
            recipient_id=message.sender_id if is_direct else None,
            content=response_text,
            metadata={
                "reply_to": message.message_id,
                "sentiment_context": sentiment,
                "topics": topics,
            },
        )

    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision using internal logic and, optionally, the DecisionEngine."""
        decision_type = context.get("type", "internal")

        if decision_type == "vote":
            decision_id = context.get("decision_id")
            options = context.get("options", [])
            default_choice = context.get("default_choice")

            if default_choice is not None:
                choice = default_choice
            elif options:
                choice = options[0]
            else:
                choice = "yes"

            reasoning = context.get(
                "reasoning", "Automated decision based on role configuration"
            )
            confidence = float(context.get("confidence", 0.8))

            if decision_id:
                try:
                    self.decision_engine.cast_vote(
                        decision_id=decision_id,
                        agent_id=self.state.agent_id,
                        choice=choice,
                        reasoning=reasoning,
                        confidence=confidence,
                    )
                except ValueError as exc:
                    return {"error": str(exc)}

            return {
                "status": "voted",
                "choice": choice,
                "reasoning": reasoning,
                "confidence": confidence,
            }

        return {"status": "skipped", "reason": "Unknown decision type"}

    async def generate_response(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a role-aware response using RAG and LLM."""
        
        # 1. Retrieve RAG Context (Global Fact Knowledge)
        rag_context = await self.knowledge_base.search(prompt, limit=2)
        context_str = "\n".join([f"- {item['content']}" for item in rag_context])
        
        # 1.5 Retrieve Personal Semantic Memory (Past Interactions)
        personal_memories = await self.memory_manager.search_semantic_memory(prompt, self.state.agent_id, limit=3)
        if personal_memories:
            memory_str = "\n".join([f"- {item['content']}" for item in personal_memories])
            if context_str:
                context_str += "\n\n"
            context_str += f"Personal Memories:\n{memory_str}"
        
        enriched_system_prompt = self.system_prompt
        if context_str:
            enriched_system_prompt += f"\n\nRelevant Context:\n{context_str}"

        # 2. Generate LLM Response
        generated = await self.nlp_processor.generate(
            enriched_system_prompt, 
            prompt, 
            context=context
        )

        role_prefixes = {
            AgentRole.MODERATOR: "As a moderator,",
            AgentRole.DEBATER: "I argue that",
            AgentRole.ANALYST: "Analysis shows",
            AgentRole.FACT_CHECKER: "Fact check",
            AgentRole.SUMMARIZER: "Summary",
            AgentRole.VOTER: "My vote is",
            AgentRole.OBSERVER: "Observation",
        }

        prefix = role_prefixes.get(self.state.role, "Response")
        return f"{prefix}: {generated}"
