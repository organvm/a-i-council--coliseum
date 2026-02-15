"""
Twitch Listener Module.

Simulates listening to a Twitch chat stream for audience interaction.
"""

import asyncio
import logging
import random
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class TwitchListener:
    """Simulated Twitch IRC listener."""

    def __init__(self, callback: Optional[Callable[[str, str], None]] = None):
        self.callback = callback
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.channel = "ai_council_coliseum"

    async def start(self):
        """Start the simulated listener."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Twitch Listener started on channel: #{self.channel}")

    async def stop(self):
        """Stop the listener."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Twitch Listener stopped")

    async def _loop(self):
        """Simulate incoming chat messages."""
        simulated_users = ["Viewer1", "CryptoFan99", "SolanaWhale", "AI_Watcher", "BasedDev"]
        simulated_messages = [
            "!vote Socrates",
            "!vote Atlas",
            "This debate is intense!",
            "LMAO that fatality",
            "Solana to the moon 🚀",
            "When token launch?",
            "!attack Machiavelli"
        ]

        while self.is_running:
            try:
                await asyncio.sleep(random.randint(2, 10))
                
                user = random.choice(simulated_users)
                msg = random.choice(simulated_messages)
                
                logger.info(f"[Twitch] {user}: {msg}")
                
                if self.callback:
                    await self.callback(user, msg)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Twitch Listener: {e}")
