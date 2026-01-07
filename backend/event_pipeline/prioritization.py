"""
Event Prioritization Module

Scores events to determine their relevance and importance to the agents.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
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
    
    def calculate_score(self, event: NormalizedEvent, now: Optional[datetime] = None) -> float:
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
        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure event.timestamp is timezone-aware if possible,
        # but if it's naive UTC (from older ingestion), we might need to handle it.
        # Assuming ingestion sets it correctly or we treat naive as UTC.
        event_ts = event.timestamp
        if event_ts.tzinfo is None:
             event_ts = event_ts.replace(tzinfo=timezone.utc)

        age_hours = (now - event_ts).total_seconds() / 3600.0
        
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
        
        now = datetime.now(timezone.utc)
        return sorted(events, key=lambda e: self.calculate_score(e, now), reverse=True)
