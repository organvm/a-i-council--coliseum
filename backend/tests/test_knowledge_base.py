
import unittest
from datetime import datetime, timedelta
from backend.ai_agents.knowledge_base import KnowledgeBase, KnowledgeEntry

class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.kb = KnowledgeBase()

    def test_get_recent_entries_empty(self):
        """Test getting recent entries from an empty knowledge base."""
        entries = self.kb.get_recent_entries(limit=10)
        self.assertEqual(entries, [])

    def test_get_recent_entries_limit(self):
        """Test that the limit parameter is respected."""
        for i in range(20):
            self.kb.add_entry(f"Content {i}", "test")

        entries = self.kb.get_recent_entries(limit=5)
        self.assertEqual(len(entries), 5)

    def test_get_recent_entries_sorting(self):
        """Test that entries are correctly sorted by created_at desc."""
        # Create entries with specific timestamps
        entry1 = self.kb.add_entry("Oldest", "test")
        entry1.created_at = datetime.utcnow() - timedelta(hours=10)

        entry2 = self.kb.add_entry("Newest", "test")
        entry2.created_at = datetime.utcnow()

        entry3 = self.kb.add_entry("Middle", "test")
        entry3.created_at = datetime.utcnow() - timedelta(hours=5)

        entries = self.kb.get_recent_entries(limit=3)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].content, "Newest")
        self.assertEqual(entries[1].content, "Middle")
        self.assertEqual(entries[2].content, "Oldest")

    def test_get_recent_entries_limit_larger_than_size(self):
        """Test getting more entries than exist."""
        self.kb.add_entry("One", "test")
        self.kb.add_entry("Two", "test")

        entries = self.kb.get_recent_entries(limit=10)
        self.assertEqual(len(entries), 2)

if __name__ == '__main__':
    unittest.main()
