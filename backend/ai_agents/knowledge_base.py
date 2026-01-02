"""
Knowledge Base Module

Provides structured knowledge storage and retrieval for AI agents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class KnowledgeEntry:
    """Single entry in the knowledge base"""
    
    def __init__(self, content: str, category: str, metadata: Optional[Dict] = None):
        self.entry_id = str(uuid.uuid4())
        self.content = content
        self.category = category
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.access_count = 0


class KnowledgeBase:
    """
    Knowledge base system for storing and retrieving information
    """
    
    def __init__(self):
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def add_entry(self, content: str, category: str, 
                  metadata: Optional[Dict] = None) -> KnowledgeEntry:
        """Add a new knowledge entry"""
        entry = KnowledgeEntry(content, category, metadata)
        self.entries[entry.entry_id] = entry
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(entry.entry_id)
        
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Retrieve a knowledge entry by ID"""
        entry = self.entries.get(entry_id)
        if entry:
            entry.access_count += 1
        return entry
    
    def search_by_category(self, category: str) -> List[KnowledgeEntry]:
        """Search entries by category"""
        entry_ids = self.categories.get(category, [])
        return [self.entries[eid] for eid in entry_ids if eid in self.entries]
    
    def search_by_content(self, query: str) -> List[KnowledgeEntry]:
        """Search entries by content (simple substring match)"""
        query_lower = query.lower()
        return [
            entry for entry in self.entries.values()
            if query_lower in entry.content.lower()
        ]
    
    def get_recent_entries(self, limit: int = 10) -> List[KnowledgeEntry]:
        """Get most recent entries"""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.created_at,
            reverse=True
        )
        return sorted_entries[:limit]
    
    def get_popular_entries(self, limit: int = 10) -> List[KnowledgeEntry]:
        """Get most accessed entries"""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.access_count,
            reverse=True
        )
        return sorted_entries[:limit]
