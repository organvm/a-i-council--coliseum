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
            logger.warning("OPENAI_API_KEY not found. NLP features will use local fallbacks.")

        self._classifier = None
    
    def _get_local_classifier(self):
        """Lazily load local zero-shot classifier"""
        if self._classifier is None:
            try:
                from transformers import pipeline
                # Use a smaller/faster model for local inference
                logger.info("Loading local classification model...")
                self._classifier = pipeline(
                    "zero-shot-classification",
                    model="valhalla/distilbart-mnli-12-1"
                )
                logger.info("Local classification model loaded.")
            except Exception as e:
                logger.error(f"Failed to load local classifier: {e}")
                return None
        return self._classifier

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
    
    def _keyword_classify(self, text: str) -> Dict[str, float]:
        """Fallback keyword-based classification"""
        text_lower = text.lower()
        scores = {
            "politics": 0.1,
            "technology": 0.1,
            "economy": 0.1,
            "entertainment": 0.1,
            "sports": 0.1,
            "science": 0.1,
            "general": 0.4
        }

        keywords = {
            "politics": ["government", "election", "policy", "president", "vote", "law", "tax"],
            "technology": ["ai", "software", "computer", "digital", "tech", "app", "model", "data"],
            "economy": ["market", "stock", "trade", "finance", "money", "business", "price"],
            "entertainment": ["movie", "music", "game", "celebrity", "film", "art"],
            "sports": ["game", "score", "team", "player", "match", "win", "loss"],
            "science": ["research", "study", "space", "health", "biology", "physics"]
        }

        for topic, words in keywords.items():
            for word in words:
                if word in text_lower:
                    scores[topic] += 0.3

        # Normalize
        total = sum(scores.values())
        if total > 0:
            return {k: v / total for k, v in scores.items()}
        return scores

    async def classify_topic(self, text: str) -> Dict[str, float]:
        """
        Classify text into topic categories
        
        Returns:
            Dict of topics with confidence scores
        """
        # 1. Try OpenAI
        if self.client:
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
            except Exception as e:
                logger.error(f"Error classifying topic with OpenAI: {e}")
                # Fall through to local methods

        # 2. Try Local Transformers Model
        classifier = self._get_local_classifier()
        if classifier:
            try:
                candidate_labels = ["politics", "technology", "economy", "entertainment", "sports", "science", "general"]
                result = classifier(text, candidate_labels)
                # result is {'sequence': ..., 'labels': [...], 'scores': [...]}
                return dict(zip(result['labels'], result['scores']))
            except Exception as e:
                logger.error(f"Error classifying topic with local model: {e}")

        # 3. Fallback to keywords
        return self._keyword_classify(text)
    
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
