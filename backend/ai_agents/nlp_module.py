"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

# Configure logging
logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Natural Language Processing module for agent text understanding
    and generation.
    """
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found. NLP features will use placeholders.")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Returns:
            Dict with sentiment label and score
        """
        # Placeholder for actual sentiment analysis
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "confidence": 0.8
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Returns:
            List of entities with type and text
        """
        # Placeholder for actual entity extraction
        return []
    
    async def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Summarize text to specified length
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        # Placeholder for actual summarization
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def _classify_topic_heuristic(self, text: str) -> Dict[str, float]:
        """
        Heuristic-based topic classification using keywords.
        Used as a fallback when LLM is unavailable.
        """
        text_lower = text.lower()

        # Keyword dictionaries for different topics
        topics_keywords = {
            "politics": [
                "government", "president", "election", "vote", "policy", "congress",
                "senate", "law", "democrat", "republican", "campaign", "candidate",
                "minister", "parliament", "diplomacy", "treaty"
            ],
            "technology": [
                "software", "hardware", "computer", "ai", "artificial intelligence",
                "internet", "cyber", "digital", "app", "code", "programming",
                "data", "algorithm", "network", "server", "cloud", "blockchain",
                "crypto", "iphone", "android", "microsoft", "google", "apple",
                "python", "javascript", "linux", "database"
            ],
            "economy": [
                "market", "stock", "trade", "finance", "bank", "money", "currency",
                "inflation", "gdp", "recession", "invest", "economy", "fiscal",
                "tax", "budget", "business", "corporate", "revenue", "profit"
            ],
            "science": [
                "research", "study", "experiment", "discovery", "space", "nasa",
                "biology", "physics", "chemistry", "medical", "health", "virus",
                "vaccine", "climate", "environment", "energy", "scientist"
            ],
            "sports": [
                "game", "match", "team", "player", "score", "win", "loss",
                "championship", "tournament", "league", "football", "basketball",
                "soccer", "baseball", "tennis", "olympics", "athlete"
            ],
            "entertainment": [
                "movie", "film", "music", "song", "album", "artist", "actor",
                "actress", "celebrity", "concert", "show", "series", "netflix",
                "cinema", "hollywood", "award", "star"
            ]
        }

        scores = {topic: 0.0 for topic in topics_keywords}
        total_matches = 0

        # Count keyword matches
        for topic, keywords in topics_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Simple presence check, could be improved with frequency count
                    # Adding a small weight for each occurrence
                    count = text_lower.count(keyword)
                    scores[topic] += count
                    total_matches += count

        # Normalize scores
        if total_matches > 0:
            normalized_scores = {
                topic: round(score / total_matches, 2)
                for topic, score in scores.items()
                if score > 0
            }
            # Ensure we have at least "general" if everything is very low confidence
            # But here we filter out 0 scores.

            # If the top score is very low, add general?
            # For now, just return what we found.
            if not normalized_scores:
                 return {"general": 1.0}

            return normalized_scores
        else:
            return {"general": 1.0}

    async def classify_topic(self, text: str) -> Dict[str, float]:
        """
        Classify text into topic categories
        
        Returns:
            Dict of topics with confidence scores
        """
        if not self.client:
            return self._classify_topic_heuristic(text)

        prompt = f"""
        Classify the following text into relevant topics (e.g., politics, technology, economy, entertainment, sports, science).
        Return a JSON object where keys are topics and values are confidence scores between 0 and 1.

        Text: {text}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies text into topics. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": 1.0}
        except Exception as e:
            logger.error(f"Error classifying topic: {e}")
            return self._classify_topic_heuristic(text)
    
    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract key terms from text
        
        Args:
            text: Input text
            top_k: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Placeholder for keyword extraction
        words = text.lower().split()
        return list(set(words[:top_k]))
