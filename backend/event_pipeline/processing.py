"""
Event Processing Module

Processes events through various transformations and enrichments.
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from .ingestion import NormalizedEvent


class ProcessedEvent(NormalizedEvent):
    """Event after processing with enrichments"""
    sentiment: Optional[Dict[str, float]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    priority_score: Optional[float] = None
    processing_timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        self.processing_timestamp = datetime.utcnow()


class EventProcessor:
    """
    Processes events with enrichments and transformations
    """
    
    def __init__(self):
        self.processors: List[Callable] = []
        self.enrichers: Dict[str, Callable] = {}
    
    def add_processor(self, processor: Callable) -> None:
        """Add a processing function"""
        self.processors.append(processor)
    
    def add_enricher(self, name: str, enricher: Callable) -> None:
        """Add an enrichment function"""
        self.enrichers[name] = enricher
    
    async def process_event(
        self,
        event: NormalizedEvent,
        enrichments: Optional[List[str]] = None
    ) -> ProcessedEvent:
        """
        Process event through pipeline
        
        Args:
            event: Event to process
            enrichments: Optional list of enrichments to apply
            
        Returns:
            Processed event
        """
        # Convert to ProcessedEvent
        processed = ProcessedEvent(**event.model_dump())
        
        # Apply processors
        for processor in self.processors:
            try:
                processed = await processor(processed)
            except Exception as e:
                print(f"Error in processor: {e}")
        
        # Apply enrichments
        if enrichments:
            for enrichment_name in enrichments:
                if enrichment_name in self.enrichers:
                    try:
                        enricher = self.enrichers[enrichment_name]
                        processed = await enricher(processed)
                    except Exception as e:
                        print(f"Error in enrichment {enrichment_name}: {e}")
        
        return processed
    
    async def batch_process(
        self,
        events: List[NormalizedEvent],
        enrichments: Optional[List[str]] = None
    ) -> List[ProcessedEvent]:
        """Process multiple events concurrently"""
        import asyncio

        # Limit concurrency to avoid overwhelming resources.
        # The number (e.g., 100) can be tuned or made configurable.
        semaphore = asyncio.Semaphore(100)

        async def _process_with_semaphore(event):
            async with semaphore:
                return await self.process_event(event, enrichments)

        tasks = [_process_with_semaphore(event) for event in events]
        return await asyncio.gather(*tasks)
    
    async def enrich_sentiment(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add sentiment analysis enrichment"""
        # Placeholder for actual sentiment analysis
        event.sentiment = {
            "positive": 0.3,
            "negative": 0.3,
            "neutral": 0.4
        }
        return event
    
    async def enrich_entities(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add entity extraction enrichment"""
        # Placeholder for actual entity extraction
        event.entities = []
        return event
    
    async def enrich_summary(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add summary enrichment"""
        # Placeholder for actual summarization
        if event.description and len(event.description) > 100:
            event.summary = event.description[:100] + "..."
        else:
            event.summary = event.description
        return event
    
    async def enrich_keywords(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add keyword extraction enrichment"""
        # Placeholder for actual keyword extraction
        text = f"{event.title} {event.description}".lower()
        words = text.split()
        # Simple word frequency
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only longer words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top 5 keywords
        # Optimization: Use heapq.nlargest instead of full sort (O(N log K) vs O(N log N))
        import heapq
        top_k = heapq.nlargest(5, word_freq.items(), key=lambda x: x[1])
        event.keywords = [word for word, _ in top_k]
        return event
