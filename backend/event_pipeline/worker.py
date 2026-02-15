"""
Autonomous Arena Worker.

Background task that feeds the Coliseum with real-world events or 
simulated "drifts" to keep the agents debating.
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import List

from ..ai_agents.orchestrator import SystemOrchestrator
from .ingestion import EventSource

logger = logging.getLogger(__name__)

# Simulated news pool for fallback/autonomous activity
SIMULATED_NEWS = [
    {
        "title": "Solana Throughput Reaches New ATH",
        "description": "The Solana network has sustained over 50,000 TPS for a 24-hour period.",
        "source": "blockchain"
    },
    {
        "title": "Ethereum L2 Gas Fees Drop to Near Zero",
        "description": "Proto-danksharding implementation has resulted in massive gas savings for users.",
        "source": "blockchain"
    },
    {
        "title": "AI Council Votes on Digital Ethics",
        "description": "A new framework for AI-to-AI communication has been proposed by the global council.",
        "source": "api"
    },
    {
        "title": "Major Tech Giant Announces Fully Autonomous Data Center",
        "description": "The data center is managed entirely by AI agents with no human intervention required.",
        "source": "news_api"
    },
    {
        "title": "Decentralized GPU Cluster Outperforms Supercomputer",
        "description": "A community-owned compute network has set a new record for model training speed.",
        "source": "blockchain"
    },
    {
        "title": "Celebrity Chef Cancels Pizza",
        "description": "Controversial take on pineapple leads to massive online fallout.",
        "source": "social_media"
    },
    {
        "title": "Streamer Banned for Being Too Good",
        "description": "Pro gamer accused of using AI assistance because human reaction times were impossible.",
        "source": "social_media"
    }
]

class AutonomousArenaWorker:
    """Task worker that feeds events into the SystemOrchestrator."""

    def __init__(self, orchestrator: SystemOrchestrator, interval_seconds: int = 300):
        self.orchestrator = orchestrator
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the autonomous feeding loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Autonomous Arena Worker started (Interval: {self.interval_seconds}s)")

    async def stop(self):
        """Stop the worker."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Autonomous Arena Worker stopped")

    async def _loop(self):
        """Main periodic loop."""
        while self.is_running:
            try:
                # Random jitter to make it feel less robotic
                jitter = random.randint(-30, 30)
                await asyncio.sleep(max(10, self.interval_seconds + jitter))
                
                await self._feed_event()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Arena Worker: {e}")

    async def _feed_event(self):
        """Inject a random event into the arena."""
        event_data = random.choice(SIMULATED_NEWS)
        source = EventSource(event_data["source"])
        
        logger.info(f"Injecting autonomous event: {event_data['title']}")
        
        processed = await self.orchestrator.ingest_event(
            source=source,
            raw_data=event_data,
            metadata={"autonomous": True}
        )
        
        if processed:
            # Trigger Combat if source is social_media
            if source == EventSource.SOCIAL_MEDIA:
                await self.orchestrator.start_battle(processed.title)
            
            # Also trigger a voting session if the priority is high
            if processed.priority_score > 1.0:
                from ..voting.voting_engine import VoteType
                await self.orchestrator.create_voting_session(
                    title=f"Arena Poll: {processed.title}",
                    description=f"Based on: {processed.summary}",
                    vote_type=VoteType.BINARY,
                    options=["Agree", "Disagree"],
                    duration_minutes=30
                )
