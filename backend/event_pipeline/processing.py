"""
Event Processing Module

Processes events through various transformations and enrichments.
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from .ingestion import NormalizedEvent
from ..ai_agents.nlp_module import NLPProcessor


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
        self.nlp_processor = NLPProcessor()

        # Register default enrichers
        self.add_enricher("sentiment", self.enrich_sentiment)
        self.add_enricher("entities", self.enrich_entities)
        self.add_enricher("summary", self.enrich_summary)
        self.add_enricher("keywords", self.enrich_keywords)
    
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
        # Default enrichments if none specified
        enrichments_to_run = enrichments or ["sentiment", "keywords", "summary"]

        for enrichment_name in enrichments_to_run:
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
        """Process multiple events"""
        processed_events = []
        for event in events:
            processed = await self.process_event(event, enrichments)
            processed_events.append(processed)
        return processed_events
    
    async def enrich_sentiment(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add sentiment analysis enrichment"""
        text = f"{event.title} {event.description or ''}"
        result = await self.nlp_processor.analyze_sentiment(text)
        event.sentiment = result
        return event
    
    async def enrich_entities(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add entity extraction enrichment"""
        text = f"{event.title} {event.description or ''}"
        entities = await self.nlp_processor.extract_entities(text)
        event.entities = entities
        return event
    
    async def enrich_summary(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add summary enrichment"""
        if event.content:
            text = event.content
        else:
            text = event.description or event.title

        summary = await self.nlp_processor.summarize(text)
        event.summary = summary
        return event
    
    async def enrich_keywords(self, event: ProcessedEvent) -> ProcessedEvent:
        """Add keyword extraction enrichment"""
        text = f"{event.title} {event.description or ''}"
        keywords = await self.nlp_processor.extract_keywords(text)
        event.keywords = keywords
        return event
