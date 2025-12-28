"""
Memory Manager Module

Manages agent memory including short-term and long-term storage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import heapq


class MemoryEntry:
    """Single memory entry"""
    
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        self.key = key
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = (
            datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        )
        self.access_count = 0
        self.last_accessed = datetime.utcnow()


class MemoryManager:
    """
    Memory management system for AI agents
    Supports short-term and long-term memory with TTL
    """
    
    def __init__(self, max_short_term: int = 100, max_long_term: int = 1000):
        self.short_term: deque = deque(maxlen=max_short_term)
        self.long_term: Dict[str, MemoryEntry] = {}
        self.max_long_term = max_long_term
        # Min-heap storing (expires_at, key) tuples for O(1) expiration check
        self.expiry_heap: List = []
    
    def add_short_term(self, value: Any) -> None:
        """Add to short-term memory (FIFO queue)"""
        self.short_term.append({
            "value": value,
            "timestamp": datetime.utcnow()
        })
    
    def get_short_term(self, limit: Optional[int] = None) -> List[Any]:
        """Get recent short-term memories"""
        memories = list(self.short_term)
        if limit:
            memories = memories[-limit:]
        return [m["value"] for m in memories]
    
    def add_long_term(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Add to long-term memory with optional TTL"""
        # Clean expired entries
        self._clean_expired()
        
        # Add new entry
        entry = MemoryEntry(key, value, ttl)
        self.long_term[key] = entry
        
        if entry.expires_at:
            heapq.heappush(self.expiry_heap, (entry.expires_at, key))

        # Enforce size limit
        if len(self.long_term) > self.max_long_term:
            self._evict_lru()
    
    def get_long_term(self, key: str) -> Optional[Any]:
        """Get from long-term memory"""
        self._clean_expired()
        
        entry = self.long_term.get(key)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            return entry.value
        return None
    
    def remove_long_term(self, key: str) -> None:
        """Remove from long-term memory"""
        if key in self.long_term:
            del self.long_term[key]
    
    def clear_short_term(self) -> None:
        """Clear short-term memory"""
        self.short_term.clear()
    
    def clear_long_term(self) -> None:
        """Clear long-term memory"""
        self.long_term.clear()
        self.expiry_heap.clear()
    
    def clear_all(self) -> None:
        """Clear all memory"""
        self.clear_short_term()
        self.clear_long_term()
    
    def _clean_expired(self) -> None:
        """Remove expired entries using min-heap for O(1) check"""
        if not self.expiry_heap:
            return

        now = datetime.utcnow()

        # Peek at the soonest expiring item
        while self.expiry_heap and self.expiry_heap[0][0] < now:
            expires_at, key = heapq.heappop(self.expiry_heap)

            # Lazy deletion check: verify key exists and expiration matches
            # This handles cases where key was updated/removed or updated with new TTL
            if key in self.long_term:
                entry = self.long_term[key]
                if entry.expires_at == expires_at:
                    del self.long_term[key]
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.long_term:
            return
        
        lru_key = min(
            self.long_term.items(),
            key=lambda item: item[1].last_accessed
        )[0]
        del self.long_term[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "long_term_max": self.max_long_term
        }
