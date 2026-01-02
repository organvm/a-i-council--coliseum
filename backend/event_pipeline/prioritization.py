"""
Event Prioritization Module

Scores events to determine their relevance and importance to the agents.
"""

from typing import List, Dict
from datetime import datetime, timedelta
from .ingestion import NormalizedEvent

class EventPrioritizer:
    """
    Prioritizes events based on keywords, recency, and potential impact.
    """
    
    def __init__(self):
        # Keywords that boost score
        self.high_priority_keywords = {
            "ai", "artificial intelligence", "crypto", "blockchain", "bitcoin",
            "ethereum", "solana", "regulation", "breakthrough", "emergency",
            "market crash", "bull run"
        }
        self.medium_priority_keywords = {
            "tech", "update", "release", "investment", "startup", "policy"
        }
    
    def calculate_score(self, event: NormalizedEvent) -> float:
        """
        Calculate priority score (0.0 to 1.0+) for an event.
        """
        score = 0.0
        text = (event.title + " " + event.description).lower()
        
        # Keyword scoring
        for kw in self.high_priority_keywords:
            if kw in text:
                score += 0.3
        
        for kw in self.medium_priority_keywords:
            if kw in text:
                score += 0.1

        # Recency scoring (decay over time)
        # Assuming event.timestamp is UTC
        now = datetime.utcnow()
        age_hours = (now - event.timestamp).total_seconds() / 3600.0
        
        # Boost for very fresh events (< 1 hour)
        if age_hours < 1:
            score += 0.2
        elif age_hours < 6:
            score += 0.1
            
        # Source reliability boost (example)
        if event.source == "internal" or event.source == "user_submission":
            score += 0.1

        return score

    def prioritize_events(self, events: List[NormalizedEvent]) -> List[NormalizedEvent]:
        """
        Sort events by calculated priority score descending.
        """
        # We can attach the score to metadata or just return sorted list
        # For now, let's just sort them.
        # Ideally, NormalizedEvent would have a 'priority_score' field,
        # but it's not in the model currently.
        # We can calculate on the fly for sorting.
        
        return sorted(events, key=self.calculate_score, reverse=True)
